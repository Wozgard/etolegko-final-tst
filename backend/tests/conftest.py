from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import Base
from app.models.campaign_offer import CampaignOfferRow


@pytest.fixture(autouse=True)
def _clear_campaign_offers() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        db.query(CampaignOfferRow).delete()
        db.commit()
    finally:
        db.close()