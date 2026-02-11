"""
简单的密码重置脚本 - 无特殊字符版本
"""
import hashlib


def main():
    # 计算默认密码的 MD5
    default_password = "SQLBot@123456"
    hashed_password = hashlib.md5(default_password.encode("utf-8")).hexdigest()

    print("=" * 70)
    print("SQLBot Admin Password Reset")
    print("=" * 70)
    print(f"\nDefault Password: {default_password}")
    print(f"MD5 Hash: {hashed_password}")

    try:
        from sqlmodel import Session, select
        from common.core.db import engine
        from apps.system.models.user import UserModel

        with Session(engine) as session:
            # 查找 admin 用户
            statement = select(UserModel).where(UserModel.account == "admin")
            admin_user = session.exec(statement).first()

            if not admin_user:
                print("\n[ERROR] Admin user not found")
                return

            print(f"\nFound admin user:")
            print(f"  ID: {admin_user.id}")
            print(f"  Account: {admin_user.account}")
            print(f"  Name: {admin_user.name}")
            print(f"  Email: {admin_user.email}")

            # 更新密码
            admin_user.password = hashed_password
            session.add(admin_user)
            session.commit()

            print(f"\n[SUCCESS] Admin password has been reset!")
            print(f"\nLogin credentials:")
            print(f"  Username: admin")
            print(f"  Password: {default_password}")
            print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Auto reset failed: {e}")
        print("\nPlease execute the following SQL manually:")
        print("-" * 70)
        print(f"UPDATE sys_user SET password = '{hashed_password}' WHERE account = 'admin';")
        print("-" * 70)


if __name__ == "__main__":
    main()
