import { LoadingOutlined, UploadOutlined, UserOutlined } from '@ant-design/icons';
import { Avatar, Button, Card, DatePicker, Form, Input, Select, Space, Typography, Upload, message } from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useState } from 'react';

import { useMyProfile, useUpdateProfile, useUploadAvatar } from '../../hooks/useProfile';
import { resolveAvatarUrl } from '../../utils/media';

const { Title, Text } = Typography;

const genderOptions = [
  { label: 'Nam', value: 'male' },
  { label: 'Nữ', value: 'female' },
  { label: 'Khác', value: 'other' },
];

function ProfileForm({ title, subtitle }) {
  const [form] = Form.useForm();
  const [avatarFile, setAvatarFile] = useState(null);

  const { data: profile, isLoading } = useMyProfile();
  const updateMutation = useUpdateProfile();
  const avatarMutation = useUploadAvatar();

  useEffect(() => {
    if (!profile) {
      return;
    }

    form.setFieldsValue({
      full_name: profile.full_name,
      date_of_birth: profile.date_of_birth ? dayjs(profile.date_of_birth) : null,
      phone: profile.phone,
      address: profile.address,
      gender: profile.gender,
      education: profile.education,
    });
  }, [form, profile]);

  const avatarPreview = useMemo(() => resolveAvatarUrl(profile?.avatar_url), [profile?.avatar_url]);

  const onSubmit = async () => {
    const values = await form.validateFields();

    const payload = {
      ...values,
      date_of_birth: values.date_of_birth ? values.date_of_birth.format('YYYY-MM-DD') : null,
    };

    try {
      await updateMutation.mutateAsync(payload);

      if (avatarFile) {
        await avatarMutation.mutateAsync(avatarFile);
        setAvatarFile(null);
      }

      message.success('Cập nhật hồ sơ thành công');
    } catch (error) {
      message.error(error?.response?.data?.detail || 'Không thể cập nhật hồ sơ');
    }
  };

  return (
    <div>
      <div className="mb-5">
        <Title level={2} className="!mb-1 !text-[52px]">{title}</Title>
        <Text className="!text-[30px] !text-[#6b7289]">{subtitle}</Text>
      </div>

      <Card className="panel-card">
        <div className="mb-5 flex flex-wrap items-center gap-4 border-b border-gray-200 pb-5">
          <Avatar
            size={96}
            src={avatarPreview || undefined}
            icon={!avatarPreview ? <UserOutlined /> : undefined}
            className="!bg-[#00011f]"
          />

          <Space direction="vertical" size={6}>
            <Upload
              maxCount={1}
              accept=".jpg,.jpeg,.png,.webp"
              beforeUpload={(file) => {
                setAvatarFile(file);
                return false;
              }}
              showUploadList={avatarFile ? { showPreviewIcon: false } : false}
            >
              <Button icon={<UploadOutlined />}>Chọn ảnh đại diện</Button>
            </Upload>
            <Text className="!text-[16px] !text-[#6b7289]">Hỗ trợ JPG, PNG, WEBP</Text>
          </Space>
        </div>

        <Form layout="vertical" form={form} disabled={isLoading}>
          <Form.Item label="Email">
            <Input value={profile?.email || ''} disabled />
          </Form.Item>

          <Form.Item name="full_name" label="Họ và tên" rules={[{ required: true, min: 2, max: 120 }]}>
            <Input />
          </Form.Item>

          <Form.Item name="date_of_birth" label="Ngày sinh">
            <DatePicker className="!w-full" format="DD/MM/YYYY" />
          </Form.Item>

          <Form.Item name="phone" label="Số điện thoại" rules={[{ min: 8, max: 20 }]}>
            <Input />
          </Form.Item>

          <Form.Item name="address" label="Địa chỉ">
            <Input />
          </Form.Item>

          <Form.Item name="gender" label="Giới tính">
            <Select allowClear options={genderOptions} placeholder="Chọn giới tính" />
          </Form.Item>

          <Form.Item name="education" label="Học vấn">
            <Input placeholder="Ví dụ: Cử nhân Công nghệ thông tin" />
          </Form.Item>

          <Button
            type="primary"
            onClick={onSubmit}
            loading={updateMutation.isPending || avatarMutation.isPending}
            icon={(updateMutation.isPending || avatarMutation.isPending) ? <LoadingOutlined /> : undefined}
            className="!h-[44px] !rounded-[12px] !bg-[#00011f] !px-6"
          >
            Lưu thay đổi
          </Button>
        </Form>
      </Card>
    </div>
  );
}

export default ProfileForm;
