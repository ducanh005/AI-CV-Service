from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    HR = "hr"
    ADMIN = "admin"


class UserGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class JobStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class InterviewMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class InterviewResultStatus(str, Enum):
    SCHEDULED = "scheduled"
    SUCCESS = "success"
    FAILED = "failed"


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    RESIGNED = "resigned"
    ON_LEAVE = "on_leave"


class ContractType(str, Enum):
    PROBATION = "probation"
    PERMANENT = "permanent"
    TEMPORARY = "temporary"


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ContractDocumentType(str, Enum):
    CONTRACT = "contract"
    APPENDIX = "appendix"
    AMENDMENT = "amendment"
    OTHER = "other"


class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"



