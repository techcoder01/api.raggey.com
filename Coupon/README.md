# Coupon API Documentation

## Overview
The Coupon API provides functionality for managing promotional codes, discount coupons, and tracking their usage. It supports both **beta/input codes** (manually entered by users) and **card-style promotional coupons** (displayed as cards in the UI).

## Features
- ✅ Beta coupon codes with usage limits
- ✅ Card promotional coupons for display
- ✅ Percentage and fixed amount discounts
- ✅ Order minimum requirements
- ✅ Maximum discount caps
- ✅ Usage limits (total and per user)
- ✅ Validity period management
- ✅ Coupon validation and application
- ✅ Usage tracking and analytics

## Models

### Coupon
Main coupon model with fields:
- `code`: Unique coupon code (e.g., BETA50, WELCOME10)
- `name_en/name_ar`: Coupon name in English/Arabic
- `description_en/description_ar`: Description in English/Arabic
- `coupon_type`: beta, card, or general
- `discount_type`: percentage or fixed
- `discount_value`: Discount amount
- `max_uses`: Total usage limit (null = unlimited)
- `max_uses_per_user`: Per-user usage limit
- `min_order_amount`: Minimum order requirement
- `max_discount_amount`: Maximum discount cap (for percentage coupons)
- `valid_from/valid_until`: Validity period
- `is_active`: Active status
- `is_featured`: Featured card display
- `card_color/card_icon`: Card styling (for card coupons)

### CouponUsage
Tracks each coupon application with:
- `coupon`: Foreign key to Coupon
- `user_id`: User who applied the coupon
- `order_id`: Associated order
- `discount_amount`: Actual discount applied
- `order_amount`: Original order amount
- `used_at`: Timestamp

## API Endpoints

### 1. List All Coupons
```
GET /api/coupons/
```
Returns all coupons (admin only for full list).

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [...]
}
```

---

### 2. Get Card Coupons for Display
```
GET /api/coupons/card-coupons/
GET /api/coupons/card-coupons/?featured=true
```

Returns active card-style promotional coupons for display in checkout UI.

**Query Parameters:**
- `featured` (optional): Filter only featured coupons (true/false)

**Response:**
```json
{
  "success": true,
  "count": 3,
  "coupons": [
    {
      "id": 2,
      "code": "WELCOME10",
      "name_en": "Welcome Discount",
      "name_ar": "خصم الترحيب",
      "description_en": "10% off your first order",
      "description_ar": "خصم 10٪ على طلبك الأول",
      "discount_type": "percentage",
      "discount_value": "10.000",
      "discount_display": "10.0%",
      "min_order_amount": "20.000",
      "is_featured": true,
      "card_color": "#0B5D35",
      "card_icon": "welcome",
      "valid_until": null
    },
    {
      "id": 3,
      "code": "EID2024",
      "name_en": "Eid Special",
      "name_ar": "عرض العيد",
      "description_en": "15 KWD off on orders above 50 KWD",
      "description_ar": "خصم 15 د.ك على الطلبات فوق 50 د.ك",
      "discount_type": "fixed",
      "discount_value": "15.000",
      "discount_display": "15.0 KWD",
      "min_order_amount": "50.000",
      "is_featured": true,
      "card_color": "#D4AF37",
      "card_icon": "eid",
      "valid_until": "2025-01-07T21:31:45.123456Z"
    }
  ]
}
```

---

### 3. Validate Coupon Code
```
POST /api/coupons/validate/
```

Validates a coupon code without applying it. Checks validity, user eligibility, and calculates discount.

**Request Body:**
```json
{
  "code": "BETA50",
  "user_id": "user123",
  "order_amount": 50.000
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Coupon is valid",
  "coupon": {
    "id": 1,
    "code": "BETA50",
    "name_en": "Beta User Discount",
    "discount_type": "percentage",
    "discount_value": "50.000",
    ...
  },
  "discount_amount": 20.0,
  "final_amount": 30.0
}
```

**Error Response (400/404):**
```json
{
  "success": false,
  "message": "Coupon has expired"
}
```

**Validation Checks:**
- ✓ Coupon exists
- ✓ Coupon is active
- ✓ Within validity period
- ✓ Usage limits not exceeded
- ✓ User hasn't exceeded per-user limit
- ✓ Order meets minimum amount requirement

---

### 4. Apply Coupon
```
POST /api/coupons/apply/
```

Applies a coupon and records its usage. This should be called when the order is confirmed.

**Request Body:**
```json
{
  "code": "BETA50",
  "user_id": "user123",
  "order_amount": 50.000,
  "order_id": "order_12345"  // optional
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Coupon applied successfully",
  "coupon": {...},
  "usage": {
    "id": 1,
    "coupon": 1,
    "coupon_code": "BETA50",
    "user_id": "user123",
    "order_id": "order_12345",
    "discount_amount": "20.000",
    "order_amount": "50.000",
    "used_at": "2024-12-08T21:35:12.123456Z"
  },
  "discount_amount": 20.0,
  "final_amount": 30.0
}
```

**Error Response (400):**
```json
{
  "success": false,
  "message": "You have already used this coupon the maximum number of times"
}
```

**Side Effects:**
- Increments `coupon.current_uses`
- Creates a `CouponUsage` record
- All operations are atomic (transaction)

---

### 5. Get Coupon by Code
```
GET /api/coupons/by-code/{code}/
```

Get detailed information about a specific coupon by its code.

**Example:**
```
GET /api/coupons/by-code/BETA50/
```

**Response:**
```json
{
  "success": true,
  "coupon": {
    "id": 1,
    "code": "BETA50",
    "name_en": "Beta User Discount",
    "name_ar": "خصم مستخدمي البيتا",
    "discount_display": "50.0%",
    "is_valid_status": {
      "valid": true,
      "message": "Valid"
    },
    ...
  }
}
```

---

### 6. Get User Coupon Usage History
```
GET /api/coupon-usages/by-user/{user_id}/
```

Get all coupons used by a specific user (admin only).

**Example:**
```
GET /api/coupon-usages/by-user/user123/
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "usages": [
    {
      "id": 1,
      "coupon_code": "BETA50",
      "coupon_name_en": "Beta User Discount",
      "discount_amount": "20.000",
      "order_amount": "50.000",
      "used_at": "2024-12-08T21:35:12Z"
    },
    ...
  ]
}
```

---

### 7. Get Order Coupon Usage
```
GET /api/coupon-usages/by-order/{order_id}/
```

Get the coupon used for a specific order (admin only).

**Example:**
```
GET /api/coupon-usages/by-order/order_12345/
```

---

## Admin Panel

### Coupon Management
Access at `/admin/Coupon/coupon/`

**Features:**
- Create/edit/delete coupons
- View usage statistics
- Bulk activate/deactivate
- Filter by type, status, date
- Visual status indicators

**Bulk Actions:**
- Activate selected coupons
- Deactivate selected coupons

### Usage Tracking
Access at `/admin/Coupon/couponusage/`

**Features:**
- View all coupon applications
- Filter by user, order, date
- Read-only (no manual creation/editing)
- Export usage data

---

## Sample Coupons

The system comes with 5 pre-seeded coupons:

1. **BETA50** - Beta user discount (50% off, max 20 KWD)
2. **WELCOME10** - Welcome discount (10% off first order)
3. **EID2024** - Eid special (15 KWD off orders above 50 KWD)
4. **FREEDEL** - Free delivery (5 KWD off)
5. **SUMMER25** - Summer sale (25% off, max 10 KWD)

### Re-seed Coupons
To add sample coupons:
```bash
python manage.py seed_coupons
```

---

## Usage Flow

### For Input Coupons (Beta codes):
1. User enters coupon code in checkout
2. Frontend calls `POST /api/coupons/validate/` to check validity
3. Display discount amount if valid
4. On order confirmation, call `POST /api/coupons/apply/`
5. Store discount in order details

### For Card Coupons:
1. Frontend calls `GET /api/coupons/card-coupons/?featured=true`
2. Display coupons as cards with styling (color, icon)
3. User selects a card coupon
4. Auto-apply code and follow same validation flow

---

## Error Codes

| Code | Message | Reason |
|------|---------|--------|
| 404 | Invalid coupon code | Coupon doesn't exist |
| 400 | Coupon is not active | Coupon deactivated |
| 400 | Coupon is not yet valid | Before valid_from date |
| 400 | Coupon has expired | After valid_until date |
| 400 | Coupon usage limit reached | Max total uses exceeded |
| 400 | You have already used this coupon... | User limit exceeded |
| 400 | Minimum order amount is X KWD | Order too small |

---

## Testing with Postman

Import the included Postman collection or use these examples:

```bash
# Get card coupons
curl -X GET http://localhost:8000/api/coupons/card-coupons/

# Validate coupon
curl -X POST http://localhost:8000/api/coupons/validate/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "BETA50",
    "user_id": "user123",
    "order_amount": 50.000
  }'

# Apply coupon
curl -X POST http://localhost:8000/api/coupons/apply/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "BETA50",
    "user_id": "user123",
    "order_amount": 50.000,
    "order_id": "order_12345"
  }'
```

---

## Database Schema

```sql
-- Coupon table
CREATE TABLE Coupon (
    id INTEGER PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    name_en VARCHAR(100),
    name_ar VARCHAR(100),
    coupon_type VARCHAR(20),
    discount_type VARCHAR(20),
    discount_value DECIMAL(10,3),
    max_uses INTEGER NULL,
    current_uses INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    ...
);

-- CouponUsage table
CREATE TABLE CouponUsage (
    id INTEGER PRIMARY KEY,
    coupon_id INTEGER REFERENCES Coupon(id),
    user_id VARCHAR(255),
    order_id VARCHAR(255),
    discount_amount DECIMAL(10,3),
    order_amount DECIMAL(10,3),
    used_at TIMESTAMP,
    INDEX idx_user_coupon (user_id, coupon_id),
    INDEX idx_order (order_id)
);
```

---

## Support

For issues or questions, contact the development team or check the admin panel at `/admin/`.
