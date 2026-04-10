from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import OnboardingStatus, TaskPriority


# ── Template ──────────────────────────────────────────
class OnboardingTaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    order: int = 0


class OnboardingTemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    tasks: list[OnboardingTaskInput] = []


class OnboardingTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    tasks: list[OnboardingTaskInput] | None = None


class OnboardingTaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    priority: str
    order: int


class OnboardingTemplateResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    company_id: int
    task_count: int = 0
    tasks: list[OnboardingTaskResponse] = []
    created_at: datetime | None = None


# ── Assignment ────────────────────────────────────────
class OnboardingAssignmentCreateRequest(BaseModel):
    employee_id: int
    template_id: int
    due_date: date | None = None
    notes: str | None = None


class OnboardingAssignmentUpdateRequest(BaseModel):
    due_date: date | None = None
    notes: str | None = None


class TaskProgressResponse(BaseModel):
    id: int
    task_id: int
    task_title: str = ""
    task_description: str | None = None
    task_priority: str = "medium"
    task_order: int = 0
    is_completed: bool = False
    completed_at: datetime | None = None
    note: str | None = None


class OnboardingAssignmentResponse(BaseModel):
    id: int
    status: str
    due_date: date | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    employee_id: int
    employee_name: str | None = None
    employee_code: str | None = None
    employee_position: str | None = None
    employee_department: str | None = None
    employee_contract_type: str | None = None
    template_id: int
    template_name: str | None = None
    assigned_by_name: str | None = None
    company_id: int
    total_tasks: int = 0
    completed_tasks: int = 0
    task_progress: list[TaskProgressResponse] = []
    created_at: datetime | None = None


# ── Task progress toggle ──────────────────────────────
class TaskToggleRequest(BaseModel):
    note: str | None = None
