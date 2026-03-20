import uuid

from pydantic import BaseModel, Field


class RunServiceCommand(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trigger_by: str = Field(default="api")
    service: str
    func: str
    params: dict = {}

    @property
    def service_name(self) -> str:
        """Ensures the service name follows the correct format by appending 'Service' if missing
        and prepending 'match.services.' if not already present."""
        formatted_service = self.service
        if not formatted_service.endswith("Service"):
            formatted_service += "Service"
        if not formatted_service.startswith("match.services."):
            formatted_service = f"match.services.{formatted_service}"
        return formatted_service
