#!/usr/bin/env python3
"""
重置 admin 用户密码的脚本
"""
import sys
from sqlmodel import Session, select

# 添加项目路径到 sys.path
sys.path.insert(0, '.')

from common.core.db import engine
from apps.system.models.user import UserModel
from common.core.security import md5pwd
from common.core.config import settings


def reset_admin_password():
    """重置 admin 用户密码为默认密码"""

    # 获取默认密码
    default_password = settings.DEFAULT_PWD
    print(f"默认密码: {default_password}")

    # 计算 MD5 哈希
    hashed_password = md5pwd(default_password)

    # 连接数据库
    with Session(engine) as session:
        # 查找 admin 用户
        statement = select(UserModel).where(UserModel.account == "admin")
        admin_user = session.exec(statement).first()

        if not admin_user:
            print("错误: 未找到 admin 用户")
            return False

        # 更新密码
        admin_user.password = hashed_password
        session.add(admin_user)
        session.commit()

        print(f"成功重置 admin 用户密码!")
        print(f"用户名: admin")
        print(f"密码: {default_password}")
        return True


if __name__ == "__main__":
    try:
        reset_admin_password()
    except Exception as e:
        print(f"重置密码失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
