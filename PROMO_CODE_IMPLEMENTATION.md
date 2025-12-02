# Promo Code System Implementation

This document describes the promo code system for granting subscription plans to users.

## Overview

The promo code system allows admins to generate one-time use promo codes for specific subscription plans. Users with Free or Trial plans can redeem these codes to upgrade to Pro plans.

## Features

- **Admin-only generation**: Only admins can create promo codes
- **One-time use**: Each promo code can only be used once
- **Plan-specific**: Each code is tied to a specific plan (pro_month or pro_year)
- **Optional expiration**: Codes can have an expiration date
- **Auto-generated or custom**: Codes can be auto-generated or custom
- **Restricted redemption**: Only users with Free or Trial plans can redeem codes

## Database Model

### PromoCode Model
- `id`: Unique identifier
- `code`: The promo code string (unique, indexed)
- `plan`: Target plan ("pro_month" or "pro_year")
- `created_by`: Admin user ID who created the code
- `used_by`: User ID who redeemed the code (null if unused)
- `used_at`: Timestamp when code was redeemed
- `is_used`: Boolean flag indicating if code has been used
- `created_at`: Creation timestamp
- `expires_at`: Optional expiration date

## API Endpoints

### Admin Endpoints

#### POST `/api/v1/admin/promo-codes`
Create a new promo code (Admin only).

**Request:**
```json
{
  "plan": "pro_month",  // or "pro_year"
  "code": "SUMMER2024",  // Optional: custom code (auto-generated if not provided)
  "expires_at": "2024-12-31T23:59:59"  // Optional: expiration date
}
```

**Response:**
```json
{
  "id": "uuid",
  "code": "SUMMER2024",
  "plan": "pro_month",
  "created_by": "admin-uuid",
  "used_by": null,
  "used_at": null,
  "is_used": false,
  "created_at": "2024-12-01T10:00:00",
  "expires_at": "2024-12-31T23:59:59"
}
```

#### GET `/api/v1/admin/promo-codes`
List all promo codes (Admin only).

**Query Parameters:**
- `include_used` (bool, default: true): Include used promo codes
- `limit` (int, optional): Limit number of results (1-100)

**Response:**
```json
{
  "promo_codes": [...],
  "total": 10
}
```

### User Endpoints

#### POST `/api/v1/promo-codes/redeem`
Redeem a promo code to get a subscription plan.

**Request:**
```json
{
  "code": "SUMMER2024"
}
```

**Response:**
```json
{
  "message": "Promo code redeemed successfully! Your subscription has been activated.",
  "plan": "pro_month",
  "expires_at": "2025-01-01T10:00:00"
}
```

**Errors:**
- `404`: Promo code not found
- `400`: Code already used, expired, or user has active Pro subscription

## Usage Examples

### Admin: Create a Promo Code

```bash
curl -X POST "http://localhost:8000/v1/admin/promo-codes" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "pro_month",
    "expires_at": "2024-12-31T23:59:59"
  }'
```

### Admin: Create Custom Promo Code

```bash
curl -X POST "http://localhost:8000/v1/admin/promo-codes" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "pro_year",
    "code": "WELCOME2024"
  }'
```

### User: Redeem Promo Code

```bash
curl -X POST "http://localhost:8000/v1/promo-codes/redeem" \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "WELCOME2024"
  }'
```

## Code Generation

Promo codes are auto-generated as 12-character uppercase alphanumeric strings, excluding ambiguous characters (0, O, I, 1). Example: `A3B7C9D2E5F8`

Custom codes must be:
- At least 6 characters long
- Unique (not already in use)
- Case-insensitive (stored in uppercase)

## Validation Rules

### Redemption Restrictions
- User must have `free` or `trial` plan
- Code must not be already used
- Code must not be expired (if expiration date is set)
- Code must exist

### Creation Restrictions
- Only admins can create codes
- Plan must be `pro_month` or `pro_year`
- Custom code must be unique and at least 6 characters

## Migration

Run the migration to create the promo code table:

```bash
cd moodlog-backend
alembic upgrade head
```

## Code Structure

- **Model**: `app/models/promo_code.py`
- **CRUD**: `app/crud/promo_code.py`
- **Schemas**: `app/schemas/promo_code.py`
- **Routes**: `app/api/v1/routes/promo_codes.py`

## Future Enhancements

Potential improvements:
- Bulk code generation
- Usage statistics and analytics
- Code categories/tags
- Discount codes (percentage or fixed amount off)
- Multi-use codes (with usage limit)
- Code sharing restrictions (one per user, etc.)





