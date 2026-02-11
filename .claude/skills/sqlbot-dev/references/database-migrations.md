# SQLBot 数据库迁移参考

## Alembic 配置

### 迁移文件位置

```
backend/
├── alembic.ini                  # Alembic 配置文件
├── alembic/
│   ├── env.py                   # 迁移环境配置
│   ├── script.py.mako           # 迁移脚本模板
│   └── versions/                # 迁移版本文件
│       ├── 001_initial.py
│       ├── 002_add_user_table.py
│       └── ...
```

## 创建迁移

### 自动生成迁移

```bash
cd backend
alembic revision --autogenerate -m "描述"
```

### 手动创建迁移

```bash
alembic revision -m "描述"
```

## 迁移脚本结构

```python
"""描述信息

Revision ID: xxx
Revises: yyy
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'xxx'
down_revision: Union[str, None] = 'yyy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级操作"""
    pass


def downgrade() -> None:
    """降级操作"""
    pass
```

## 常见迁移操作

### 创建表

```python
def upgrade() -> None:
    op.create_table(
        'resource',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000)),
        sa.Column('created_by', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resource_id', 'resource', ['id'])
    op.create_index('ix_resource_name', 'resource', ['name'])

def downgrade() -> None:
    op.drop_index('ix_resource_name', table_name='resource')
    op.drop_index('ix_resource_id', table_name='resource')
    op.drop_table('resource')
```

### 添加列

```python
def upgrade() -> None:
    op.add_column('resource',
        sa.Column('status', sa.Integer(), server_default='1')
    )

def downgrade() -> None:
    op.drop_column('resource', 'status')
```

### 修改列

```python
def upgrade() -> None:
    op.alter_column('resource',
        'name',
        existing_type=sa.String(255),
        type_=sa.String(500),
        nullable=False
    )

def downgrade() -> None:
    op.alter_column('resource',
        'name',
        existing_type=sa.String(500),
        type_=sa.String(255),
        nullable=False
    )
```

### 添加外键

```python
def upgrade() -> None:
    op.add_column('resource',
        sa.Column('user_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_resource_user_id',
        'resource', 'sys_user',
        ['user_id'], ['uid']
    )

def downgrade() -> None:
    op.drop_constraint('fk_resource_user_id', 'resource', type_='foreignkey')
    op.drop_column('resource', 'user_id')
```

### 添加 pgvector 列

```python
def upgrade() -> None:
    # 启用 pgvector 扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 添加向量列
    op.add_column('resource',
        sa.Column('embedding', postgresql.ARRAY(sa.Float(), dimensions=1), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('resource', 'embedding')
```

### 创建索引

```python
def upgrade() -> None:
    # 普通索引
    op.create_index('ix_resource_name', 'resource', ['name'])

    # 唯一索引
    op.create_index('uq_resource_code', 'resource', ['code'], unique=True)

    # 复合索引
    op.create_index('ix_resource_user_status', 'resource', ['user_id', 'status'])

    # GIN 索引 (用于 JSONB)
    op.create_index('ix_resource_data', 'resource', ['data'], postgresql_using='gin')

def downgrade() -> None:
    op.drop_index('ix_resource_user_status', table_name='resource')
    op.drop_index('uq_resource_code', table_name='resource')
    op.drop_index('ix_resource_name', table_name='resource')
```

### 数据迁移

```python
def upgrade() -> None:
    # 批量插入数据
    from sqlalchemy.orm import Session
    session = Session(bind=op.get_bind())

    try:
        session.execute(
            sa.insert(Resource.__table__).values([
                {'name': 'Resource 1', 'description': 'Description 1'},
                {'name': 'Resource 2', 'description': 'Description 2'},
            ])
        )
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def downgrade() -> None:
    # 清空数据
    from sqlalchemy.orm import Session
    session = Session(bind=op.get_bind())

    try:
        session.execute(sa.delete(Resource.__table__))
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
```

## 执行迁移

### 升级到最新版本

```bash
alembic upgrade head
```

### 升级到特定版本

```bash
alembic upgrade <revision_id>
```

### 降级一个版本

```bash
alembic downgrade -1
```

### 降级到特定版本

```bash
alembic downgrade <revision_id>
```

### 查看当前版本

```bash
alembic current
```

### 查看迁移历史

```bash
alembic history
```

## SQLAlchemy 模型

### 基础模型

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from common.db.base_class import Base

class Resource(Base):
    __tablename__ = "resource"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000))
    status = Column(Integer, server_default='1')
    created_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 关系模型

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Comment(Base):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True)
    content = Column(String(1000))
    resource_id = Column(Integer, ForeignKey('resource.id'))

    # 关系
    resource = relationship("Resource", back_populates="comments")

class Resource(Base):
    __tablename__ = "resource"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    # 反向关系
    comments = relationship("Comment", back_populates="resource")
```

## 最佳实践

### 1. 迁移脚本编写

- **原子性**: 每个迁移只做一件事
- **可逆性**: 确保 downgrade 正确实现
- **幂等性**: 迁移可以重复执行而不出错

### 2. 数据库兼容性

```python
# PostgreSQL 特定
from sqlalchemy.dialects import postgresql

op.execute('CREATE EXTENSION IF NOT EXISTS vector')
```

### 3. 大数据迁移

```python
def upgrade() -> None:
    # 分批处理
    batch_size = 1000
    offset = 0

    while True:
        results = session.execute(
            sa.select(Resource.id).offset(offset).limit(batch_size)
        ).scalars().all()

        if not results:
            break

        for row in results:
            # 处理数据
            pass

        session.commit()
        offset += batch_size
```

### 4. 默认值

```python
# 使用 server_default 设置数据库默认值
created_at = Column(DateTime, server_default=func.now())

# 使用 default 设置 Python 默认值
status = Column(Integer, default=1)
```

## 常见问题

### 迁移冲突

```bash
# 查看冲突
alembic heads

# 合并分支
alembic merge -m "merge migrations" <rev1> <rev2>
```

### 重置迁移

```bash
# 降级到基础版本
alembic downgrade base

# 删除版本文件后重新生成
alembic revision --autogenerate -m "initial"
```

### 测试迁移

```python
import pytest
from alembic import command
from alembic.config import Config

def test_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
```
