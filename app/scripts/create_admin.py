#!/usr/bin/env python3
"""
Script to create an admin user.
Usage: python -m app.scripts.create_admin
"""
from app.services.encryption_key_service import create_and_store_wrapped_key
from app.core.security import get_password_hash
from app.crud import user as user_crud
from sqlmodel import Session
from app.db.session import engine
import sys
from pathlib import Path
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def create_admin_user():
    """Create an admin user interactively."""
    print("=" * 60)
    print("🔐 Create Admin User")
    print("=" * 60)
    print()

    # Get email
    email = input("Enter admin email: ").strip().lower()
    if not email:
        print("❌ Email is required!")
        sys.exit(1)

    # Validate email format (basic check)
    if "@" not in email or "." not in email.split("@")[1]:
        print("❌ Invalid email format!")
        sys.exit(1)

    with Session(engine) as session:
        # Check if user already exists
        existing_user = user_crud.get_user_by_email(session, email=email)
        if existing_user:
            print(f"\n⚠️  User with email {email} already exists!")
            response = (
                input("Do you want to make this user an admin? (y/n): ").strip().lower()
            )

            if response == "y":
                existing_user.is_admin = True
                session.add(existing_user)
                session.commit()
                session.refresh(existing_user)
                print(f"\n✅ User {email} is now an admin!")
                return
            else:
                print("❌ Cancelled.")
                sys.exit(0)

        # Get password
        password = getpass("Enter admin password: ")
        if not password:
            print("❌ Password is required!")
            sys.exit(1)

        password_confirm = getpass("Confirm admin password: ")
        if password != password_confirm:
            print("❌ Passwords do not match!")
            sys.exit(1)

        if len(password) < 8:
            print(
                "⚠️  Warning: Password is less than 8 characters. Consider using a stronger password."
            )
            response = input("Continue anyway? (y/n): ").strip().lower()
            if response != "y":
                print("❌ Cancelled.")
                sys.exit(0)

        # Get optional name
        name = input("Enter admin name (optional): ").strip()
        if not name:
            name = None

        try:
            # Create user
            hashed_password = get_password_hash(password)
            user = user_crud.create_user(
                session,
                email=email,
                hashed_password=hashed_password,
            )

            # Set admin flag
            user.is_admin = True
            if name:
                user.name = name

            # Generate and store encryption key
            create_and_store_wrapped_key(session, user_id=user.id)

            session.add(user)
            session.commit()
            session.refresh(user)

            print()
            print("=" * 60)
            print("✅ Admin user created successfully!")
            print("=" * 60)
            print(f"   Email: {user.email}")
            print(f"   Name: {user.name or 'N/A'}")
            print(f"   Admin: {user.is_admin}")
            print(f"   User ID: {user.id}")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Error creating admin user: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    create_admin_user()
