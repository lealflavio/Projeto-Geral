# Frontend Documentation

## Overview

The frontend provides an interactive user interface for visualizing data extracted from technical reports. It features dashboards, filters, and data export capabilities for the Projeto-Geral system.

## Technology Stack

- **Framework**: React
- **UI Library**: Material-UI
- **State Management**: Redux
- **Charts**: Chart.js
- **API Client**: Axios
- **Deployment**: Netlify

## Features

- **Dashboard**: Visual representation of KPIs and report metrics
- **Report Viewer**: Detailed view of extracted report data
- **Technician Management**: Interface for managing technician information
- **User Management**: Admin interface for user accounts
- **Settings**: System configuration options
- **Export**: Data export in various formats (CSV, PDF, Excel)

## Project Structure

```
frontend/
├── public/              # Static files
├── src/
│   ├── assets/          # Images, fonts, etc.
│   ├── components/      # Reusable UI components
│   │   ├── common/      # Generic components
│   │   ├── dashboard/   # Dashboard-specific components
│   │   ├── reports/     # Report-related components
│   │   └── layout/      # Layout components
│   ├── config/          # Configuration files
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── redux/           # Redux store, actions, reducers
│   ├── services/        # API services
│   ├── styles/          # Global styles
│   ├── utils/           # Utility functions
│   ├── App.js           # Main application component
│   └── index.js         # Entry point
└── package.json         # Dependencies and scripts
```

## Component Documentation

### Dashboard Components

#### DashboardPage

Main dashboard page that displays KPIs and charts.

Props:
- `period`: Time period for data (day, week, month, year)
- `refreshInterval`: Auto-refresh interval in seconds

#### KPICard

Card component for displaying a single KPI.

Props:
- `title`: KPI title
- `value`: KPI value
- `icon`: Icon to display
- `color`: Card color
- `trend`: Trend indicator (up, down, neutral)
- `trendValue`: Percentage change

#### ReportChart

Chart component for visualizing report data.

Props:
- `data`: Chart data
- `type`: Chart type (bar, line, pie)
- `options`: Chart.js options

### Report Components

#### ReportList

List of reports with filtering and sorting.

Props:
- `reports`: Array of report objects
- `onSelectReport`: Callback for report selection
- `filters`: Filter options

#### ReportDetail

Detailed view of a single report.

Props:
- `report`: Report object
- `onBack`: Callback for back button
- `onEdit`: Callback for edit button

### Layout Components

#### MainLayout

Main application layout with header, sidebar, and content area.

Props:
- `children`: Content to render
- `title`: Page title

#### Sidebar

Navigation sidebar component.

Props:
- `items`: Navigation items
- `collapsed`: Whether sidebar is collapsed

## API Integration

The frontend communicates with the backend API using Axios. API services are organized by domain:

```javascript
// src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
```

Example service for reports:

```javascript
// src/services/reportService.js
import api from './api';

export const getReports = async (params) => {
  const response = await api.get('/reports', { params });
  return response.data;
};

export const getReportById = async (id) => {
  const response = await api.get(`/reports/${id}`);
  return response.data;
};

export const createReport = async (data) => {
  const response = await api.post('/reports', data);
  return response.data;
};

// More methods...
```

## State Management

Redux is used for global state management. The store is organized by domain:

```javascript
// src/redux/store.js
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import reportReducer from './slices/reportSlice';
import technicianReducer from './slices/technicianSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    reports: reportReducer,
    technicians: technicianReducer,
    ui: uiReducer,
  },
});
```

## Authentication

The frontend uses JWT for authentication. Tokens are stored in localStorage and included in API requests:

```javascript
// src/services/authService.js
import api from './api';

export const login = async (credentials) => {
  const response = await api.post('/auth/login', credentials);
  const { access_token, refresh_token, user } = response.data;
  
  localStorage.setItem('token', access_token);
  localStorage.setItem('refreshToken', refresh_token);
  localStorage.setItem('user', JSON.stringify(user));
  
  return user;
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user');
};

// More methods...
```

## Routing

React Router is used for client-side routing:

```javascript
// src/App.js
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PrivateRoute from './components/common/PrivateRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ReportsPage from './pages/ReportsPage';
import ReportDetailPage from './pages/ReportDetailPage';
import TechniciansPage from './pages/TechniciansPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
        <Route path="/reports" element={<PrivateRoute><ReportsPage /></PrivateRoute>} />
        <Route path="/reports/:id" element={<PrivateRoute><ReportDetailPage /></PrivateRoute>} />
        <Route path="/technicians" element={<PrivateRoute><TechniciansPage /></PrivateRoute>} />
        <Route path="/settings" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Theming

Material-UI theming is used for consistent styling:

```javascript
// src/styles/theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    // More typography settings...
  },
  // More theme settings...
});

export default theme;
```

## Local Development

1. Install dependencies:
   ```bash
   cd dashboard/frontend
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`.

## Building for Production

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Testing

Run unit tests:

```bash
npm test
```

Run end-to-end tests:

```bash
npm run test:e2e
```

## Deployment

The frontend is deployed on Netlify. Deployment is triggered automatically when changes are pushed to the `master` branch.

## Performance Optimization

- Code splitting for route-based components
- Lazy loading for images and heavy components
- Memoization for expensive calculations
- Virtualized lists for large data sets
- Optimized bundle size with tree shaking

## Accessibility

The frontend follows WCAG 2.1 AA guidelines:

- Proper semantic HTML
- ARIA attributes where necessary
- Keyboard navigation support
- Color contrast compliance
- Screen reader compatibility

## Browser Compatibility

The frontend supports:

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## Troubleshooting

### Common Issues

#### API Connection Errors

If the frontend cannot connect to the API:

1. Check that the backend is running
2. Verify the API URL in `.env`
3. Check for CORS issues in the browser console

#### Authentication Issues

If login fails or protected routes are inaccessible:

1. Clear localStorage and try logging in again
2. Check that the token is valid
3. Verify that the API is returning the correct response format

#### Rendering Problems

If components don't render correctly:

1. Check the browser console for errors
2. Verify that the data structure matches what components expect
3. Try clearing the browser cache

---

Documentation updated: May 2025
