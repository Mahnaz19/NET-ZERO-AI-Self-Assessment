from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class SubmissionCreate(BaseModel):
    business_name: Optional[str] = None
    postcode: Optional[str] = None
    answers: Dict[str, Any]


class SubmissionOut(BaseModel):
    id: int
    business_name: Optional[str] = None
    postcode: Optional[str] = None
    raw_answers: Dict[str, Any]
    status: str
    created_at: datetime
    report_json: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class ReportOut(BaseModel):
    id: int
    report_json: Optional[Dict[str, Any]] = None

