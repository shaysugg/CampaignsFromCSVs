from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from functools import cache
from pika.adapters.blocking_connection import BlockingChannel
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, col, create_engine, select
from app.db import SessionDeps, create_tables, get_redis
from app.tasks import process_file, c, process_csv
import redis

from app.models import Campaign, Recipiet


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    get_redis().close()


app = FastAPI(lifespan=lifespan)


@app.post("/files")
async def create_file(file: Annotated[UploadFile, File()]):

    if not file.filename:
        raise HTTPException(400, detail="file doesn't have name")
    file_name_parts = file.filename.split(".")
    if len(file_name_parts) != 2:
        raise HTTPException(400, detail="invalid file name")
    if file_name_parts[1].lower() != "pdf":
        raise HTTPException(400, detail="file is not pdf")

    dest_path = f"./uploads/{file.filename}"

    with open(dest_path, mode="wb") as dest_file:
        dest_file.write(file.file.read())

    r = process_file.delay(dest_path)
    id = r.task_id
    res = {"name": dest_file.name, "process_status_id": id}
    return JSONResponse(content=res)


@app.get("/status/{task_id}")
def task_status(task_id: str):
    from celery.result import AsyncResult

    r: AsyncResult = c.AsyncResult(task_id)

    return JSONResponse(content={"id": task_id, "status": r.state})


class PDFAnalyzOut(BaseModel):
    file_path: str
    num_of_pages: int
    word_count: int


@app.get("/result/{task_id}")
def task_result(task_id: str):
    from celery.result import AsyncResult

    r: AsyncResult = c.AsyncResult(task_id)
    if not r.ready():
        HTTPException(400, "task hasn't finished yet")
    try:
        analyze: dict = r.get(timeout=0)
        return PDFAnalyzOut(**analyze)
    except Exception as e:
        print(e)
        raise HTTPException(400)


# create campaigns


class CreateCampaign(BaseModel):
    name: str
    content: str
    schedule_at: datetime | None


@app.post("/campaign")
def create_campaign(campaign: CreateCampaign, session: SessionDeps):
    c = Campaign(**campaign.model_dump())
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


# schedule campagin, save on db, let celery daemon check it later
class UpdateCampaign(BaseModel):
    name: str | None = Field(default=None)
    content: str | None = Field(default=None)
    state: int | None = Field(default=None)
    schedule_at: datetime | None = Field(default=None)


@app.patch("/campaign/{campaign_id}")
def update_campaign(campaign_id: int, campaign: UpdateCampaign, session: SessionDeps):
    c = session.get(Campaign, campaign_id)
    if not c:
        raise HTTPException(404)
    u = campaign.model_dump(exclude_unset=True)
    c.sqlmodel_update(u)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@app.delete("/campaign/{campaign_id}")
def delete_campaign(campaign_id: int, session: SessionDeps):
    c = session.get(Campaign, campaign_id)
    if not c:
        raise HTTPException(404)
    session.delete(c)
    session.commit()
    return JSONResponse("deleted")


@app.get("/campaign")
def get_campaigns(session: SessionDeps):
    campaigns = session.exec(select(Campaign).order_by(col(Campaign.id))).all()
    return campaigns


# upload a csv for campaign recipts (possible use of celery)


@app.post("/campaign/{campaign_id}/recipiets")
def create_recipiets(campaign_id: int, file: UploadFile):
    if not file.filename:
        raise HTTPException(400)
    components = file.filename.split(".")
    if len(components) != 2:
        raise HTTPException(400)
    ext = components[1]
    if ext.lower() != "csv":
        raise HTTPException(400)

    dest_path = f"./csvs/{file.filename}"

    with open(dest_path, mode="wb") as dest_file:
        dest_file.write(file.file.read())

    r = process_csv.delay(dest_path, campaign_id)
    id = r.task_id
    res = {"name": dest_file.name, "process_status_id": id}
    return JSONResponse(content=res)


@app.get("/campaign/{campaign_id}/recipiets")
def get_campaigns_recipiets(campaign_id: int, session: SessionDeps):
    campaigns = session.exec(
        select(Recipiet)
        .where(Recipiet.campaign_id == campaign_id)
        .order_by(col(Recipiet.campaign_id))
    ).all()
    return campaigns
