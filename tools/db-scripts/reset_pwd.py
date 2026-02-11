"""
简单的密码重置脚本
"""
import hashlib


def main():
    # 计算默认密码的 MD5
    default_password = "SQLBot@123456"
    hashed_password = hashlib.md5(default_password.encode("utf-8")).hexdigest()

    print("=" * 70)
    print("SQLBot Admin 密码重置")
    print("=" * 70)
    print(f"\n默认密码: {default_password}")
    print(f"MD5 哈希: {hashed_password}")

    try:
        from sqlmodel import Session, select
        from common.core.db import engine
        from apps.system.models.user import UserModel

        with Session(engine) as session:
            # 查找 admin 用户
            statement = select(UserModel).where(UserModel.account == "admin")
            admin_user = session.exec(statement).first()

            if not admin_user:
                print("\n❌ 错误: 未找到 admin 用户")
                return

            print(f"\n找到 admin 用户:")
            print(f"  ID: {admin_user.id}")
            print(f"  账号: {admin_user.account}")
            print(f"  姓名: {admin_user.name}")
            print(f"  邮箱: {admin_user.email}")

            # 更新密码
            admin_user.password = hashed_password
            session.add(admin_user)
            session.commit()

            print(f"\n✅ 成功重置 admin 用户密码!")
            print(f"\n登录信息:")
            print(f"  用户名: admin")
            print(f"  密码: {default_password}")
            print("=" * 70)

    except Exception as e:
        print(f"\n❌ 自动重置失败: {e}")
        print("\n请手动执行以下 SQL 语句:")
        print("-" * 70)
        print(f"UPDATE sys_user SET password = '{hashed_password}' WHERE account = 'admin';")
        print("-" * 70)


if __name__ == "__main__":
    main()
