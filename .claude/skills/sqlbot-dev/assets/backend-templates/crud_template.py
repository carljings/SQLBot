"""
CRUD 操作模板
文件位置: backend/apps/{module}/crud/{resource}.py
"""
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import Resource
from .schemas import ResourceCreate, ResourceUpdate


def list_resources(
    session: Session,
    skip: int = 0,
    limit: int = 100,
    keyword: str | None = None
) -> list[Resource]:
    """获取资源列表"""
    stmt = select(Resource)

    # 关键词搜索
    if keyword:
        stmt = stmt.where(Resource.name.ilike(f"%{keyword}%"))

    # 分页
    stmt = stmt.offset(skip).limit(limit)

    return list(session.scalars(stmt).all())


def count_resources(
    session: Session,
    keyword: str | None = None
) -> int:
    """统计资源数量"""
    stmt = select(func.count(Resource.id))

    if keyword:
        stmt = stmt.where(Resource.name.ilike(f"%{keyword}%"))

    return session.scalar(stmt)


def get_resource(session: Session, id: int) -> Resource | None:
    """获取单个资源"""
    return session.get(Resource, id)


def create_resource(
    session: Session,
    data: ResourceCreate,
    user_id: str
) -> Resource:
    """创建资源"""
    db_obj = Resource(
        **data.model_dump(),
        created_by=user_id
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_resource(
    session: Session,
    id: int,
    data: ResourceUpdate
) -> Resource:
    """更新资源"""
    db_obj = session.get(Resource, id)
    if not db_obj:
        raise ValueError("Resource not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(db_obj, field, value)

    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_resource(session: Session, id: int) -> None:
    """删除资源"""
    db_obj = session.get(Resource, id)
    if not db_obj:
        raise ValueError("Resource not found")

    session.delete(db_obj)
    session.commit()
