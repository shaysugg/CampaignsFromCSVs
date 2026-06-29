from datetime import datetime, timezone
from functools import cache
from time import sleep

from celery import Celery, chain
import redis
from sqlmodel import Session, col, select, func
from .db import db_engine, get_redis, get_session
from .models import Campaign, Recipiet
import logging
import csv

c = Celery(config_source="app.celeryconfig")


@c.on_after_configure.connect
def setup_tasks(sender: Celery, **kwargs):

    sender.add_periodic_task(
        10,
        check_campaigns_need_to_start.s(),
        name="check_campaigns_need_to_start",
    )

    sender.add_periodic_task(
        10,
        check_campaigns_need_to_mark_complete.s(),
        name="check_campaigns_need_to_mark_complete",
    )


@c.task
def process_file(file_path: str):
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    word_count = 0
    for p in reader.pages:
        text = p.extract_text()
        word_count += len(text.split(" "))

        return {
            "file_path": file_path,
            "num_of_pages": len(reader.pages),
            "word_count": word_count,
        }


# read through csv, save on db
@c.task
def process_csv(path: str, campaign_id: int):
    with open(path, mode="r") as file:
        reader = csv.reader(file)
        with get_session() as session:
            for row in reader:
                r = Recipiet(campaign_id=campaign_id, email=row[1])
                session.add(r)
            session.commit()


# check campaigns that need to be marked as complete
@c.task
def check_campaigns_need_to_mark_complete():
    redis = get_redis()
    with get_session() as session:
        stm = select(Campaign).where(Campaign.state == 1)
        campaigns = session.exec(stm).all()

        updated = False
        for c in campaigns:
            recipiet_count_stm = select(func.count(col(Recipiet.id))).where(
                Recipiet.campaign_id == c.id
            )
            recipiet_count = session.exec(recipiet_count_stm).first() or 0
            sent = redis.get(f"campaign:{c.id}")
            print(int(sent))
            if recipiet_count >= int(sent):
                c.state = 2
                session.add(c)
                updated = True
        if updated:
            session.commit()


# check campaigns that needs to be running
# select db where need to be sent
# schedul sending tasks
@c.task
def check_campaigns_need_to_start():
    with get_session() as session:
        stm = (
            select(Campaign)
            .where(Campaign.schedule_at < datetime.now(timezone.utc))
            .where(Campaign.state == 0)
        )
        campaigns = session.exec(stm).all()
        for c in campaigns:
            start_campaign.delay(c.id)


# send campaign task(campaign id)
# get recipienrts
# call send
@c.task
def start_campaign(campaign_id: int):
    redis = get_redis()
    redis.set(f"campaign:{campaign_id}", 0)
    with get_session() as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            return  # todo error handle
        campaign.state = 1
        session.add(campaign)
        session.commit()
        stm = select(Recipiet).where(Recipiet.campaign_id == campaign_id)
        recs = session.exec(stm).all()
        for r in recs:
            send_email.delay(r.email, campaign.content, campaign.id)


# sending email to one recipie task
# save result to redis (total, sent, failed)
@cache
def logger() -> logging.Logger:
    l = logging.getLogger("emails")
    file_handler = logging.FileHandler("emails.log", mode="a", encoding="utf-8")

    formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )
    file_handler.setFormatter(formatter)
    l.addHandler(file_handler)
    l.level = 10
    return l


# todo: retry
@c.task
def send_email(dest_email: str, content: str, campaign_id: int):
    # todo
    redis = get_redis()
    sleep(0.2)
    l = logger()
    l.info(f"sent email to {dest_email}")
    redis.incr(f"campaign:{campaign_id}")
    return True
