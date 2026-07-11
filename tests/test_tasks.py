from sqlmodel import create_engine
import app.db as db
from app.models import Campaign, Recipiet
from app.tasks import check_campaigns_need_to_mark_complete

mock_db_engine = create_engine("sqlite:///:memory:")


def test_check_campaigns_need_to_mark_complete(monkeypatch, session, redis):

    def get_mock_redis():
        return redis

    def mock_session():
        return session

    c = Campaign(id=0, name="test", content="", state=1, schedule_at=None)

    rec_num = 10

    redis.set(f"campaign:{c.id}", rec_num)

    monkeypatch.setattr(db, "get_session", mock_session)
    monkeypatch.setattr(db, "get_redis", get_mock_redis)
    c = Campaign(name="test", content="", state=1, schedule_at=None)

    session.add(c)
    session.commit()
    for _ in range(rec_num):
        r = Recipiet(campaign_id=c.id, email="")
        session.add(r)
    session.commit()

    r = check_campaigns_need_to_mark_complete.apply_async()
    assert r.successful()

    uc = session.get(Campaign, c.id)
    assert uc.state == 2
