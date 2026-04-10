import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Select, Space, Typography } from 'antd';
import { ArrowLeftOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import AuthLayout from '../../layouts/AuthLayout';
import { authService } from '../../services/authService';
import { useAuthStore } from '../../store/authStore';
import { tokenStorage } from '../../utils/storage';
import {
  extractRoleFromOAuthState,
  extractAllowedRoles,
  getOAuthGuardSet,
  getSocialProviderLabel,
  isRoleRequiredError,
  isSupportedSocialProvider,
  normalizeOAuthProfile,
  roleLabel,
} from '../../utils/socialAuth';

const { Text } = Typography;

function navigateByRole(navigate, role) {
  if (role === 'hr') {
    navigate('/hr/dashboard', { replace: true });
    return;
  }
  if (role === 'admin') {
    navigate('/admin/dashboard', { replace: true });
    return;
  }
  navigate('/user/dashboard', { replace: true });
}

function SocialOAuthCallbackPage() {
  const navigate = useNavigate();
  const authStore = useAuthStore();
  const { provider: providerParam } = useParams();
  const [searchParams] = useSearchParams();

  const provider = useMemo(() => (providerParam || '').toLowerCase(), [providerParam]);
  const providerLabel = getSocialProviderLabel(provider);

  const [status, setStatus] = useState('Đang khởi tạo phiên xác thực...');
  const [errorMessage, setErrorMessage] = useState('');
  const [pendingPayload, setPendingPayload] = useState(null);
  const [needRoleSelection, setNeedRoleSelection] = useState(false);
  const [allowedRoles, setAllowedRoles] = useState(['user', 'hr', 'admin']);
  const [selectedRole, setSelectedRole] = useState('user');
  const [isCompletingRole, setIsCompletingRole] = useState(false);

  const finalizeSocialAuth = async (payload, role = null) => {
    const registerPayload = role ? { ...payload, role } : payload;

    const tokens = await authService.oauthRegister(provider, registerPayload);
    tokenStorage.setSession({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      user: authStore.user || { role: 'user' },
    });

    const me = await authService.me();
    authStore.setSession({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      user: me,
    });

    setStatus('Xác thực thành công. Đang chuyển vào hệ thống...');
    navigateByRole(navigate, me.role);
  };

  useEffect(() => {
    if (!isSupportedSocialProvider(provider)) {
      setErrorMessage('Nhà cung cấp OAuth không hợp lệ.');
      setStatus('Không thể xác thực tài khoản.');
      return;
    }

    const code = (searchParams.get('code') || '').trim();
    const state = (searchParams.get('state') || '').trim();
    const preferredRoleFromState = extractRoleFromOAuthState(state);
    const oauthError = (searchParams.get('error') || '').trim();
    const oauthErrorDescription = (searchParams.get('error_description') || '').trim();

    if (oauthError) {
      setStatus('Xác thực thất bại.');
      setErrorMessage(
        oauthErrorDescription ? `${oauthError}: ${oauthErrorDescription}` : oauthError,
      );
      return;
    }

    if (!code) {
      setStatus('Thiếu mã xác thực từ nhà cung cấp OAuth.');
      setErrorMessage('Vui lòng quay lại trang đăng nhập và thử lại.');
      return;
    }

    const guardSet = getOAuthGuardSet();
    const guardKey = `${provider}:${code}:${state || 'no-state'}`;
    if (guardSet?.has(guardKey)) {
      return;
    }
    guardSet?.add(guardKey);

    const run = async () => {
      try {
        setStatus(`Đang đổi mã xác thực ${providerLabel}...`);
        const tokenData = await authService.oauthExchangeToken(provider, code);
        const providerAccessToken = tokenData?.access_token;
        if (!providerAccessToken) {
          throw new Error(`Không nhận được access token từ ${providerLabel}`);
        }

        setStatus(`Đang lấy hồ sơ ${providerLabel}...`);
        const profile = await authService.oauthFetchProfile(
          provider,
          providerAccessToken,
          tokenData?.id_token,
        );

        const normalizedPayload = normalizeOAuthProfile(provider, profile);

        setPendingPayload(normalizedPayload);
        setStatus('Đang liên kết tài khoản...');

        try {
          await finalizeSocialAuth(normalizedPayload);
        } catch (registerError) {
          if (isRoleRequiredError(registerError)) {
            const roles = extractAllowedRoles(registerError);
            const preferredRole = preferredRoleFromState && roles.includes(preferredRoleFromState)
              ? preferredRoleFromState
              : null;

            if (preferredRole) {
              try {
                await finalizeSocialAuth(normalizedPayload, preferredRole);
                return;
              } catch {
                // Fallback to manual role selection UI below.
              }
            }

            setNeedRoleSelection(true);
            setAllowedRoles(roles);
            setSelectedRole(preferredRole || roles[0] || 'user');
            setStatus('Lần đầu đăng nhập social, vui lòng chọn vai trò tài khoản.');
            setErrorMessage('');
            return;
          }
          throw registerError;
        }
      } catch (error) {
        setStatus(`Xác thực ${providerLabel} thất bại.`);
        setErrorMessage(error?.response?.data?.detail || error?.message || 'Vui lòng thử lại.');
      }
    };

    run();
  }, [provider, providerLabel, searchParams]);

  const onCompleteRole = async () => {
    if (!pendingPayload) {
      setErrorMessage('Thiếu dữ liệu hồ sơ social, vui lòng thử lại.');
      return;
    }

    setIsCompletingRole(true);
    setErrorMessage('');
    try {
      setStatus('Đang hoàn tất đăng ký social...');
      await finalizeSocialAuth(pendingPayload, selectedRole);
    } catch (error) {
      setStatus('Không thể hoàn tất đăng ký social.');
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Vui lòng thử lại.');
    } finally {
      setIsCompletingRole(false);
    }
  };

  return (
    <AuthLayout title="SmartHire" subtitle={`Xác thực ${providerLabel}`}>
      <Space direction="vertical" size={20} className="w-full">
        <Alert
          type={errorMessage ? 'error' : 'info'}
          showIcon
          message={status}
          description={errorMessage || `Hệ thống đang xử lý đăng nhập với ${providerLabel}.`}
        />

        {needRoleSelection && (
          <Card className="panel-card">
            <Space direction="vertical" size={14} className="w-full">
              <Text className="!text-[20px] !font-semibold">Chọn vai trò để hoàn tất đăng ký</Text>
              <Select
                value={selectedRole}
                onChange={setSelectedRole}
                options={allowedRoles.map((role) => ({ value: role, label: roleLabel(role) }))}
              />
              <div className="flex gap-3">
                <Button
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  loading={isCompletingRole}
                  onClick={onCompleteRole}
                >
                  Hoàn tất
                </Button>
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate('/login', { replace: true })}
                >
                  Quay lại đăng nhập
                </Button>
              </div>
            </Space>
          </Card>
        )}

        <Button onClick={() => navigate('/login', { replace: true })}>Về trang đăng nhập</Button>
      </Space>
    </AuthLayout>
  );
}

export default SocialOAuthCallbackPage;
