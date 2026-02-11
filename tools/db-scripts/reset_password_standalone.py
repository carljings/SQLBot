#!/usr/bin/env python3
"""
独立的密码重置脚本 - 不依赖项目依赖
使用 psycopg2 或 psycopg 连接数据库
"""
import hashlib
import sys

def calculate_md5(password: str) -> str:
    """计算密码的 MD5 哈希值"""
    m = hashlib.md5()
    m.update(password.encode("utf-8"))
    return m.hexdigest()

def reset_password_with_psycopg():
    """使用 psycopg 重置密码"""
    try:
        import psycopg
    except ImportError:
        print("错误: 未安装 psycopg")
        print("请运行: pip install psycopg")
        return False

    # 数据库连接信息
    db_config = {
        "host": "localhost",
        "port": 5432,
        "user": "root",
        "password": "Password123@pg",
        "dbname": "sqlbot"
    }

    # 默认密码
    default_password = "SQLBot@123456"
    hashed_password = calculate_md5(default_password)

    print(f"默认密码: {default_password}")
    print(f"MD5 哈希: {hashed_password}")

    try:
        # 连接数据库
        conn = psycopg.connect(**db_config)
        cursor = conn.cursor()

        # 查看当前 admin 用户
        cursor.execute("SELECT id, account, name, email FROM sys_user WHERE account = 'admin'")
        admin_user = cursor.fetchone()

        if not admin_user:
            print("错误: 未找到 admin 用户")
            return False

        print(f"\n找到 admin 用户:")
        print(f"  ID: {admin_user[0]}")
        print(f"  账号: {admin_user[1]}")
        print(f"  姓名: {admin_user[2]}")
        print(f"  邮箱: {admin_user[3]}")

        # 更新密码
        cursor.execute(
            "UPDATE sys_user SET password = %s WHERE account = 'admin'",
            (hashed_password,)
        )
        conn.commit()

        print(f"\n✓ 成功重置 admin 用户密码!")
        print(f"  用户名: admin")
        print(f"  密码: {default_password}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"数据库操作失败: {e}")
        return False

def reset_password_manual():
    """手动方式 - 提供 SQL 语句"""
    default_password = "SQLBot@123456"
    hashed_password = calculate_md5(default_password)

    print("\n=== 手动重置密码 ===")
    print(f"默认密码: {default_password}")
    print(f"MD5 哈希: {hashed_password}")
    print("\n请在数据库中执行以下 SQL 语句:")
    print("-" * 60)
    print(f"UPDATE sys_user SET password = '{hashed_password}' WHERE account = 'admin';")
    print("-" * 60)
    print("\n或者使用 psql 命令:")
    print(f"psql -h localhost -p 5432 -U root -d sqlbot -c \"UPDATE sys_user SET password = '{hashed_password}' WHERE account = 'admin';\"")

if __name__ == "__main__":
    print("SQLBot Admin 密码重置工具\n")

    # 尝试使用 psycopg 连接
    print("尝试连接数据库...")
    success = reset_password_with_psycopg()

    if not success:
        print("\n自动重置失败，提供手动重置方法:")
        reset_password_manual()
