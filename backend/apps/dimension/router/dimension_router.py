"""
维度值管理 API 路由
"""
from typing import List

from fastapi import APIRouter

from common.core.deps import SessionDep, CurrentUser, Trans
from ..models.dimension_model import DimensionValueInfo, DimensionValueResponse, DimensionValueQuery
from ..curd.dimension_crud import (
    get_dimension_list,
    get_dimension_by_id,
    get_all_dimensions,
    create_dimension,
    update_dimension,
    delete_dimension,
    enable_dimension
)

router = APIRouter()


@router.get("/list", response_model=dict)
async def list_dimensions(
    session: SessionDep,
    current_user: CurrentUser,
    name: str = None,
    code: str = None,
    enabled: bool = None,
    page: int = 1,
    page_size: int = 10,
):
    """
    获取维度值列表（分页）

    Args:
        session: 数据库会话
        current_user: 当前用户
        name: 维度名称（模糊查询）
        code: 维度编码（模糊查询）
        enabled: 是否启用
        page: 页码
        page_size: 每页大小

    Returns:
        维度值列表
    """
    oid = current_user.oid if current_user.oid is not None else 1

    query = DimensionValueQuery(
        name=name,
        code=code,
        enabled=enabled,
        page=page,
        page_size=page_size
    )

    dimensions, current_page, page_size, total_count = get_dimension_list(
        session=session,
        oid=oid,
        query=query
    )

    return {
        "items": dimensions,
        "current_page": current_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1
    }


@router.get("/all", response_model=List[dict])
async def list_all_dimensions(
    session: SessionDep,
    current_user: CurrentUser,
    enabled_only: bool = True,
):
    """
    获取所有维度值（用于下拉选择）

    Args:
        session: 数据库会话
        current_user: 当前用户
        enabled_only: 是否只获取启用的

    Returns:
        维度值列表
    """
    oid = current_user.oid if current_user.oid is not None else 1

    dimensions = get_all_dimensions(
        session=session,
        oid=oid,
        enabled_only=enabled_only
    )

    return [
        {
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "value_count": len(d.values) if d.values else 0
        }
        for d in dimensions
    ]


@router.get("/{dimension_id}", response_model=dict)
async def get_dimension(
    dimension_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    获取维度值详情

    Args:
        dimension_id: 维度值ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        维度值详情
    """
    oid = current_user.oid if current_user.oid is not None else 1

    dimension = get_dimension_by_id(
        session=session,
        oid=oid,
        dimension_id=dimension_id
    )

    if not dimension:
        return {"error": "Dimension not found"}

    return {
        "id": dimension.id,
        "name": dimension.name,
        "code": dimension.code,
        "description": dimension.description,
        "values": dimension.values or [],
        "value_labels": dimension.value_labels or {},
        "is_system": dimension.is_system,
        "enabled": dimension.enabled,
        "create_time": dimension.create_time,
        "value_count": len(dimension.values) if dimension.values else 0
    }


@router.post("/", response_model=dict)
async def create_dimension_endpoint(
    session: SessionDep,
    current_user: CurrentUser,
    trans: Trans,
    info: DimensionValueInfo,
):
    """
    创建维度值

    Args:
        session: 数据库会话
        current_user: 当前用户
        trans: 翻译器
        info: 维度值信息

    Returns:
        创建的维度值ID
    """
    oid = current_user.oid if current_user.oid is not None else 1

    dimension_id = create_dimension(
        session=session,
        trans=trans,
        oid=oid,
        info=info,
        user_id=current_user.id
    )

    return {"id": dimension_id, "message": "Dimension created successfully"}


@router.put("/{dimension_id}", response_model=dict)
async def update_dimension_endpoint(
    dimension_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    trans: Trans,
    info: DimensionValueInfo,
):
    """
    更新维度值

    Args:
        dimension_id: 维度值ID
        session: 数据库会话
        current_user: 当前用户
        trans: 翻译器
        info: 维度值信息

    Returns:
        更新的结果
    """
    oid = current_user.oid if current_user.oid is not None else 1

    info.id = dimension_id
    update_dimension(
        session=session,
        trans=trans,
        oid=oid,
        info=info,
        user_id=current_user.id
    )

    return {"id": dimension_id, "message": "Dimension updated successfully"}


@router.delete("/{dimension_id}", response_model=dict)
async def delete_dimension_endpoint(
    dimension_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    trans: Trans,
):
    """
    删除维度值

    Args:
        dimension_id: 维度值ID
        session: 数据库会话
        current_user: 当前用户
        trans: 翻译器

    Returns:
        删除的结果
    """
    oid = current_user.oid if current_user.oid is not None else 1

    delete_dimension(
        session=session,
        trans=trans,
        oid=oid,
        dimension_id=dimension_id
    )

    return {"message": "Dimension deleted successfully"}


@router.patch("/{dimension_id}/enable", response_model=dict)
async def enable_dimension_endpoint(
    dimension_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    trans: Trans,
    enabled: bool,
):
    """
    启用/禁用维度值

    Args:
        dimension_id: 维度值ID
        session: 数据库会话
        current_user: 当前用户
        trans: 翻译器
        enabled: 是否启用

    Returns:
        操作结果
    """
    oid = current_user.oid if current_user.oid is not None else 1

    enable_dimension(
        session=session,
        trans=trans,
        oid=oid,
        dimension_id=dimension_id,
        enabled=enabled
    )

    return {"message": f"Dimension {'enabled' if enabled else 'disabled'} successfully"}
