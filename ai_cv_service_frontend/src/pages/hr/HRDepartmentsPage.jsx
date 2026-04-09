import {
  ApartmentOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Spin,
  Typography,
  message,
} from 'antd';
import { useCallback, useEffect, useState } from 'react';

import { departmentService } from '../../services/departmentService';

const { Title, Text } = Typography;
const { TextArea } = Input;

function HRDepartmentsPage() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form] = Form.useForm();

  const fetchDepartments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await departmentService.list();
      setDepartments(data);
    } catch {
      message.error('Không thể tải danh sách phòng ban');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (dept) => {
    setEditing(dept);
    form.setFieldsValue({ name: dept.name, description: dept.description });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editing) {
        await departmentService.update(editing.id, values);
        message.success('Cập nhật phòng ban thành công');
      } else {
        await departmentService.create(values);
        message.success('Tạo phòng ban thành công');
      }
      setModalOpen(false);
      fetchDepartments();
    } catch (err) {
      if (err.response?.data?.detail) {
        message.error(err.response.data.detail);
      }
    }
  };

  const handleDelete = async (id) => {
    try {
      await departmentService.delete(id);
      message.success('Xóa phòng ban thành công');
      fetchDepartments();
    } catch (err) {
      message.error(err.response?.data?.detail || 'Không thể xóa phòng ban');
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 !text-[52px]">Phòng ban</Title>
          <Text className="!text-[30px] !text-[#6b7289]">Quản lý cơ cấu tổ chức công ty</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={openCreate}>
          Thêm phòng ban
        </Button>
      </div>

      <Spin spinning={loading}>
        {departments.length === 0 && !loading ? (
          <Empty description="Chưa có phòng ban nào" className="mt-12" />
        ) : (
          <Row gutter={[16, 16]} className="mt-5">
            {departments.map((dept) => (
              <Col xs={24} md={12} xl={8} key={dept.id}>
                <Card className="panel-card !h-full">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100">
                        <ApartmentOutlined className="text-xl text-blue-600" />
                      </div>
                      <div>
                        <h3 className="m-0 text-lg font-semibold">{dept.name}</h3>
                        {dept.description && (
                          <p className="m-0 mt-1 text-sm text-gray-500">{dept.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button type="text" icon={<EditOutlined />} onClick={() => openEdit(dept)} />
                      <Popconfirm
                        title="Xóa phòng ban này?"
                        description="Phòng ban không có nhân viên mới xóa được"
                        onConfirm={() => handleDelete(dept.id)}
                        okText="Xóa"
                        cancelText="Hủy"
                      >
                        <Button type="text" danger icon={<DeleteOutlined />} />
                      </Popconfirm>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-4 border-t border-gray-100 pt-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <TeamOutlined /> {dept.employee_count} nhân viên
                    </span>
                    {dept.manager_name && (
                      <span className="flex items-center gap-1">
                        <UserOutlined /> {dept.manager_name}
                      </span>
                    )}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      <Modal
        title={editing ? 'Chỉnh sửa phòng ban' : 'Thêm phòng ban mới'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText={editing ? 'Cập nhật' : 'Tạo'}
        cancelText="Hủy"
      >
        <Form form={form} layout="vertical" className="mt-4">
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

export default HRDepartmentsPage;
