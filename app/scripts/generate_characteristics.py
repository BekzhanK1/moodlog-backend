#!/usr/bin/env python3
"""
Script to generate characteristics for all existing users.
This can be run to backfill characteristics for users who already have entries.
"""
from app.core.crypto import decrypt_data
from app.services.encryption_key_service import get_user_data_key
from app.services.characteristic_generator_service import CharacteristicGeneratorService
from app.crud import user_characteristic as char_crud
from app.crud import entry as entry_crud
from app.models import User
from app.db.session import engine
from sqlmodel import Session, select
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def generate_characteristics_for_all_users():
    """Generate characteristics for all users who have entries"""
    print("🚀 Starting characteristics generation for all users...")

    char_service = CharacteristicGeneratorService()

    with Session(engine) as session:
        # Get all users
        users = session.exec(select(User)).all()
        print(f"📊 Found {len(users)} users")

        processed = 0
        skipped = 0
        errors = 0

        for user in users:
            try:
                # Get all non-draft entries for the user
                all_entries = entry_crud.get_recent_entries(
                    session, user_id=user.id, limit=50, exclude_drafts=True
                )

                if not all_entries:
                    print(f"⏭️  Skipping user {user.email} - no entries found")
                    skipped += 1
                    continue

                print(
                    f"📝 Processing user {user.email} ({len(all_entries)} entries)..."
                )

                # Get encryption key
                data_key = get_user_data_key(session, user_id=user.id)

                # Decrypt entries and collect data
                decrypted_contents = []
                mood_ratings = []
                tags_list = []

                for entry in all_entries:
                    decrypted_content = decrypt_data(entry.encrypted_content, data_key)
                    # Use summary if available, otherwise content
                    if entry.encrypted_summary:
                        decrypted_summary = decrypt_data(
                            entry.encrypted_summary, data_key
                        )
                        decrypted_contents.append(decrypted_summary)
                    else:
                        decrypted_contents.append(decrypted_content)

                    mood_ratings.append(
                        entry.mood_rating if entry.mood_rating is not None else 0.0
                    )
                    tags_list.append(entry.tags if entry.tags else [])

                # Generate characteristics
                characteristics = char_service.generate_characteristics(
                    decrypted_contents, mood_ratings, tags_list
                )

                # Save characteristics
                char_crud.create_or_update_characteristic(
                    session,
                    user_id=user.id,
                    general_description=characteristics.get("general_description"),
                    main_themes=characteristics.get("main_themes"),
                    emotional_profile=characteristics.get("emotional_profile"),
                    writing_style=characteristics.get("writing_style"),
                )

                print(f"✅ Generated characteristics for {user.email}")
                processed += 1

            except Exception as e:
                print(f"❌ Error processing user {user.email}: {e}")
                import traceback

                traceback.print_exc()
                errors += 1

        print("\n" + "=" * 50)
        print("📊 Summary:")
        print(f"   ✅ Processed: {processed}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   ❌ Errors: {errors}")
        print("=" * 50)


if __name__ == "__main__":
    generate_characteristics_for_all_users()
