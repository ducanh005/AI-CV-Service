import {
  ApartmentOutlined,
  ArrowLeftOutlined,
  DeleteOutlined,
  EditOutlined,
  MailOutlined,
  PhoneOutlined,
  PlusOutlined,
  SearchOutlined,
  SettingOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Badge,
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { departmentService } from '../../services/departmentService';
import { employeeService } from '../../services/employeeService';
import { resolveAvatarUrl } from '../../utils/media';

const { Title, Text } = Typography;
const { TextArea } = Input;

const STATUS_MAP = {
  active: { color: 'green', label: 'Đang làm' },
  resigned: { color: 'red', label: 'Nghỉ việc' },
  on_leave: { color: 'orange', label: 'Tạm nghỉ' },
};

const CONTRACT_MAP = {
  probation: 'Thử việc',
  permanent: 'Chính thức',
  temporary: 'Thời vụ',
};

const DEPT_COLORS = [
  'from-blue-500 to-blue-600',
  'from-emerald-500 to-emerald-600',
  'from-violet-500 to-violet-600',
  'from-amber-500 to-amber-600',
  'from-rose-500 to-rose-600',
  'from-cyan-500 to-cyan-600',
  'from-indigo-500 to-indigo-600',
  'from-teal-500 to-teal-600',
];

function HRStaffPage() {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDept, setSelectedDept] = useState(null);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState(null);

  // Employee modals
  const [empModalOpen, setEmpModalOpen] = useState(false);
  const [editingEmp, setEditingEmp] = useState(null);
  const [detailModal, setDetailModal] = useState(null);
  const [empForm] = Form.useForm();

  // Department modals
  const [deptModalOpen, setDeptModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [deptForm] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [empData, deptData] = await Promise.all([
        employeeService.list(),
        departmentService.list(),
      ]);
      setEmployees(empData);
      setDepartments(deptData);
    } catch {
      message.error('Không thể tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const deptOptions = useMemo(
    () => departments.map((d) => ({ value: d.id, label: d.name })),
    [departments],
  );

  // Employees filtered for the selected department
  const deptEmployees = useMemo(() => {
    if (!selectedDept) return [];
    return employees.filter((emp) => {
      const hitDept = emp.department_id === selectedDept.id;
      const hitSearch =
        !search ||
        emp.full_name?.toLowerCase().includes(search.toLowerCase()) ||
        emp.email?.toLowerCase().includes(search.toLowerCase()) ||
        emp.employee_code?.toLowerCase().includes(search.toLowerCase());
      const hitStatus = !filterStatus || emp.status === filterStatus;
      return hitDept && hitSearch && hitStatus;
    });
  }, [employees, selectedDept, search, filterStatus]);

  // Stats for overview
  const totalEmployees = employees.length;
  const activeCount = employees.filter((e) => e.status === 'active').length;
  const onLeaveCount = employees.filter((e) => e.status === 'on_leave').length;

  // ---- Employee handlers ----
  const openCreateEmp = () => {
    setEditingEmp(null);
    empForm.resetFields();
    if (selectedDept) {
      empForm.setFieldsValue({ department_id: selectedDept.id });
    }
    setEmpModalOpen(true);
  };

  const openEditEmp = (emp) => {
    setEditingEmp(emp);
    empForm.setFieldsValue({
      user_id: emp.user_id,
      department_id: emp.department_id,
      employee_code: emp.employee_code,
      position: emp.position,
      contract_type: emp.contract_type,
      status: emp.status,
      start_date: emp.start_date ? dayjs(emp.start_date) : null,
      end_date: emp.end_date ? dayjs(emp.end_date) : null,
      identity_number: emp.identity_number,
      notes: emp.notes,
    });
    setEmpModalOpen(true);
  };

  const handleEmpSubmit = async () => {
    try {
      const values = await empForm.validateFields();
      const payload = {
        ...values,
        start_date: values.start_date?.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD') || null,
      };
      if (editingEmp) {
        const { user_id, employee_code, ...updatePayload } = payload;
        await employeeService.update(editingEmp.id, updatePayload);
        message.success('Cập nhật nhân viên thành công');
      } else {
        await employeeService.create(payload);
        message.success('Thêm nhân viên thành công');
      }
      setEmpModalOpen(false);
      fetchData();
    } catch (err) {
      if (err.response?.data?.detail) {
        message.error(err.response.data.detail);
      }
    }
  };

  const handleDeleteEmp = async (id) => {
    try {
      await employeeService.delete(id);
      message.success('Xóa nhân viên thành công');
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa');
    }
  };

  // ---- Department handlers ----
  const openCreateDept = () => {
    setEditingDept(null);
    deptForm.resetFields();
    setDeptModalOpen(true);
  };

  const openEditDept = (dept, e) => {
    e?.stopPropagation();
    setEditingDept(dept);
    deptForm.setFieldsValue({ name: dept.name, description: dept.description });
    setDeptModalOpen(true);
  };

  const handleDeptSubmit = async () => {
    try {
      const values = await deptForm.validateFields();
      if (editingDept) {
        await departmentService.update(editingDept.id, values);
        message.success('Cập nhật phòng ban thành công');
      } else {
        await departmentService.create(values);
        message.success('Tạo phòng ban thành công');
      }
      setDeptModalOpen(false);
      fetchData();
    } catch (err) {
      if (err.response?.data?.detail) {
        message.error(err.response.data.detail);
      }
    }
  };

  const handleDeleteDept = async (id, e) => {
    e?.stopPropagation();
    try {
      await departmentService.delete(id);
      message.success('Xóa phòng ban thành công');
      if (selectedDept?.id === id) setSelectedDept(null);
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa phòng ban');
    }
  };

  // ---- RENDER: Department list (overview) ----
  const renderDepartmentView = () => (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 !text-[52px]">Nhân sự</Title>
          <Text className="!text-[30px] !text-[#6b7289]">Quản lý nhân viên theo phòng ban</Text>
        </div>
        <div className="flex gap-2">
          <Button icon={<PlusOutlined />} onClick={openCreateDept}>Thêm phòng ban</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateEmp}>Thêm nhân viên</Button>
        </div>
      </div>

      {/* Stats */}
      <Row gutter={16} className="mt-5">
        <Col xs={24} md={8}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-100">
                <ApartmentOutlined className="text-lg text-blue-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Phòng ban</p>
                <p className="m-0 text-2xl font-bold">{departments.length}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-green-100">
                <TeamOutlined className="text-lg text-green-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Tổng nhân viên</p>
                <p className="m-0 text-2xl font-bold">{totalEmployees} <span className="text-sm font-normal text-green-600">({activeCount} đang làm)</span></p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-orange-100">
                <UserOutlined className="text-lg text-orange-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Tạm nghỉ</p>
                <p className="m-0 text-2xl font-bold">{onLeaveCount}</p>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Department cards */}
      <Title level={4} className="!mt-6 !mb-3">Chọn phòng ban để xem nhân viên</Title>
      {departments.length === 0 && !loading ? (
        <Empty description="Chưa có phòng ban nào" className="mt-8" />
      ) : (
        <Row gutter={[16, 16]}>
          {departments.map((dept, idx) => {
            const colorClass = DEPT_COLORS[idx % DEPT_COLORS.length];
            return (
              <Col xs={24} sm={12} lg={8} xl={6} key={dept.id}>
                <Card
                  className="panel-card !h-full cursor-pointer transition-all hover:shadow-lg hover:-translate-y-1"
                  onClick={() => { setSelectedDept(dept); setSearch(''); setFilterStatus(null); }}
                >
                  <div className="flex items-start justify-between">
                    <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${colorClass}`}>
                      <ApartmentOutlined className="text-xl text-white" />
                    </div>
                    <div className="flex gap-0.5">
                      <Button type="text" size="small" icon={<SettingOutlined />} onClick={(e) => openEditDept(dept, e)} />
                      <Popconfirm
                        title="Xóa phòng ban?"
                        description="Chỉ xóa được khi không còn nhân viên"
                        onConfirm={(e) => handleDeleteDept(dept.id, e)}
                        onCancel={(e) => e?.stopPropagation()}
                        okText="Xóa"
                        cancelText="Hủy"
                      >
                        <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={(e) => e.stopPropagation()} />
                      </Popconfirm>
                    </div>
                  </div>

                  <h3 className="mt-4 mb-1 text-lg font-semibold">{dept.name}</h3>
                  {dept.description && (
                    <p className="m-0 text-sm text-gray-400 line-clamp-2">{dept.description}</p>
                  )}

                  <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
                    <span className="flex items-center gap-1.5 text-sm text-gray-500">
                      <TeamOutlined /> {dept.employee_count} nhân viên
                    </span>
                    {dept.manager_name && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <UserOutlined /> {dept.manager_name}
                      </span>
                    )}
                  </div>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );

  // ---- RENDER: Employee list of selected department ----
  const renderEmployeeView = () => (
    <div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            className="!text-lg"
            onClick={() => setSelectedDept(null)}
          />
          <div>
            <Title level={2} className="!mb-0 !text-[40px]">{selectedDept.name}</Title>
            <Text className="!text-[16px] !text-[#6b7289]">
              {selectedDept.description || 'Phòng ban'} · {deptEmployees.length} nhân viên
            </Text>
          </div>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={openCreateEmp}>
          Thêm nhân viên
        </Button>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <Input
          className="search-input !max-w-[300px]"
          prefix={<SearchOutlined />}
          placeholder="Tìm kiếm nhân viên..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
        <Select
          className="!min-w-[160px]"
          placeholder="Trạng thái"
          value={filterStatus}
          onChange={setFilterStatus}
          allowClear
          options={[
            { value: 'active', label: 'Đang làm' },
            { value: 'resigned', label: 'Nghỉ việc' },
            { value: 'on_leave', label: 'Tạm nghỉ' },
          ]}
        />
      </div>

      {deptEmployees.length === 0 ? (
        <Empty description="Chưa có nhân viên trong phòng ban này" className="mt-12" />
      ) : (
        <Row gutter={[16, 16]} className="mt-5">
          {deptEmployees.map((emp) => {
            const st = STATUS_MAP[emp.status] || STATUS_MAP.active;
            return (
              <Col xs={24} md={12} xl={6} key={emp.id}>
                <Card
                  className="panel-card !h-full cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => setDetailModal(emp)}
                >
                  <div className="flex justify-end gap-1">
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={(e) => { e.stopPropagation(); openEditEmp(emp); }}
                    />
                    <Popconfirm
                      title="Xóa nhân viên này?"
                      onConfirm={(e) => { e?.stopPropagation(); handleDeleteEmp(emp.id); }}
                      onCancel={(e) => e?.stopPropagation()}
                      okText="Xóa"
                      cancelText="Hủy"
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
                  </div>

                  <div className="text-center">
                    <Avatar
                      size={80}
                      className="!bg-[#00011f] !text-[20px]"
                      src={resolveAvatarUrl(emp.avatar_url) || undefined}
                    >
                      {(emp.full_name || 'N')[0]}
                    </Avatar>
                    <h3 className="mt-3 text-base font-semibold">{emp.full_name}</h3>
                    <p className="m-0 text-sm text-gray-500">{emp.position}</p>
                    <Tag color={st.color} className="mt-2">{st.label}</Tag>
                  </div>

                  <div className="mt-4 space-y-2 border-t border-gray-100 pt-4 text-sm text-gray-500">
                    <p className="m-0 flex items-center gap-2"><MailOutlined /> {emp.email}</p>
                    {emp.phone && <p className="m-0 flex items-center gap-2"><PhoneOutlined /> {emp.phone}</p>}
                    <p className="m-0 flex items-center gap-2">
                      <UserOutlined /> {emp.employee_code} · {CONTRACT_MAP[emp.contract_type] || emp.contract_type}
                    </p>
                  </div>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );

  return (
    <div>
      <Spin spinning={loading}>
        {selectedDept ? renderEmployeeView() : renderDepartmentView()}
      </Spin>

      {/* Employee Detail Modal */}
      <Modal
        title="Chi tiết nhân viên"
        open={!!detailModal}
        onCancel={() => setDetailModal(null)}
        footer={null}
        width={520}
      >
        {detailModal && (
          <div className="space-y-3">
            <div className="text-center">
              <Avatar
                size={96}
                className="!bg-[#00011f] !text-[24px]"
                src={resolveAvatarUrl(detailModal.avatar_url) || undefined}
              >
                {(detailModal.full_name || 'N')[0]}
              </Avatar>
              <h2 className="mt-3 text-xl font-bold">{detailModal.full_name}</h2>
              <p className="text-gray-500">{detailModal.position}</p>
            </div>
            <div className="grid grid-cols-2 gap-3 rounded-lg bg-gray-50 p-4 text-sm">
              <div><span className="font-medium text-gray-600">Mã NV:</span> {detailModal.employee_code}</div>
              <div><span className="font-medium text-gray-600">Phòng ban:</span> {detailModal.department_name}</div>
              <div><span className="font-medium text-gray-600">Email:</span> {detailModal.email}</div>
              <div><span className="font-medium text-gray-600">SĐT:</span> {detailModal.phone || '—'}</div>
              <div><span className="font-medium text-gray-600">Loại HĐ:</span> {CONTRACT_MAP[detailModal.contract_type]}</div>
              <div>
                <span className="font-medium text-gray-600">Trạng thái:</span>{' '}
                <Badge color={STATUS_MAP[detailModal.status]?.color} text={STATUS_MAP[detailModal.status]?.label} />
              </div>
              <div><span className="font-medium text-gray-600">Ngày vào:</span> {detailModal.start_date}</div>
              <div><span className="font-medium text-gray-600">CMND/CCCD:</span> {detailModal.identity_number || '—'}</div>
              {detailModal.notes && (
                <div className="col-span-2"><span className="font-medium text-gray-600">Ghi chú:</span> {detailModal.notes}</div>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Employee Create/Edit Modal */}
      <Modal
        title={editingEmp ? 'Chỉnh sửa nhân viên' : 'Thêm nhân viên mới'}
        open={empModalOpen}
        onOk={handleEmpSubmit}
        onCancel={() => setEmpModalOpen(false)}
        okText={editingEmp ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
        width={600}
      >
        <Form form={empForm} layout="vertical" className="mt-4">
          <Row gutter={16}>
            {!editingEmp && (
              <Col span={12}>
                <Form.Item
                  name="user_id"
                  label="User ID"
                  rules={[{ required: true, message: 'Bắt buộc' }]}
                >
                  <InputNumber className="!w-full" placeholder="ID người dùng" min={1} />
                </Form.Item>
              </Col>
            )}
            {!editingEmp && (
              <Col span={12}>
                <Form.Item
                  name="employee_code"
                  label="Mã nhân viên"
                  rules={[{ required: true, message: 'Bắt buộc' }]}
                >
                  <Input placeholder="VD: NV001" />
                </Form.Item>
              </Col>
            )}
            <Col span={12}>
              <Form.Item
                name="department_id"
                label="Phòng ban"
                rules={[{ required: !editingEmp, message: 'Bắt buộc' }]}
              >
                <Select placeholder="Chọn phòng ban" options={deptOptions} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="position"
                label="Chức vụ"
                rules={[{ required: !editingEmp, message: 'Bắt buộc' }]}
              >
                <Input placeholder="VD: Senior Developer" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="contract_type" label="Loại hợp đồng">
                <Select
                  placeholder="Chọn loại HĐ"
                  options={[
                    { value: 'probation', label: 'Thử việc' },
                    { value: 'permanent', label: 'Chính thức' },
                    { value: 'temporary', label: 'Thời vụ' },
                  ]}
                />
              </Form.Item>
            </Col>
            {editingEmp && (
              <Col span={12}>
                <Form.Item name="status" label="Trạng thái">
                  <Select
                    placeholder="Chọn trạng thái"
                    options={[
                      { value: 'active', label: 'Đang làm' },
                      { value: 'resigned', label: 'Nghỉ việc' },
                      { value: 'on_leave', label: 'Tạm nghỉ' },
                    ]}
                  />
                </Form.Item>
              </Col>
            )}
            <Col span={12}>
              <Form.Item
                name="start_date"
                label="Ngày bắt đầu"
                rules={[{ required: !editingEmp, message: 'Bắt buộc' }]}
              >
                <DatePicker className="!w-full" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_date" label="Ngày kết thúc">
                <DatePicker className="!w-full" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="identity_number" label="CMND/CCCD">
                <Input placeholder="Số CMND/CCCD" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="notes" label="Ghi chú">
                <Input.TextArea rows={2} placeholder="Ghi chú thêm..." />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Department Create/Edit Modal */}
      <Modal
        title={editingDept ? 'Chỉnh sửa phòng ban' : 'Thêm phòng ban mới'}
        open={deptModalOpen}
        onOk={handleDeptSubmit}
        onCancel={() => setDeptModalOpen(false)}
        okText={editingDept ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
      >
        <Form form={deptForm} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label="Tên phòng ban"
            rules={[{ required: true, message: 'Vui lòng nhập tên phòng ban' }]}
          >
            <Input placeholder="VD: Phòng Công nghệ" />
          </Form.Item>
          <Form.Item name="description" label="Mô tả">
            <TextArea rows={3} placeholder="Mô tả ngắn về phòng ban" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default HRStaffPage;
