import {
  CalendarOutlined,
  MailOutlined,
  SearchOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Progress,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useAuthStore } from '../../store/authStore';

import { useApplicationsByJob, useDeleteApplication, useReviewApplication } from '../../hooks/useApplications';
import { useJobs } from '../../hooks/useJobs';
import {
  useNotifyScreeningResult,
  useRankCandidatesAsyncStatus,
  useRankCandidatesAsyncSubmit,
} from '../../hooks/useCV';
import { useCreateInterview, useSendGmailEmail } from '../../hooks/useIntegrations';

const { Title, Text } = Typography;

const statusTone = {
  pending: 'gold',
  accepted: 'green',
  rejected: 'red',
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const uploadsBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '');

function HRCandidatesPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [isInterviewOpen, setIsInterviewOpen] = useState(false);
  const [isEmailOpen, setIsEmailOpen] = useState(false);
  const [emailTarget, setEmailTarget] = useState(null);
  const [emailResult, setEmailResult] = useState('accepted');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailMessage, setEmailMessage] = useState('');
  const [interviewTarget, setInterviewTarget] = useState(null);
  const [aiJobId, setAiJobId] = useState(undefined);
  const [aiThreshold, setAiThreshold] = useState('60');
  const [aiScoringJobId, setAiScoringJobId] = useState(null);
  const [lastFinishedScoringJobId, setLastFinishedScoringJobId] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState(undefined);
  const [interviewForm] = Form.useForm();

  const rankCandidatesAsyncSubmitMutation = useRankCandidatesAsyncSubmit();
  const { data: aiStatusData, isFetching: aiStatusFetching } = useRankCandidatesAsyncStatus(
    aiScoringJobId,
    isAiOpen && Boolean(aiScoringJobId)
  );
  const notifyScreeningResultMutation = useNotifyScreeningResult();
  const createInterviewMutation = useCreateInterview();
  const reviewApplicationMutation = useReviewApplication();
  const deleteApplicationMutation = useDeleteApplication();
  const sendGmailEmailMutation = useSendGmailEmail();
  const { data: jobsData } = useJobs({ page: 1, page_size: 100 });
  const { data: applicationsData, isLoading: applicationsLoading } = useApplicationsByJob(
    { jobId: selectedJobId, page: 1, pageSize: 100 },
    Boolean(selectedJobId),
    { refetchInterval: 5000 }
  );

  const jobs = useMemo(() => {
    const allJobs = jobsData?.items || [];
    if (user?.role !== 'hr' || !user?.company_id) {
      return allJobs;
    }

    return allJobs.filter((job) => job.company_id === user.company_id);
  }, [jobsData?.items, user?.role, user?.company_id]);

  useEffect(() => {
    if (!jobs.length) {
      if (aiJobId !== undefined) {
        setAiJobId(undefined);
      }
      return;
    }

    const selectedExists = aiJobId !== undefined && jobs.some((job) => job.id === aiJobId);
    if (!selectedExists) {
      setAiJobId(jobs[0].id);
    }
  }, [jobs, aiJobId]);

  useEffect(() => {
    if (!jobs.length) {
      if (selectedJobId !== undefined) {
        setSelectedJobId(undefined);
      }
      return;
    }

    const selectedExists = selectedJobId !== undefined && jobs.some((job) => job.id === selectedJobId);
    if (!selectedExists) {
      setSelectedJobId(jobs[0].id);
    }
  }, [jobs, selectedJobId]);

  useEffect(() => {
    if (!aiStatusData) {
      return;
    }

    const isDoneStatus = ['completed', 'partial_failed', 'failed'].includes(aiStatusData.status);
    const isFullyDone = isDoneStatus && (aiStatusData.processed_items + aiStatusData.failed_items >= aiStatusData.total_items);
    if (!isFullyDone) {
      return;
    }

    if (lastFinishedScoringJobId === aiStatusData.scoring_job_id) {
      return;
    }

    setLastFinishedScoringJobId(aiStatusData.scoring_job_id);
    queryClient.invalidateQueries({ queryKey: ['applications'] });
    message.success('AI đã chấm xong toàn bộ CV cho đợt lọc này');
  }, [aiStatusData, lastFinishedScoringJobId, queryClient]);

  const aiIsDoneStatus = ['completed', 'partial_failed', 'failed'].includes(aiStatusData?.status || '');
  const aiIsFullyDone =
    Boolean(aiStatusData)
    && aiIsDoneStatus
    && ((aiStatusData.processed_items + aiStatusData.failed_items) >= aiStatusData.total_items);
  const aiIsScoring = Boolean(aiScoringJobId) && !aiIsFullyDone;

  const dataSource = useMemo(() => {
    const items = applicationsData?.items || [];
    return items.filter((candidate) => {
      const hitSearch = !search || (candidate.candidate_email || '').toLowerCase().includes(search.toLowerCase());
      const hitStatus = statusFilter === 'all' || candidate.status === statusFilter;
      return hitSearch && hitStatus;
    });
  }, [applicationsData?.items, search, statusFilter]);

  const normalizeStatusLabel = (status) => {
    if (status === 'accepted') return 'Đạt yêu cầu';
    if (status === 'rejected') return 'Chưa phù hợp';
    return 'Đang chờ';
  };

  const buildEmailTemplate = (candidate, result) => {
    const jobName = candidate?.job_title || 'vị trí ứng tuyển';
    const candidateName = candidate?.candidate_name || 'Ứng viên';

    if (result === 'accepted') {
      return {
        subject: `[AI CV Service] Kết quả ứng tuyển - ${jobName}`,
        message: `Chào ${candidateName},\n\nChúc mừng bạn đã vượt qua vòng sàng lọc cho vị trí ${jobName}.\nHR sẽ liên hệ với bạn để trao đổi lịch phỏng vấn trong thời gian sớm nhất.\n\nTrân trọng,\nAI CV Service HR Team`,
      };
    }

    return {
      subject: `[AI CV Service] Kết quả ứng tuyển - ${jobName}`,
      message: `Chào ${candidateName},\n\nCảm ơn bạn đã ứng tuyển vị trí ${jobName}.\nSau khi xem xét, chúng tôi rất tiếc phải thông báo rằng hồ sơ của bạn chưa phù hợp ở thời điểm hiện tại.\nChúc bạn sớm tìm được cơ hội phù hợp hơn.\n\nTrân trọng,\nAI CV Service HR Team`,
    };
  };

  const openEmailModal = (row) => {
    const inferredResult = row.status === 'rejected' ? 'rejected' : 'accepted';
    const template = buildEmailTemplate(row, inferredResult);
    setEmailTarget(row);
    setEmailResult(inferredResult);
    setEmailSubject(template.subject);
    setEmailMessage(template.message);
    setIsEmailOpen(true);
  };

  const buildNotifiedNotes = (prevNotes = '') => {
    const markerPrefix = '[MAIL_SENT]';
    const cleanedNotes = (prevNotes || '')
      .split('\n')
      .filter((line) => !line.startsWith(markerPrefix))
      .join('\n')
      .trim();
    const marker = `${markerPrefix} ${new Date().toISOString()}`;
    return cleanedNotes ? `${cleanedNotes}\n${marker}` : marker;
  };

  const columns = [
    {
      title: 'Tên ứng viên',
      dataIndex: 'name',
      key: 'name',
      render: (_, row) => (
        <div>
          <div className="text-[16px] font-semibold leading-tight">{row.candidate_name || `Candidate #${row.candidate_id}`}</div>
          <div className="text-[13px] text-[#6b7289]">✉ {row.candidate_email || '-'}</div>
        </div>
      ),
    },
    { title: 'Vị trí', dataIndex: 'job_title', key: 'job_title', className: 'text-[14px]' },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (value, row) => (
        <div className="flex min-w-[180px] flex-col gap-2">
          <Tag color={statusTone[value] || 'default'} className="!m-0 !w-fit !rounded-full !px-3 !py-1 !text-[12px] !font-medium !leading-[16px]">
            {normalizeStatusLabel(value)}
          </Tag>
          <Select
            size="small"
            value={value}
            className="!w-full"
            options={[
              { value: 'pending', label: 'Đang chờ' },
              { value: 'accepted', label: 'Đạt yêu cầu' },
              { value: 'rejected', label: 'Chưa phù hợp' },
            ]}
            onChange={async (nextStatus) => {
              try {
                await reviewApplicationMutation.mutateAsync({
                  applicationId: row.id,
                  payload: { status: nextStatus },
                });
                message.success('Đã cập nhật trạng thái ứng viên');
              } catch (error) {
                message.error(error?.response?.data?.detail || 'Không thể cập nhật trạng thái');
              }
            }}
          />
        </div>
      ),
    },
    {
      title: 'Điểm AI',
      key: 'ai_score',
      render: (_, row) => (typeof row.ai_score === 'number' ? `${Math.round(row.ai_score)}/100` : 'Chưa chấm'),
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
          <Button icon={<MailOutlined />} type="text" onClick={() => openEmailModal(row)} />
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
          <Popconfirm
            title="Xóa ứng viên này?"
            description="Thao tác sẽ xóa hồ sơ ứng tuyển khỏi danh sách hiện tại."
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true, loading: deleteApplicationMutation.isPending }}
            onConfirm={async () => {
              try {
                await deleteApplicationMutation.mutateAsync(row.id);
                message.success('Đã xóa ứng viên khỏi danh sách');
              } catch (error) {
                message.error(error?.response?.data?.detail || 'Không thể xóa ứng viên');
              }
            }}
          >
            <Button danger type="text">Xóa</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const aiResultRows = aiStatusData?.items || [];
  const processedRows = aiResultRows.filter((row) => row.status === 'processed');
  const totalPassed = processedRows.filter((row) => row.passed).length;

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
      render: (_, row) => (typeof row.score === 'number' ? `${Math.round(row.score)}/100` : '-'),
    },
    {
      title: 'Kết quả',
      key: 'passed',
      render: (_, row) => {
        if (row.status === 'queued') {
          return <Tag color="blue" className="!rounded-full !px-3">Đang chờ</Tag>;
        }
        if (row.status === 'failed') {
          return <Tag color="red" className="!rounded-full !px-3">Lỗi</Tag>;
        }
        return (
          <Tag color={row.passed ? 'green' : 'red'} className="!rounded-full !px-3">
            {row.passed ? 'Đạt' : 'Không đạt'}
          </Tag>
        );
      },
    },
    {
      title: 'Phân tích AI',
      dataIndex: 'reasoning',
      key: 'reasoning',
      render: (value, row) => <Text className="!text-[14px]">{value || row.error || '-'}</Text>,
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, row) => (
        <Space>
          <Button
            icon={<MailOutlined />}
            disabled={row.status !== 'processed'}
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
            disabled={row.status !== 'processed' || !row.passed}
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
          <Title level={2} className="!mb-1 !text-[40px]">Quản lý ứng viên</Title>
          <Text className="!text-[20px] !text-[#6b7289]">Theo dõi và quản lý toàn bộ ứng viên ứng tuyển</Text>
        </div>

        <Space>
          <Button
            type="primary"
            className="!h-[50px] !rounded-[14px] !border-0 !bg-gradient-to-r !from-violet-600 !to-pink-600 !text-[16px]"
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
          disabled={!jobs.length}
          options={jobs.map((job) => ({ value: job.id, label: `${job.id} - ${job.title}` }))}
        />
      </div>

      <Table
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={applicationsLoading}
        pagination={false}
        scroll={{ x: 980, y: 520 }}
        className="panel-card"
      />
      {!jobs.length && <p className="mt-3 text-[16px] text-[#6b7289]">Chưa có job để quản lý ứng viên. Vui lòng tạo job tại trang Tin tuyển dụng.</p>}

      <Modal
        open={isEmailOpen}
        onCancel={() => {
          setIsEmailOpen(false);
          setEmailTarget(null);
        }}
        footer={null}
        width={820}
        title={<span className="text-[30px]">Soạn email kết quả ứng tuyển</span>}
      >
        <Card className="panel-card">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <div className="mb-1 text-[13px] text-[#6b7289]">Ứng viên</div>
              <div className="text-[15px] font-semibold">{emailTarget?.candidate_name || '-'}</div>
            </div>
            <div>
              <div className="mb-1 text-[13px] text-[#6b7289]">Email nhận</div>
              <div className="text-[15px] font-semibold">{emailTarget?.candidate_email || '-'}</div>
            </div>
          </div>

          <div className="mt-4">
            <div className="mb-1 text-[13px] text-[#6b7289]">Kết quả</div>
            <Select
              value={emailResult}
              className="!w-full"
              options={[
                { value: 'accepted', label: 'Đạt yêu cầu' },
                { value: 'rejected', label: 'Chưa phù hợp' },
              ]}
              onChange={(next) => {
                setEmailResult(next);
                const template = buildEmailTemplate(emailTarget, next);
                setEmailSubject(template.subject);
                setEmailMessage(template.message);
              }}
            />
          </div>

          <div className="mt-4">
            <div className="mb-1 text-[13px] text-[#6b7289]">Tiêu đề</div>
            <Input value={emailSubject} onChange={(e) => setEmailSubject(e.target.value)} />
          </div>

          <div className="mt-4">
            <div className="mb-1 text-[13px] text-[#6b7289]">Nội dung email</div>
            <Input.TextArea rows={8} value={emailMessage} onChange={(e) => setEmailMessage(e.target.value)} />
          </div>

          <div className="mt-4 flex justify-end gap-3">
            <Button
              type="primary"
              loading={sendGmailEmailMutation.isPending}
              onClick={async () => {
                const toEmail = emailTarget?.candidate_email;
                if (!toEmail) {
                  message.error('Không tìm thấy email ứng viên');
                  return;
                }

                if (!emailSubject.trim() || !emailMessage.trim()) {
                  message.error('Vui lòng nhập đầy đủ tiêu đề và nội dung email');
                  return;
                }

                try {
                  await sendGmailEmailMutation.mutateAsync({
                    to_email: toEmail,
                    subject: emailSubject.trim(),
                    body: emailMessage.trim(),
                  });

                  await reviewApplicationMutation.mutateAsync({
                    applicationId: emailTarget.id,
                    payload: {
                      status: emailResult,
                      notes: buildNotifiedNotes(emailTarget.notes),
                    },
                  });

                  message.success(`Đã gửi email trực tiếp tới ${toEmail}`);
                  setIsEmailOpen(false);
                  setEmailTarget(null);
                } catch (error) {
                  message.error(error?.response?.data?.detail || 'Không thể gửi email trực tiếp');
                }
              }}
            >
              Gửi email ngay
            </Button>
          </div>
        </Card>
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
            loading={rankCandidatesAsyncSubmitMutation.isPending || aiIsScoring}
            disabled={aiIsScoring}
            onClick={async () => {
              if (!jobs.length) {
                message.error('Chưa có job phù hợp để lọc CV');
                return;
              }
              if (!aiJobId) {
                message.error('Vui lòng chọn job để lọc');
                return;
              }
              try {
                const result = await rankCandidatesAsyncSubmitMutation.mutateAsync({
                  jobId: aiJobId,
                  minScore: Number(aiThreshold) || 60,
                  notifyCandidates: false,
                });
                setAiScoringJobId(result.scoring_job_id);
                message.success('Đã gửi yêu cầu chấm điểm CV, hệ thống đang xử lý');
              } catch (error) {
                message.error(error?.response?.data?.detail || 'Không thể lọc CV');
              }
            }}
          >
            {aiIsScoring ? 'AI đang chấm CV...' : 'Lọc CV bằng AI'}
          </Button>
        </div>

        {aiIsScoring && (
          <div className="mt-5 panel-card p-4">
            <div className="mb-3 text-[15px] text-[#6b7289]">
              AI đang chấm CV, vui lòng chờ. Kết quả sẽ tự hiển thị sau khi chấm xong.
            </div>
            <div className="mb-3">
              <Progress
                percent={
                  aiStatusData?.total_items
                    ? Math.round(((aiStatusData.processed_items + aiStatusData.failed_items) / aiStatusData.total_items) * 100)
                    : 0
                }
                status="active"
                strokeColor="#1d4ed8"
              />
            </div>
            <div className="mb-3 text-[15px] text-[#6b7289]">
              Trạng thái: {aiStatusData?.status || 'queued'}. Đã gửi {aiStatusData?.submitted_items || 0}/{aiStatusData?.total_items || 0} yêu cầu,
              đã chấm {aiStatusData?.processed_items || 0} ứng viên, lỗi {aiStatusData?.failed_items || 0},
              còn chờ {aiStatusData?.pending_items ?? (aiStatusData?.total_items || 0)}.
              {aiStatusFetching ? ' Đang cập nhật...' : ''}
            </div>
            <Spin size="large" />
          </div>
        )}

        {aiStatusData && aiIsFullyDone && (
          <div className="mt-5 panel-card p-4">
            <div className="mb-3 text-[15px] text-[#6b7289]">
              Trạng thái: {aiStatusData.status}. Đã gửi {aiStatusData.submitted_items}/{aiStatusData.total_items} yêu cầu,
              đã chấm {aiStatusData.processed_items} ứng viên, đạt {totalPassed} ứng viên, lỗi {aiStatusData.failed_items},
              còn chờ {aiStatusData.pending_items} (ngưỡng: {aiStatusData.min_score}).
              {aiStatusFetching ? ' Đang cập nhật...' : ''}
            </div>
            <Table
              rowKey="request_id"
              columns={aiColumns}
              dataSource={aiResultRows}
              pagination={false}
              scroll={{ x: 900, y: 380 }}
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
