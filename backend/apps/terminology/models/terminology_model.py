from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import VECTOR
from pydantic import BaseModel
from sqlalchemy import Column, String, Text, BigInteger, DateTime, Identity, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


class Terminology(SQLModel, table=True):
    __tablename__ = "terminology"
    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, default=1))
    pid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))
    create_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    word: Optional[str] = Field(max_length=255)
    description: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    embedding: Optional[List[float]] = Field(sa_column=Column(VECTOR(), nullable=True))
    specific_ds: Optional[bool] = Field(sa_column=Column(Boolean, default=False))
    datasource_ids: Optional[List[int]] = Field(default=[], sa_column=Column(JSONB))

    # 新增字段：支持表/字段级关联
    table_ids: Optional[List[int]] = Field(default=[], sa_column=Column(JSONB))
    field_ids: Optional[List[int]] = Field(default=[], sa_column=Column(JSONB))
    scope: Optional[str] = Field(default='global', sa_column=Column(String(20), server_default=text("'global'")))

    enabled: Optional[bool] = Field(sa_column=Column(Boolean, default=True))


class TerminologyInfo(BaseModel):
    id: Optional[int] = None
    create_time: Optional[datetime] = None
    word: Optional[str] = None
    description: Optional[str] = None
    other_words: Optional[List[str]] = []
    specific_ds: Optional[bool] = False
    datasource_ids: Optional[List[int]] = []
    datasource_names: Optional[List[str]] = []

    # 新增字段
    table_ids: Optional[List[int]] = []
    field_ids: Optional[List[int]] = []
    scope: Optional[str] = 'global'
    table_names: Optional[List[str]] = []  # 用于前端显示

    enabled: Optional[bool] = True
