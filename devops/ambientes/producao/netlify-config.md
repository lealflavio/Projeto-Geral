# Configuração de Produção - Netlify.com

## Frontend Service Configuration
- Site Name: wondercom-automation
- Build Command: `cd dashboard/frontend && npm install && npm run build`
- Publish Directory: dashboard/frontend/dist
- Auto-Deploy: Yes (on main branch)
- Environment Variables:
  - VITE_API_URL: https://wondercom-automation-backend.onrender.com
  - NODE_ENV: production
- Deploy Contexts:
  - Production: main branch
  - Preview: pull requests
- Build Settings:
  - Base Directory: dashboard/frontend
  - Package Manager: npm
  - Node Version: 16.x
- Domain Settings:
  - Primary Domain: wondercom-automation.netlify.app
  - Custom Domain: (if applicable)
- Deploy Notifications:
  - Email on failed deploys
  - Slack integration (if applicable)
