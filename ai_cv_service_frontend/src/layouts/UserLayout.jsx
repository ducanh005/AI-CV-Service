import { Layout } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';

import TopBar from '../components/common/TopBar';
import { useAuthStore } from '../store/authStore';
import { resolveAvatarUrl } from '../utils/media';

const { Content } = Layout;

function UserLayout() {
  const navigate = useNavigate();
  const { user, clearSession } = useAuthStore();

  return (
    <Layout className="min-h-screen bg-[#f6f6f8]">
      <TopBar
        userName={user?.full_name || 'Người dùng'}
        userAvatar={resolveAvatarUrl(user?.avatar_url)}
        onProfile={() => navigate('/user/profile')}
        onLogout={() => {
          clearSession();
          navigate('/login');
        }}
      />
      <Content className="px-9 pb-10 pt-6">
        <Outlet />
      </Content>
    </Layout>
  );
}

export default UserLayout;
