import { EnvironmentOutlined, GlobalOutlined } from '@ant-design/icons';
import { Card, Col, Row, Typography } from 'antd';

import { useJobs } from '../../hooks/useJobs';

const { Title, Text, Paragraph } = Typography;

function CompanyPage() {
  const { data } = useJobs({ page: 1, page_size: 8 });
  const jobs = data?.items || [];

  return (
    <div className="space-y-6">
      <Card className="panel-card">
        <Title level={2} className="!mb-2 !text-[52px]">Tech Solutions</Title>
        <div className="mb-3 flex gap-6 text-[18px] text-[#6b7289]">
          <span className="flex items-center gap-2"><EnvironmentOutlined /> Hà Nội</span>
          <span className="flex items-center gap-2"><GlobalOutlined /> techsolutions.com</span>
        </div>
        <Paragraph className="!mb-0 !text-[30px] !text-[#4b5563]">
          Công ty công nghệ với môi trường năng động, chuyên phát triển sản phẩm web và AI.
        </Paragraph>
      </Card>

      <div>
        <Title level={3} className="!text-[42px]">Việc làm tại công ty</Title>
        <Row gutter={[16, 16]}>
          {jobs.map((job) => (
            <Col xs={24} md={12} key={job.id}>
              <Card className="panel-card" title={<span className="text-[20px] font-semibold">{job.title}</span>}>
                <Text className="!text-[18px] !text-[#6b7289]">{job.location || 'Hà Nội'}</Text>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
}

export default CompanyPage;
