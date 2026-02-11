"""
维度值管理 CRUD 操作
"""
import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, select, func, delete, update

from common.core.config import settings
from common.core.deps import SessionDep, Trans
from ..models.dimension_model import DimensionValue, DimensionValueInfo, DimensionValueResponse, DimensionValueQuery


def get_dimension_list(
    session: SessionDep,
    oid: int,
    query: DimensionValueQuery
) -> tuple[List[DimensionValueResponse], int, int, int]:
    """
    获取维度值列表

    Args:
        session: 数据库会话
        oid: 组织ID
        query: 查询条件

    Returns:
        (维度列表, 当前页, 每页大小, 总数)
    """
    # 构建查询条件
    conditions = [DimensionValue.oid == oid]

    if query.name:
        conditions.append(DimensionValue.name.ilike(f"%{query.name}%"))
    if query.code:
        conditions.append(DimensionValue.code.ilike(f"%{query.code}%"))
    if query.enabled is not None:
        conditions.append(DimensionValue.enabled == query.enabled)

    # 获取总数
    count_stmt = select(func.count()).select_from(DimensionValue).where(and_(*conditions))
    total_count = session.execute(count_stmt).scalar()

    # 计算分页
    page_size = max(1, min(query.page_size, 100))
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    current_page = max(1, min(query.page, total_pages)) if total_pages > 0 else 1

    # 获取分页数据
    stmt = (
        select(DimensionValue)
        .where(and_(*conditions))
        .order_by(DimensionValue.create_time.desc())
        .offset((current_page - 1) * page_size)
        .limit(page_size)
    )

    results = session.execute(stmt).scalars().all()

    # 转换为响应对象
    dimension_list = []
    for item in results:
        dimension_list.append(DimensionValueResponse(
            id=item.id,
            name=item.name,
            code=item.code,
            description=item.description,
            values=item.values or [],
            value_labels=item.value_labels or {},
            is_system=item.is_system,
            enabled=item.enabled,
            create_time=item.create_time,
            value_count=len(item.values) if item.values else 0
        ))

    return dimension_list, current_page, page_size, total_count


def get_dimension_by_id(session: SessionDep, oid: int, dimension_id: int) -> Optional[DimensionValue]:
    """根据ID获取维度值"""
    stmt = select(DimensionValue).where(
        and_(DimensionValue.id == dimension_id, DimensionValue.oid == oid)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_all_dimensions(session: SessionDep, oid: int, enabled_only: bool = True) -> List[DimensionValue]:
    """
    获取所有维度值（用于下拉选择）

    Args:
        session: 数据库会话
        oid: 组织ID
        enabled_only: 是否只获取启用的

    Returns:
        维度值列表
    """
    conditions = [DimensionValue.oid == oid]
    if enabled_only:
        conditions.append(DimensionValue.enabled == True)

    stmt = (
        select(DimensionValue)
        .where(and_(*conditions))
        .order_by(DimensionValue.name)
    )
    return session.execute(stmt).scalars().all()


def create_dimension(
    session: SessionDep,
    trans: Trans,
    oid: int,
    info: DimensionValueInfo,
    user_id: int
) -> int:
    """
    创建维度值

    Args:
        session: 数据库会话
        trans: 翻译器
        oid: 组织ID
        info: 维度值信息
        user_id: 用户ID

    Returns:
        创建的维度值ID
    """
    # 验证必填字段
    if not info.name or not info.name.strip():
        raise HTTPException(status_code=400, detail=trans("i18n_dimension.name_required"))

    if not info.code or not info.code.strip():
        raise HTTPException(status_code=400, detail=trans("i18n_dimension.code_required"))

    # 检查编码是否已存在
    existing = session.query(DimensionValue).filter(
        and_(
            DimensionValue.code == info.code.strip(),
            DimensionValue.oid == oid
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=trans("i18n_dimension.code_exists"))

    # 创建维度值
    dimension = DimensionValue(
        oid=oid,
        name=info.name.strip(),
        code=info.code.strip(),
        description=info.description.strip() if info.description else None,
        values=info.values or [],
        value_labels=info.value_labels or {},
        is_system=False,
        enabled=info.enabled if info.enabled is not None else True,
        create_time=datetime.datetime.now(),
        create_by=user_id
    )

    session.add(dimension)
    session.flush()
    session.refresh(dimension)
    session.commit()

    return dimension.id


def update_dimension(
    session: SessionDep,
    trans: Trans,
    oid: int,
    info: DimensionValueInfo,
    user_id: int
) -> int:
    """
    更新维度值

    Args:
        session: 数据库会话
        trans: 翻译器
        oid: 组织ID
        info: 维度值信息
        user_id: 用户ID

    Returns:
        更新的维度值ID
    """
    if not info.id:
        raise HTTPException(status_code=400, detail=trans("i18n_dimension.id_required"))

    # 检查是否存在
    dimension = session.query(DimensionValue).filter(
        and_(DimensionValue.id == info.id, DimensionValue.oid == oid)
    ).first()

    if not dimension:
        raise HTTPException(status_code=404, detail=trans("i18n_dimension.not_found"))

    # 系统预置的维度值不允许修改编码
    if dimension.is_system and dimension.code != info.code:
        raise HTTPException(status_code=400, detail=trans("i18n_dimension.system_cannot_modify_code"))

    # 检查编码是否与其他记录冲突
    if info.code and info.code.strip() != dimension.code:
        existing = session.query(DimensionValue).filter(
            and_(
                DimensionValue.code == info.code.strip(),
                DimensionValue.oid == oid,
                DimensionValue.id != info.id
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=trans("i18n_dimension.code_exists"))

    # 更新字段
    dimension.name = info.name.strip() if info.name else dimension.name
    dimension.code = info.code.strip() if info.code and not dimension.is_system else dimension.code
    dimension.description = info.description.strip() if info.description else None
    dimension.values = info.values if info.values is not None else dimension.values
    dimension.value_labels = info.value_labels if info.value_labels is not None else dimension.value_labels
    dimension.enabled = info.enabled if info.enabled is not None else dimension.enabled
    dimension.update_time = datetime.datetime.now()
    dimension.update_by = user_id

    session.add(dimension)
    session.commit()

    return dimension.id


def delete_dimension(session: SessionDep, trans: Trans, oid: int, dimension_id: int) -> bool:
    """
    删除维度值

    Args:
        session: 数据库会话
        trans: 翻译器
        oid: 组织ID
        dimension_id: 维度值ID

    Returns:
        是否删除成功
    """
    # 检查是否存在
    dimension = session.query(DimensionValue).filter(
        and_(DimensionValue.id == dimension_id, DimensionValue.oid == oid)
    ).first()

    if not dimension:
        raise HTTPException(status_code=404, detail=trans("i18n_dimension.not_found"))

    # 系统预置的维度值不允许删除
    if dimension.is_system:
        raise HTTPException(status_code=400, detail=trans("i18n_dimension.system_cannot_delete"))

    # TODO: 检查是否有字段正在使用此维度值
    # field_count = session.query(CoreField).filter(CoreField.dimension_id == dimension_id).count()
    # if field_count > 0:
    #     raise HTTPException(status_code=400, detail=trans("i18n_dimension.in_use"))

    session.delete(dimension)
    session.commit()

    return True


def enable_dimension(session: SessionDep, trans: Trans, oid: int, dimension_id: int, enabled: bool) -> bool:
    """
    启用/禁用维度值

    Args:
        session: 数据库会话
        trans: 翻译器
        oid: 组织ID
        dimension_id: 维度值ID
        enabled: 是否启用

    Returns:
        是否操作成功
    """
    dimension = session.query(DimensionValue).filter(
        and_(DimensionValue.id == dimension_id, DimensionValue.oid == oid)
    ).first()

    if not dimension:
        raise HTTPException(status_code=404, detail=trans("i18n_dimension.not_found"))

    dimension.enabled = enabled
    dimension.update_time = datetime.datetime.now()
    session.add(dimension)
    session.commit()

    return True
