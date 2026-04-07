import {
  DeleteOutlined,
  DollarOutlined,
  EditOutlined,
  EnvironmentOutlined,
  PlusOutlined,
  UsergroupAddOutlined,
} from '@ant-design/icons';
import { Button, Card, Col, Form, Input, Modal, Popconfirm, Row, Select, Tag, Typography, message } from 'antd';
import { useState } from 'react';

import { useCreateJob, useDeleteJob, useJobs, useUpdateJob } from '../../hooks/useJobs';

const { Title, Text } = Typography;

function HRJobsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [form] = Form.useForm();

  const { data } = useJobs({ page: 1, page_size: 50 });
  const jobs = data?.items || [];

  const createMutation = useCreateJob();
  const updateMutation = useUpdateJob();
  const deleteMutation = useDeleteJob();

  const openCreate = () => {
    setEditingJob(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEdit = (job) => {
    setEditingJob(job);
    form.setFieldsValue(job);
    setIsModalOpen(true);
  };

  const onSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingJob) {
        await updateMutation.mutateAsync({ id: editingJob.id, payload: values });
        message.success('Cập nhật tin tuyển dụng thành công');
      } else {
        await createMutation.mutateAsync(values);
        message.success('Đăng tin tuyển dụng thành công');
      }
      setIsModalOpen(false);
    } catch {
      message.error('Không thể lưu tin tuyển dụng');
    }
  };

  const onDeleteJob = async (jobId) => {
    try {
      await deleteMutation.mutateAsync(jobId);
      message.success('Đã xóa tin tuyển dụng');
    } catch {
      message.error('Xóa tin tuyển dụng thất bại');
    }
  };

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 !text-[40px]">Tin tuyển dụng</Title>
          <Text className="!text-[20px] !text-[#6b7289]">Quản lý các vị trí tuyển dụng đang mở</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={openCreate}
          className="!h-[50px] !rounded-[14px] !bg-[#00011f] !px-7 !text-[16px]"
        >
          Đăng tin tuyển dụng
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {jobs.map((job) => (
          <Col xs={24} xl={12} xxl={8} key={job.id}>
            <Card className="panel-card !h-full">
              <div className="flex h-full flex-col">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <h3
                    className="m-0 text-[26px] font-semibold leading-tight"
                    style={{
                      display: '-webkit-box',
                      overflow: 'hidden',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {job.title}
                  </h3>
                  <Tag color={job.status === 'open' ? 'green' : 'default'} className="!m-0 !rounded-full !px-3 !py-1 !text-[13px] !font-medium !leading-[18px]">
                  {job.status === 'open' ? 'Đang mở' : 'Đã đóng'}
                  </Tag>
                </div>

                <div className="min-h-[96px] space-y-2 text-[15px] text-[#6b7289]">
                  <p className="m-0 flex items-center gap-2"><EnvironmentOutlined /> {job.location || 'Hà Nội'}</p>
                  <p className="m-0 flex items-center gap-2"><DollarOutlined /> {job.salary_min || 20}-{job.salary_max || 40} triệu</p>
                  <p className="m-0 flex items-center gap-2"><UsergroupAddOutlined /> 45 ứng viên</p>
                </div>

                <div className="mt-auto flex items-center justify-end gap-2 border-t border-gray-200 pt-3">
                  <Button icon={<EditOutlined />} onClick={() => openEdit(job)} />
                  <Popconfirm
                    title="Xóa tin tuyển dụng"
                    description="Bạn chắc chắn muốn xóa tin này?"
                    okText="Xóa"
                    cancelText="Hủy"
                    onConfirm={() => onDeleteJob(job.id)}
                  >
                    <Button danger icon={<DeleteOutlined />} loading={deleteMutation.isPending} />
                  </Popconfirm>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Modal
        open={isModalOpen}
        title={<span className="text-[38px]">{editingJob ? 'Chỉnh sửa công việc' : 'Tạo công việc'}</span>}
        onCancel={() => setIsModalOpen(false)}
        onOk={onSubmit}
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form layout="vertical" form={form} initialValues={{ status: 'open' }}>
          <Form.Item name="title" label="Tiêu đề" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Mô tả" rules={[{ required: true }]}><Input.TextArea rows={4} /></Form.Item>
          <Form.Item name="location" label="Địa điểm"><Input /></Form.Item>
          <Form.Item name="salary_min" label="Lương tối thiểu"><Input type="number" /></Form.Item>
          <Form.Item name="salary_max" label="Lương tối đa"><Input type="number" /></Form.Item>
          <Form.Item name="required_skills" label="Kỹ năng"><Select mode="tags" /></Form.Item>
          <Form.Item name="status" label="Trạng thái"><Select options={[{ value: 'open', label: 'Đang mở' }, { value: 'closed', label: 'Đã đóng' }]} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default HRJobsPage;
