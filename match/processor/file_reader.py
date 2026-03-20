import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import aiohttp
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document
from loguru import logger


class FileDownloader:
    """Handles downloading files from URLs to temporary files."""

    @staticmethod
    async def download_to_temp(url: str, suffix: str = "") -> tuple[str, str]:
        """Download a file from URL to a temporary file and return the path and detected mime type."""
        temp_file: Optional[str] = None
        try:
            logger.info(f"Downloading file from URL: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_msg = f"Failed to download file. Status code: {response.status}"
                        raise ValueError(error_msg)

                    # Get content type from headers
                    content_type = response.headers.get("content-type", "").lower()

                    # Create a temporary file with appropriate extension
                    fd, temp_file = tempfile.mkstemp(suffix=suffix)
                    os.close(fd)  # Close the file descriptor

                    # Write the content to the temporary file
                    content = await response.read()
                    with open(temp_file, "wb") as f:
                        f.write(content)

                    logger.info(f"File downloaded to temporary file: {temp_file}")
                    return temp_file, content_type
        except Exception as e:
            # Clean up on error
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            logger.error(f"Error downloading file: {e}")
            raise


class FileReader(ABC):
    """Abstract base class for file readers."""

    @abstractmethod
    async def read_file(self, file_path: str) -> str:
        """Read content from a file."""
        pass

    @staticmethod
    def is_url(path: str) -> bool:
        """Check if the path is a URL."""
        return path.startswith("http://") or path.startswith("https://")


class PDFReader(FileReader):
    """PDF file reader implementation."""

    async def read_file(self, file_path: str) -> str:
        try:
            loader = PyPDFLoader(file_path)
            pages = []
            async for page in loader.alazy_load():
                pages.append(page)

            # Extract content from pages
            content = []
            for page in pages:
                content.append(page.page_content)
                content.append("\n")

            return "\n".join(content)
        except Exception as e:
            logger.error(f"Error reading PDF file: {e}")
            return ""


class MarkdownReader(FileReader):
    """Markdown file reader implementation."""

    async def read_file(self, file_path: str) -> str:
        try:
            loader = UnstructuredMarkdownLoader(file_path)
            data = loader.load()

            if not data:
                logger.warning(f"No content found in markdown file: {file_path}")
                return ""

            # Combine all documents if there are multiple
            content = []
            for doc in data:
                if isinstance(doc, Document):
                    content.append(doc.page_content)

            return "\n\n".join(content)
        except Exception as e:
            logger.error(f"Error reading markdown file: {e}")
            return ""


class FileReaderFactory:
    """Factory for creating appropriate file readers."""

    _readers = {
        ".pdf": PDFReader,
        ".md": MarkdownReader,
        ".markdown": MarkdownReader,
    }

    _mime_type_mapping = {
        "application/pdf": ".pdf",
        "text/markdown": ".md",
        "text/x-markdown": ".md",
    }

    @classmethod
    def get_reader(cls, file_path: str) -> FileReader:
        """Get appropriate reader based on file extension."""
        file_ext = Path(file_path).suffix.lower()

        if file_ext not in cls._readers:
            supported_formats = ", ".join(cls._readers.keys())
            msg = f"Unsupported file format: {file_ext}. Supported formats: {supported_formats}"
            raise ValueError(msg)

        return cls._readers[file_ext]()  # type: ignore

    @classmethod
    def get_reader_by_content_type(cls, content_type: str) -> FileReader:
        """Get appropriate reader based on content type."""
        file_ext = cls._mime_type_mapping.get(content_type.split(";")[0].strip())

        if not file_ext:
            supported_types = ", ".join(cls._mime_type_mapping.keys())
            msg = f"Unsupported content type: {content_type}. Supported types: {supported_types}"
            raise ValueError(msg)

        return cls._readers[file_ext]()  # type: ignore

    @classmethod
    def get_download_suffix(cls, file_path: str) -> str:
        """Get appropriate file suffix for downloading."""
        file_ext = Path(file_path).suffix.lower()
        return file_ext if file_ext in cls._readers else ""

    @classmethod
    def detect_file_type(cls, file_path: str, content_type: str = "") -> str:
        """Detect file type from extension or content type."""
        # First try file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext in cls._readers:
            return file_ext

        # If no extension or unsupported, try content type
        if content_type:
            detected_ext = cls._mime_type_mapping.get(content_type.split(";")[0].strip())
            if detected_ext:
                return detected_ext

        # Try to detect from file content (simple magic number check)
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                if header.startswith(b"%PDF"):
                    return ".pdf"
        except Exception:
            pass

        msg = f"Cannot detect file type for: {file_path}"
        raise ValueError(msg)


async def read_file(file_path: Union[str, List[str]]) -> str:  # noqa: C901
    """
    Read content from file(s). Supports both local files and URLs.

    Args:
        file_path: Single file path/URL or list of file paths/URLs

    Returns:
        String content of the file(s)

    Raises:
        ValueError: If no content is extracted or unsupported file format
    """

    async def get_single_file_content(path: str) -> str:
        temp_file: Optional[str] = None
        try:
            actual_path = path
            content_type = ""

            # Download if URL
            if FileReader.is_url(path):
                temp_file, content_type = await FileDownloader.download_to_temp(path)
                actual_path = temp_file

            # Detect file type and get appropriate reader
            try:
                file_ext = FileReaderFactory.detect_file_type(actual_path, content_type)
                # Update temp file with correct extension if needed
                if temp_file and not actual_path.endswith(file_ext):
                    new_temp_file = actual_path + file_ext
                    os.rename(actual_path, new_temp_file)
                    actual_path = new_temp_file
                    temp_file = new_temp_file

                reader = FileReaderFactory.get_reader(actual_path)
            except ValueError as e:
                # Try content type based reader if extension detection fails
                if content_type:
                    try:
                        reader = FileReaderFactory.get_reader_by_content_type(content_type)
                    except ValueError:
                        raise e
                else:
                    raise e

            content = await reader.read_file(actual_path)
            return content

        except Exception as e:
            logger.error(f"Error processing file {path}: {e}")
            return ""
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
                logger.debug(f"Deleted temporary file: {temp_file}")

    if isinstance(file_path, list):
        error_cnt = 0
        tasks = [get_single_file_content(path) for path in file_path]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result == "":
                error_cnt += 1

        if error_cnt == len(file_path):
            error_msg = "No content extracted from any of the files."
            raise ValueError(error_msg)

        return "\n\n".join(filter(None, results))  # Filter out empty results
    else:
        result = await get_single_file_content(file_path)
        if result == "":
            error_msg = f"No content extracted from the file: {file_path}"
            raise ValueError(error_msg)
        return result


# Backward compatibility
async def read_pdf(file_path: Union[str, List[str]]) -> str:
    """Deprecated: Use read_file() instead."""
    logger.warning("read_pdf() is deprecated. Use read_file() instead.")
    return await read_file(file_path)
