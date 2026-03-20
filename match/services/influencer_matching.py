import ast
import traceback
from typing import Any, Dict, List

import aiohttp
import jsonpickle
from loguru import logger
from pydantic import BaseModel
from redis.asyncio import ConnectionPool

from match.ai_model.agent.influencer_matcher_agent.graph import InfluencerMatcherGraph
from match.config import Settings
from match.models.influencer_matcher import InfluencerMatcherResponse, InfuencerMatcherRequestInput
from match.processor.file_reader import read_file
from match.utils.post_to_api import post_campaign_result


class InfluencerMatcherService:
    def __init__(
        self,
        influencer_matcher_graph: InfluencerMatcherGraph,
        redis_pool: ConnectionPool,
        settings: Settings,
    ):
        self.influencer_matcher_graph = influencer_matcher_graph
        self.redis_pool = redis_pool
        self.settings = settings

    async def match_influencers(self, input_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Match influencers based on the input data.

        Args:
            input_data: List of campaign data dictionaries containing s3_pdf_link and optional campaign_id

        Returns:
            List of processed campaign results

        Raises:
            ValueError: If no influencer recommendations could be generated
        """
        results = []

        for input_item in input_data:
            try:
                result = await self._process_single_campaign(input_item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing campaign: {str(e)}")
                traceback.print_exc()

        return results

    async def _process_single_campaign(self, input_item: Dict) -> Dict[str, Any]:
        """Process a single campaign input and return the matching results."""
        request_input = InfuencerMatcherRequestInput.model_validate(input_item)

        # Read the PDF file
        requirements = await read_file(request_input.s3_pdf_links)

        # Get influencer recommendations
        response = await self.influencer_matcher_graph.invoke(
            requirements,
            request_input.description,
            request_input.brand_template,
            request_input.brand_id,
        )

        # Process and validate the response
        result = self._build_result_from_response(response, str(request_input.campaign_id))

        # Send result to webhook
        await self._send_result_to_webhook(result)

        return result

    def _build_result_from_response(self, response: Dict, campaign_id: str) -> Dict[str, Any]:
        """Build the result dictionary from the graph response."""
        # Process input metadata
        input_metadata = response.get("extracted_input_metadata", None)
        if isinstance(input_metadata, BaseModel):
            input_metadata = input_metadata.model_dump()

        # Get last generated plan
        plans = response.get("generate_plan", [])
        last_generated_plan = plans[-1] if plans else None

        # Get table division recommendation
        rec_table_division = response.get("rec_table_division", None)
        if isinstance(rec_table_division, BaseModel):
            rec_table_division = rec_table_division.model_dump()

        # Get plan summary
        rec_plan_summary = response.get("rec_plan_summary", None)

        # Process recommended influencers
        rec_influencer = response.get("rec_influencer", None)

        if rec_influencer:
            # Convert main_category from string to list
            processed_influencers = [
                {
                    **item,
                    "main_category": ast.literal_eval(str(item["main_category"])),
                    "id": str(item["id"]),
                    "unique_id": str(item["unique_id"]),
                }
                for item in rec_influencer
            ]
        else:
            processed_influencers = None
            error_msg = "No influencer recommendations found in the response"
            logger.warning(error_msg)

        # Build the result dictionary
        result = {
            "input_metadata": input_metadata,
            "recommend_plan": last_generated_plan,
            "rec_table_division": rec_table_division,
            "recommend_influencers": processed_influencers,
            "rec_plan_summary": rec_plan_summary,
            "debug_info": {
                "state_of_graph": jsonpickle.encode(response),
            },
            "campaign_id": str(campaign_id),
        }

        return result

    async def _send_result_to_webhook(self, result: Dict) -> None:
        """Send the result to the webhook endpoint."""

        if self.settings.campaign_webhook_url is None:
            logger.warning("Campaign webhook URL is not set. Skipping webhook notification.")
            return
        pydantic_result = InfluencerMatcherResponse(**result)
        logger.info(f"Sending result to webhook for campaign: {result['campaign_id']}")

        try:
            api_response = await post_campaign_result(pydantic_result.model_dump(), self.settings.campaign_webhook_url)
            logger.success(f"Successfully sent result to webhook: {api_response}")
        except aiohttp.ClientResponseError as e:
            logger.error(f"Webhook request failed: {e.status} {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error sending to webhook: {str(e)}")
