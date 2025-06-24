# Complete API Testing Guide - Asset Management System

## Initial Setup & Verification

### Step 1: Start the Server
```bash
python manage.py runserver
```
**Expected Result**: Server should start on `http://127.0.0.1:8000/`

### Step 2: Access Swagger Documentation
Navigate to: `http://127.0.0.1:8000/swagger/`

**What you should see:**
- Complete API documentation interface
- All endpoints listed with descriptions
- Interactive "Try it out" buttons
- Schema definitions for models

---

## Testing Each API Endpoint

### 1. CREATE ASSET (POST /api/assets/)

**Purpose**: Create a new asset with service and expiration times

**Step-by-step:**
1. In Swagger, find **"POST /api/assets/"**
2. Click **"Try it out"**
3. Replace the example JSON with this test data:

```json
{
  "name": "Server Rack A1",
  "description": "Main server rack in data center",
  "service_time": "2025-06-24T15:30:00Z",
  "expiration_time": "2025-06-25T10:00:00Z",
  "is_serviced": false
}
```

**Important Notes:**
- `service_time` must be BEFORE `expiration_time`
- Times should be in future (adjust dates as needed)
- Use ISO 8601 format with 'Z' for UTC

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "name": "Server Rack A1",
  "description": "Main server rack in data center",
  "service_time": "2025-06-24T15:30:00Z",
  "expiration_time": "2025-06-25T10:00:00Z",
  "is_serviced": false,
  "is_expired": false,
  "is_service_overdue": false,
  "created_at": "2025-06-24T12:00:00.123456Z",
  "updated_at": "2025-06-24T12:00:00.123456Z"
}
```

**Test Invalid Data (Should Fail):**
```json
{
  "name": "Invalid Asset",
  "service_time": "2025-06-25T10:00:00Z",
  "expiration_time": "2025-06-24T15:30:00Z"
}
```
**Expected**: 400 Bad Request with validation error

---

### 2. GET ALL ASSETS (GET /api/assets/)

**Purpose**: Retrieve list of all assets

**Step-by-step:**
1. Find **"GET /api/assets/"**
2. Click **"Try it out"**
3. Click **"Execute"**

**Expected Response (200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Server Rack A1",
      "description": "Main server rack in data center",
      "service_time": "2025-06-24T15:30:00Z",
      "expiration_time": "2025-06-25T10:00:00Z",
      "is_serviced": false,
      "is_expired": false,
      "is_service_overdue": false,
      "created_at": "2025-06-24T12:00:00.123456Z",
      "updated_at": "2025-06-24T12:00:00.123456Z"
    }
  ]
}
```

---

### 3. GET SINGLE ASSET (GET /api/assets/{id}/)

**Purpose**: Retrieve specific asset details

**Step-by-step:**
1. Find **"GET /api/assets/{id}/"**
2. Click **"Try it out"**
3. Enter asset ID: `1`
4. Click **"Execute"**

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "name": "Server Rack A1",
  "description": "Main server rack in data center",
  "service_time": "2025-06-24T15:30:00Z",
  "expiration_time": "2025-06-25T10:00:00Z",
  "is_serviced": false,
  "is_expired": false,
  "is_service_overdue": false,
  "created_at": "2025-06-24T12:00:00.123456Z",
  "updated_at": "2025-06-24T12:00:00.123456Z"
}
```

**Test Non-existent Asset:**
- Use ID: `999`
- **Expected**: 404 Not Found

---

### 4. UPDATE ASSET (PUT /api/assets/{id}/)

**Purpose**: Update an existing asset

**Step-by-step:**
1. Find **"PUT /api/assets/{id}/"**
2. Click **"Try it out"**
3. Enter asset ID: `1`
4. Use this updated data:

```json
{
  "name": "Server Rack A1 - Updated",
  "description": "Updated description - Main server rack",
  "service_time": "2025-06-24T16:00:00Z",
  "expiration_time": "2025-06-25T12:00:00Z",
  "is_serviced": false
}
```

**Expected Response (200 OK):**
- Same structure as create, but with updated values
- `updated_at` timestamp should be newer

---

### 5. MARK ASSET AS SERVICED (POST /api/assets/{id}/mark_serviced/)

**Purpose**: Mark an asset as serviced

**Step-by-step:**
1. Find **"POST /api/assets/{id}/mark_serviced/"**
2. Click **"Try it out"**
3. Enter asset ID: `1`
4. Click **"Execute"** (no body needed)

**Expected Response (200 OK):**
```json
{
  "message": "Asset Server Rack A1 - Updated marked as serviced",
  "asset": {
    "id": 1,
    "name": "Server Rack A1 - Updated",
    "is_serviced": true,
    // ... other fields
  }
}
```

---

### 6. CREATE TEST ASSETS FOR TIMING TESTS

**Purpose**: Create assets to test notification and violation logic

**Create Asset Due for Service Soon:**
```json
{
  "name": "Asset Due Soon",
  "description": "Asset needing service in 10 minutes",
  "service_time": "2025-06-24T12:25:00Z",
  "expiration_time": "2025-06-25T12:00:00Z",
  "is_serviced": false
}
```

**Create Overdue Asset:**
```json
{
  "name": "Overdue Asset",
  "description": "Asset that missed service time",
  "service_time": "2025-06-24T10:00:00Z",
  "expiration_time": "2025-06-25T12:00:00Z",
  "is_serviced": false
}
```

**Create Expired Asset:**
```json
{
  "name": "Expired Asset",
  "description": "Asset that has expired",
  "service_time": "2025-06-24T10:00:00Z",
  "expiration_time": "2025-06-24T11:00:00Z",
  "is_serviced": false
}
```

**Important**: Adjust the timestamps based on your current time. For testing:
- "Due Soon" should be current_time + 10 minutes
- "Overdue" should be current_time - 2 hours
- "Expired" should have expiration_time < current_time

**Note**: In case you don't want to create it manually use my script which is in scripts folder just go to `scripts/dynamic_json_generator.py`

---

### 7. RUN CHECKS (POST /api/run-checks/)

**Purpose**: Trigger the periodic check for notifications and violations

**Step-by-step:**
1. First, ensure you have test assets created (from step 6)
2. Find **"POST /api/run-checks/"**
3. Click **"Try it out"**
4. Click **"Execute"** (no body needed)

**Expected Response (200 OK):**
```json
{
  "notifications_created": 1,
  "violations_created": 2,
  "message": "Check completed. Created 1 notifications and 2 violations.",
  "details": {
    "notifications": [
      {
        "asset": "Asset Due Soon",
        "type": "service",
        "time": "2025-06-24T12:25:00Z"
      }
    ],
    "violations": [
      {
        "asset": "Overdue Asset",
        "type": "not_serviced",
        "due_time": "2025-06-24T10:00:00Z"
      },
      {
        "asset": "Expired Asset",
        "type": "expired",
        "expired_time": "2025-06-24T11:00:00Z"
      }
    ]
  }
}
```

**Run Again Immediately:**
- **Expected**: Same response but with `notifications_created: 0` and `violations_created: 0`
- This proves duplicate prevention is working

---

### 8. GET NOTIFICATIONS (GET /api/notifications/)

**Purpose**: View all created notifications

**Step-by-step:**
1. Find **"GET /api/notifications/"**
2. Click **"Try it out"**
3. Click **"Execute"**

**Expected Response (200 OK):**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "asset": 2,
      "asset_name": "Asset Due Soon",
      "notification_type": "service",
      "message": "Service reminder: Asset \"Asset Due Soon\" needs service at 2025-06-24T12:25:00Z",
      "sent_at": "2025-06-24T12:15:00.123456Z"
    }
  ]
}
```

**Test Filtering:**
- Add query parameter: `?type=service`
- Add query parameter: `?asset=2`

---

### 9. GET VIOLATIONS (GET /api/violations/)

**Purpose**: View all created violations

**Step-by-step:**
1. Find **"GET /api/violations/"**
2. Click **"Try it out"**
3. Click **"Execute"**

**Expected Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "asset": 3,
      "asset_name": "Overdue Asset",
      "violation_type": "not_serviced",
      "description": "Service overdue: Asset \"Overdue Asset\" was due for service at 2025-06-24T10:00:00Z",
      "created_at": "2025-06-24T12:15:00.123456Z"
    },
    {
      "id": 2,
      "asset": 4,
      "asset_name": "Expired Asset",
      "violation_type": "expired",
      "description": "Asset expired: Asset \"Expired Asset\" expired at 2025-06-24T11:00:00Z",
      "created_at": "2025-06-24T12:15:00.123456Z"
    }
  ]
}
```

**Test Filtering:**
- Add query parameter: `?type=expired`
- Add query parameter: `?asset=3`

---

### 10. DELETE ASSET (DELETE /api/assets/{id}/)

**Purpose**: Remove an asset from the system

**Step-by-step:**
1. Find **"DELETE /api/assets/{id}/"**
2. Click **"Try it out"**
3. Enter asset ID: `1`
4. Click **"Execute"**

**Expected Response (204 No Content):**
- Empty response body
- Status code: 204

**Verify Deletion:**
- Try to GET the same asset ID
- **Expected**: 404 Not Found

---

## Complete Testing Workflow

### Scenario 1: Normal Asset Lifecycle
1. **Create asset** with future service/expiration times
2. **Get asset** to verify creation
3. **Update asset** description
4. **Mark as serviced** when service time approaches
5. **Run checks** to ensure no violations created for serviced asset
6. **Delete asset** when no longer needed

### Scenario 2: Notification Testing
1. **Create asset** with service_time = current_time + 10 minutes
2. **Run checks** immediately → should create notification
3. **Get notifications** → verify notification exists
4. **Run checks** again → should not create duplicate

### Scenario 3: Violation Testing
1. **Create asset** with service_time in the past
2. **Run checks** → should create violation
3. **Get violations** → verify violation exists
4. **Mark asset as serviced** → should not affect existing violation

---

## Error Testing Checklist

### Test These Error Scenarios:

1. **Invalid Asset Data:**
   - Empty name: `{"name": ""}`
   - Service time after expiration: `{"service_time": "2025-06-25T10:00:00Z", "expiration_time": "2025-06-24T10:00:00Z"}`
   - Invalid date format: `{"service_time": "invalid-date"}`

2. **Non-existent Resources:**
   - GET asset with ID 9999
   - PUT asset with ID 9999
   - DELETE asset with ID 9999

3. **Invalid HTTP Methods:**
   - Try POST on `/api/assets/1/` (should be PUT)
   - Try DELETE on `/api/run-checks/` (should be POST)

---

## Success Indicators

**Your API is working correctly if:**

1. All CRUD operations return proper status codes (200, 201, 204, 400, 404)
2. Asset validation prevents invalid data (service_time >= expiration_time)
3. `/run-checks/` creates notifications for assets due within 15 minutes
4. `/run-checks/` creates violations for overdue/expired assets
5. Duplicate notifications/violations are prevented
6. Filtering works on notifications and violations endpoints
7. `mark_serviced` properly updates asset status
8. All responses include proper JSON structure and required fields

---

## Database Verification (Optional)

**Access Django Admin:**
1. Create superuser: `python manage.py createsuperuser`
2. Navigate to: `http://127.0.0.1:8000/admin/`
3. Login and verify data in tables:
   - Assets
   - Notifications  
   - Violations

**Or use Django Shell:**
```bash
python manage.py shell
```

```python
from assets.models import Asset, Notification, Violation

# Check counts
print(f"Assets: {Asset.objects.count()}")
print(f"Notifications: {Notification.objects.count()}")
print(f"Violations: {Violation.objects.count()}")

# Check specific records
print(Asset.objects.all())
print(Notification.objects.all())
print(Violation.objects.all())
```

This comprehensive testing guide ensures every aspect of your Asset Management API is functioning correctly!