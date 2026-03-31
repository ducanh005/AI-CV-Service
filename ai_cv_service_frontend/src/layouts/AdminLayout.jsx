import { Card, Col, Row, Statistic, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';

import TopBar from '../components/common/TopBar';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

function AdminLayout() {
  const navigate = useNavigate();
  const { user, clearSession } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#f6f6f8]">
      <TopBar
        userName={user?.full_name || 'Admin'}
        onLogout={() => {
          clearSession();
          navigate('/login');
        }}
      />
      <div className="mx-auto max-w-[1320px] p-8">
        <Title level={2} className="!mb-1 !text-[19px]">Bảng điều khiển Admin</Title>
        <Text className="!text-[18px] !text-[#6b7289]">Quản lý nền tảng tuyển dụng và nhân sự</Text>

        <Row gutter={[16, 16]} className="mt-6">
          <Col xs={24} md={8}>
            <Card className="panel-card">
              <Statistic title="Tổng người dùng" value={1248} />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card className="panel-card">
              <Statistic title="Công ty hoạt động" value={64} />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card className="panel-card">
              <Statistic title="Đơn ứng tuyển" value={9234} />
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
}

export default AdminLayout;
