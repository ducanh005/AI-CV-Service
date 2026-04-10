import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SearchOutlined,
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
  TimePicker,
  Typography,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { attendanceService } from '../../services/attendanceService';
import { employeeService } from '../../services/employeeService';

const { Title, Text } = Typography;

const STATUS_MAP = {
  present: { color: 'green', label: 'Có mặt', icon: <CheckCircleOutlined /> },
  absent: { color: 'red', label: 'Vắng mặt', icon: <CloseCircleOutlined /> },
  late: { color: 'orange', label: 'Đi muộn', icon: <ClockCircleOutlined /> },
  half_day: { color: 'blue', label: 'Nửa ngày', icon: <ClockCircleOutlined /> },
};

function HRAttendancePage() {
  const [attendances, setAttendances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [filterEmp, setFilterEmp] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [filterDate, setFilterDate] = useState(null);

  // Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [attData, empData] = await Promise.all([
        attendanceService.list(),
        employeeService.list(),
      ]);
      setAttendances(attData);
      setEmployees(empData);
    } catch {
      message.error('Không thể tải dữ liệu chấm công');
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
    return attendances.filter((a) => {
      const hitEmp = !filterEmp || a.employee_id === filterEmp;
      const hitStatus = !filterStatus || a.status === filterStatus;
      const hitDate = !filterDate || a.date === filterDate.format('YYYY-MM-DD');
      return hitEmp && hitStatus && hitDate;
    });
  }, [attendances, filterEmp, filterStatus, filterDate]);

  // Stats
  const todayStr = dayjs().format('YYYY-MM-DD');
  const todayRecords = attendances.filter((a) => a.date === todayStr);
  const presentToday = todayRecords.filter((a) => a.status === 'present').length;
  const lateToday = todayRecords.filter((a) => a.status === 'late').length;
  const absentToday = todayRecords.filter((a) => a.status === 'absent').length;

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ date: dayjs(), status: 'present' });
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditing(record);
    form.setFieldsValue({
      employee_id: record.employee_id,
      date: dayjs(record.date),
      check_in: record.check_in ? dayjs(record.check_in, 'HH:mm:ss') : null,
      check_out: record.check_out ? dayjs(record.check_out, 'HH:mm:ss') : null,
      status: record.status,
      notes: record.notes,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        date: values.date?.format('YYYY-MM-DD'),
        check_in: values.check_in?.format('HH:mm:ss') || null,
        check_out: values.check_out?.format('HH:mm:ss') || null,
      };
      if (editing) {
        const { employee_id, date, ...updatePayload } = payload;
        await attendanceService.update(editing.id, updatePayload);
        message.success('Cập nhật thành công');
      } else {
        await attendanceService.create(payload);
        message.success('Thêm chấm công thành công');
      }
      setModalOpen(false);
      fetchData();
    } catch (err) {
      if (err.response?.data?.detail) message.error(err.response.data.detail);
    }
  };

  const handleDelete = async (id) => {
    try {
      await attendanceService.delete(id);
      message.success('Đã xóa');
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa');
    }
  };

  const columns = [
    {
      title: 'Ngày',
      dataIndex: 'date',
      key: 'date',
      width: 120,
      render: (v) => dayjs(v).format('DD/MM/YYYY'),
      sorter: (a, b) => a.date.localeCompare(b.date),
    },
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
      title: 'Check-in',
      dataIndex: 'check_in',
      key: 'check_in',
      width: 100,
      render: (v) => v ? dayjs(v, 'HH:mm:ss').format('HH:mm') : '—',
    },
    {
      title: 'Check-out',
      dataIndex: 'check_out',
      key: 'check_out',
      width: 100,
      render: (v) => v ? dayjs(v, 'HH:mm:ss').format('HH:mm') : '—',
    },
    {
      title: 'Giờ làm',
      dataIndex: 'work_hours',
      key: 'work_hours',
      width: 90,
      render: (v) => v != null ? `${v.toFixed(1)}h` : '—',
    },
    {
      title: 'Trạng thái',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (v) => {
        const s = STATUS_MAP[v] || STATUS_MAP.present;
        return <Tag color={s.color}>{s.icon} {s.label}</Tag>;
      },
    },
    {
      title: 'Ghi chú',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
    {
      title: '',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <div className="flex gap-1">
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="Xóa bản ghi?" onConfirm={() => handleDelete(record.id)} okText="Xóa" cancelText="Hủy">
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 !text-[52px]">Chấm công</Title>
          <Text className="!text-[30px] !text-[#6b7289]">Quản lý chấm công nhân viên</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={openCreate}>
          Thêm chấm công
        </Button>
      </div>

      {/* Stats */}
      <Row gutter={16} className="mt-5 mb-5">
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-100">
                <ClockCircleOutlined className="text-lg text-blue-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Hôm nay</p>
                <p className="m-0 text-2xl font-bold">{todayRecords.length}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-green-100">
                <CheckCircleOutlined className="text-lg text-green-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Có mặt</p>
                <p className="m-0 text-2xl font-bold text-green-600">{presentToday}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-orange-100">
                <ClockCircleOutlined className="text-lg text-orange-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Đi muộn</p>
                <p className="m-0 text-2xl font-bold text-orange-600">{lateToday}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-red-100">
                <CloseCircleOutlined className="text-lg text-red-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Vắng mặt</p>
                <p className="m-0 text-2xl font-bold text-red-600">{absentToday}</p>
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
            { value: 'present', label: 'Có mặt' },
            { value: 'absent', label: 'Vắng mặt' },
            { value: 'late', label: 'Đi muộn' },
            { value: 'half_day', label: 'Nửa ngày' },
          ]}
        />
        <DatePicker
          placeholder="Lọc theo ngày"
          value={filterDate}
          onChange={setFilterDate}
          format="DD/MM/YYYY"
          allowClear
        />
      </div>

      <Spin spinning={loading}>
        <Card className="panel-card">
          <Table
            dataSource={filtered}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (t) => `Tổng ${t} bản ghi` }}
            size="middle"
            locale={{ emptyText: <Empty description="Chưa có dữ liệu chấm công" /> }}
          />
        </Card>
      </Spin>

      {/* Create / Edit Modal */}
      <Modal
        title={editing ? 'Chỉnh sửa chấm công' : 'Thêm chấm công'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText={editing ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
        width={520}
      >
        <Form form={form} layout="vertical" className="mt-4">
          {!editing && (
            <Form.Item name="employee_id" label="Nhân viên" rules={[{ required: true, message: 'Bắt buộc' }]}>
              <Select
                showSearch
                placeholder="Chọn nhân viên"
                options={empOptions}
                filterOption={(input, opt) => (opt?.label ?? '').toLowerCase().includes(input.toLowerCase())}
              />
            </Form.Item>
          )}
          {!editing && (
            <Form.Item name="date" label="Ngày" rules={[{ required: true, message: 'Bắt buộc' }]}>
              <DatePicker className="!w-full" format="DD/MM/YYYY" />
            </Form.Item>
          )}
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="check_in" label="Giờ vào">
                <TimePicker className="!w-full" format="HH:mm" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="check_out" label="Giờ ra">
                <TimePicker className="!w-full" format="HH:mm" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="status" label="Trạng thái" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'present', label: 'Có mặt' },
                { value: 'absent', label: 'Vắng mặt' },
                { value: 'late', label: 'Đi muộn' },
                { value: 'half_day', label: 'Nửa ngày' },
              ]}
            />
          </Form.Item>
          <Form.Item name="notes" label="Ghi chú">
            <Input.TextArea rows={2} placeholder="Ghi chú thêm..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default HRAttendancePage;
