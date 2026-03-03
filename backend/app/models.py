import datetime as dt

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from .db import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow)
    business_name = Column(String, nullable=True)
    postcode = Column(String, nullable=True)

    # Raw questionnaire answers as submitted by the business owner.
    # We use Postgres JSONB for flexibility and indexing later.
    raw_answers = Column(JSONB, nullable=False)

    status = Column(String, nullable=False, default="received")

    # Stores the computed assessment/report payload once ready.
    report_json = Column(JSONB, nullable=True)

