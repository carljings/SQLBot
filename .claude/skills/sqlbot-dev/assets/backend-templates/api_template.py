"""
API 路由模板
文件位置: backend/apps/{module}/api/{resource}.py
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.core.deps import SessionDep, CurrentUser

router = APIRouter(tags=["Resource"], prefix="/resource")


# ===== Pydantic Schemas =====
class ResourceCreate(BaseModel):
    """创建资源请求模型"""
    name: str
    description: str


class ResourceUpdate(BaseModel):
    """更新资源请求模型"""
    name: str | None = None
    description: str | None = None


class Resource(BaseModel):
    """资源响应模型"""
    id: int
    name: str
    description: str
    created_by: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True


# ===== API Endpoints =====
@router.get("/list", response_model=list[Resource], summary="get_resource_list")
async def list_resources(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    keyword: str | None = None
):
    """获取资源列表"""
    from .crud import list_resources
    return list_resources(session, skip=skip, limit=limit, keyword=keyword)


@router.get("/{id}", response_model=Resource, summary="get_resource")
async def get_resource(
    id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    """获取单个资源"""
    from .crud import get_resource
    return get_resource(session, id)


@router.post("/", response_model=Resource, summary="create_resource")
async def create_resource(
    data: ResourceCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """创建资源"""
    from .crud import create_resource
    return create_resource(session, data, current_user.uid)


@router.put("/{id}", response_model=Resource, summary="update_resource")
async def update_resource(
    id: int,
    data: ResourceUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    """更新资源"""
    from .crud import update_resource
    return update_resource(session, id, data)


@router.delete("/{id}", summary="delete_resource")
async def delete_resource(
    id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    """删除资源"""
    from .crud import delete_resource
    delete_resource(session, id)
    return {"message": "删除成功"}
