import {
  CalendarOutlined,
  MailOutlined,
  PlusOutlined,
  SearchOutlined,
  StarOutlined,
  LinkedinOutlined,
} from '@ant-design/icons';
import {
  Button,
  Checkbox,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';

import { useApplicationsByJob, useCreateCandidate } from '../../hooks/useApplications';
import { useJobs } from '../../hooks/useJobs';
import { useScoreUploadedCV } from '../../hooks/useCV';
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
  const [aiJobId, setAiJobId] = useState(undefined);
  const [aiThreshold, setAiThreshold] = useState('60');
  const [aiResult, setAiResult] = useState(null);
  const [notifyCandidates, setNotifyCandidates] = useState(false);
  const [candidateEmailForNotify, setCandidateEmailForNotify] = useState('');
  const [uploadedPdf, setUploadedPdf] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState(undefined);
  const [isAddCandidateOpen, setIsAddCandidateOpen] = useState(false);
  const [addCandidateForm] = Form.useForm();

  const linkedinMutation = useLinkedinOauthUrl();
  const scoreUploadedCVMutation = useScoreUploadedCV();
  const { data: jobsData } = useJobs({ page: 1, page_size: 50 });
  const jobs = jobsData?.items || [];
  const { data: applicationsData, isLoading: applicationsLoading } = useApplicationsByJob(
    { jobId: selectedJobId, page: 1, pageSize: 100 },
    Boolean(selectedJobId)
  );
  const createCandidateMutation = useCreateCandidate();

  useEffect(() => {
    if (!selectedJobId && jobs.length) {
      setSelectedJobId(jobs[0].id);
    }
    if (!aiJobId && jobs.length) {
      setAiJobId(jobs[0].id);
    }
  }, [jobs, selectedJobId, aiJobId]);

  const dataSource = useMemo(() => {
    const items = applicationsData?.items || [];
    return items.filter((candidate) => {
      const hitSearch = !search || (candidate.candidate_name || '').toLowerCase().includes(search.toLowerCase());
      const hitStatus = statusFilter === 'all' || candidate.status === statusFilter;
      return hitSearch && hitStatus;
    });
  }, [applicationsData?.items, search, statusFilter]);

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
      title: 'Điểm AI',
      dataIndex: 'ai_score',
      key: 'ai_score',
      render: (value) => (value == null ? '-' : Number(value).toFixed(2)),
    },
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
      render: () => (
        <Space>
          <Button icon={<MailOutlined />} type="text" />
          <Button icon={<CalendarOutlined />} type="text" onClick={() => setIsInterviewOpen(true)} />
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
          placeholder="Tìm kiếm ứng viên..."
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
          options={jobs.map((job) => ({ value: job.id, label: `${job.id} - ${job.title}` }))}
        />
        <Button
          className="!h-[52px] !rounded-[14px] !bg-[#00011f] !px-8 !text-[18px] !text-white"
          icon={<PlusOutlined />}
          onClick={() => setIsAddCandidateOpen(true)}
        >
          Thêm ứng viên
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={applicationsLoading}
        pagination={false}
        className="panel-card"
      />
      {!jobs.length && <p className="mt-3 text-[16px] text-[#6b7289]">Chưa có job để lọc. Vui lòng tạo job tại trang Tin tuyển dụng.</p>}

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
        <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
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
          <Upload
            beforeUpload={(file) => {
              setUploadedPdf(file);
              return false;
            }}
            maxCount={1}
            accept=".pdf"
          >
            <Button className="!h-[40px]">{uploadedPdf ? uploadedPdf.name : 'Chọn file PDF'}</Button>
          </Upload>
        </div>

        <div className="mb-4">
          <Checkbox checked={notifyCandidates} onChange={(e) => setNotifyCandidates(e.target.checked)}>
            Gửi email pass/fail tự động cho ứng viên sau khi lọc
          </Checkbox>
        </div>

        {notifyCandidates && (
          <div className="mb-4">
            <Input
              value={candidateEmailForNotify}
              onChange={(e) => setCandidateEmailForNotify(e.target.value)}
              placeholder="Email ứng viên để gửi kết quả pass/fail"
            />
          </div>
        )}

        <div className="mb-4 flex justify-end">
          <Button
            type="primary"
            className="!bg-[#00011f]"
            loading={scoreUploadedCVMutation.isPending}
            onClick={async () => {
              if (!aiJobId) {
                message.error('Vui lòng chọn job để lọc');
                return;
              }
              if (!uploadedPdf) {
                message.error('Vui lòng chọn file PDF cần chấm');
                return;
              }
              if (notifyCandidates && !candidateEmailForNotify) {
                message.error('Vui lòng nhập email ứng viên để gửi kết quả');
                return;
              }
              try {
                const result = await scoreUploadedCVMutation.mutateAsync({
                  jobId: aiJobId,
                  minScore: Number(aiThreshold) || 60,
                  file: uploadedPdf,
                  notifyCandidates,
                  candidateEmail: candidateEmailForNotify,
                });
                setAiResult(result);
                message.success('AI chấm CV thành công');
              } catch (error) {
                message.error(error?.response?.data?.detail || 'Không thể chấm CV');
              }
            }}
          >
            Chấm CV bằng AI
          </Button>
        </div>

        {aiResult && (
          <div className="mt-5 panel-card p-4">
            <p className="m-0 text-[16px] font-semibold">
              Kết quả: {aiResult.passed ? 'PASS' : 'FAIL'} ({aiResult.score}/{100})
            </p>
            <div className="mt-2 text-[14px] text-[#6b7289]">
              Min score: {aiResult.min_score}
            </div>
            <div className="mt-2 text-[14px]">
              {aiResult.reasoning}
            </div>
          </div>
        )}
      </Modal>

      <Modal
        open={isAddCandidateOpen}
        onCancel={() => setIsAddCandidateOpen(false)}
        footer={null}
        title={<span className="text-[32px]">Thêm ứng viên mới</span>}
      >
        <Form
          form={addCandidateForm}
          layout="vertical"
          onFinish={async (values) => {
            try {
              await createCandidateMutation.mutateAsync({
                email: values.email,
                full_name: values.full_name,
              });
              message.success('Tạo ứng viên thành công (mật khẩu mặc định: Candidate@123)');
              addCandidateForm.resetFields();
              setIsAddCandidateOpen(false);
            } catch (error) {
              message.error(error?.response?.data?.detail || 'Không thể tạo ứng viên');
            }
          }}
        >
          <Form.Item name="full_name" label="Họ tên" rules={[{ required: true, message: 'Nhập họ tên' }]}>
            <Input className="!h-[46px]" />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, message: 'Nhập email' }]}>
            <Input className="!h-[46px]" />
          </Form.Item>
          <p className="mb-4 text-[14px] text-[#6b7289]">Mật khẩu ứng viên sẽ được tạo mặc định: Candidate@123</p>
          <div className="flex justify-end gap-2">
            <Button onClick={() => setIsAddCandidateOpen(false)}>Hủy</Button>
            <Button type="primary" htmlType="submit" loading={createCandidateMutation.isPending}>
              Tạo ứng viên
            </Button>
          </div>
        </Form>
      </Modal>

      <Modal
        open={isInterviewOpen}
        onCancel={() => setIsInterviewOpen(false)}
        footer={null}
        width={820}
        title={<span className="text-[40px]">Đặt lịch phỏng vấn</span>}
      >
        <Form layout="vertical" onFinish={() => { message.success('Đặt lịch thành công'); setIsInterviewOpen(false); }}>
          <Form.Item label="Tiêu đề" name="title" initialValue="Phỏng vấn - Nguyễn Văn An" rules={[{ required: true }]}>
            <Input className="!h-[50px]" />
          </Form.Item>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Form.Item label="Ngày" name="date" rules={[{ required: true }]}><Input placeholder="dd/mm/yyyy" className="!h-[50px]" /></Form.Item>
            <Form.Item label="Giờ" name="time" rules={[{ required: true }]}><Input placeholder="--:--" className="!h-[50px]" /></Form.Item>
          </div>
          <Form.Item label="Người tham gia" name="emails"><Select mode="tags" placeholder="email@example.com" /></Form.Item>
          <Form.Item label="Ghi chú" name="note"><Input.TextArea rows={3} /></Form.Item>
          <div className="flex justify-end gap-3">
            <Button onClick={() => setIsInterviewOpen(false)}>Hủy</Button>
            <Button htmlType="submit" type="primary" className="!bg-[#7ed9a0] !text-[#072d12]">Tạo lịch hẹn</Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}

export default HRCandidatesPage;
