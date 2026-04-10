import {
  CheckCircleFilled,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  FileTextOutlined,
  MinusCircleOutlined,
  PlusOutlined,
  RocketOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Badge,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Tabs,
  Tag,
  Timeline,
  Typography,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { employeeService } from '../../services/employeeService';
import { onboardingService } from '../../services/onboardingService';

const { Title, Text } = Typography;
const { TextArea } = Input;

const STATUS_MAP = {
  not_started: { color: 'default', label: 'Chưa bắt đầu', icon: <ClockCircleOutlined /> },
  in_progress: { color: 'processing', label: 'Đang thực hiện', icon: <RocketOutlined /> },
  completed: { color: 'success', label: 'Hoàn thành', icon: <CheckCircleFilled /> },
};

const PRIORITY_MAP = {
  high: { color: 'red', label: 'Cao' },
  medium: { color: 'orange', label: 'Trung bình' },
  low: { color: 'blue', label: 'Thấp' },
};

function HROnboardingPage() {
  const [templates, setTemplates] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('assignments');

  // Template modal
  const [tmplModalOpen, setTmplModalOpen] = useState(false);
  const [editingTmpl, setEditingTmpl] = useState(null);
  const [tmplForm] = Form.useForm();

  // Assignment modal
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [assignForm] = Form.useForm();

  // Detail modal (assignment checklist)
  const [detailAssignment, setDetailAssignment] = useState(null);

  // Filters
  const [searchAssign, setSearchAssign] = useState('');
  const [filterStatus, setFilterStatus] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [tmplData, assignData, empData] = await Promise.all([
        onboardingService.listTemplates(),
        onboardingService.listAssignments(),
        employeeService.list(),
      ]);
      setTemplates(tmplData);
      setAssignments(assignData);
      setEmployees(empData);
    } catch {
      message.error('Không thể tải dữ liệu onboarding');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredAssignments = useMemo(() => {
    return assignments.filter((a) => {
      const hitSearch =
        !searchAssign ||
        a.employee_name?.toLowerCase().includes(searchAssign.toLowerCase()) ||
        a.employee_code?.toLowerCase().includes(searchAssign.toLowerCase()) ||
        a.template_name?.toLowerCase().includes(searchAssign.toLowerCase());
      const hitStatus = !filterStatus || a.status === filterStatus;
      return hitSearch && hitStatus;
    });
  }, [assignments, searchAssign, filterStatus]);

  const tmplOptions = useMemo(
    () => templates.map((t) => ({ value: t.id, label: `${t.name} (${t.task_count} bước)` })),
    [templates],
  );

  const empOptions = useMemo(
    () =>
      employees
        .filter((e) => e.contract_type === 'probation')
        .map((e) => ({
          value: e.id,
          label: `${e.full_name} (${e.employee_code}) — ${e.position || 'N/A'}`,
        })),
    [employees],
  );

  // ── Template handlers ─────────────────────────────

  const openCreateTmpl = () => {
    setEditingTmpl(null);
    tmplForm.resetFields();
    tmplForm.setFieldsValue({ tasks: [{ title: '', priority: 'medium', order: 0 }] });
    setTmplModalOpen(true);
  };

  const openEditTmpl = (tmpl) => {
    setEditingTmpl(tmpl);
    tmplForm.setFieldsValue({
      name: tmpl.name,
      description: tmpl.description,
      tasks: tmpl.tasks.map((t) => ({
        title: t.title,
        description: t.description,
        priority: t.priority,
        order: t.order,
      })),
    });
    setTmplModalOpen(true);
  };

  const handleTmplSubmit = async () => {
    try {
      const values = await tmplForm.validateFields();
      const payload = {
        name: values.name,
        description: values.description || null,
        tasks: (values.tasks || []).map((t, i) => ({
          title: t.title,
          description: t.description || null,
          priority: t.priority || 'medium',
          order: t.order ?? i,
        })),
      };
      if (editingTmpl) {
        await onboardingService.updateTemplate(editingTmpl.id, payload);
        message.success('Cập nhật mẫu thành công');
      } else {
        await onboardingService.createTemplate(payload);
        message.success('Tạo mẫu onboarding thành công');
      }
      setTmplModalOpen(false);
      fetchData();
    } catch (err) {
      if (err.response?.data?.detail) message.error(err.response.data.detail);
    }
  };

  const handleDeleteTmpl = async (id) => {
    try {
      await onboardingService.deleteTemplate(id);
      message.success('Xóa mẫu thành công');
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa');
    }
  };

  // ── Assignment handlers ───────────────────────────

  const openCreateAssign = () => {
    assignForm.resetFields();
    setAssignModalOpen(true);
  };

  const handleAssignSubmit = async () => {
    try {
      const values = await assignForm.validateFields();
      await onboardingService.createAssignment({
        employee_id: values.employee_id,
        template_id: values.template_id,
        due_date: values.due_date?.format('YYYY-MM-DD') || null,
        notes: values.notes || null,
      });
      message.success('Giao onboarding thành công');
      setAssignModalOpen(false);
      fetchData();
    } catch (err) {
      if (err.response?.data?.detail) message.error(err.response.data.detail);
    }
  };

  const handleDeleteAssign = async (id) => {
    try {
      await onboardingService.deleteAssignment(id);
      message.success('Xóa phân công thành công');
      fetchData();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa');
    }
  };

  const handleToggleTask = async (assignmentId, taskId) => {
    try {
      const updated = await onboardingService.toggleTask(assignmentId, taskId);
      setDetailAssignment(updated);
      // Refresh list
      setAssignments((prev) =>
        prev.map((a) => (a.id === updated.id ? updated : a)),
      );
      // Auto-conversion notification
      if (updated.status === 'completed' && updated.employee_contract_type === 'permanent') {
        message.success(`${updated.employee_name} đã hoàn thành onboarding và được chuyển sang nhân viên chính thức!`);
        // Refresh employee list to reflect contract change
        const empData = await employeeService.list();
        setEmployees(empData);
      }
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể cập nhật');
    }
  };

  // ── Stats ─────────────────────────────────────────
  const totalAssignments = assignments.length;
  const completedCount = assignments.filter((a) => a.status === 'completed').length;
  const inProgressCount = assignments.filter((a) => a.status === 'in_progress').length;
  const notStartedCount = assignments.filter((a) => a.status === 'not_started').length;

  // ── RENDER: Assignments tab ───────────────────────
  const renderAssignments = () => (
    <div>
      {/* Stats */}
      <Row gutter={16} className="mb-5">
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-100">
                <RocketOutlined className="text-lg text-blue-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Tổng phân công</p>
                <p className="m-0 text-2xl font-bold">{totalAssignments}</p>
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
                <p className="m-0 text-sm text-gray-500">Đang thực hiện</p>
                <p className="m-0 text-2xl font-bold">{inProgressCount}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-green-100">
                <CheckCircleFilled className="text-lg text-green-600" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Hoàn thành</p>
                <p className="m-0 text-2xl font-bold">{completedCount}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card className="panel-card">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-gray-100">
                <ClockCircleOutlined className="text-lg text-gray-500" />
              </div>
              <div>
                <p className="m-0 text-sm text-gray-500">Chưa bắt đầu</p>
                <p className="m-0 text-2xl font-bold">{notStartedCount}</p>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <Input
          className="search-input !max-w-[300px]"
          prefix={<SearchOutlined />}
          placeholder="Tìm nhân viên, mẫu..."
          value={searchAssign}
          onChange={(e) => setSearchAssign(e.target.value)}
          allowClear
        />
        <Select
          className="!min-w-[180px]"
          placeholder="Trạng thái"
          value={filterStatus}
          onChange={setFilterStatus}
          allowClear
          options={[
            { value: 'not_started', label: 'Chưa bắt đầu' },
            { value: 'in_progress', label: 'Đang thực hiện' },
            { value: 'completed', label: 'Hoàn thành' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateAssign}>
          Giao Onboarding
        </Button>
      </div>

      {/* Assignment cards */}
      {filteredAssignments.length === 0 ? (
        <Empty description="Chưa có phân công onboarding nào" className="mt-10" />
      ) : (
        <Row gutter={[16, 16]}>
          {filteredAssignments.map((a) => {
            const st = STATUS_MAP[a.status] || STATUS_MAP.not_started;
            const pct = a.total_tasks > 0 ? Math.round((a.completed_tasks / a.total_tasks) * 100) : 0;
            const overdue = a.due_date && dayjs(a.due_date).isBefore(dayjs(), 'day') && a.status !== 'completed';
            return (
              <Col xs={24} md={12} xl={8} key={a.id}>
                <Card
                  className="panel-card !h-full cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => setDetailAssignment(a)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar size={44} className="!bg-[#00011f]" icon={<UserOutlined />} />
                      <div>
                        <h4 className="m-0 text-base font-semibold">{a.employee_name}</h4>
                        <p className="m-0 text-xs text-gray-400">{a.employee_code} · {a.employee_position || '—'}</p>
                        <p className="m-0 text-xs text-gray-400">{a.employee_department || '—'}</p>
                      </div>
                    </div>
                    <Popconfirm
                      title="Xóa phân công này?"
                      onConfirm={(e) => { e?.stopPropagation(); handleDeleteAssign(a.id); }}
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

                  <div className="mt-3">
                    <p className="m-0 mb-1 text-sm font-medium text-gray-700">
                      <FileTextOutlined className="mr-1" /> {a.template_name}
                    </p>
                    <Badge status={st.color} text={st.label} />
                    {a.employee_contract_type === 'permanent' && (
                      <Tag color="green" className="ml-2">Chính thức</Tag>
                    )}
                    {a.employee_contract_type === 'probation' && (
                      <Tag color="orange" className="ml-2">Thử việc</Tag>
                    )}
                    {overdue && <Tag color="red" className="ml-2">Quá hạn</Tag>}
                  </div>

                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                      <span>{a.completed_tasks}/{a.total_tasks} bước</span>
                      <span>{pct}%</span>
                    </div>
                    <Progress percent={pct} showInfo={false} strokeColor={pct === 100 ? '#52c41a' : '#1677ff'} size="small" />
                  </div>

                  {a.due_date && (
                    <p className="m-0 mt-2 text-xs text-gray-400">
                      Hạn: {dayjs(a.due_date).format('DD/MM/YYYY')}
                    </p>
                  )}
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );

  // ── RENDER: Templates tab ─────────────────────────
  const renderTemplates = () => (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <Text className="text-gray-500">Các mẫu onboarding có sẵn trong công ty</Text>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateTmpl}>
          Tạo mẫu mới
        </Button>
      </div>

      {templates.length === 0 ? (
        <Empty description="Chưa có mẫu onboarding nào" className="mt-10" />
      ) : (
        <Row gutter={[16, 16]}>
          {templates.map((tmpl) => (
            <Col xs={24} md={12} xl={8} key={tmpl.id}>
              <Card className="panel-card !h-full">
                <div className="flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600">
                    <FileTextOutlined className="text-lg text-white" />
                  </div>
                  <div className="flex gap-1">
                    <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEditTmpl(tmpl)} />
                    <Popconfirm
                      title="Xóa mẫu này?"
                      description="Chỉ xóa được khi không còn phân công đang hoạt động"
                      onConfirm={() => handleDeleteTmpl(tmpl.id)}
                      okText="Xóa"
                      cancelText="Hủy"
                    >
                      <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </div>
                </div>

                <h3 className="mt-3 mb-1 text-lg font-semibold">{tmpl.name}</h3>
                {tmpl.description && (
                  <p className="m-0 text-sm text-gray-400 line-clamp-2">{tmpl.description}</p>
                )}

                <div className="mt-3 border-t border-gray-100 pt-3">
                  <p className="m-0 text-sm text-gray-500 mb-2">
                    <CheckCircleOutlined className="mr-1" /> {tmpl.task_count} bước cần hoàn thành
                  </p>
                  {tmpl.tasks.slice(0, 3).map((t) => (
                    <div key={t.id} className="flex items-center gap-2 text-sm text-gray-600 py-0.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-gray-300" />
                      <span className="truncate">{t.title}</span>
                      <Tag color={PRIORITY_MAP[t.priority]?.color} className="!text-xs !ml-auto">
                        {PRIORITY_MAP[t.priority]?.label}
                      </Tag>
                    </div>
                  ))}
                  {tmpl.tasks.length > 3 && (
                    <p className="m-0 mt-1 text-xs text-gray-400">
                      +{tmpl.tasks.length - 3} bước khác...
                    </p>
                  )}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );

  return (
    <div>
      <div className="mb-5">
        <Title level={2} className="!mb-1 !text-[52px]">Onboarding</Title>
        <Text className="!text-[30px] !text-[#6b7289]">Quản lý quy trình tiếp nhận nhân viên mới</Text>
      </div>

      <Spin spinning={loading}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'assignments',
              label: (
                <span className="flex items-center gap-1.5">
                  <RocketOutlined /> Phân công ({assignments.length})
                </span>
              ),
              children: renderAssignments(),
            },
            {
              key: 'templates',
              label: (
                <span className="flex items-center gap-1.5">
                  <FileTextOutlined /> Mẫu Onboarding ({templates.length})
                </span>
              ),
              children: renderTemplates(),
            },
          ]}
        />
      </Spin>

      {/* ── Detail / Checklist Modal ─────────────────── */}
      <Modal
        title={
          detailAssignment
            ? `Onboarding: ${detailAssignment.employee_name}`
            : 'Chi tiết'
        }
        open={!!detailAssignment}
        onCancel={() => setDetailAssignment(null)}
        footer={null}
        width={600}
      >
        {detailAssignment && (() => {
          const a = detailAssignment;
          const st = STATUS_MAP[a.status] || STATUS_MAP.not_started;
          const pct = a.total_tasks > 0 ? Math.round((a.completed_tasks / a.total_tasks) * 100) : 0;
          return (
            <div className="space-y-4">
              <div className="rounded-lg bg-gray-50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="m-0 text-sm text-gray-500">Vị trí: <span className="font-medium text-gray-700">{a.employee_position || '—'}</span></p>
                    <p className="m-0 text-sm text-gray-500">Phòng ban: <span className="font-medium text-gray-700">{a.employee_department || '—'}</span></p>
                    <p className="m-0 text-sm text-gray-500">Mẫu: <span className="font-medium text-gray-700">{a.template_name}</span></p>
                    <p className="m-0 text-sm text-gray-500">Người giao: {a.assigned_by_name || '—'}</p>
                    {a.due_date && <p className="m-0 text-sm text-gray-500">Hạn: {dayjs(a.due_date).format('DD/MM/YYYY')}</p>}
                  </div>
                  <div className="text-center">
                    <Progress type="circle" percent={pct} size={64} strokeColor={pct === 100 ? '#52c41a' : '#1677ff'} />
                    <div className="mt-1">
                      <Badge status={st.color} text={st.label} />
                    </div>
                  </div>
                </div>
                {a.notes && <p className="m-0 mt-2 text-sm text-gray-400">Ghi chú: {a.notes}</p>}
              </div>

              <div>
                <h4 className="mb-3 text-base font-semibold">Danh sách công việc</h4>
                <div className="space-y-2">
                  {a.task_progress.map((tp) => {
                    const pri = PRIORITY_MAP[tp.task_priority] || PRIORITY_MAP.medium;
                    return (
                      <div
                        key={tp.id}
                        className={`flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                          tp.is_completed ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white'
                        }`}
                      >
                        <Checkbox
                          checked={tp.is_completed}
                          onChange={() => handleToggleTask(a.id, tp.task_id)}
                          className="mt-0.5"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-sm font-medium ${tp.is_completed ? 'line-through text-gray-400' : 'text-gray-800'}`}
                            >
                              {tp.task_title}
                            </span>
                            <Tag color={pri.color} className="!text-xs">{pri.label}</Tag>
                          </div>
                          {tp.task_description && (
                            <p className="m-0 mt-0.5 text-xs text-gray-400">{tp.task_description}</p>
                          )}
                          {tp.completed_at && (
                            <p className="m-0 mt-1 text-xs text-green-500">
                              <CheckCircleFilled className="mr-1" />
                              Hoàn thành lúc {dayjs(tp.completed_at).format('DD/MM/YYYY HH:mm')}
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })()}
      </Modal>

      {/* ── Template Create/Edit Modal ───────────────── */}
      <Modal
        title={editingTmpl ? 'Chỉnh sửa mẫu Onboarding' : 'Tạo mẫu Onboarding mới'}
        open={tmplModalOpen}
        onOk={handleTmplSubmit}
        onCancel={() => setTmplModalOpen(false)}
        okText={editingTmpl ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
        width={700}
      >
        <Form form={tmplForm} layout="vertical" className="mt-4">
          <Form.Item
            name="name"
            label="Tên mẫu"
            rules={[{ required: true, message: 'Vui lòng nhập tên mẫu' }]}
          >
            <Input placeholder="VD: Onboarding Nhân viên mới" />
          </Form.Item>
          <Form.Item name="description" label="Mô tả">
            <TextArea rows={2} placeholder="Mô tả ngắn về quy trình" />
          </Form.Item>

          <div className="mb-2 font-medium">Danh sách bước</div>
          <Form.List name="tasks">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...rest }) => (
                  <div key={key} className="mb-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
                    <Row gutter={12}>
                      <Col span={14}>
                        <Form.Item
                          {...rest}
                          name={[name, 'title']}
                          rules={[{ required: true, message: 'Bắt buộc' }]}
                          className="!mb-2"
                        >
                          <Input placeholder="Tên bước" />
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item {...rest} name={[name, 'priority']} className="!mb-2">
                          <Select
                            placeholder="Ưu tiên"
                            options={[
                              { value: 'high', label: 'Cao' },
                              { value: 'medium', label: 'Trung bình' },
                              { value: 'low', label: 'Thấp' },
                            ]}
                          />
                        </Form.Item>
                      </Col>
                      <Col span={4} className="flex items-start justify-end">
                        <Button
                          type="text"
                          danger
                          icon={<MinusCircleOutlined />}
                          onClick={() => remove(name)}
                        />
                      </Col>
                      <Col span={20}>
                        <Form.Item {...rest} name={[name, 'description']} className="!mb-0">
                          <Input placeholder="Mô tả (tùy chọn)" />
                        </Form.Item>
                      </Col>
                      <Col span={4}>
                        <Form.Item {...rest} name={[name, 'order']} className="!mb-0">
                          <InputNumber placeholder="#" min={0} className="!w-full" />
                        </Form.Item>
                      </Col>
                    </Row>
                  </div>
                ))}
                <Button type="dashed" onClick={() => add({ priority: 'medium', order: fields.length })} block icon={<PlusOutlined />}>
                  Thêm bước
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* ── Assignment Create Modal ──────────────────── */}
      <Modal
        title="Giao Onboarding cho nhân viên"
        open={assignModalOpen}
        onOk={handleAssignSubmit}
        onCancel={() => setAssignModalOpen(false)}
        okText="Giao"
        cancelText="Hủy"
        width={520}
      >
        <Form form={assignForm} layout="vertical" className="mt-4">
          <Form.Item
            name="employee_id"
            label="Nhân viên"
            rules={[{ required: true, message: 'Chọn nhân viên' }]}
          >
            <Select
              showSearch
              placeholder="Chọn nhân viên"
              options={empOptions}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
          <Form.Item
            name="template_id"
            label="Mẫu Onboarding"
            rules={[{ required: true, message: 'Chọn mẫu' }]}
          >
            <Select placeholder="Chọn mẫu onboarding" options={tmplOptions} />
          </Form.Item>
          <Form.Item name="due_date" label="Hạn hoàn thành">
            <DatePicker className="!w-full" format="DD/MM/YYYY" />
          </Form.Item>
          <Form.Item name="notes" label="Ghi chú">
            <TextArea rows={2} placeholder="Ghi chú thêm..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default HROnboardingPage;
