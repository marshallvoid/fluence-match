from pathlib import Path

from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.post("/delete_table_cache")
def delete_table_cache() -> dict:
    """
    Influencer Matcher API endpoint that deletes all CSV cache files under data_for_ai.
    """
    cache_dir = Path("data_for_ai")
    if not cache_dir.exists() or not cache_dir.is_dir():
        raise HTTPException(status_code=404, detail="Cache directory not found")

    deleted_files = []
    for csv_file in cache_dir.glob("*.csv"):
        try:
            csv_file.unlink()
            deleted_files.append(csv_file.name)
        except Exception as e:
            logger.error(f"Failed to delete {csv_file.name}: {e}")
            continue

    return {"status": "success", "deleted_files": deleted_files}
