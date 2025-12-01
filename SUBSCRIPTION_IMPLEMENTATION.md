# Subscription System Implementation

This document describes the subscription system implementation with Webkassa.kz payment gateway integration.

## Overview

The subscription system supports four plans:
- **Free**: Basic features with limited AI questions (5 per day)
- **Trial**: 14-day full Pro access
- **Pro Monthly**: Monthly subscription
- **Pro Yearly**: Annual subscription

## Database Models

### User Model Updates
Added subscription fields to the `User` model:
- `plan`: Current plan ("free", "trial", "pro_month", "pro_year")
- `plan_started_at`: When the current plan started
- `plan_expires_at`: When the current plan expires
- `trial_used`: Whether the user has used their trial
- `subscription_status`: Status ("active", "expired", "cancelled")

### Subscription Model
Tracks subscription history and changes for each user.

### Payment Model
Stores all payment transactions with Webkassa.kz integration data.

## Features Gating

Pro features (gated behind subscription):
- Main themes (ThemesCard)
- Weekly insights
- Monthly insights
- Voice recording
- Visual themes
- Visual effects
- Unlimited AI questions (Free: 5 per day)

## API Endpoints

### GET `/api/v1/subscriptions/plans`
Get all available subscription plans with features and pricing.

### GET `/api/v1/subscriptions/current`
Get current user's subscription status and features.

### POST `/api/v1/subscriptions/start-trial`
Start a 14-day free trial (one-time use).

### POST `/api/v1/subscriptions/subscribe`
Initiate subscription payment. Returns payment URL for Webkassa.kz.

**Request:**
```json
{
  "plan": "pro_month"  // or "pro_year"
}
```

**Response:**
```json
{
  "payment_id": "uuid",
  "order_id": "uuid",
  "payment_url": "https://webkassa.kz/payment/...",
  "amount": 2990.0
}
```

### POST `/api/v1/subscriptions/webhook/webkassa`
Webhook endpoint for Webkassa.kz payment notifications. This should be configured in Webkassa dashboard.

### GET `/api/v1/subscriptions/payment/{payment_id}/status`
Check payment status (for polling from frontend).

## Configuration

Add these environment variables to your `.env` file:

```env
# Webkassa.kz settings
WEBKASSA_API_URL=https://api.webkassa.kz/v1
WEBKASSA_API_KEY=your-webkassa-api-key
WEBKASSA_CASHBOX_ID=your-cashbox-id

# Frontend URL for payment redirects
FRONTEND_URL=http://localhost:3000
```

## Usage in Code

### Check if user can use a feature:

```python
from app.services.plan_service import can_use_feature, is_plan_active

if is_plan_active(user) and can_use_feature(user, "has_themes"):
    # User can access themes
    pass
```

### Protect an endpoint with Pro feature requirement:

```python
from app.core.deps import require_pro_feature

@router.get("/themes")
def get_themes(
    current_user: User = Depends(require_pro_feature("has_themes"))
):
    # This endpoint requires Pro subscription
    pass
```

### Get AI questions limit:

```python
from app.services.plan_service import get_ai_questions_limit

limit = get_ai_questions_limit(user)  # Returns None for unlimited, or int for limit
```

## Migration

Run the migration to create the subscription tables:

```bash
cd moodlog-backend
alembic upgrade head
```

## Pricing Configuration

Edit `app/services/plan_service.py` to adjust pricing:

```python
PLAN_CONFIG = {
    "pro_month": {
        "price_monthly": 2990,  # Adjust this
        ...
    },
    "pro_year": {
        "price_yearly": 29900,  # Adjust this
        ...
    },
}
```

## Webhook Security

**Important**: In production, you should verify the webhook signature from Webkassa.kz for security. The current implementation accepts webhooks without signature verification.

## Next Steps

1. Configure Webkassa.kz credentials in environment variables
2. Set up webhook URL in Webkassa dashboard: `https://your-domain.com/api/v1/subscriptions/webhook/webkassa`
3. Test the payment flow
4. Implement frontend components for:
   - Plan selection page
   - Payment flow
   - Subscription status display
   - Feature gating UI

