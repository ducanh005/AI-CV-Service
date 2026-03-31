import { CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { Card, List, Tag, Typography } from 'antd';

const { Title, Text } = Typography;

const interviews = [
  {
    id: 1,
    title: 'Senior Developer - ABC Corp',
    startsAt: '2026-03-28 09:00',
    duration: '60 phút',
    status: 'Đã xác nhận',
  },
  {
    id: 2,
    title: 'Product Manager - XYZ Ltd',
    startsAt: '2026-03-30 14:00',
    duration: '45 phút',
    status: 'Chờ xác nhận',
  },
];

function InterviewPage() {
  return (
    <div>
      <Title level={2} className="!mb-1 !text-[52px]">Lịch phỏng vấn</Title>
      <Text className="!text-[18px] !text-[#6b7289]">Theo dõi các buổi phỏng vấn sắp tới</Text>

      <List
        className="mt-6"
        dataSource={interviews}
        renderItem={(item) => (
          <List.Item>
            <Card className="panel-card w-full">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="m-0 text-[38px] font-semibold">{item.title}</h3>
                  <p className="mb-0 mt-2 flex items-center gap-2 text-[18px] text-[#6b7289]">
                    <CalendarOutlined /> {item.startsAt}
                  </p>
                  <p className="mb-0 mt-1 flex items-center gap-2 text-[18px] text-[#6b7289]">
                    <ClockCircleOutlined /> {item.duration}
                  </p>
                </div>
                <Tag className="!rounded-full !px-4 !py-2 !text-[16px]">{item.status}</Tag>
              </div>
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
}

export default InterviewPage;
