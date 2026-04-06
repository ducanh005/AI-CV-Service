import { ArrowRightOutlined } from '@ant-design/icons';
import { Alert, Button, Divider, Form, Input, Typography, message } from 'antd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import AuthFooterHint from '../../components/auth/AuthFooterHint';
import AuthLayout from '../../layouts/AuthLayout';
import { useLogin } from '../../hooks/useAuth';
import { authService } from '../../services/authService';
import { buildSocialState, getSocialProviderLabel } from '../../utils/socialAuth';
import { USER_ROLES } from '../../utils/constants';
import { tokenStorage } from '../../utils/storage';

const { Text } = Typography;

function LoginPage() {
  const navigate = useNavigate();
  const loginMutation = useLogin();
  const [socialLoadingProvider, setSocialLoadingProvider] = useState('');

  const socialEnabled = import.meta.env.VITE_SOCIAL_AUTH_ENABLED !== 'false';

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

  const onSocialAuthStart = async (provider, mode) => {
    setSocialLoadingProvider(provider);
    try {
      const result = await authService.oauthAuthorize(provider, mode, buildSocialState(mode));
      if (!result?.auth_url) {
        throw new Error('Không nhận được URL xác thực social');
      }
      window.location.href = result.auth_url;
    } catch (error) {
      message.error(
        error?.response?.data?.detail ||
          `Không thể bắt đầu đăng nhập bằng ${getSocialProviderLabel(provider)}`,
      );
      setSocialLoadingProvider('');
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

        {socialEnabled && (
          <>
            <Divider className="!my-6 !text-[16px] !text-[#6b7289]">Hoặc tiếp tục với</Divider>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <Button
                block
                onClick={() => onSocialAuthStart('google', 'login')}
                loading={socialLoadingProvider === 'google'}
                className="!h-[48px] !rounded-[12px]"
              >
                Google (Gmail)
              </Button>
              <Button
                block
                onClick={() => onSocialAuthStart('linkedin', 'login')}
                loading={socialLoadingProvider === 'linkedin'}
                className="!h-[48px] !rounded-[12px]"
              >
                LinkedIn
              </Button>
            </div>
          </>
        )}
      </Form>

      <AuthFooterHint type="login" />
    </AuthLayout>
  );
}

export default LoginPage;
