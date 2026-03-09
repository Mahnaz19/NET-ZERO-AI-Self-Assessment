import datetime as dt

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .db import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    postcode = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("business_name", "postcode", name="uq_business_name_postcode"),
    )

    submissions = relationship("Submission", back_populates="business")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow)

    business_name = Column(String, nullable=True)
    postcode = Column(String, nullable=True)

    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    business = relationship("Business", back_populates="submissions")

    raw_answers = Column(JSONB, nullable=False)

    status = Column(String, nullable=False, default="received")

    report_json = Column(JSONB, nullable=True)
