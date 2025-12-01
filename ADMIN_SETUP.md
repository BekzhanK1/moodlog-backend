# Admin User Setup

This document describes how to create and manage admin users in Moodlog.

## Creating an Admin User

### Using the Script (Recommended)

Run the interactive script to create an admin user:

```bash
# From the moodlog-backend directory
python -m app.scripts.create_admin
```

Or using Make:

```bash
make create-admin
```

The script will prompt you for:
- **Email**: Admin user's email address
- **Password**: Admin user's password (will be hidden for security)
- **Name** (optional): Admin user's display name

**Note**: If a user with the email already exists, the script will offer to make them an admin instead of creating a new user.

### Example Usage

```bash
$ python -m app.scripts.create_admin
============================================================
🔐 Create Admin User
============================================================

Enter admin email: admin@example.com
Enter admin password: 
Confirm admin password: 
Enter admin name (optional): Admin User

============================================================
✅ Admin user created successfully!
============================================================
   Email: admin@example.com
   Name: Admin User
   Admin: True
   User ID: 123e4567-e89b-12d3-a456-426614174000
============================================================
```

## Using Admin Privileges in Code

### Protect an Endpoint with Admin Requirement

Use the `require_admin` dependency to protect admin-only endpoints:

```python
from app.core.deps import require_admin
from app.models import User

@router.get("/admin/users")
def list_all_users(
    current_user: User = Depends(require_admin)
):
    """List all users - Admin only"""
    # Only admins can access this endpoint
    ...
```

### Check if User is Admin

You can also check the `is_admin` field directly:

```python
from app.core.deps import get_current_user

@router.get("/some-endpoint")
def some_endpoint(
    current_user: User = Depends(get_current_user)
):
    if current_user.is_admin:
        # Admin-specific logic
        ...
    else:
        # Regular user logic
        ...
```

## Database Migration

After pulling the latest code, run the migration to add the `is_admin` field:

```bash
alembic upgrade head
```

## Security Notes

- Admin users have full access to all endpoints protected with `require_admin`
- Use admin privileges carefully and only for necessary operations
- Consider implementing additional security measures for admin endpoints (e.g., IP whitelisting, 2FA)
- Admin status is stored in the database and cannot be changed through regular API endpoints (only via direct database access or the script)

## Future Admin Features

Potential admin features to implement:
- View all users and their statistics
- Manage user subscriptions
- View system analytics
- Manage application settings
- Access audit logs
- User management (suspend, delete, etc.)

