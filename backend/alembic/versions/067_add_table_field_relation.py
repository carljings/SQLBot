"""add table and field relation to terminology and data_training

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # ===================================================
    # 术语表扩展：支持表/字段级关联
    # ===================================================

    # 添加 table_ids 字段
    op.add_column(
        'terminology',
        sa.Column('table_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]')
    )

    # 添加 field_ids 字段
    op.add_column(
        'terminology',
        sa.Column('field_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]')
    )

    # 添加 scope 字段
    op.add_column(
        'terminology',
        sa.Column('scope', sa.String(length=20), nullable=True, server_default='global')
    )

    # 添加索引
    op.create_index('idx_terminology_table_ids', 'terminology', ['table_ids'], postgresql_using='gin')
    op.create_index('idx_terminology_field_ids', 'terminology', ['field_ids'], postgresql_using='gin')
    op.create_index('idx_terminology_scope', 'terminology', ['scope'])

    # ===================================================
    # SQL 示例表扩展：支持表关联
    # ===================================================

    # 添加 table_ids 字段
    op.add_column(
        'data_training',
        sa.Column('table_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]')
    )

    # 添加索引
    op.create_index('idx_data_training_table_ids', 'data_training', ['table_ids'], postgresql_using='gin')

    # ===================================================
    # 数据迁移：为现有数据设置默认范围
    # ===================================================
    op.execute("UPDATE terminology SET scope = 'global' WHERE scope IS NULL")
    op.execute("UPDATE terminology SET table_ids = '[]' WHERE table_ids IS NULL")
    op.execute("UPDATE terminology SET field_ids = '[]' WHERE field_ids IS NULL")
    op.execute("UPDATE data_training SET table_ids = '[]' WHERE table_ids IS NULL")


def downgrade():
    # ===================================================
    # 回滚 SQL 示例表
    # ===================================================

    # 删除索引
    op.drop_index('idx_data_training_table_ids', table_name='data_training')

    # 删除 table_ids 字段
    op.drop_column('data_training', 'table_ids')

    # ===================================================
    # 回滚术语表
    # ===================================================

    # 删除索引
    op.drop_index('idx_terminology_scope', table_name='terminology')
    op.drop_index('idx_terminology_field_ids', table_name='terminology')
    op.drop_index('idx_terminology_table_ids', table_name='terminology')

    # 删除字段
    op.drop_column('terminology', 'scope')
    op.drop_column('terminology', 'field_ids')
    op.drop_column('terminology', 'table_ids')
