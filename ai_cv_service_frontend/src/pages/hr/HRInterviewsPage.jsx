import {
  CalendarOutlined,
  DeleteOutlined,
  EditOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import dayjs from "dayjs";
import { useMemo, useState } from "react";

import { useApplicationsByCompany } from "../../hooks/useApplications";
import {
  useCreateInterview,
  useDeleteInterview,
  useInterviews,
  useUpdateInterview,
  useSyncInterview,
} from "../../hooks/useInterviews";

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const statusColor = {
  scheduled: "gold",
  success: "green",
  failed: "red",
};

function HRInterviewsPage() {
  const [form] = Form.useForm();
  const [editingInterview, setEditingInterview] = useState(null);
  const [localInterviews, setLocalInterviews] = useState([]);

  const { data: interviews = [], isLoading } = useInterviews();
  const { data: applicationsData } = useApplicationsByCompany(
    { page: 1, pageSize: 100, status: "accepted" },
    true
  );

  const createInterviewMutation = useCreateInterview();
  const updateInterviewMutation = useUpdateInterview();
  const deleteInterviewMutation = useDeleteInterview();
  const syncInterviewMutation = useSyncInterview();

  const applications = applicationsData?.items || [];

  const displayedInterviews = useMemo(() => {
    const serverIds = new Set(interviews.map((item) => item.id));
    const localOnlyInterviews = localInterviews.filter(
      (item) => !serverIds.has(item.id)
    );
    return [...localOnlyInterviews, ...interviews];
  }, [interviews, localInterviews]);

  const applicationOptions = useMemo(() => {
    return applications.map((item) => ({
      value: item.id,
      label: `${item.candidate_name || item.candidate_email} - ${item.job_title || `Job #${item.job_id}`}`,
    }));
  }, [applications]);

  const handleSubmit = async (values) => {
    try {
      const [startsAt, endsAt] = values.time_range || [];
      if (!startsAt || !endsAt) {
        message.error("Vui lòng chọn thời gian bắt đầu và kết thúc");
        return;
      }

      const payload = {
        application_id: values.application_id,
        title: values.title,
        starts_at: startsAt.toDate().toISOString(),
        ends_at: endsAt.toDate().toISOString(),
        interview_mode: values.interview_mode,
        location: values.location || null,
        notes: values.notes || null,
      };

      console.log("[DEBUG] Submitting interview payload:", payload);

      if (editingInterview) {
        const updated = await updateInterviewMutation.mutateAsync({
          id: editingInterview.id,
          payload,
        });
        setLocalInterviews((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item))
        );
        message.success("Cập nhật lịch phỏng vấn thành công");
      } else {
        const created = await createInterviewMutation.mutateAsync(payload);
        console.log("[DEBUG] Interview created response:", created);
        setLocalInterviews((prev) => [created, ...prev]);
        message.success("Tạo lịch phỏng vấn thành công");
      }

      setEditingInterview(null);
      form.resetFields();
    } catch (error) {
      console.error("[ERROR] Interview submission failed:", {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message,
      });

      let errorMsg = "Không thể lưu lịch phỏng vấn";
      if (error?.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error?.response?.data?.message) {
        errorMsg = error.response.data.message;
      } else if (typeof error?.response?.data === "string") {
        errorMsg = error.response.data;
      } else if (error?.message) {
        errorMsg = error.message;
      }

      message.error(errorMsg);
    }
  };

  const handleEdit = (row) => {
    setEditingInterview(row);
    form.setFieldsValue({
      application_id: row.application_id,
      title: row.title,
      interview_mode: row.interview_mode,
      location: row.location,
      notes: row.notes,
      time_range: [dayjs(row.starts_at), dayjs(row.ends_at)],
    });
  };

  const handleDelete = async (id) => {
    try {
      await deleteInterviewMutation.mutateAsync(id);
      setLocalInterviews((prev) => prev.filter((item) => item.id !== id));
      message.success("Đã xóa lịch phỏng vấn");
      if (editingInterview?.id === id) {
        setEditingInterview(null);
        form.resetFields();
      }
    } catch (error) {
      message.error(error?.response?.data?.detail || "Không thể xóa lịch");
    }
  };

  const handleSyncInterview = async (row) => {
    try {
      const synced = await syncInterviewMutation.mutateAsync(row.id);
      setLocalInterviews((prev) =>
        prev.map((item) => (item.id === synced.id ? synced : item))
      );
      message.success("Đồng bộ với Google Calendar thành công");
    } catch (error) {
      message.error(error?.response?.data?.detail || "Không thể đồng bộ lịch phỏng vấn");
    }
  };

  const handleChangeStatus = async (row, nextStatus) => {
    try {
      await updateInterviewMutation.mutateAsync({
        id: row.id,
        payload: { result_status: nextStatus },
      });
      message.success("Cập nhật trạng thái thành công");
    } catch (error) {
      message.error(
        error?.response?.data?.detail || "Không thể cập nhật trạng thái"
      );
    }
  };

  const columns = [
    {
      title: "Ứng viên",
      key: "candidate",
      render: (_, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{row.candidate_name || `Candidate #${row.candidate_id}`}</Text>
          <Text type="secondary">{row.candidate_email || "-"}</Text>
          <Text type="secondary">{row.job_title || "-"}</Text>
        </Space>
      ),
    },
    {
      title: "Thông tin lịch",
      key: "info",
      render: (_, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{row.title}</Text>
          <Text>
            {dayjs(row.starts_at).format("DD/MM/YYYY HH:mm")} -{" "}
            {dayjs(row.ends_at).format("DD/MM/YYYY HH:mm")}
          </Text>
          <Text>
            {row.interview_mode === "online" ? "Online" : "Offline"}
            {row.location ? ` - ${row.location}` : ""}
          </Text>
          {row.notes ? <Text type="secondary">{row.notes}</Text> : null}
          {!row.calendar_event_id ? (
            <Tag color="orange" className="!rounded-full !px-2">
              Chưa đồng bộ
            </Tag>
          ) : null}
          {row.calendar_url ? (
            <a href={row.calendar_url} target="_blank" rel="noreferrer">
              <LinkOutlined /> Mở Google Calendar
            </a>
          ) : null}
        </Space>
      ),
    },
    {
      title: "Trạng thái",
      key: "status",
      render: (_, row) => (
        <Space direction="vertical">
          <Tag color={statusColor[row.result_status] || "default"}>
            {row.result_status?.toUpperCase()}
          </Tag>
          <Select
            size="small"
            value={row.result_status}
            style={{ width: 130 }}
            options={[
              { value: "scheduled", label: "Scheduled" },
              { value: "success", label: "Success" },
              { value: "failed", label: "Failed" },
            ]}
            onChange={(value) => handleChangeStatus(row, value)}
          />
        </Space>
      ),
    },
    {
      title: "Thao tác",
      key: "actions",
      render: (_, row) => (
        <Space>
          {!row.calendar_event_id ? (
            <Button
              type="default"
              onClick={() => handleSyncInterview(row)}
              loading={syncInterviewMutation.isPending}
            >
              Đồng bộ
            </Button>
          ) : null}
          <Button
            icon={<EditOutlined />}
            onClick={() => handleEdit(row)}
          >
            Sửa
          </Button>
          <Popconfirm
            title="Xóa lịch phỏng vấn?"
            okText="Xóa"
            cancelText="Hủy"
            onConfirm={() => handleDelete(row.id)}
          >
            <Button danger icon={<DeleteOutlined />}>
              Xóa
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size={24} className="w-full">
      <div>
        <Title level={3} className="!mb-1">
          Lịch phỏng vấn
        </Title>
        <Text type="secondary">
          Tạo lịch từ application, quản lý trạng thái và mở event trên Google Calendar
        </Text>
      </div>

      <Card>
        <Form
          layout="vertical"
          form={form}
          onFinish={handleSubmit}
          initialValues={{
            interview_mode: "online",
          }}
        >
          <Form.Item
            name="application_id"
            label="Ứng viên / Application"
            rules={[{ required: true, message: "Vui lòng chọn application" }]}
          >
            <Select
              showSearch
              placeholder="Chọn application"
              options={applicationOptions}
              optionFilterProp="label"
            />
          </Form.Item>

          <Form.Item
            name="title"
            label="Tiêu đề phỏng vấn"
            rules={[{ required: true, message: "Vui lòng nhập tiêu đề" }]}
          >
            <Input placeholder="Ví dụ: Phỏng vấn vòng 1 - Backend" />
          </Form.Item>

          <Form.Item
            name="time_range"
            label="Ngày giờ phỏng vấn"
            rules={[{ required: true, message: "Vui lòng chọn thời gian" }]}
          >
            <RangePicker
              showTime
              format="DD/MM/YYYY HH:mm"
              className="w-full"
            />
          </Form.Item>

          <Form.Item
            name="interview_mode"
            label="Hình thức"
            rules={[{ required: true, message: "Vui lòng chọn hình thức" }]}
          >
            <Select
              options={[
                { value: "online", label: "Online" },
                { value: "offline", label: "Offline" },
              ]}
            />
          </Form.Item>

          <Form.Item
            shouldUpdate={(prev, cur) => prev.interview_mode !== cur.interview_mode}
            noStyle
          >
            {({ getFieldValue }) => {
              const isOffline = getFieldValue("interview_mode") === "offline";
              return (
                <Form.Item
                  name="location"
                  label={isOffline ? "Địa điểm" : "Link / nền tảng"}
                  rules={
                    isOffline
                      ? [{ required: true, message: "Vui lòng nhập địa điểm" }]
                      : []
                  }
                >
                  <Input
                    placeholder={
                      isOffline
                        ? "Ví dụ: Văn phòng tầng 5"
                        : "Ví dụ: Google Meet / Zoom"
                    }
                  />
                </Form.Item>
              );
            }}
          </Form.Item>

          <Form.Item name="notes" label="Ghi chú">
            <TextArea rows={4} placeholder="Nhập ghi chú cho buổi phỏng vấn" />
          </Form.Item>

          <Space>
            <Button
              type="primary"
              htmlType="submit"
              icon={<CalendarOutlined />}
              loading={
                createInterviewMutation.isPending || updateInterviewMutation.isPending
              }
            >
              {editingInterview ? "Cập nhật lịch" : "Lưu lịch"}
            </Button>
            {editingInterview ? (
              <Button
                onClick={() => {
                  setEditingInterview(null);
                  form.resetFields();
                }}
              >
                Hủy sửa
              </Button>
            ) : null}
          </Space>
        </Form>
      </Card>

      <Card title="Danh sách phỏng vấn">
        <Table
          rowKey="id"
          columns={columns}
          dataSource={displayedInterviews}
          loading={isLoading}
          pagination={{ pageSize: 8 }}
        />
      </Card>
    </Space>
  );
}

export default HRInterviewsPage;