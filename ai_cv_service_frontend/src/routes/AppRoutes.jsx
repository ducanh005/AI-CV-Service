import { Navigate, Route, Routes } from 'react-router-dom';

import ProtectedRoute from './ProtectedRoute';
import { AuthProvider, useAuthStore } from '../store/authStore';
import LoginPage from '../pages/auth/LoginPage';
import RegisterPage from '../pages/auth/RegisterPage';
import UserLayout from '../layouts/UserLayout';
import HRLayout from '../layouts/HRLayout';
import UserDashboardPage from '../pages/user/UserDashboardPage';
import JobDetailPage from '../pages/user/JobDetailPage';
import CompanyPage from '../pages/user/CompanyPage';
import InterviewPage from '../pages/user/InterviewPage';
import UserProfilePage from '../pages/user/UserProfilePage';
import HRDashboardPage from '../pages/hr/HRDashboardPage';
import HRCandidatesPage from '../pages/hr/HRCandidatesPage';
import HRJobsPage from '../pages/hr/HRJobsPage';
import HRStaffPage from '../pages/hr/HRStaffPage';
import HRIntegrationsPage from '../pages/hr/HRIntegrationsPage';
import HRProfilePage from '../pages/hr/HRProfilePage';
import AdminDashboardPage from '../pages/admin/AdminDashboardPage';
import NotFoundPage from '../pages/NotFoundPage';

function RootRedirect() {
  const { user } = useAuthStore();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role === 'hr') {
    return <Navigate to="/hr/dashboard" replace />;
  }
  if (user.role === 'admin') {
    return <Navigate to="/admin/dashboard" replace />;
  }
  return <Navigate to="/user/dashboard" replace />;
}

function AppRoutesContent() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute allowedRoles={['user']} />}>
        <Route path="/user" element={<UserLayout />}>
          <Route path="dashboard" element={<UserDashboardPage />} />
          <Route path="jobs/:id" element={<JobDetailPage />} />
          <Route path="company" element={<CompanyPage />} />
          <Route path="interviews" element={<InterviewPage />} />
          <Route path="profile" element={<UserProfilePage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute allowedRoles={['hr']} />}>
        <Route path="/hr" element={<HRLayout />}>
          <Route path="dashboard" element={<HRDashboardPage />} />
          <Route path="candidates" element={<HRCandidatesPage />} />
          <Route path="jobs" element={<HRJobsPage />} />
          <Route path="staff" element={<HRStaffPage />} />
          <Route path="integrations" element={<HRIntegrationsPage />} />
          <Route path="profile" element={<HRProfilePage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

function AppRoutes() {
  return (
    <AuthProvider>
      <AppRoutesContent />
    </AuthProvider>
  );
}

export default AppRoutes;
