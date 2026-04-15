import {
  AppstoreOutlined,
  TeamOutlined,
  SolutionOutlined,
  UserOutlined,
  LogoutOutlined,
  CalendarOutlined,
  ScheduleOutlined,
} from '@ant-design/icons';
import { Avatar, Layout, Menu, Typography } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuthStore } from '../store/authStore';
import { resolveAvatarUrl } from '../utils/media';

const { Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: '/hr/dashboard', icon: <AppstoreOutlined />, label: 'Bảng điều khiển' },
  { key: '/hr/candidates', icon: <SolutionOutlined />, label: 'Ứng viên' },
  { key: '/hr/jobs', icon: <TeamOutlined />, label: 'Tin tuyển dụng' },
  { key: '/hr/staff', icon: <TeamOutlined />, label: 'Nhân sự' },
  { key: '/hr/onboarding', icon: <SolutionOutlined />, label: 'Onboarding' },
  { key: '/hr/attendance', icon: <ScheduleOutlined />, label: 'Chấm công' },
  { key: "/hr/interviews", icon: <CalendarOutlined />, label: "Lịch phỏng vấn" },
  { key: '/hr/profile', icon: <UserOutlined />, label: 'Hồ sơ' },
];

function HRLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearSession } = useAuthStore();
  const avatarUrl = resolveAvatarUrl(user?.avatar_url);

  return (
    <Layout className="smart-layout min-h-screen bg-[#f6f6f8]">
      <Sider width={300} className="flex flex-col">
        <div className="px-7 pb-6 pt-6 text-[48px] font-bold text-[#030521]">SmartHire</div>
        <Menu
          className="smart-menu border-0 bg-transparent px-3"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />

        <div className="mt-auto border-t border-gray-200 p-7">
          <div className="mb-4 flex items-center gap-3">
            <Avatar className="bg-[#00011f]" size={46} src={avatarUrl || undefined}>
              {(user?.full_name || 'H').charAt(0)}
            </Avatar>
            <div className="min-w-0">
              <div className="truncate text-[17px] font-semibold text-[#111827]">{user?.full_name || 'HR Manager'}</div>
              <Text className="!block !truncate !text-[13px] !text-[#6b7289]">{user?.email || 'hr@company.com'}</Text>
            </div>
          </div>

          <button
            type="button"
            className="flex items-center gap-2 rounded-lg bg-transparent px-1 py-1 text-[15px] font-semibold text-[#111827] transition-colors hover:text-[#2563eb]"
            onClick={() => {
              clearSession();
              navigate('/login');
            }}
          >
            <LogoutOutlined />
            Đăng xuất
          </button>
        </div>
      </Sider>

      <Content className="p-8">
        <Outlet />
      </Content>
    </Layout>
  );
}

export default HRLayout;
