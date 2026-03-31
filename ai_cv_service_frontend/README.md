# Smart Recruitment & HR Management Platform - Frontend

Production-ready React frontend for SmartHire, aligned to provided designs for User/HR/Admin flows.

## Tech Stack

- React + Vite
- Ant Design
- TailwindCSS
- TanStack Query
- React Router v6
- Axios (JWT + refresh interceptors)

## Folder Structure

```text
src/
 ├── assets/
 │   └── styles.css
 ├── components/
 │   ├── auth/
 │   ├── common/
 │   ├── hr/
 │   └── user/
 ├── pages/
 │   ├── auth/
 │   ├── hr/
 │   ├── user/
 │   └── admin/
 ├── layouts/
 ├── services/
 ├── hooks/
 ├── store/
 ├── routes/
 ├── utils/
 ├── App.jsx
 └── main.jsx
```

## Main Screens Implemented

- Authentication
    - Login page
    - Register page
    - Role selection and role-based redirect
- Candidate (User)
    - Dashboard with stats + tabs (Jobs / My Applications)
    - Job list cards and apply flow
    - CV upload + AI score preview
    - Job detail page
    - Company profile + company jobs
    - Interview schedule page
- HR
    - Dashboard analytics
    - Candidate management table
    - LinkedIn import modal
    - AI CV screening modal
    - Interview scheduling modal
    - Job management (create/edit/delete)
    - Staff directory
    - Integrations page (LinkedIn/Gmail/Calendar/AI)
- Admin
    - Admin dashboard summary

## API Integration

- Base URL: `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`)
- Axios instance with:
    - Access token auto attach
    - Auto refresh on 401 using refresh token
    - Retry original request after token refresh
    - Session clear and redirect to login when refresh fails

Key service files:

- `src/services/api.js`
- `src/services/authService.js`
- `src/services/jobService.js`
- `src/services/applicationService.js`
- `src/services/cvService.js`
- `src/services/companyService.js`
- `src/services/interviewService.js`
- `src/services/integrationService.js`

## State & Data

- Session persisted in `localStorage`
- Auth context in `src/store/authStore.jsx`
- React Query hooks for all API interactions in `src/hooks/*`

## Route Protection

- `src/routes/ProtectedRoute.jsx`
- Role-based route isolation:
    - `/user/*` for candidate
    - `/hr/*` for HR
    - `/admin/*` for admin

## Setup Instructions

1. Install dependencies:

```bash
npm install
```

2. Configure env:

```bash
cp .env.example .env
```

3. Start dev server:

```bash
npm run dev
```

4. Build production:

```bash
npm run build
```

## Notes

- Frontend is responsive for desktop and mobile breakpoints.
- Ant Design components are styled with Tailwind utility classes and global CSS overrides to match provided UI language.
