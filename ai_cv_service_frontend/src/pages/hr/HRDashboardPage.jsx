import { BarChartOutlined, RiseOutlined, TeamOutlined, UserSwitchOutlined } from '@ant-design/icons';
import { Card, Col, Progress, Row, Typography } from 'antd';

import { useHRDashboard } from '../../hooks/useApplications';

const { Title, Text } = Typography;

function HRDashboardPage() {
  const { data } = useHRDashboard();
  const overview = data?.overview || { total_candidates: 0, open_jobs: 0, hired: 0, hire_rate: 0 };
  const monthlyApplications = data?.monthly_applications || [];
  const statusBreakdown = data?.status_breakdown || { pending: 0, accepted: 0, rejected: 0 };

  const cards = [
    { label: 'Tổng ứng viên', value: overview.total_candidates, change: '', icon: <TeamOutlined />, color: '#2563eb' },
    { label: 'Vị trí tuyển dụng', value: overview.open_jobs, change: '', icon: <BarChartOutlined />, color: '#22c55e' },
    { label: 'Đã tuyển dụng', value: overview.hired, change: '', icon: <UserSwitchOutlined />, color: '#9333ea' },
    { label: 'Tỷ lệ tuyển dụng', value: `${overview.hire_rate}%`, change: '', icon: <RiseOutlined />, color: '#f97316' },
  ];

  const monthlyMax = Math.max(1, ...monthlyApplications.map((item) => item.count || 0));
  const totalStatus = statusBreakdown.pending + statusBreakdown.accepted + statusBreakdown.rejected;

  return (
    <div>
      <Title level={2} className="!mb-1 !text-[52px]">Bảng điều khiển</Title>
      <Text className="!text-[30px] !text-[#6b7289]">Tổng quan về hoạt động tuyển dụng và nhân sự</Text>

      <Row gutter={[16, 16]} className="mt-5">
        {cards.map((item) => (
          <Col xs={24} xl={12} xxl={6} key={item.label}>
            <Card className="panel-card">
              <div className="mb-4 flex items-start justify-between">
                <div
                  className="flex h-14 w-14 items-center justify-center rounded-xl text-[18px] text-white"
                  style={{ background: item.color }}
                >
                  {item.icon}
                </div>
                <span className="text-[18px] text-green-600">{item.change}</span>
              </div>
              <p className="mb-2 text-[20px] text-[#6b7289]">{item.label}</p>
              <p className="m-0 text-[19px] font-semibold">{item.value}</p>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} className="mt-5">
        <Col xs={24} xl={12}>
          <Card className="panel-card" title={<span className="text-[38px]">Thống kê ứng viên theo tháng</span>}>
            <div className="space-y-3">
              {monthlyApplications.map((item) => (
                <div key={item.month}>
                  <div className="mb-1 flex justify-between text-[16px] text-[#6b7289]">
                    <span>{item.month}</span>
                    <span>{item.count}</span>
                  </div>
                  <Progress percent={(item.count / monthlyMax) * 100} showInfo={false} strokeColor="#14b8a6" />
                </div>
              ))}
              {!monthlyApplications.length && <p className="text-[16px] text-[#6b7289]">Chưa có dữ liệu ứng tuyển theo tháng.</p>}
            </div>
          </Card>
        </Col>

        <Col xs={24} xl={12}>
          <Card className="panel-card" title={<span className="text-[38px]">Phân bổ theo phòng ban</span>}>
            <div className="space-y-3 text-[18px]">
              <div className="flex items-center justify-between"><span>Pending</span><span className="text-amber-500">{totalStatus ? Math.round((statusBreakdown.pending / totalStatus) * 100) : 0}%</span></div>
              <div className="flex items-center justify-between"><span>Accepted</span><span className="text-emerald-500">{totalStatus ? Math.round((statusBreakdown.accepted / totalStatus) * 100) : 0}%</span></div>
              <div className="flex items-center justify-between"><span>Rejected</span><span className="text-rose-500">{totalStatus ? Math.round((statusBreakdown.rejected / totalStatus) * 100) : 0}%</span></div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default HRDashboardPage;
