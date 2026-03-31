import { ArrowLeftOutlined } from '@ant-design/icons';
import { UploadOutlined } from '@ant-design/icons';
import { Button, Card, Space, Typography, Upload, message } from 'antd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useUploadCV } from '../../hooks/useCV';
import ProfileForm from '../../components/profile/ProfileForm';

const { Text } = Typography;

function UserProfilePage() {
  const navigate = useNavigate();
  const [cvFile, setCvFile] = useState(null);
  const [lastUploadedName, setLastUploadedName] = useState('');
  const uploadCvMutation = useUploadCV();

  const handleUploadCv = async () => {
    if (!cvFile) {
      message.warning('Vui lòng chọn file CV trước khi tải lên');
      return;
    }

    try {
      const uploaded = await uploadCvMutation.mutateAsync(cvFile);
      setLastUploadedName(uploaded?.file_name || cvFile.name);
      setCvFile(null);
      message.success('Tải CV thành công');
    } catch (error) {
      message.error(error?.response?.data?.detail || 'Không thể tải CV');
    }
  };

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} className="!mb-4" onClick={() => navigate('/user/dashboard')}>
        Quay về Dashboard
      </Button>

      <Card className="panel-card !mb-4" title={<span className="text-[22px] font-semibold">CV của bạn</span>}>
        <Space direction="vertical" size={12} className="w-full">
          <Upload
            maxCount={1}
            accept=".pdf,.doc,.docx"
            beforeUpload={(file) => {
              setCvFile(file);
              return false;
            }}
            showUploadList={cvFile ? { showPreviewIcon: false } : false}
          >
            <Button icon={<UploadOutlined />}>Chọn file CV</Button>
          </Upload>

          <Button type="primary" loading={uploadCvMutation.isPending} onClick={handleUploadCv} className="!w-fit">
            Tải CV lên
          </Button>

          {lastUploadedName && <Text className="!text-[#6b7289]">CV gần nhất: {lastUploadedName}</Text>}
        </Space>
      </Card>

      <ProfileForm title="Hồ sơ cá nhân" subtitle="Cập nhật thông tin hồ sơ để nhận gợi ý việc làm tốt hơn" />
    </div>
  );
}

export default UserProfilePage;
