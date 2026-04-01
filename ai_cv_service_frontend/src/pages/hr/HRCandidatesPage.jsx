import {
  CalendarOutlined,
  MailOutlined,
  SearchOutlined,
  StarOutlined,
  LinkedinOutlined,
} from '@ant-design/icons';
import {
  Button,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';

import { useApplicationsByCompany, useApplicationsByJob } from '../../hooks/useApplications';
import { useJobs } from '../../hooks/useJobs';
import { useNotifyScreeningResult, useRankCandidates } from '../../hooks/useCV';
import { useCreateInterview } from '../../hooks/useIntegrations';
import { useLinkedinOauthUrl } from '../../hooks/useIntegrations';

const { Title, Text } = Typography;

const statusTone = {
  pending: 'gold',
  accepted: 'green',
  rejected: 'red',
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const uploadsBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '');

function HRCandidatesPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isLinkedinOpen, setIsLinkedinOpen] = useState(false);
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [isInterviewOpen, setIsInterviewOpen] = useState(false);
  const [interviewTarget, setInterviewTarget] = useState(null);
  const [aiJobId, setAiJobId] = useState(undefined);
  const [aiThreshold, setAiThreshold] = useState('60');
  const [aiResult, setAiResult] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState('all');
  const [interviewForm] = Form.useForm();

  const linkedinMutation = useLinkedinOauthUrl();
  const rankCandidatesMutation = useRankCandidates();
  const notifyScreeningResultMutation = useNotifyScreeningResult();
  const createInterviewMutation = useCreateInterview();
  const { data: jobsData } = useJobs({ page: 1, page_size: 50 });
  const jobs = jobsData?.items || [];
  const isAllJobsMode = selectedJobId === 'all';
  const { data: applicationsData, isLoading: applicationsLoading } = useApplicationsByJob(
    { jobId: selectedJobId, page: 1, pageSize: 100 },
    Boolean(selectedJobId) && !isAllJobsMode
  );
  const { data: companyApplicationsData, isLoading: companyApplicationsLoading } = useApplicationsByCompany(
    { page: 1, pageSize: 100 },
    isAllJobsMode
  );

  useEffect(() => {
    if (!aiJobId && jobs.length) {
      setAiJobId(jobs[0].id);
    }
  }, [jobs, aiJobId]);

  const dataSource = useMemo(() => {
    const items = isAllJobsMode ? (companyApplicationsData?.items || []) : (applicationsData?.items || []);
    return items.filter((candidate) => {
      const hitSearch = !search || (candidate.candidate_email || '').toLowerCase().includes(search.toLowerCase());
      const hitStatus = statusFilter === 'all' || candidate.status === statusFilter;
      return hitSearch && hitStatus;
    });
  }, [isAllJobsMode, companyApplicationsData?.items, applicationsData?.items, search, statusFilter]);

  const columns = [
    {
      title: 'Tên ứng viên',
      dataIndex: 'name',
      key: 'name',
      render: (_, row) => (
        <div>
          <div className="text-[20px] font-semibold">{row.candidate_name || `Candidate #${row.candidate_id}`}</div>
          <div className="text-[16px] text-[#6b7289]">✉ {row.candidate_email || '-'}</div>
        </div>
      ),
    },
    { title: 'Vị trí', dataIndex: 'job_title', key: 'job_title', className: 'text-[18px]' },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (value) => <Tag color={statusTone[value] || 'default'} className="!rounded-full !px-3 !text-[26px]">{value}</Tag>,
    },
    {
      title: 'Ngày ứng tuyển',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (value) => (value ? new Date(value).toLocaleDateString('vi-VN') : '-'),
    },
    {
      title: 'CV',
      key: 'cv',
      render: (_, row) => {
        if (!row.cv_file_path) {
          return <Text type="secondary">Chưa có CV</Text>;
        }

        const cvUrl = `${uploadsBaseUrl}/${row.cv_file_path}`;
        return (
          <Button
            size="small"
            onClick={() => window.open(cvUrl, '_blank', 'noopener,noreferrer')}
          >
            Xem CV
          </Button>
        );
      },
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, row) => (
        <Space>
          <Button icon={<MailOutlined />} type="text" />
          <Button
            icon={<CalendarOutlined />}
            type="text"
            onClick={() => {
              setInterviewTarget({
                application_id: row.id,
                candidate_name: row.candidate_name,
                candidate_email: row.candidate_email,
                passed: true,
              });
              setIsInterviewOpen(true);
              interviewForm.setFieldsValue({ starts_at: undefined, ends_at: undefined, notes: undefined });
            }}
          />
        </Space>
      ),
    },
  ];

  const aiResultRows = aiResult?.items || [];

  const aiColumns = [
    {
      title: 'Ứng viên',
      key: 'candidate',
      render: (_, row) => (
        <div>
          <div className="text-[18px] font-semibold">{row.candidate_name}</div>
          <div className="text-[14px] text-[#6b7289]">{row.candidate_email}</div>
        </div>
      ),
    },
    {
      title: 'Điểm AI',
      key: 'score',
      render: (_, row) => `${Math.round(row.score)}/100`,
    },
    {
      title: 'Kết quả',
      key: 'passed',
      render: (_, row) => (
        <Tag color={row.passed ? 'green' : 'red'} className="!rounded-full !px-3">
          {row.passed ? 'Đạt' : 'Không đạt'}
        </Tag>
      ),
    },
    {
      title: 'Phân tích AI',
      dataIndex: 'reasoning',
      key: 'reasoning',
      render: (value) => <Text className="!text-[14px]">{value || '-'}</Text>,
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, row) => (
        <Space>
          <Button
            icon={<MailOutlined />}
            loading={notifyScreeningResultMutation.isPending}
            onClick={async () => {
              try {
                const result = await notifyScreeningResultMutation.mutateAsync({
                  applicationId: row.application_id,
                  minScore: Number(aiThreshold) || 60,
                });
                message.success(
                  result.passed
                    ? `Đã gửi email pass cho ${row.candidate_email}`
                    : `Đã gửi email từ chối cho ${row.candidate_email}`
                );
              } catch (error) {
                message.error(error?.response?.data?.detail || 'Không thể gửi email kết quả');
              }
            }}
          >
            Gửi email
          </Button>
          <Button
            icon={<CalendarOutlined />}
            type="primary"
            disabled={!row.passed}
            onClick={() => {
              setInterviewTarget(row);
              setIsInterviewOpen(true);
              interviewForm.setFieldsValue({ starts_at: undefined, ends_at: undefined, notes: undefined });
            }}
          >
            Đặt lịch
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Title level={2} className="!mb-1 !text-[52px]">Quản lý ứng viên</Title>
          <Text className="!text-[30px] !text-[#6b7289]">Theo dõi và quản lý toàn bộ ứng viên ứng tuyển</Text>
        </div>

        <Space>
          <Button
            type="primary"
            className="!h-[56px] !rounded-[14px] !bg-gradient-to-r !from-blue-600 !to-blue-500 !text-[18px]"
            icon={<LinkedinOutlined />}
            onClick={() => setIsLinkedinOpen(true)}
          >
            Import từ LinkedIn
          </Button>
          <Button
            type="primary"
            className="!h-[56px] !rounded-[14px] !border-0 !bg-gradient-to-r !from-violet-600 !to-pink-600 !text-[18px]"
            icon={<StarOutlined />}
            onClick={() => setIsAiOpen(true)}
          >
            AI Lọc CV
          </Button>
        </Space>
      </div>

      <div className="mb-4 flex gap-3">
        <Input
          className="search-input"
          prefix={<SearchOutlined />}
          placeholder="Lọc danh sách theo email ứng viên..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          className="!min-w-[220px]"
          options={[{ value: 'all', label: 'Tất cả trạng thái' }, ...Object.keys(statusTone).map((status) => ({ value: status, label: status }))]}
        />
        <Select
          value={selectedJobId}
          onChange={setSelectedJobId}
          className="!min-w-[260px]"
          placeholder="Chọn job để xem ứng viên"
          options={[
            { value: 'all', label: 'Tất cả job' },
            ...jobs.map((job) => ({ value: job.id, label: `${job.id} - ${job.title}` })),
          ]}
        />
      </div>

      <Table
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={isAllJobsMode ? companyApplicationsLoading : applicationsLoading}
        pagination={false}
        className="panel-card"
      />
      {!jobs.length && <p className="mt-3 text-[16px] text-[#6b7289]">Chưa có job để quản lý ứng viên. Vui lòng tạo job tại trang Tin tuyển dụng.</p>}

      <Modal
        open={isLinkedinOpen}
        onCancel={() => setIsLinkedinOpen(false)}
        footer={null}
        width={980}
        title={<span className="text-[40px]">Import từ LinkedIn</span>}
      >
        <Space direction="vertical" className="w-full">
          <Input className="search-input" placeholder="Tìm kiếm theo vị trí, kỹ năng, địa điểm..." />
          <div className="panel-card flex min-h-[260px] flex-col items-center justify-center p-5 text-center">
            <LinkedinOutlined className="mb-3 text-[22px] text-[#7a8194]" />
            <p className="m-0 text-[22px] font-semibold">Chưa có kết quả</p>
            <p className="mt-2 text-[18px] text-[#6b7289]">Nhập từ khóa và nhấn Tìm kiếm để bắt đầu</p>
          </div>
          <div className="flex justify-end gap-3">
            <Button onClick={() => setIsLinkedinOpen(false)}>Hủy</Button>
            <Button
              type="primary"
              loading={linkedinMutation.isPending}
              onClick={async () => {
                try {
                  const result = await linkedinMutation.mutateAsync();
                  window.open(result.oauth_url, '_blank');
                } catch {
                  message.error('Không thể mở LinkedIn OAuth');
                }
              }}
            >
              Import
            </Button>
          </div>
        </Space>
      </Modal>

      <Modal
        open={isAiOpen}
        onCancel={() => setIsAiOpen(false)}
        footer={null}
        width={980}
        title={<span className="text-[40px]">AI Lọc CV Thông Minh</span>}
      >
        <div className="mb-3 text-[15px] text-[#6b7289]">
          AI sẽ đọc tiêu chí từ tin tuyển dụng đã chọn và phân tích toàn bộ CV của ứng viên đã ứng tuyển vào tin đó.
        </div>

        <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2">
          <Select
            value={aiJobId}
            onChange={setAiJobId}
            placeholder="Chọn job cần lọc"
            options={jobs.map((job) => ({ value: job.id, label: `${job.id} - ${job.title}` }))}
          />
          <Input
            value={aiThreshold}
            onChange={(e) => setAiThreshold(e.target.value)}
            placeholder="Ngưỡng điểm, ví dụ 60"
          />
        </div>

        <div className="mb-4 flex justify-end">
          <Button
            type="primary"
            className="!bg-[#00011f]"
            loading={rankCandidatesMutation.isPending}
            onClick={async () => {
              if (!aiJobId) {
                message.error('Vui lòng chọn job để lọc');
                return;
              }
              try {
                const result = await rankCandidatesMutation.mutateAsync({
                  jobId: aiJobId,
                  minScore: Number(aiThreshold) || 60,
                  notifyCandidates: false,
                });
                setAiResult(result);
                message.success('AI lọc CV thành công');
              } catch (error) {
                message.error(error?.response?.data?.detail || 'Không thể lọc CV');
              }
            }}
          >
            Lọc CV bằng AI
          </Button>
        </div>

        {aiResult && (
          <div className="mt-5 panel-card p-4">
            <div className="mb-3 text-[15px] text-[#6b7289]">
              Đã chấm {aiResult.total_scored} ứng viên, đạt {aiResult.total_passed} ứng viên (ngưỡng: {aiResult.min_score}).
            </div>
            <Table
              rowKey="application_id"
              columns={aiColumns}
              dataSource={aiResultRows}
              pagination={false}
            />
          </div>
        )}
      </Modal>

      <Modal
        open={isInterviewOpen}
        onCancel={() => {
          setIsInterviewOpen(false);
          setInterviewTarget(null);
        }}
        footer={null}
        width={820}
        title={<span className="text-[40px]">Đặt lịch phỏng vấn</span>}
      >
        <Form
          form={interviewForm}
          layout="vertical"
          onFinish={async (values) => {
            if (!interviewTarget) {
              message.error('Chưa chọn ứng viên để đặt lịch');
              return;
            }
            try {
              await createInterviewMutation.mutateAsync({
                application_id: interviewTarget.application_id,
                starts_at: new Date(values.starts_at).toISOString(),
                ends_at: new Date(values.ends_at).toISOString(),
                notes: values.notes,
              });
              message.success('Đặt lịch phỏng vấn thành công');
              setIsInterviewOpen(false);
              setInterviewTarget(null);
              interviewForm.resetFields();
            } catch (error) {
              message.error(error?.response?.data?.detail || 'Không thể đặt lịch phỏng vấn');
            }
          }}
        >
          <div className="mb-3 text-[15px] text-[#6b7289]">
            Ứng viên: {interviewTarget?.candidate_name || '-'} ({interviewTarget?.candidate_email || '-'})
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Form.Item label="Bắt đầu" name="starts_at" rules={[{ required: true, message: 'Chọn thời gian bắt đầu' }]}>
              <Input type="datetime-local" className="!h-[50px]" />
            </Form.Item>
            <Form.Item label="Kết thúc" name="ends_at" rules={[{ required: true, message: 'Chọn thời gian kết thúc' }]}>
              <Input type="datetime-local" className="!h-[50px]" />
            </Form.Item>
          </div>
          <Form.Item label="Ghi chú" name="notes"><Input.TextArea rows={3} /></Form.Item>
          <div className="flex justify-end gap-3">
            <Button onClick={() => {
              setIsInterviewOpen(false);
              setInterviewTarget(null);
            }}>
              Hủy
            </Button>
            <Button
              htmlType="submit"
              type="primary"
              loading={createInterviewMutation.isPending}
              className="!bg-[#7ed9a0] !text-[#072d12]"
            >
              Tạo lịch hẹn
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}

export default HRCandidatesPage;
