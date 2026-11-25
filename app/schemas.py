"""Schémas Pydantic : ce que l'API reçoit et renvoie (validation automatique)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Priority, Status


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 (type de jeton, pas un secret)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    priority: Priority = Priority.medium
    due_date: date | None = None


class TaskUpdate(BaseModel):
    """Mise à jour partielle : seuls les champs envoyés sont modifiés."""

    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: Status | None = None
    priority: Priority | None = None
    due_date: date | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    status: Status
    priority: Priority
    due_date: date | None
    created_at: datetime
    updated_at: datetime


class TaskPage(BaseModel):
    items: list[TaskOut]
    total: int
    limit: int
    offset: int


class TaskStats(BaseModel):
    total: int
    todo: int
    doing: int
    done: int
    overdue: int
    completion_rate: float
