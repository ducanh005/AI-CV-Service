from app.models.ai_score import AIScore
from app.models.application import Application
from app.models.attendance import Attendance
from app.models.company import Company
from app.models.contract import Contract
from app.models.contract_document import ContractDocument
from app.models.contract_status_history import ContractStatusHistory
from app.models.cv import CV
from app.models.department import Department
from app.models.employee import Employee
from app.models.interview import Interview
from app.models.onboarding import (
    OnboardingAssignment,
    OnboardingTask,
    OnboardingTaskProgress,
    OnboardingTemplate,
)
from app.models.job import Job
from app.models.role import Role
from app.models.scoring_job import ScoringJob
from app.models.scoring_job_item import ScoringJobItem
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User

__all__ = [
    "AIScore",
    "Application",
    "Attendance",
    "Company",
    "Contract",
    "ContractDocument",
    "ContractStatusHistory",
    "CV",
    "Department",
    "Employee",
    "Interview",
    "OnboardingAssignment",
    "OnboardingTask",
    "OnboardingTaskProgress",
    "OnboardingTemplate",
    "Job",
    "Role",
    "ScoringJob",
    "ScoringJobItem",
    "TokenBlacklist",
    "User",
]
