import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { Alert, Col, Input, Modal, Row, Segmented, Space, Tag, Typography, Upload, message } from 'antd';
import { useMemo, useState } from 'react';

import { useApplyJob, useMyApplications } from '../../hooks/useApplications';
import { useJobs } from '../../hooks/useJobs';
import { useScoreCV, useUploadCV } from '../../hooks/useCV';
import UserJobCard from '../../components/user/UserJobCard';
import LoadingState from '../../components/common/LoadingState';
import ErrorState from '../../components/common/ErrorState';
import { useDebounce } from '../../hooks/useDebounce';

const { Title, Text } = Typography;

const statusIcon = {
  'Đơn đã nộp': <FileTextOutlined className="text-[20px] text-[#d1d5db]" />,
  'Đang xem xét': <ClockCircleOutlined className="text-[20px] text-[#bfdbfe]" />,
  'Được chấp nhận': <CheckCircleOutlined className="text-[20px] text-[#bbf7d0]" />,
};

const statusLabelMap = {
  pending: 'Đang xem xét',
  accepted: 'Được chấp nhận',
  rejected: 'Từ chối',
};

function UserDashboardPage() {
  const [tab, setTab] = useState('jobs');
  const [search, setSearch] = useState('');
  const [applyJob, setApplyJob] = useState(null);
  const [cvFile, setCvFile] = useState(null);
  const [aiScoreResult, setAiScoreResult] = useState(null);

  const debouncedSearch = useDebounce(search);
  const applyMutation = useApplyJob();
  const uploadMutation = useUploadCV();
  const scoreMutation = useScoreCV();
  const { data: myAppsData } = useMyApplications({ page: 1, pageSize: 50 }, true);

  const { data, isLoading, error } = useJobs({ page: 1, page_size: 20, q: debouncedSearch || undefined });
  const jobs = data?.items || [];

  const myApplications = myAppsData?.items || [];
  const myStats = myAppsData?.stats || { total: 0, pending: 0, accepted: 0, rejected: 0 };

  const stats = useMemo(
    () => [
      { label: 'Đơn đã nộp', value: myStats.total },
      { label: 'Đang xem xét', value: myStats.pending },
      { label: 'Được chấp nhận', value: myStats.accepted },
    ],
    [myStats]
  );

  const handleApply = async () => {
    if (!applyJob) {
      return;
    }

    if (!cvFile) {
      message.error('Vui lòng tải lên CV trước khi ứng tuyển');
      return;
    }

    try {
      let cvId;
      const uploaded = await uploadMutation.mutateAsync(cvFile);
      cvId = uploaded.id;
      const score = await scoreMutation.mutateAsync({
        cv_id: cvId,
        job_description: applyJob.description,
      });
      setAiScoreResult(score);

      await applyMutation.mutateAsync({ job_id: applyJob.id, cv_id: cvId });
      message.success('Ứng tuyển thành công');
      setApplyJob(null);
      setCvFile(null);
    } catch (err) {
      message.error('Không thể ứng tuyển, vui lòng thử lại');
    }
  };

  return (
    <div>
      <div className="mb-6">
        <Title level={2} className="!mb-1 !text-[56px] !font-bold">Chào mừng trở lại!</Title>
        <Text className="!text-[34px] !text-[#6b7289]">Khám phá cơ hội nghề nghiệp mới</Text>
      </div>

      <Row gutter={[16, 16]}>
        {stats.map((item) => (
          <Col xs={24} lg={8} key={item.label}>
            <div className="panel-card flex items-center justify-between p-5">
              <div>
                <p className="mb-2 text-[20px] text-[#6b7289]">{item.label}</p>
                <p className="m-0 text-[20px] font-semibold">{item.value}</p>
              </div>
              {statusIcon[item.label]}
            </div>
          </Col>
        ))}
      </Row>

      <div className="mt-7 border-b border-gray-200">
        <Segmented
          options={[
            { label: 'Việc làm', value: 'jobs' },
            { label: 'Đơn của tôi', value: 'applications' },
          ]}
          value={tab}
          onChange={setTab}
          size="large"
          className="!mb-4 !bg-transparent"
        />
      </div>

      {tab === 'jobs' && (
        <div className="mt-5">
          <Input
            className="search-input mb-5"
            placeholder="Tìm kiếm công việc, công ty, địa điểm..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          {isLoading && <LoadingState />}
          {error && <ErrorState message={error.message} />}

          <Row gutter={[16, 16]}>
            {jobs.map((job) => (
              <Col key={job.id} xs={24} xl={12}>
                <UserJobCard
                  job={{
                    ...job,
                    company: 'Digital Agency',
                    salary: `${job.salary_min || 20}-${job.salary_max || 40} triệu`,
                    type: 'Full-time',
                  }}
                  onApply={setApplyJob}
                />
              </Col>
            ))}
          </Row>
        </div>
      )}

      {tab === 'applications' && (
        <div className="mt-5 space-y-4">
          {myApplications.map((application) => (
            <div key={application.id} className="panel-card flex items-start justify-between p-6">
              <div>
                <h3 className="m-0 text-[16px]">{application.job_title || `Job #${application.job_id}`}</h3>
                <p className="my-2 text-[20px] text-[#6b7289]">{application.company_name || 'Company'}</p>
                <p className="m-0 text-[20px] text-[#6b7289]">Nộp đơn: {new Date(application.created_at).toLocaleDateString('vi-VN')}</p>
              </div>
              <Tag className="!rounded-full !px-4 !py-2 !text-[18px]">{statusLabelMap[application.status] || application.status}</Tag>
            </div>
          ))}
          {!myApplications.length && <p className="text-[16px] text-[#6b7289]">Bạn chưa có đơn ứng tuyển nào.</p>}
        </div>
      )}

      <Modal
        open={!!applyJob}
        title={<span className="text-[40px]">Ứng tuyển: {applyJob?.title}</span>}
        onCancel={() => setApplyJob(null)}
        onOk={handleApply}
        okText="Xác nhận ứng tuyển"
        cancelText="Hủy"
        confirmLoading={applyMutation.isPending || uploadMutation.isPending || scoreMutation.isPending}
      >
        <Space direction="vertical" className="w-full" size={16}>
          <Upload
            beforeUpload={(file) => {
              setCvFile(file);
              return false;
            }}
            maxCount={1}
            accept=".pdf,.doc,.docx"
          >
            <button type="button" className="h-12 rounded-xl border border-dashed border-gray-300 px-4 text-[16px]">
              Tải lên CV (PDF/DOCX)
            </button>
          </Upload>

          {aiScoreResult && (
            <Alert
              type="success"
              showIcon
              message={`Điểm AI: ${aiScoreResult.score}`}
              description={aiScoreResult.reasoning}
            />
          )}
        </Space>
      </Modal>
    </div>
  );
}

export default UserDashboardPage;
