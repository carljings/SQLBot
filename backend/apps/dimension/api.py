"""
维度值管理 API 入口
"""
from fastapi import APIRouter

from .router.dimension_router import router as dimension_router

router = APIRouter(prefix="/dimension", tags=["dimension"])

# 包含维度值管理的所有路由
router.include_router(dimension_router)
