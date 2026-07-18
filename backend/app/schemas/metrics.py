from datetime import date, datetime

from pydantic import BaseModel


class SiteOut(BaseModel):
    id: int
    key: str
    name: str

    model_config = {"from_attributes": True}


class SprintOut(BaseModel):
    id: int
    name: str
    state: str
    start_date: datetime | None
    end_date: datetime | None
    goal: str | None

    model_config = {"from_attributes": True}


class SprintSummaryOut(BaseModel):
    sprint: SprintOut
    status_counts: dict[str, int]


class ScopeChangeItem(BaseModel):
    issue_key: str
    summary: str
    changed_at: datetime


class SprintScopeChangesOut(BaseModel):
    added: list[ScopeChangeItem]
    removed: list[ScopeChangeItem]


class BurndownPointOut(BaseModel):
    day: date
    remaining_issues: int
    remaining_points: float


class VelocityPointOut(BaseModel):
    sprint_id: int
    sprint_name: str
    planned_points: float
    delivered_points: float


class PersonOut(BaseModel):
    id: int
    display_name: str
    email: str | None

    model_config = {"from_attributes": True}


class WorkloadItem(BaseModel):
    status_category: str
    count: int


class HighlightItem(BaseModel):
    issue_key: str
    summary: str
    resolved_at: datetime | None
