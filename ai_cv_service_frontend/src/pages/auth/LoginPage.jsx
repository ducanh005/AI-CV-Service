import { ArrowRightOutlined } from '@ant-design/icons';
import { Alert, Button, Form, Input, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';

import AuthFooterHint from '../../components/auth/AuthFooterHint';
import AuthLayout from '../../layouts/AuthLayout';
import { useLogin } from '../../hooks/useAuth';
import { USER_ROLES } from '../../utils/constants';
import { tokenStorage } from '../../utils/storage';

const { Text } = Typography;

function LoginPage() {
  const navigate = useNavigate();
  const loginMutation = useLogin();

  const onFinish = async (values) => {
    try {
      await loginMutation.mutateAsync(values);

      const sessionUser = tokenStorage.getUser();
      if (sessionUser?.role === USER_ROLES.HR) {
        navigate('/hr/dashboard');
      } else if (sessionUser?.role === USER_ROLES.ADMIN) {
        navigate('/admin/dashboard');
      } else {
        navigate('/user/dashboard');
      }
    } catch (error) {
      // handled in UI
    }
  };

  return (
    <AuthLayout title="SmartHire" subtitle="Đăng nhập vào tài khoản">
      <Form layout="vertical" requiredMark={false} onFinish={onFinish} size="large">
        <Form.Item label={<span className="text-[20px] font-semibold">Email</span>} name="email" rules={[{ required: true }]}> 
          <Input placeholder="email@example.com" className="!h-[56px] !text-[18px]" />
        </Form.Item>

        <Form.Item label={<span className="text-[20px] font-semibold">Mật khẩu</span>} name="password" rules={[{ required: true }]}> 
          <Input.Password placeholder="••••••••" className="!h-[56px] !text-[18px]" />
        </Form.Item>

        {loginMutation.error && (
          <Alert
            type="error"
            showIcon
            className="mb-4"
            message="Đăng nhập thất bại"
            description={loginMutation.error?.response?.data?.detail || 'Vui lòng thử lại'}
          />
        )}

        <Button
          htmlType="submit"
          type="primary"
          block
          loading={loginMutation.isPending}
          icon={<ArrowRightOutlined />}
          className="!h-[56px] !rounded-[14px] !bg-[#00011f] !text-[20px] !font-semibold"
        >
          Đăng nhập
        </Button>

        <div className="mt-6 text-center">
          <Text className="!text-[19px]">Chưa có tài khoản? </Text>
          <button
            type="button"
            className="border-0 bg-transparent p-0 text-[19px] font-semibold"
            onClick={() => navigate('/register')}
          >
            Đăng ký
          </button>
        </div>
      </Form>

      <AuthFooterHint type="login" />
    </AuthLayout>
  );
}

export default LoginPage;
