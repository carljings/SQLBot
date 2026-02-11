"""
维度值管理模块
用于管理字段的枚举值/字典值，提升SQL生成准确性
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, Text, BigInteger, DateTime, Identity, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


class DimensionValue(SQLModel, table=True):
    """维度值表"""
    __tablename__ = "dimension_value"

    id: int = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    oid: int = Field(sa_column=Column(BigInteger(), default=1), description="组织ID")
    name: str = Field(sa_column=Column(Text), description="维度名称")
    code: str = Field(sa_column=Column(Text), description="维度编码，英文标识")
    description: Optional[str] = Field(sa_column=Column(Text, nullable=True), description="维度描述")
    values: List[str] = Field(sa_column=Column(JSONB, default=[]), description="维度值列表")
    value_labels: Optional[dict] = Field(sa_column=Column(JSONB, nullable=True, default={}), description="值标签映射，如 {'completed': '已完成', 'pending': '待处理'}")
    is_system: bool = Field(sa_column=Column(Boolean, default=False), description="是否系统预置")
    enabled: bool = Field(sa_column=Column(Boolean, default=True), description="是否启用")
    create_time: datetime = Field(sa_column=Column(DateTime(timezone=False), default=datetime.now), description="创建时间")
    update_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True), description="更新时间")
    create_by: Optional[int] = Field(sa_column=Column(BigInteger(), nullable=True), description="创建人")
    update_by: Optional[int] = Field(sa_column=Column(BigInteger(), nullable=True), description="更新人")


class DimensionValueInfo(BaseModel):
    """维度值信息DTO"""
    id: Optional[int] = None
    oid: Optional[int] = 1
    name: str = ""
    code: str = ""
    description: Optional[str] = None
    values: List[str] = []
    value_labels: Optional[dict] = None
    is_system: Optional[bool] = False
    enabled: Optional[bool] = True


class DimensionValueQuery(BaseModel):
    """维度值查询条件"""
    name: Optional[str] = None
    code: Optional[str] = None
    enabled: Optional[bool] = None
    page: int = 1
    page_size: int = 10


class DimensionValueResponse(BaseModel):
    """维度值响应"""
    id: int
    name: str
    code: str
    description: Optional[str]
    values: List[str]
    value_labels: Optional[dict]
    is_system: bool
    enabled: bool
    create_time: datetime
    value_count: int = 0  # 值数量
