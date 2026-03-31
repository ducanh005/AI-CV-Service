import {
  AppstoreOutlined,
  TeamOutlined,
  SolutionOutlined,
  UserOutlined,
  ApiOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { Avatar, Layout, Menu, Typography } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuthStore } from '../store/authStore';

const { Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: '/hr/dashboard', icon: <AppstoreOutlined />, label: 'Bảng điều khiển' },
  { key: '/hr/candidates', icon: <SolutionOutlined />, label: 'Ứng viên' },
  { key: '/hr/jobs', icon: <TeamOutlined />, label: 'Tin tuyển dụng' },
  { key: '/hr/staff', icon: <UserOutlined />, label: 'Nhân viên' },
  { key: '/hr/integrations', icon: <ApiOutlined />, label: 'Tích hợp' },
];

function HRLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearSession } = useAuthStore();

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
            <Avatar className="bg-[#00011f]" size={44}>
              {(user?.full_name || 'H').charAt(0)}
            </Avatar>
            <div>
              <div className="text-[36px] font-semibold text-[#111827]">HR Manager</div>
              <Text className="!text-[30px] !text-[#6b7289]">{user?.email || 'hr@company.com'}</Text>
            </div>
          </div>

          <button
            type="button"
            className="flex items-center gap-2 bg-transparent text-[36px] font-semibold text-[#111827]"
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
