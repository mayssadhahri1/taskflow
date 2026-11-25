"""CRUD des tâches : chaque utilisateur ne voit et ne modifie que ses propres tâches."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Priority, Status, Task, User
from app.schemas import TaskCreate, TaskOut, TaskPage, TaskStats, TaskUpdate
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def get_owned_task(task_id: int, db: Session, user: User) -> Task:
    task = db.get(Task, task_id)
    # 404 aussi quand la tâche appartient à quelqu'un d'autre : on ne révèle pas son existence
    if task is None or task.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tâche introuvable")
    return task


@router.get("", response_model=TaskPage)
def list_tasks(
    status_filter: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    q: str | None = Query(default=None, max_length=100, description="Recherche dans le titre"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskPage:
    query = select(Task).where(Task.owner_id == user.id)
    if status_filter:
        query = query.where(Task.status == status_filter)
    if priority:
        query = query.where(Task.priority == priority)
    if q:
        query = query.where(Task.title.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Task.created_at.desc(), Task.id.desc()).limit(limit).offset(offset)).all()
    return TaskPage(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Task:
    task = Task(**data.model_dump(), owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Déclarée avant /{task_id} pour que "stats" ne soit pas lu comme un identifiant
@router.get("/stats", response_model=TaskStats)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TaskStats:
    rows = db.execute(select(Task.status, func.count()).where(Task.owner_id == user.id).group_by(Task.status)).all()
    counts = {s.value: 0 for s in Status}
    counts.update({s.value: n for s, n in rows})
    total = sum(counts.values())
    overdue = (
        db.scalar(
            select(func.count()).where(
                Task.owner_id == user.id, Task.status != Status.done, Task.due_date < date.today()
            )
        )
        or 0
    )
    return TaskStats(
        total=total,
        overdue=overdue,
        completion_rate=round(counts["done"] / total, 2) if total else 0.0,
        **counts,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Task:
    return get_owned_task(task_id, db, user)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Task:
    task = get_owned_task(task_id, db, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    db.delete(get_owned_task(task_id, db, user))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
