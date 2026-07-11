from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import col, select

from app.db import SessionDeps
from app.models import Campaign, Recipiet
from app.schemas import CreateCampaign, UpdateCampaign
from app.tasks import process_csv

router = APIRouter(prefix="/campaign")


@router.post("/campaign")
def create_campaign(campaign: CreateCampaign, session: SessionDeps):
    c = Campaign(**campaign.model_dump())
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


# schedule campagin, save on db, let celery daemon check it later


@router.patch("/campaign/{campaign_id}")
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


@router.delete("/campaign/{campaign_id}")
def delete_campaign(campaign_id: int, session: SessionDeps):
    c = session.get(Campaign, campaign_id)
    if not c:
        raise HTTPException(404)
    session.delete(c)
    session.commit()
    return JSONResponse("deleted")


@router.get("/campaign")
def get_campaigns(session: SessionDeps):
    campaigns = session.exec(select(Campaign).order_by(col(Campaign.id))).all()
    return campaigns


# upload a csv for campaign recipts (possible use of celery)


@router.post("/campaign/{campaign_id}/recipiets")
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


@router.get("/campaign/{campaign_id}/recipiets")
def get_campaigns_recipiets(campaign_id: int, session: SessionDeps):
    campaigns = session.exec(
        select(Recipiet)
        .where(Recipiet.campaign_id == campaign_id)
        .order_by(col(Recipiet.campaign_id))
    ).all()
    return campaigns
