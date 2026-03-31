import { UserAddOutlined } from '@ant-design/icons';
import { Alert, Button, Form, Input, Select, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';

import AuthFooterHint from '../../components/auth/AuthFooterHint';
import AuthLayout from '../../layouts/AuthLayout';
import { useRegister } from '../../hooks/useAuth';

const { Text } = Typography;

const roleOptions = [
  { label: 'Ứng viên', value: 'user' },
  { label: 'HR', value: 'hr' },
  { label: 'Admin', value: 'admin' },
];

function RegisterPage() {
  const navigate = useNavigate();
  const registerMutation = useRegister();

  const onFinish = async (values) => {
    try {
      await registerMutation.mutateAsync(values);
      if (values.role === 'hr') {
        navigate('/hr/dashboard');
      } else if (values.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/user/dashboard');
      }
    } catch (error) {
      // handled in UI
    }
  };

  return (
    <AuthLayout title="SmartHire" subtitle="Tạo tài khoản mới">
      <Form
        layout="vertical"
        requiredMark={false}
        onFinish={onFinish}
        size="large"
        initialValues={{ role: 'user' }}
      >
        <Form.Item label={<span className="text-[20px] font-semibold">Họ và tên</span>} name="full_name" rules={[{ required: true }]}> 
          <Input placeholder="Nguyễn Văn A" className="!h-[56px] !text-[18px]" />
        </Form.Item>

        <Form.Item label={<span className="text-[20px] font-semibold">Email</span>} name="email" rules={[{ required: true }]}> 
          <Input placeholder="email@example.com" className="!h-[56px] !text-[18px]" />
        </Form.Item>

        <Form.Item label={<span className="text-[20px] font-semibold">Mật khẩu</span>} name="password" rules={[{ required: true }]}> 
          <Input.Password placeholder="••••••••" className="!h-[56px] !text-[18px]" />
        </Form.Item>

        <Form.Item label={<span className="text-[20px] font-semibold">Vai trò</span>} name="role" rules={[{ required: true }]}> 
          <Select options={roleOptions} className="!text-[18px]" />
        </Form.Item>

        {registerMutation.error && (
          <Alert
            type="error"
            showIcon
            className="mb-4"
            message="Đăng ký thất bại"
            description={registerMutation.error?.response?.data?.detail || 'Vui lòng thử lại'}
          />
        )}

        <Button
          htmlType="submit"
          type="primary"
          block
          loading={registerMutation.isPending}
          icon={<UserAddOutlined />}
          className="!h-[56px] !rounded-[14px] !bg-[#00011f] !text-[20px] !font-semibold"
        >
          Đăng ký
        </Button>

        <div className="mt-6 text-center">
          <Text className="!text-[19px]">Đã có tài khoản? </Text>
          <button
            type="button"
            className="border-0 bg-transparent p-0 text-[19px] font-semibold"
            onClick={() => navigate('/login')}
          >
            Đăng nhập
          </button>
        </div>
      </Form>

      <AuthFooterHint type="register" />
    </AuthLayout>
  );
}

export default RegisterPage;
