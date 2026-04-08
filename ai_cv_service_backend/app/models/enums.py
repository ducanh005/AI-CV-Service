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
