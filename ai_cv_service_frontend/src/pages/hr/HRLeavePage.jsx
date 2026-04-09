import {
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import {
  Badge,
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Select,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { employeeService } from '../../services/employeeService';
import { leaveRequestService } from '../../services/leaveRequestService';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const LEAVE_TYPE_MAP = {
  annual: { color: 'blue', label: 'Phép năm' },
  sick: { color: 'red', label: 'Ốm đau' },
  personal: { color: 'purple', label: 'Việc riêng' },
  maternity: { color: 'pink', label: 'Thai sản' },
  unpaid: { color: 'default', label: 'Không lương' },
};

const STATUS_MAP = {
  pending: { color: 'gold', label: 'Chờ duyệt', icon: <ClockCircleOutlined /> },
  approved: { color: 'green', label: 'Đã duyệt', icon: <CheckCircleOutlined /> },
  rejected: { color: 'red', label: 'Từ chối', icon: <CloseCircleOutlined /> },
};

function HRLeavePage() {
  const [leaves, setLeaves] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [filterEmp, setFilterEmp] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [filterType, setFilterType] = useState(null);

  // Create / Edit modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();

  // Approve / Reject modal
  const [approveModal, setApproveModal] = useState(null); // leave record
  const [approveAction, setApproveAction] = useState(null); // 'approved' | 'rejected'
  const [rejectedReason, setRejectedReason] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [lData, eData] = await Promise.all([
        leaveRequestService.list(),
        employeeService.list(),
      ]);
      setLeaves(lData);
      setEmployees(eData);
    } catch {
      message.error('Không thể tải dữ liệu nghỉ phép');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const empOptions = useMemo(
    () => employees.map((e) => ({ value: e.id, label: `${e.full_name} (${e.employee_code})` })),
    [employees],
  );

  const filtered = useMemo(() => {
    return leaves.filter((l) => {
      const hitEmp = !filterEmp || l.employee_id === filterEmp;
      const hitStatus = !filterStatus || l.status === filterStatus;
      const hitType = !filterType || l.leave_type === filterType;
      return hitEmp && hitStatus && hitType;
    });
  }, [leaves, filterEmp, filterStatus, filterType]);

  // Stats
  const pendingCount = leaves.filter((l) => l.status === 'pending').length;
  const approvedCount = leaves.filter((l) => l.status === 'approved').length;
  const totalDaysApproved = leaves
    .filter((l) => l.status === 'approved')
    .reduce((s, l) => s + (l.total_days || 0), 0);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ leave_type: 'annual' });
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditing(record);
    form.setFieldsValue({
      employee_id: record.employee_id,
      leave_type: record.leave_type,
      date_range: [dayjs(record.start_date), dayjs(record.end_date)],
      reason: record.reason,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        employee_id: values.employee_id,
        leave_type: values.leave_type,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
        reason: values.reason || '',
      };
      if (editing) {
        await leaveRequestService.update(editing.id, payload);
        message.success('Cập nhật thành công');
      } else {
        await leaveRequestService.create(payload);
        message.success('Tạo đơn nghỉ phép thành công');
      }
      setModalOpen(false);
      fetchData();
    } catch (err) {
      if (err.response?.data?.detail) message.error(err.response.data.detail);
    }
  };

  const handleDelete = async (id) => {
    try {
      await leaveRequestService.delete(id);
      message.success('Đã xóa');
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa');
    }
  };

  const openApproveModal = (record, action) => {
    setApproveModal(record);
    setApproveAction(action);
    setRejectedReason('');
  };

  const handleApprove = async () => {
    try {
      await leaveRequestService.approve(approveModal.id, {
        status: approveAction,
        rejected_reason: approveAction === 'rejected' ? rejectedReason : undefined,
      });
      message.success(approveAction === 'approved' ? 'Đã duyệt đơn' : 'Đã từ chối đơn');
      setApproveModal(null);
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Thao tác thất bại');
    }
  };

  const columns = [
    {
      title: 'Nhân viên',
      key: 'employee',
      width: 200,
      render: (_, r) => (
        <div>
          <div className="font-medium">{r.employee_name}</div>
          <div className="text-xs text-gray-400">{r.employee_code} · {r.department_name}</div>
        </div>
      ),
    },
    {
      title: 'Loại phép',
      dataIndex: 'leave_type',
      key: 'leave_type',
      width: 120,
      render: (v) => {
        const t = LEAVE_TYPE_MAP[v] || LEAVE_TYPE_MAP.annual;
        return <Tag color={t.color}>{t.label}</Tag>;
      },
    },
    {
      title: 'Từ ngày',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 120,
      render: (v) => dayjs(v).format('DD/MM/YYYY'),
      sorter: (a, b) => a.start_date.localeCompare(b.start_date),
    },
    {
      title: 'Đến ngày',
      dataIndex: 'end_date',
      key: 'end_date',
      width: 120,
      render: (v) => dayjs(v).format('DD/MM/YYYY'),
    },
    {
      title: 'Số ngày',
      dataIndex: 'total_days',
      key: 'total_days',
      width: 80,
      align: 'center',
    },
    {
      title: 'Lý do',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (v) => {
        const s = STATUS_MAP[v] || STATUS_MAP.pending;
        return <Tag color={s.color}>{s.icon} {s.label}</Tag>;
      },
    },
    {
      title: '',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <div className="flex gap-1">
          {record.status === 'pending' && (
            <>
              <Button type="text" size="small" style={{ color: '#52c41a' }} onClick={() => openApproveModal(record, 'approved')}>
                Duyệt
              </Button>
              <Button type="text" size="small" danger onClick={() => openApproveModal(record, 'rejected')}>
                Từ chối
              </Button>
            </>
          )}
          {record.status === 'pending' && (
            <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          )}
          {record.status === 'pending' && (
            <Popconfirm title="Xóa đơn này?" onConfirm={() => handleDelete(record.id)} okText="Xóa" cancelText="Hủy">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 !text-[52px]">Nghỉ phép</Title>
          <Text className="!text-[30px] !text-[#6b7289]">Quản lý đơn nghỉ phép nhân viên</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={openCreate}>
          Tạo đơn nghỉ phép
        </Button>
      </div>

      {/* Stats */}
      <Row gutter={16} className="mt-5 mb-5">
        <Col xs={24} md={8}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-yellow-100">
                <ClockCircleOutlined className="text-lg text-yellow-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Chờ duyệt</p>
                <p className="m-0 text-2xl font-bold text-yellow-600">{pendingCount}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-green-100">
                <CheckCircleOutlined className="text-lg text-green-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Đã duyệt</p>
                <p className="m-0 text-2xl font-bold text-green-600">{approvedCount}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-100">
                <CalendarOutlined className="text-lg text-blue-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Tổng ngày nghỉ (đã duyệt)</p>
                <p className="m-0 text-2xl font-bold text-blue-600">{totalDaysApproved}</p>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <Select
          className="!min-w-[220px]"
          showSearch
          placeholder="Nhân viên"
          value={filterEmp}
          onChange={setFilterEmp}
          allowClear
          options={empOptions}
          filterOption={(input, opt) => (opt?.label ?? '').toLowerCase().includes(input.toLowerCase())}
        />
        <Select
          className="!min-w-[150px]"
          placeholder="Trạng thái"
          value={filterStatus}
          onChange={setFilterStatus}
          allowClear
          options={[
            { value: 'pending', label: 'Chờ duyệt' },
            { value: 'approved', label: 'Đã duyệt' },
            { value: 'rejected', label: 'Từ chối' },
          ]}
        />
        <Select
          className="!min-w-[150px]"
          placeholder="Loại phép"
          value={filterType}
          onChange={setFilterType}
          allowClear
          options={[
            { value: 'annual', label: 'Phép năm' },
            { value: 'sick', label: 'Ốm đau' },
            { value: 'personal', label: 'Việc riêng' },
            { value: 'maternity', label: 'Thai sản' },
            { value: 'unpaid', label: 'Không lương' },
          ]}
        />
      </div>

      <Spin spinning={loading}>
        <Card className="panel-card">
          <Table
            dataSource={filtered}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (t) => `Tổng ${t} đơn` }}
            size="middle"
            locale={{ emptyText: <Empty description="Chưa có đơn nghỉ phép" /> }}
          />
        </Card>
      </Spin>

      {/* Create / Edit Modal */}
      <Modal
        title={editing ? 'Chỉnh sửa đơn nghỉ phép' : 'Tạo đơn nghỉ phép'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText={editing ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
        width={520}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item name="employee_id" label="Nhân viên" rules={[{ required: true, message: 'Bắt buộc' }]}>
            <Select
              showSearch
              placeholder="Chọn nhân viên"
              options={empOptions}
              disabled={!!editing}
              filterOption={(input, opt) => (opt?.label ?? '').toLowerCase().includes(input.toLowerCase())}
            />
          </Form.Item>
          <Form.Item name="leave_type" label="Loại phép" rules={[{ required: true, message: 'Bắt buộc' }]}>
            <Select
              options={[
                { value: 'annual', label: 'Phép năm' },
                { value: 'sick', label: 'Ốm đau' },
                { value: 'personal', label: 'Việc riêng' },
                { value: 'maternity', label: 'Thai sản' },
                { value: 'unpaid', label: 'Không lương' },
              ]}
            />
          </Form.Item>
          <Form.Item name="date_range" label="Từ ngày – Đến ngày" rules={[{ required: true, message: 'Bắt buộc' }]}>
            <RangePicker className="!w-full" format="DD/MM/YYYY" />
          </Form.Item>
          <Form.Item name="reason" label="Lý do">
            <Input.TextArea rows={3} placeholder="Lý do xin nghỉ..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Approve / Reject Modal */}
      <Modal
        title={approveAction === 'approved' ? 'Duyệt đơn nghỉ phép' : 'Từ chối đơn nghỉ phép'}
        open={!!approveModal}
        onOk={handleApprove}
        onCancel={() => setApproveModal(null)}
        okText={approveAction === 'approved' ? 'Duyệt' : 'Từ chối'}
        okButtonProps={approveAction === 'rejected' ? { danger: true } : {}}
        cancelText="Hủy"
      >
        {approveModal && (
          <div className="mt-2 mb-4">
            <p><strong>Nhân viên:</strong> {approveModal.employee_name}</p>
            <p><strong>Loại:</strong> {LEAVE_TYPE_MAP[approveModal.leave_type]?.label}</p>
            <p><strong>Thời gian:</strong> {dayjs(approveModal.start_date).format('DD/MM/YYYY')} → {dayjs(approveModal.end_date).format('DD/MM/YYYY')} ({approveModal.total_days} ngày)</p>
            <p><strong>Lý do:</strong> {approveModal.reason || '—'}</p>
          </div>
        )}
        {approveAction === 'rejected' && (
          <div>
            <label className="mb-1 block font-medium">Lý do từ chối</label>
            <Input.TextArea
              rows={3}
              value={rejectedReason}
              onChange={(e) => setRejectedReason(e.target.value)}
              placeholder="Nhập lý do từ chối..."
            />
          </div>
        )}
      </Modal>
    </div>
  );
}

export default HRLeavePage;
