#!/usr/bin/env python3
"""
测试维度值 API
"""
import sys
sys.path.insert(0, '.')

from sqlmodel import Session
from common.core.db import engine
from apps.dimension.curd.dimension_crud import create_dimension
from apps.dimension.models.dimension_model import DimensionValueInfo
from common.utils.locale import I18n


def test_create_dimension():
    """测试创建维度值"""

    # 创建翻译器
    trans = I18n("zh-CN")

    # 创建测试数据
    info = DimensionValueInfo(
        name="测试维度",
        code="test_dimension",
        description="这是一个测试维度",
        values=["value1", "value2", "value3"],
        value_labels={"value1": "值1", "value2": "值2", "value3": "值3"},
        enabled=True
    )

    with Session(engine) as session:
        try:
            dimension_id = create_dimension(
                session=session,
                trans=trans,
                oid=1,
                info=info,
                user_id=1
            )
            print(f"[SUCCESS] Created dimension with ID: {dimension_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create dimension: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    test_create_dimension()
