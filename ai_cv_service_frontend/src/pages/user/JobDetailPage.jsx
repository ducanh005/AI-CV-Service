import { ArrowLeftOutlined, DollarOutlined, EnvironmentOutlined, TagsOutlined } from '@ant-design/icons';
import { Button, Card, Space, Tag, Typography } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';

import { useJobs } from '../../hooks/useJobs';

const { Title, Paragraph, Text } = Typography;

function JobDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { data } = useJobs({ page: 1, page_size: 50 });

  const job = (data?.items || []).find((item) => item.id === Number(id));

  if (!job) {
    return (
      <Card className="panel-card">
        <p className="text-[30px]">Không tìm thấy công việc.</p>
      </Card>
    );
  }

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} className="!mb-4" onClick={() => navigate('/user/dashboard')}>
        Quay lại
      </Button>

      <Card className="panel-card">
        <Title level={2} className="!mb-2 !text-[48px]">{job.title}</Title>
        <Text className="!mb-3 !block !text-[32px] !text-[#6b7289]">Digital Agency</Text>

        <Space wrap className="mb-4">
          <Tag icon={<EnvironmentOutlined />} className="!text-[28px]">{job.location || 'Hà Nội'}</Tag>
          <Tag icon={<DollarOutlined />} className="!text-[28px]">{job.salary_min || 20}-{job.salary_max || 40} triệu</Tag>
          <Tag icon={<TagsOutlined />} className="!text-[28px]">{job.status}</Tag>
        </Space>

        <Paragraph className="!text-[30px] !text-[#374151]">{job.description}</Paragraph>

        <div className="mt-5">
          <Title level={4} className="!text-[34px]">Kỹ năng yêu cầu</Title>
          <Space wrap>
            {(job.required_skills || []).map((skill) => (
              <Tag key={skill} className="!rounded-full !px-4 !py-1 !text-[26px]">{skill}</Tag>
            ))}
          </Space>
        </div>
      </Card>
    </div>
  );
}

export default JobDetailPage;
