# Configuração de Produção - Render.com

## Backend Service Configuration
- Service Type: Web Service
- Name: wondercom-automation-backend
- Environment: Node
- Build Command: `cd dashboard/backend && pip install -r requirements.txt`
- Start Command: `cd dashboard/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Auto-Deploy: Yes (on main branch)
- Instance Type: Standard (CPU optimized)
- Region: Oregon (US West)
- Health Check Path: /api/health
- Environment Variables:
  - DATABASE_URL: $DATABASE_URL (from Render dashboard)
  - SECRET_KEY: $SECRET_KEY (from Render dashboard)
  - ALGORITHM: HS256
  - ACCESS_TOKEN_EXPIRE_MINUTES: 30
  - FRONTEND_URL: https://wondercom-automation.netlify.app
  - GOOGLE_APPLICATION_CREDENTIALS: /etc/secrets/google-credentials.json
  - TWILIO_AUTH_TOKEN: $TWILIO_AUTH_TOKEN (from Render dashboard)

## Database Configuration
- Service Type: PostgreSQL
- Name: wondercom-automation-db
- PostgreSQL Version: 13
- Instance Type: Standard
- Region: Oregon (US West)
- Database Name: wondercom_db
- User: wondercom_db_user
- Password: Auto-generated (store securely)

## Secrets Management
- Create secret files for sensitive credentials
- Mount secret files to appropriate paths
- Use environment variables for connection strings
