import {
  EditOutlined,
  HistoryOutlined,
  PlusOutlined,
  SearchOutlined,
  StopOutlined,
  SyncOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useMemo, useState } from 'react';

import {
  useContractHistory,
  useContracts,
  useContractTargets,
  useCreateContract,
  useRenewContract,
  useTerminateContract,
  useUpdateContract,
  useUploadContractDocument,
} from '../../hooks/useContracts';
import { useAuthStore } from '../../store/authStore';

const { Title, Text } = Typography;

const CONTRACT_TYPE_OPTIONS = [
  { value: 'full_time', label: 'Toàn thời gian' },
  { value: 'part_time', label: 'Bán thời gian' },
];

const CONTRACT_STATUS_OPTIONS = [
  { value: 'active', label: 'Đang hiệu lực' },
  { value: 'expired', label: 'Hết hạn' },
  { value: 'terminated', label: 'Đã chấm dứt' },
];

const DOCUMENT_TYPE_OPTIONS = [
  { value: 'contract', label: 'Hợp đồng chính' },
  { value: 'appendix', label: 'Phụ lục' },
  { value: 'decision', label: 'Quyết định' },
  { value: 'other', label: 'Khác' },
];

const STATUS_COLOR = {
  active: 'green',
  expired: 'orange',
  terminated: 'red',
};

const STATUS_LABEL = Object.fromEntries(CONTRACT_STATUS_OPTIONS.map((item) => [item.value, item.label]));
const TYPE_LABEL = Object.fromEntries(CONTRACT_TYPE_OPTIONS.map((item) => [item.value, item.label]));

function formatDate(value) {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleDateString('vi-VN');
}

function formatMoney(value, currency = 'VND') {
  if (typeof value !== 'number') {
    return '-';
  }
  return `${value.toLocaleString('vi-VN')} ${currency}`;
}

function HRStaffPage() {
  const { user } = useAuthStore();
  const [form] = Form.useForm();
  const [renewForm] = Form.useForm();
  const [terminateForm] = Form.useForm();
  const [uploadForm] = Form.useForm();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingContract, setEditingContract] = useState(null);

  const [renewingContract, setRenewingContract] = useState(null);
  const [terminatingContract, setTerminatingContract] = useState(null);
  const [historyContract, setHistoryContract] = useState(null);
  const [uploadContract, setUploadContract] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);

  const companyId = user?.role === 'admin' ? user?.company_id : undefined;

  const queryParams = useMemo(() => {
    const params = {
      page: 1,
      page_size: 100,
      current_only: true,
      expiring_threshold_days: 30,
    };

    if (search) {
      params.q = search;
    }
    if (statusFilter !== 'all') {
      params.status = statusFilter;
    }
    if (typeFilter !== 'all') {
      params.contract_type = typeFilter;
    }
    if (companyId) {
      params.company_id = companyId;
    }
    return params;
  }, [search, statusFilter, typeFilter, companyId]);

  const statsQueryParams = useMemo(() => {
    const params = {
      page: 1,
      page_size: 100,
      current_only: true,
      expiring_threshold_days: 30,
    };

    if (companyId) {
      params.company_id = companyId;
    }
    return params;
  }, [companyId]);

  const { data: targetsData } = useContractTargets({ companyId }, true);
  const { data: contractsData, isLoading: contractsLoading, refetch } = useContracts(queryParams, true);
  const { data: statsContractsData } = useContracts(statsQueryParams, true);
  const { data: historyData, isLoading: historyLoading } = useContractHistory(
    historyContract?.id,
    { companyId },
    Boolean(historyContract?.id)
  );

  const createContractMutation = useCreateContract();
  const updateContractMutation = useUpdateContract();
  const renewContractMutation = useRenewContract();
  const terminateContractMutation = useTerminateContract();
  const uploadDocumentMutation = useUploadContractDocument();

  const targets = targetsData || [];
  const contracts = contractsData?.items || [];
  const statsContracts = statsContractsData?.items || [];

  const stats = useMemo(() => {
    const active = statsContracts.filter((item) => item.status === 'active').length;
    const expiringSoon = statsContracts.filter((item) => item.expiring_soon).length;
    const expired = statsContracts.filter((item) => item.status === 'expired').length;
    const terminated = statsContracts.filter((item) => item.status === 'terminated').length;
    return { active, expiringSoon, expired, terminated };
  }, [statsContracts]);

  const targetOptions = useMemo(
    () =>
      targets.map((item) => ({
        value: item.source_application_id,
        label: `${item.full_name} (${item.email}) - Đã accept: ${item.accepted_job_title}`,
      })),
    [targets]
  );

  const openCreateModal = () => {
    setEditingContract(null);
    form.resetFields();
    form.setFieldsValue({
      contract_type: 'full_time',
      salary_currency: 'VND',
    });
    setIsEditorOpen(true);
  };

  const openEditModal = (contract) => {
    setEditingContract(contract);
    form.resetFields();
    form.setFieldsValue({
      source_application_id: contract.source_application_id,
      contract_type: contract.contract_type,
      start_date: contract.start_date ? dayjs(contract.start_date) : null,
      end_date: contract.end_date ? dayjs(contract.end_date) : null,
      salary_amount: contract.salary_amount,
      salary_currency: contract.salary_currency,
      benefits: contract.benefits,
      terms: contract.terms,
      notes: contract.notes,
    });
    setIsEditorOpen(true);
  };

  const submitEditorForm = async (values) => {
    try {
      if (!editingContract) {
        const payload = {
          source_application_id: values.source_application_id,
          contract_type: values.contract_type,
          start_date: values.start_date.format('YYYY-MM-DD'),
          end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
          salary_amount: values.salary_amount ?? null,
          salary_currency: values.salary_currency || 'VND',
          benefits: values.benefits || null,
          terms: values.terms || null,
          notes: values.notes || null,
        };
        await createContractMutation.mutateAsync({ payload, companyId });
        message.success('Đã tạo hợp đồng mới');
      } else {
        const payload = {
          contract_type: values.contract_type,
          start_date: values.start_date.format('YYYY-MM-DD'),
          end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
          salary_amount: values.salary_amount ?? null,
          salary_currency: values.salary_currency || 'VND',
          benefits: values.benefits || null,
          terms: values.terms || null,
          notes: values.notes || null,
        };
        await updateContractMutation.mutateAsync({
          id: editingContract.id,
          payload,
          companyId,
        });
        message.success('Đã cập nhật hợp đồng');
      }

      setIsEditorOpen(false);
      setEditingContract(null);
      form.resetFields();
    } catch (error) {
      message.error(error?.response?.data?.detail || 'Không thể lưu hợp đồng');
    }
  };

  const submitRenew = async (values) => {
    if (!renewingContract) {
      return;
    }
    try {
      await renewContractMutation.mutateAsync({
        id: renewingContract.id,
        companyId,
        payload: {
          start_date: values.start_date.format('YYYY-MM-DD'),
          end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : null,
          title: values.title || null,
          contract_type: values.contract_type || null,
          salary_amount: values.salary_amount ?? null,
          salary_currency: values.salary_currency || null,
          benefits: values.benefits || null,
          terms: values.terms || null,
          notes: values.notes || null,
          reason: values.reason || 'Gia hạn hợp đồng',
        },
      });
      message.success('Đã tạo phiên bản gia hạn');
      setRenewingContract(null);
      renewForm.resetFields();
    } catch (error) {
      message.error(error?.response?.data?.detail || 'Không thể gia hạn hợp đồng');
    }
  };

  const submitTerminate = async (values) => {
    if (!terminatingContract) {
      return;
    }
    try {
      await terminateContractMutation.mutateAsync({
        id: terminatingContract.id,
        companyId,
        payload: {
          reason: values.reason,
          terminated_at: values.terminated_at ? values.terminated_at.toISOString() : null,
        },
      });
      message.success('Đã chấm dứt hợp đồng');
      setTerminatingContract(null);
      terminateForm.resetFields();
    } catch (error) {
      message.error(error?.response?.data?.detail || 'Không thể chấm dứt hợp đồng');
    }
  };

  const submitUpload = async (values) => {
    if (!uploadContract || !uploadFile) {
      message.error('Vui lòng chọn file trước khi tải lên');
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('document_type', values.document_type);
    if (values.notes) {
      formData.append('notes', values.notes);
    }

    try {
      await uploadDocumentMutation.mutateAsync({
        id: uploadContract.id,
        formData,
        companyId,
      });
      message.success('Đã tải tài liệu hợp đồng');
      setUploadContract(null);
      setUploadFile(null);
      uploadForm.resetFields();
    } catch (error) {
      message.error(error?.response?.data?.detail || 'Không thể tải tài liệu hợp đồng');
    }
  };

  const columns = [
    {
      title: 'Mã hợp đồng',
      dataIndex: 'contract_code',
      key: 'contract_code',
      render: (value, row) => (
        <div>
          <div className="text-[18px] font-semibold">{value}</div>
          <div className="text-[14px] text-[#6b7289]">v{row.version} - {row.title}</div>
        </div>
      ),
    },
    {
      title: 'Nhân sự',
      key: 'employee',
      render: (_, row) => (
        <div>
          <div className="text-[18px] font-semibold">{row.employee_name}</div>
          <div className="text-[14px] text-[#6b7289]">{row.employee_email}</div>
        </div>
      ),
    },
    {
      title: 'Loại',
      dataIndex: 'contract_type',
      key: 'contract_type',
      render: (value) => <Tag>{TYPE_LABEL[value] || value}</Tag>,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      render: (value, row) => (
        <Space direction="vertical" size={4}>
          <Tag color={STATUS_COLOR[value] || 'default'}>{STATUS_LABEL[value] || value}</Tag>
          {row.expiring_soon && <Tag color="orange">Sắp hết hạn ({row.days_to_expiry} ngày)</Tag>}
        </Space>
      ),
    },
    {
      title: 'Hiệu lực',
      key: 'period',
      render: (_, row) => (
        <div>
          <div>{formatDate(row.start_date)} - {formatDate(row.end_date)}</div>
          <div className="text-[14px] text-[#6b7289]">Ký: {formatDate(row.signed_at)}</div>
        </div>
      ),
    },
    {
      title: 'Lương',
      key: 'salary',
      render: (_, row) => formatMoney(row.salary_amount, row.salary_currency),
    },
    {
      title: 'Tài liệu',
      key: 'docs',
      render: (_, row) => `${row.documents?.length || 0} file`,
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, row) => (
        <Space wrap>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(row)}>
            Sửa
          </Button>
          <Button
            size="small"
            icon={<SyncOutlined />}
            onClick={() => {
              setRenewingContract(row);
              renewForm.resetFields();
              renewForm.setFieldsValue({
                contract_type: row.contract_type,
                salary_amount: row.salary_amount,
                salary_currency: row.salary_currency,
              });
            }}
          >
            Gia hạn
          </Button>
          {row.status !== 'terminated' && (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => {
                setTerminatingContract(row);
                terminateForm.resetFields();
              }}
            >
              Chấm dứt
            </Button>
          )}
          <Button
            size="small"
            icon={<UploadOutlined />}
            onClick={() => {
              setUploadContract(row);
              setUploadFile(null);
              uploadForm.resetFields();
            }}
          >
            Tài liệu
          </Button>
          <Button size="small" icon={<HistoryOutlined />} onClick={() => setHistoryContract(row)}>
            Lịch sử
          </Button>
        </Space>
      ),
    },
  ];

  const historyColumns = [
    {
      title: 'Thời điểm',
      dataIndex: 'changed_at',
      key: 'changed_at',
      render: (value) => formatDate(value),
    },
    {
      title: 'Chuyển trạng thái',
      key: 'transition',
      render: (_, row) => `${row.from_status || 'none'} -> ${row.to_status}`,
    },
    {
      title: 'Ghi chú',
      dataIndex: 'note',
      key: 'note',
      render: (value) => value || '-',
    },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Title level={2} className="!mb-1 !text-[52px]">Quản lý hợp đồng nhân sự</Title>
          <Text className="!text-[30px] !text-[#6b7289]">Theo dõi vòng đời hợp đồng của nhân viên và ứng viên đã hired</Text>
        </div>
        <Space>
          <Button icon={<SyncOutlined />} onClick={() => refetch()}>Làm mới</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>Thêm hợp đồng</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} md={12} xl={6}>
          <Card className="panel-card"><Statistic title="Đang hiệu lực" value={stats.active} /></Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="panel-card"><Statistic title="Sắp hết hạn (< 30 ngày)" value={stats.expiringSoon} /></Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="panel-card"><Statistic title="Hợp đồng hết hạn" value={stats.expired} /></Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="panel-card"><Statistic title="Đã chấm dứt" value={stats.terminated} /></Card>
        </Col>
      </Row>

      <div className="mt-4 flex gap-3">
        <Input
          className="search-input"
          prefix={<SearchOutlined />}
          placeholder="Tìm mã hợp đồng, tên nhân sự, email..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Select
          className="!min-w-[220px]"
          value={statusFilter}
          onChange={setStatusFilter}
          options={[{ value: 'all', label: 'Tất cả trạng thái' }, ...CONTRACT_STATUS_OPTIONS]}
        />
        <Select
          className="!min-w-[220px]"
          value={typeFilter}
          onChange={setTypeFilter}
          options={[{ value: 'all', label: 'Tất cả loại hợp đồng' }, ...CONTRACT_TYPE_OPTIONS]}
        />
      </div>

      <div className="mt-4">
        <Table
          className="panel-card"
          columns={columns}
          dataSource={contracts}
          loading={contractsLoading}
          rowKey="id"
          pagination={false}
        />
      </div>

      <Modal
        open={isEditorOpen}
        onCancel={() => {
          setIsEditorOpen(false);
          setEditingContract(null);
        }}
        onOk={() => form.submit()}
        confirmLoading={createContractMutation.isPending || updateContractMutation.isPending}
        title={editingContract ? 'Cập nhật hợp đồng' : 'Thêm hợp đồng mới'}
        width={900}
      >
        <Form form={form} layout="vertical" onFinish={submitEditorForm}>
          <Row gutter={16}>
            <Col span={24}>
              {!editingContract ? (
                <Form.Item
                  label="Ứng viên đã accept"
                  name="source_application_id"
                  rules={[{ required: true, message: 'Vui lòng chọn ứng viên đã accept' }]}
                >
                  <Select showSearch optionFilterProp="label" options={targetOptions} />
                </Form.Item>
              ) : (
                <Form.Item label="Tiêu đề hợp đồng (tự động)">
                  <Input value={editingContract.title} disabled readOnly />
                </Form.Item>
              )}
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item label="Loại hợp đồng" name="contract_type" rules={[{ required: true, message: 'Vui lòng chọn loại hợp đồng' }]}>
                <Select options={CONTRACT_TYPE_OPTIONS} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Ngày bắt đầu" name="start_date" rules={[{ required: true, message: 'Vui lòng chọn ngày bắt đầu' }]}>
                <DatePicker className="!w-full" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Ngày kết thúc" name="end_date">
                <DatePicker className="!w-full" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Mức lương" name="salary_amount">
                <InputNumber min={0} className="!w-full" placeholder="Nhập mức lương" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Loại tiền" name="salary_currency">
                <Input placeholder="VND" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="Quyền lợi" name="benefits">
            <Input.TextArea rows={3} placeholder="Ví dụ: BHXH, bảo hiểm sức khỏe, thưởng KPI..." />
          </Form.Item>

          <Form.Item label="Điều khoản" name="terms">
            <Input.TextArea rows={4} placeholder="Các điều khoản chính của hợp đồng" />
          </Form.Item>

          <Form.Item label="Ghi chú" name="notes">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={Boolean(renewingContract)}
        onCancel={() => {
          setRenewingContract(null);
          renewForm.resetFields();
        }}
        onOk={() => renewForm.submit()}
        title={renewingContract ? `Gia hạn: ${renewingContract.contract_code}` : 'Gia hạn hợp đồng'}
        confirmLoading={renewContractMutation.isPending}
        width={860}
      >
        <Form form={renewForm} layout="vertical" onFinish={submitRenew}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Ngày bắt đầu phiên bản mới" name="start_date" rules={[{ required: true, message: 'Vui lòng chọn ngày bắt đầu' }]}>
                <DatePicker className="!w-full" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Ngày kết thúc" name="end_date">
                <DatePicker className="!w-full" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Loại hợp đồng" name="contract_type">
                <Select options={CONTRACT_TYPE_OPTIONS} allowClear />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Tiêu đề (nếu đổi)" name="title">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Lương" name="salary_amount">
                <InputNumber min={0} className="!w-full" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Loại tiền" name="salary_currency">
                <Input placeholder="VND" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="Lý do gia hạn" name="reason">
            <Input.TextArea rows={2} placeholder="Ví dụ: Gia hạn thêm 12 tháng" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={Boolean(terminatingContract)}
        onCancel={() => {
          setTerminatingContract(null);
          terminateForm.resetFields();
        }}
        onOk={() => terminateForm.submit()}
        title={terminatingContract ? `Chấm dứt: ${terminatingContract.contract_code}` : 'Chấm dứt hợp đồng'}
        confirmLoading={terminateContractMutation.isPending}
      >
        <Form form={terminateForm} layout="vertical" onFinish={submitTerminate}>
          <Form.Item label="Ngày chấm dứt" name="terminated_at">
            <DatePicker className="!w-full" showTime format="DD/MM/YYYY HH:mm" />
          </Form.Item>
          <Form.Item label="Lý do" name="reason" rules={[{ required: true, message: 'Vui lòng nhập lý do chấm dứt' }]}>
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={Boolean(uploadContract)}
        onCancel={() => {
          setUploadContract(null);
          setUploadFile(null);
          uploadForm.resetFields();
        }}
        onOk={() => uploadForm.submit()}
        title={uploadContract ? `Tài liệu: ${uploadContract.contract_code}` : 'Tải tài liệu hợp đồng'}
        confirmLoading={uploadDocumentMutation.isPending}
      >
        <Form form={uploadForm} layout="vertical" onFinish={submitUpload}>
          <Form.Item label="Loại tài liệu" name="document_type" rules={[{ required: true, message: 'Vui lòng chọn loại tài liệu' }]}>
            <Select options={DOCUMENT_TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item label="Tập tin" required>
            <Upload
              maxCount={1}
              beforeUpload={(file) => {
                setUploadFile(file);
                return false;
              }}
              onRemove={() => {
                setUploadFile(null);
              }}
            >
              <Button icon={<UploadOutlined />}>Chọn file</Button>
            </Upload>
          </Form.Item>
          <Form.Item label="Ghi chú" name="notes">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={Boolean(historyContract)}
        onCancel={() => setHistoryContract(null)}
        footer={null}
        title={historyContract ? `Lịch sử: ${historyContract.contract_code}` : 'Lịch sử hợp đồng'}
        width={920}
      >
        <Table
          rowKey="id"
          columns={historyColumns}
          dataSource={historyData || []}
          loading={historyLoading}
          pagination={false}
        />
      </Modal>
    </div>
  );
}

export default HRStaffPage;
