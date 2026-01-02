# OpenCATS SaaS REST API Documentation

Version: 1.0
Base URL: `https://yourapp.com/api/v1`

## Authentication

### JWT Token Authentication

Most API endpoints require JWT token authentication. To authenticate:

1. **Login to get token:**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 86400,
  "user": {
    "user_id": 1,
    "username": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "access_level": 400,
    "site_id": 1
  }
}
```

2. **Use token in subsequent requests:**
```bash
GET /api/v1/candidates
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### API Key Authentication (Enterprise Only)

Enterprise plan customers can use API keys for server-to-server authentication:

```bash
GET /api/v1/candidates
X-API-Key: your-api-key-here
```

### Refresh Token

Tokens expire after 24 hours. Refresh before expiration:

```bash
POST /api/v1/auth/refresh
Authorization: Bearer <current-token>
```

## Rate Limiting

- Login endpoint: 5 requests per minute
- Other endpoints: Rate limits apply based on subscription plan

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Filtering & Search

Most list endpoints support filtering and search:

**Common Parameters:**
- `search`: Full-text search
- `sort`: Field to sort by
- `order`: `asc` or `desc`
- `hot_only`: Filter hot items (true/false)

## Error Responses

All errors return consistent JSON:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "field": "field_name"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions or plan limit)
- `404` - Not Found
- `409` - Conflict (duplicate)
- `500` - Internal Server Error

---

## Candidates API

### List Candidates

```bash
GET /api/v1/candidates?page=1&per_page=20&search=python&hot_only=true
```

**Query Parameters:**
- `search`: Search name, email, or skills
- `hot_only`: Filter hot candidates (true/false)
- `active_only`: Filter active candidates (true/false)
- `sort`: Field to sort by (default: date_created)
- `order`: asc/desc (default: desc)

**Response:**
```json
{
  "data": [
    {
      "candidate_id": 123,
      "first_name": "John",
      "last_name": "Doe",
      "email1": "john@example.com",
      "phone_cell": "555-1234",
      "key_skills": "Python, Flask, SQL",
      "is_hot": true,
      "date_created": "2024-01-15T10:30:00"
    }
  ],
  "pagination": {...}
}
```

### Get Candidate

```bash
GET /api/v1/candidates/123
```

Returns full candidate details including attachments.

### Create Candidate

```bash
POST /api/v1/candidates
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email1": "john@example.com",
  "phone_cell": "555-1234",
  "key_skills": "Python, Flask, SQL",
  "is_hot": false
}
```

**Plan Limits:** Checks max_candidates limit

**Response:** `201 Created`

### Update Candidate

```bash
PUT /api/v1/candidates/123
Content-Type: application/json

{
  "phone_cell": "555-5678",
  "key_skills": "Python, Flask, SQL, Docker"
}
```

Partial updates supported.

### Delete Candidate

```bash
DELETE /api/v1/candidates/123
```

Soft delete (sets `is_admin_hidden=True`)

### Get Candidate Pipeline

```bash
GET /api/v1/candidates/123/pipeline
```

Returns all jobs the candidate is associated with.

### Add Candidate to Job

```bash
POST /api/v1/candidates/123/pipeline
Content-Type: application/json

{
  "joborder_id": 45,
  "status": 200
}
```

**Status Codes:**
- `0` - No Contact
- `200` - Contacted
- `250` - Candidate Responded
- `300` - Qualifying
- `400` - Submitted
- `500` - Interviewing
- `600` - Offered
- `650` - Offer Accepted
- `700` - Declined Offer
- `800` - Placed

### Get Candidate Activities

```bash
GET /api/v1/candidates/123/activities
```

Returns activity history (last 50 activities).

---

## Job Orders API

### List Jobs

```bash
GET /api/v1/jobs?page=1&status=0&company_id=10
```

**Query Parameters:**
- `status`: 0=Active, 1=On Hold, 2=Closed, 3=Canceled, 4=Filled
- `company_id`: Filter by company
- `search`: Search title or description
- `hot_only`: Filter hot jobs
- `public_only`: Filter public jobs

### Get Job

```bash
GET /api/v1/jobs/123
```

Returns full job details including company and contact info.

### Create Job

```bash
POST /api/v1/jobs
Content-Type: application/json

{
  "company_id": 10,
  "contact_id": 15,
  "title": "Senior Python Developer",
  "type": 1,
  "status": 0,
  "openings": 2,
  "description": "Looking for experienced Python developer...",
  "salary": "$120k-$150k",
  "city": "San Francisco",
  "state": "CA"
}
```

**Plan Limits:** Checks max_jobs limit

### Update Job

```bash
PUT /api/v1/jobs/123
Content-Type: application/json

{
  "status": 1,
  "notes": "Put on hold pending budget approval"
}
```

### Delete Job

```bash
DELETE /api/v1/jobs/123
```

### Get Job Pipeline

```bash
GET /api/v1/jobs/123/pipeline?status=400
```

Returns all candidates in the job pipeline, grouped by status.

**Response:**
```json
{
  "data": [
    {
      "status": 400,
      "status_name": "Submitted",
      "count": 5,
      "candidates": [...]
    }
  ],
  "total_candidates": 15
}
```

### Update Pipeline Status

```bash
PUT /api/v1/jobs/123/pipeline/456/status
Content-Type: application/json

{
  "status": 400,
  "notes": "Submitted to hiring manager"
}
```

Automatically updates `openings_available` when status = 800 (Placed).

### Get Job Activities

```bash
GET /api/v1/jobs/123/activities
```

---

## Companies API

### List Companies

```bash
GET /api/v1/companies?search=tech&city=San Francisco
```

**Query Parameters:**
- `search`: Search name, city, or technologies
- `hot_only`: Filter hot companies
- `city`: Filter by city
- `state`: Filter by state

### Get Company

```bash
GET /api/v1/companies/123
```

Returns company with contacts and recent job orders.

### Create Company

```bash
POST /api/v1/companies
Content-Type: application/json

{
  "name": "TechCorp Inc",
  "phone1": "555-1234",
  "url": "https://techcorp.com",
  "city": "San Francisco",
  "state": "CA",
  "key_technologies": "Python, AWS, Docker"
}
```

### Update Company

```bash
PUT /api/v1/companies/123
Content-Type: application/json

{
  "phone1": "555-5678",
  "notes": "Updated contact information"
}
```

### Delete Company

```bash
DELETE /api/v1/companies/123
```

**Validation:** Cannot delete if company has active job orders.

---

## Contacts API

### List Contacts

```bash
GET /api/v1/contacts?company_id=10&hot_only=true
```

**Query Parameters:**
- `company_id`: Filter by company
- `search`: Search name, email, or title
- `hot_only`: Filter hot contacts
- `active_only`: Exclude contacts who left company

### Get Contact

```bash
GET /api/v1/contacts/123
```

Returns contact with company info and reporting hierarchy.

### Create Contact

```bash
POST /api/v1/contacts
Content-Type: application/json

{
  "company_id": 10,
  "first_name": "Jane",
  "last_name": "Smith",
  "title": "Hiring Manager",
  "email1": "jane@techcorp.com",
  "phone_work": "555-1234"
}
```

### Update Contact

```bash
PUT /api/v1/contacts/123
Content-Type: application/json

{
  "title": "Senior Hiring Manager",
  "phone_work": "555-5678"
}
```

### Delete Contact

```bash
DELETE /api/v1/contacts/123
```

### Mark Contact as Left Company

```bash
POST /api/v1/contacts/123/mark-left-company
```

Sets `left_company=true` without deleting the record.

---

## Usage Examples

### Python

```python
import requests

# Login
response = requests.post('https://yourapp.com/api/v1/auth/login', json={
    'username': 'user@example.com',
    'password': 'password123'
})
token = response.json()['token']

# Get candidates
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://yourapp.com/api/v1/candidates', headers=headers)
candidates = response.json()['data']

# Create candidate
new_candidate = {
    'first_name': 'John',
    'last_name': 'Doe',
    'email1': 'john@example.com',
    'key_skills': 'Python, Flask'
}
response = requests.post('https://yourapp.com/api/v1/candidates',
                        headers=headers, json=new_candidate)
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('https://yourapp.com/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password123'
  })
});
const {token} = await loginResponse.json();

// Get candidates
const response = await fetch('https://yourapp.com/api/v1/candidates', {
  headers: {'Authorization': `Bearer ${token}`}
});
const {data: candidates} = await response.json();

// Create candidate
const newCandidate = {
  first_name: 'John',
  last_name: 'Doe',
  email1: 'john@example.com',
  key_skills: 'Python, Flask'
};
const createResponse = await fetch('https://yourapp.com/api/v1/candidates', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(newCandidate)
});
```

### cURL

```bash
# Login
curl -X POST https://yourapp.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password123"}'

# Get candidates (replace TOKEN)
curl https://yourapp.com/api/v1/candidates \
  -H "Authorization: Bearer TOKEN"

# Create candidate
curl -X POST https://yourapp.com/api/v1/candidates \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email1": "john@example.com",
    "key_skills": "Python, Flask"
  }'
```

---

## Webhooks (Coming Soon)

Webhook notifications for:
- Candidate created/updated
- Job order created/updated
- Pipeline status changed
- Placement made

---

## Rate Limits by Plan

| Plan | Requests/Hour | Concurrent |
|------|--------------|------------|
| Starter | 1,000 | 5 |
| Professional | 5,000 | 10 |
| Enterprise | 20,000 | 25 |

---

## Support

For API support:
- Email: api@yourapp.com
- Documentation: https://docs.yourapp.com
- Status: https://status.yourapp.com
