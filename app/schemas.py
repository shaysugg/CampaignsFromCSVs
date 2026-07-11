from datetime import datetime

from pydantic import BaseModel, Field


class CreateCampaign(BaseModel):
    name: str
    content: str
    schedule_at: datetime | None = Field(default=None)


class UpdateCampaign(BaseModel):
    name: str | None = Field(default=None)
    content: str | None = Field(default=None)
    state: int | None = Field(default=None)
    schedule_at: datetime | None = Field(default=None)
