from datetime import datetime

from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    name: str
    content: str
    state: int = Field(default=0)
    schedule_at: datetime | None


class Recipiet(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    campaign_id: int = Field(index=True)
    email: str
