from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    HR = "hr"
    ADMIN = "admin"


class JobStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
