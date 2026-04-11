import {
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  LeftOutlined,
  PlusOutlined,
  RightOutlined,
  StarFilled,
  WarningOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Spin,
  TimePicker,
  Typography,
  message,
} from 'antd';
import dayjs from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { attendanceService } from '../../services/attendanceService';
import { employeeService } from '../../services/employeeService';

dayjs.extend(isoWeek);

const { Title } = Typography;

const STANDARD_HOURS = 9.75; // 8:00 - 17:45
const STANDARD_START = dayjs('08:00', 'HH:mm');

function calcCoefficient(status, workHours) {
  if (status === 'absent') return 0;
  if (status === 'half_day') return 0.5;
  if (!workHours || workHours <= 0) return 0;
  const coeff = Math.min(workHours / STANDARD_HOURS, 1.0);
  return Math.round(coeff * 100) / 100;
}

function getDayCellBg(status, coeff) {
  if (status === 'absent') return '#fff1f0';
  if (status === 'half_day') return '#fff7e6';
  if (coeff >= 0.95) return '#f0fff4';
  if (coeff >= 0.9) return '#f0fff4';
  return '#fff';
}

function getCoeffColor(status, coeff) {
  if (status === 'absent') return '#cf1322';
  if (status === 'half_day') return '#d48806';
  if (status === 'late') return '#d48806';
  if (coeff >= 0.95) return '#389e0d';
  return '#389e0d';
}

function getMonthCalendarDays(year, month) {
  const firstDay = dayjs(`${year}-${String(month).padStart(2, '0')}-01`);
  const lastDay = firstDay.endOf('month');
  const startOfWeek = firstDay.isoWeekday(); // 1=Mon
  const days = [];

  for (let i = 1; i < startOfWeek; i++) {
    days.push({ date: firstDay.subtract(startOfWeek - i, 'day'), isCurrentMonth: false });
  }
  for (let d = firstDay; d.isBefore(lastDay) || d.isSame(lastDay, 'day'); d = d.add(1, 'day')) {
    days.push({ date: d, isCurrentMonth: true });
  }
  while (days.length % 7 !== 0) {
    days.push({ date: days[days.length - 1].date.add(1, 'day'), isCurrentMonth: false });
  }
  return days;
}

const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

function HRAttendancePage() {
  const [attendances, setAttendances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmpId, setSelectedEmpId] = useState(null);
  const [currentMonth, setCurrentMonth] = useState(dayjs());
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();

  const fetchEmployees = useCallback(async () => {
    try {
      const data = await employeeService.list();
      setEmployees(data);
      if (data.length > 0 && !selectedEmpId) setSelectedEmpId(data[0].id);
    } catch {
      message.error('Không thể tải danh sách nhân viên');
    }
  }, []);

  const fetchAttendances = useCallback(async () => {
    if (!selectedEmpId) return;
    setLoading(true);
    try {
      const from_date = currentMonth.startOf('month').format('YYYY-MM-DD');
      const to_date = currentMonth.endOf('month').format('YYYY-MM-DD');
      const data = await attendanceService.list({ employee_id: selectedEmpId, from_date, to_date });
      setAttendances(data);
    } catch {
      message.error('Không thể tải dữ liệu chấm công');
    } finally {
      setLoading(false);
    }
  }, [selectedEmpId, currentMonth]);

  useEffect(() => { fetchEmployees(); }, [fetchEmployees]);
  useEffect(() => { fetchAttendances(); }, [fetchAttendances]);

  const empOptions = useMemo(
    () => employees.map((e) => ({ value: e.id, label: `${e.full_name} (${e.employee_code})` })),
    [employees],
  );

  const attMap = useMemo(() => {
    const map = {};
    attendances.forEach((a) => { map[a.date] = a; });
    return map;
  }, [attendances]);

  const stats = useMemo(() => {
    const year = currentMonth.year();
    const month = currentMonth.month();
    const monthAtts = attendances.filter((a) => {
      const d = dayjs(a.date);
      return d.year() === year && d.month() === month;
    });

    const firstDay = currentMonth.startOf('month');
    const lastDay = dayjs().isBefore(currentMonth.endOf('month')) ? dayjs() : currentMonth.endOf('month');
    let totalWorkDays = 0;
    for (let d = firstDay; !d.isAfter(lastDay, 'day'); d = d.add(1, 'day')) {
      if (d.day() !== 0 && d.day() !== 6) totalWorkDays++;
    }

    const daysWorked = monthAtts.filter((a) => a.status !== 'absent').length;
    const totalOvertime = monthAtts.reduce((sum, a) => {
      if (a.work_hours && a.work_hours > STANDARD_HOURS) return sum + (a.work_hours - STANDARD_HOURS);
      return sum;
    }, 0);
    const lateEarlyHours = monthAtts.reduce((sum, a) => {
      if (!a.check_in) return sum;
      const ci = dayjs(a.check_in, 'HH:mm:ss');
      if (ci.isAfter(STANDARD_START)) return sum + ci.diff(STANDARD_START, 'minute') / 60;
      return sum;
    }, 0);
    const daysOff = monthAtts.filter((a) => a.status === 'absent').length;

    return { totalWorkDays, daysWorked, totalOvertime, lateEarlyHours, daysOff };
  }, [attendances, currentMonth]);

  const calendarDays = useMemo(
    () => getMonthCalendarDays(currentMonth.year(), currentMonth.month() + 1),
    [currentMonth],
  );

  const prevMonth = () => setCurrentMonth((m) => m.subtract(1, 'month'));
  const nextMonth = () => setCurrentMonth((m) => m.add(1, 'month'));
  const goToday = () => setCurrentMonth(dayjs());

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ employee_id: selectedEmpId, date: dayjs(), status: 'present' });
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
      fetchAttendances();
    } catch (err) {
      if (err.response?.data?.detail) message.error(err.response.data.detail);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <Select
          className="!min-w-[280px]"
          showSearch
          placeholder="Chọn nhân viên"
          value={selectedEmpId}
          onChange={setSelectedEmpId}
          options={empOptions}
          filterOption={(input, opt) => (opt?.label ?? '').toLowerCase().includes(input.toLowerCase())}
          size="large"
        />
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={openCreate}>
          Thêm chấm công
        </Button>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between mb-4">
        <Title level={4} className="!mb-0" style={{ color: '#e8590c' }}>
          Bảng công tháng {currentMonth.month() + 1}
        </Title>
        <div className="flex items-center gap-2">
          <Button size="small" onClick={goToday}>Tháng này</Button>
          <Button size="small" icon={<LeftOutlined />} onClick={prevMonth} />
          <Button size="small" icon={<RightOutlined />} onClick={nextMonth} />
          <span className="ml-2 text-sm text-gray-500 flex items-center gap-1">
            <CalendarOutlined /> Tháng {currentMonth.month() + 1}/{currentMonth.year()}
          </span>
        </div>
      </div>

      {/* Stats */}
      <Row gutter={12} className="mb-4">
        {[
          { icon: <CalendarOutlined style={{ color: '#e8590c', fontSize: 18 }} />, bg: '#fff2e8', value: stats.totalWorkDays, color: '#e8590c', label: 'Tổng công của tháng' },
          { icon: <CheckCircleOutlined style={{ color: '#16a34a', fontSize: 18 }} />, bg: '#f0fdf4', value: stats.daysWorked, color: '#16a34a', label: 'Tổng công đã đi làm' },
          { icon: <ClockCircleOutlined style={{ color: '#2563eb', fontSize: 18 }} />, bg: '#eff6ff', value: stats.totalOvertime.toFixed(2), color: '#2563eb', label: 'Tổng giờ làm thêm' },
          { icon: <WarningOutlined style={{ color: '#ca8a04', fontSize: 18 }} />, bg: '#fef9c3', value: stats.lateEarlyHours.toFixed(2), color: '#ca8a04', label: 'Tổng giờ đi muộn, về sớm' },
          { icon: <CloseCircleOutlined style={{ color: '#dc2626', fontSize: 18 }} />, bg: '#fef2f2', value: String(stats.daysOff).padStart(2, '0'), color: '#dc2626', label: 'Tổng số ngày nghỉ' },
        ].map((s, i) => (
          <Col key={i} xs={24} sm={12} md={4} lg={4} xl={4} style={{ flex: 1 }}>
            <div className="rounded-xl bg-white px-4 py-3 flex items-center gap-3" style={{ border: '1px solid #f0f0f0' }}>
              <div className="flex h-10 w-10 items-center justify-center rounded-full shrink-0" style={{ backgroundColor: s.bg }}>
                {s.icon}
              </div>
              <div>
                <div className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</div>
                <div className="text-[11px] text-gray-400 whitespace-nowrap">{s.label}</div>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      {/* Calendar */}
      <Spin spinning={loading}>
        <Card className="panel-card !p-0" styles={{ body: { padding: 0 } }}>
          {/* Weekday header */}
          <div className="grid grid-cols-7" style={{ borderBottom: '1px solid #e5e7eb' }}>
            {WEEKDAYS.map((wd, i) => (
              <div
                key={wd}
                className="py-2.5 text-center text-sm font-semibold"
                style={{
                  color: i >= 5 ? '#9ca3af' : '#6b7280',
                  borderRight: i < 6 ? '1px solid #e5e7eb' : 'none',
                }}
              >
                {wd}
              </div>
            ))}
          </div>

          {/* Calendar rows */}
          {Array.from({ length: Math.ceil(calendarDays.length / 7) }).map((_, weekIdx) => (
            <div key={weekIdx} className="grid grid-cols-7" style={{ borderBottom: '1px solid #e5e7eb' }}>
              {calendarDays.slice(weekIdx * 7, weekIdx * 7 + 7).map((dayInfo, colIdx) => {
                const { date: d, isCurrentMonth } = dayInfo;
                const dateStr = d.format('YYYY-MM-DD');
                const record = attMap[dateStr];
                const isToday = d.isSame(dayjs(), 'day');
                const isWeekend = d.day() === 0 || d.day() === 6;

                const coeff = record ? calcCoefficient(record.status, record.work_hours) : null;
                const bg = record ? getDayCellBg(record.status, coeff) : '#fff';
                const coeffColor = record ? getCoeffColor(record.status, coeff) : '#595959';

                const ciStr = record?.check_in ? dayjs(record.check_in, 'HH:mm:ss').format('H:mm') : null;
                const coStr = record?.check_out ? dayjs(record.check_out, 'HH:mm:ss').format('H:mm') : null;
                const hasOT = record?.work_hours && record.work_hours > STANDARD_HOURS;

                return (
                  <div
                    key={colIdx}
                    className="relative min-h-[110px] p-2 cursor-pointer transition-colors hover:brightness-95"
                    style={{
                      borderRight: colIdx < 6 ? '1px solid #e5e7eb' : 'none',
                      backgroundColor: !isCurrentMonth ? '#fafafa' : bg,
                      opacity: isCurrentMonth ? 1 : 0.35,
                    }}
                    onClick={() => { if (record && isCurrentMonth) openEdit(record); }}
                  >
                    {/* Date */}
                    <div className="flex items-start justify-between">
                      <span className={`text-xs ${isCurrentMonth ? 'text-gray-500' : 'text-gray-300'}`}>
                        {d.date() === 1 ? `${d.month() + 1}/${d.date()}` : d.date()}
                      </span>
                      {isToday && (
                        <span className="inline-flex h-5 w-5 items-center justify-center rounded text-[11px] font-bold text-white" style={{ backgroundColor: '#2563eb' }}>
                          {d.date()}
                        </span>
                      )}
                    </div>

                    {record && isCurrentMonth && (
                      <div className="mt-1 text-center">
                        {/* Tags */}
                        <div className="mb-0.5 flex justify-center gap-0.5 min-h-[18px]">
                          {record.status === 'late' && (
                            <span className="text-[10px] px-1 rounded font-medium" style={{ backgroundColor: '#dcfce7', color: '#16a34a' }}>KL</span>
                          )}
                          {record.status === 'half_day' && (
                            <span className="text-[10px] px-1 rounded font-medium" style={{ backgroundColor: '#fef9c3', color: '#ca8a04' }}>NN</span>
                          )}
                          {hasOT && (
                            <span className="text-[10px] px-1 rounded font-medium" style={{ backgroundColor: '#dbeafe', color: '#2563eb' }}>OT</span>
                          )}
                          {record.status === 'absent' && (
                            <span className="text-[10px] px-1 rounded font-medium" style={{ backgroundColor: '#fee2e2', color: '#dc2626' }}>VM</span>
                          )}
                        </div>

                        {/* Coefficient */}
                        <div className="text-xl font-bold" style={{ color: coeffColor }}>
                          {coeff.toFixed(2)}
                        </div>

                        {/* Time range */}
                        {record.status === 'absent' ? (
                          <div className="text-[11px] text-red-400 mt-0.5">XXXX - XXXX</div>
                        ) : ciStr && coStr ? (
                          <div className="text-[11px] text-gray-400 mt-0.5">{ciStr} - {coStr}</div>
                        ) : null}

                        {/* Status label */}
                        {record.status !== 'absent' && (
                          <div className="text-[11px] text-gray-400">HC</div>
                        )}

                        {/* OT star */}
                        {hasOT && <StarFilled className="absolute top-2 right-2 text-amber-400 text-xs" />}
                      </div>
                    )}

                    {isWeekend && !record && isCurrentMonth && (
                      <div className="mt-6 text-center text-xs text-gray-300">Nghỉ</div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </Card>
      </Spin>

      {/* Modal */}
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
