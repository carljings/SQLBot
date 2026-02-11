#!/usr/bin/env python3
"""
使用项目数据库连接重置 admin 密码
"""
import os
import sys
import hashlib

# 设置环境变量，确保使用本地数据库
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "root")
os.environ.setdefault("POSTGRES_PASSWORD", "Password123@pg")
os.environ.setdefault("POSTGRES_DB", "sqlbot")

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def calculate_md5(password: str) -> str:
    """计算密码的 MD5 哈希值"""
    m = hashlib.md5()
    m.update(password.encode("utf-8"))
    return m.hexdigest()

def main():
    # 默认密码
    default_password = "SQLBot@123456"
    hashed_password = calculate_md5(default_password)

    print("SQLBot Admin 密码重置工具")
    print("=" * 60)
    print(f"默认密码: {default_password}")
    print(f"MD5 哈希: {hashed_password}")
    print("=" * 60)

    try:
        # 导入项目的数据库引擎
        from common.core.db import engine
        from sqlalchemy import text

        # 执行 SQL
        with engine.connect() as conn:
            # 查看当前 admin 用户
            result = conn.execute(
                text("SELECT id, account, name, email FROM sys_user WHERE account = 'admin'")
            )
            admin_user = result.fetchone()

            if not admin_user:
                print("\n错误: 未找到 admin 用户")
                return False

            print(f"\n找到 admin 用户:")
            print(f"  ID: {admin_user[0]}")
            print(f"  账号: {admin_user[1]}")
            print(f"  姓名: {admin_user[2]}")
            print(f"  邮箱: {admin_user[3]}")

            # 更新密码
            conn.execute(
                text("UPDATE sys_user SET password = :password WHERE account = 'admin'"),
                {"password": hashed_password}
            )
            conn.commit()

            print(f"\n✓ 成功重置 admin 用户密码!")
            print(f"  用户名: admin")
            print(f"  密码: {default_password}")
            return True

    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("\n请使用以下 SQL 语句手动重置密码:")
        print("-" * 60)
        print(f"UPDATE sys_user SET password = '{hashed_password}' WHERE account = 'admin';")
        print("-" * 60)
        return False
    except Exception as e:
        print(f"\n数据库操作失败: {e}")
        print("\n请使用以下 SQL 语句手动重置密码:")
        print("-" * 60)
        print(f"UPDATE sys_user SET password = '{hashed_password}' WHERE account = 'admin';")
        print("-" * 60)
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
