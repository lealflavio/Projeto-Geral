# Backend API Documentation

## Overview

The backend API provides RESTful endpoints for storing and retrieving data extracted from technical reports. It handles authentication, data processing, and business logic for the Projeto-Geral system.

## Technology Stack

- **Framework**: Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Deployment**: Render

## API Endpoints

### Authentication

#### Login

```
POST /api/auth/login
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "User Name",
    "email": "user@example.com",
    "role": "admin"
  }
}
```

#### Refresh Token

```
POST /api/auth/refresh
```

Request headers:
```
Authorization: Bearer <refresh_token>
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Reports

#### Get All Reports

```
GET /api/reports
```

Query parameters:
- `page` (optional): Page number for pagination
- `per_page` (optional): Items per page
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `technician_id` (optional): Filter by technician

Response:
```json
{
  "reports": [
    {
      "id": 1,
      "title": "Report Title",
      "date": "2025-05-01",
      "technician": "John Doe",
      "equipment": ["Equipment 1", "Equipment 2"],
      "materials": ["Material 1", "Material 2"],
      "status": "processed"
    },
    ...
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
}
```

#### Get Report by ID

```
GET /api/reports/{id}
```

Response:
```json
{
  "id": 1,
  "title": "Report Title",
  "date": "2025-05-01",
  "technician": "John Doe",
  "equipment": ["Equipment 1", "Equipment 2"],
  "materials": ["Material 1", "Material 2"],
  "status": "processed",
  "content": {
    "section1": "Content of section 1",
    "section2": "Content of section 2",
    ...
  }
}
```

#### Create Report

```
POST /api/reports
```

Request body:
```json
{
  "title": "New Report",
  "date": "2025-05-10",
  "technician_id": 5,
  "equipment": ["Equipment 1", "Equipment 2"],
  "materials": ["Material 1", "Material 2"],
  "content": {
    "section1": "Content of section 1",
    "section2": "Content of section 2"
  }
}
```

Response:
```json
{
  "id": 101,
  "message": "Report created successfully"
}
```

### Technicians

#### Get All Technicians

```
GET /api/technicians
```

Response:
```json
{
  "technicians": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "active": true
    },
    ...
  ]
}
```

#### Get Technician by ID

```
GET /api/technicians/{id}
```

Response:
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "active": true,
  "reports_count": 42,
  "last_report_date": "2025-05-01"
}
```

### Dashboard Data

#### Get KPI Summary

```
GET /api/dashboard/kpi
```

Response:
```json
{
  "total_reports": 1250,
  "reports_this_month": 42,
  "active_technicians": 15,
  "average_processing_time": "1.5 seconds"
}
```

#### Get Reports by Period

```
GET /api/dashboard/reports-by-period
```

Query parameters:
- `period` (optional): "day", "week", "month", "year" (default: "month")
- `start_date` (optional): Start date for custom period
- `end_date` (optional): End date for custom period

Response:
```json
{
  "labels": ["2025-05-01", "2025-05-02", ...],
  "data": [5, 7, 3, ...]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or invalid credentials
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

## Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Rate Limiting

API requests are limited to 100 requests per minute per IP address. When the limit is exceeded, the API returns a `429 Too Many Requests` status code.

## Database Schema

The backend uses the following main tables:

- `users`: User accounts and authentication
- `technicians`: Information about technicians
- `reports`: Extracted report data
- `equipment`: Equipment mentioned in reports
- `materials`: Materials mentioned in reports

## Local Development

1. Install dependencies:
   ```bash
   cd dashboard/backend
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run database migrations:
   ```bash
   python manage.py db upgrade
   ```

4. Start the development server:
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`.

## Testing

Run the test suite:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=app
```

## Deployment

The backend is deployed on Render. Deployment is triggered automatically when changes are pushed to the `master` branch.

## Monitoring

The backend includes monitoring endpoints for health checks:

```
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.2.3",
  "database": "connected",
  "uptime": "5d 12h 30m"
}
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

If you encounter database connection issues:

1. Verify PostgreSQL is running
2. Check database credentials in `.env`
3. Ensure the database exists and is accessible

#### JWT Token Issues

If authentication fails:

1. Check that the token is valid and not expired
2. Verify the secret key in the configuration
3. Ensure the token is included in the Authorization header

## Performance Considerations

- The API uses connection pooling for database connections
- Responses are cached where appropriate
- Large result sets are paginated
- Heavy processing tasks are handled asynchronously

---

Documentation updated: May 2025
