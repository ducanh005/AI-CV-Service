import {
  ApiOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LinkedinOutlined,
  MailOutlined,
  RobotOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { Button, Card, Col, Form, Input, Modal, Row, Space, Typography, message } from 'antd';
import { useState } from 'react';

import { useSendTestEmail } from '../../hooks/useIntegrations';
import { integrationCards } from '../../utils/mockData';

const { Title, Text } = Typography;

const iconByKey = {
  linkedin: <LinkedinOutlined className="text-[20px]" />,
  gmail: <MailOutlined className="text-[20px]" />,
  calendar: <CalendarOutlined className="text-[20px]" />,
  ai: <RobotOutlined className="text-[20px]" />,
};

function HRIntegrationsPage() {
  const [openProvider, setOpenProvider] = useState(null);
  const [form] = Form.useForm();
  const sendEmailMutation = useSendTestEmail();

  return (
    <div>
      <Title level={2} className="!mb-1 !text-[52px]">Tích hợp dịch vụ</Title>
      <Text className="!text-[30px] !text-[#6b7289]">Kết nối SmartHire với các công cụ bên thứ ba</Text>

      <Row gutter={[16, 16]} className="mt-5">
        {integrationCards.map((item) => (
          <Col key={item.key} xs={24} xl={12}>
            <Card className="panel-card">
              <div className="mb-4 flex items-start justify-between">
                <div className="flex gap-4">
                  <div className={`h-14 w-14 rounded-xl bg-gradient-to-r ${item.color} text-white flex items-center justify-center`}>
                    {iconByKey[item.key]}
                  </div>
                  <div>
                    <h3 className="m-0 text-[40px]">{item.title}</h3>
                    <p className="mt-1 text-[18px] text-[#6b7289]">{item.description}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-gray-200 pt-3">
                <div className="text-[18px]">
                  {item.connected ? (
                    <span className="text-emerald-600"><CheckCircleOutlined /> Đã kết nối</span>
                  ) : (
                    <span className="text-[#6b7289]"><CloseCircleOutlined /> Chưa kết nối</span>
                  )}
                </div>
                <Button icon={<SettingOutlined />} onClick={() => setOpenProvider(item.key)}>
                  {item.connected ? 'Cài đặt' : 'Kết nối'}
                </Button>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <div className="mt-10">
        <Title level={3} className="!text-[16px]">Tính năng tích hợp</Title>
        <Row gutter={[16, 16]}>
          {[['Tự động tìm ứng viên', 'Import hồ sơ ứng viên từ LinkedIn với bộ lọc thông minh'], ['Email tự động', 'Gửi email mời phỏng vấn và cập nhật cho ứng viên'], ['Đặt lịch thông minh', 'Tự động tạo lịch phỏng vấn trên Google Calendar'], ['AI đánh giá CV', 'Phân tích và chấm điểm CV tự động bằng AI']].map((item) => (
            <Col xs={24} md={12} xl={6} key={item[0]}>
              <Card className="panel-card !h-full" title={<span className="text-[20px]">{item[0]}</span>}>
                <Text className="!text-[16px] !text-[#6b7289]">{item[1]}</Text>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      <Modal
        open={!!openProvider}
        onCancel={() => setOpenProvider(null)}
        onOk={() => setOpenProvider(null)}
        okText="Kết nối"
        cancelText="Hủy"
        title={<span className="text-[38px]">Kết nối {openProvider || ''}</span>}
      >
        <Form layout="vertical" form={form}>
          <Form.Item label="API Key" name="apiKey"><Input placeholder="Nhập API Key" /></Form.Item>
          <Form.Item label="Client Secret" name="secret"><Input placeholder="Nhập Client Secret" /></Form.Item>
          {openProvider === 'gmail' && (
            <Form.Item label="Email test" name="email"><Input placeholder="example@email.com" /></Form.Item>
          )}
        </Form>

        {openProvider === 'gmail' && (
          <Space>
            <Button
              loading={sendEmailMutation.isPending}
              onClick={async () => {
                const values = await form.validateFields();
                try {
                  await sendEmailMutation.mutateAsync(values.email);
                  message.success('Đã gửi email test');
                } catch {
                  message.error('Không thể gửi email test');
                }
              }}
            >
              Gửi test
            </Button>
          </Space>
        )}
      </Modal>
    </div>
  );
}

export default HRIntegrationsPage;
