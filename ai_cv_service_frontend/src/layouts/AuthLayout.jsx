import { Typography } from 'antd';

const { Title, Text } = Typography;

function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="mb-8 text-center">
          <Title level={1} className="!mb-2 !text-[55px] !font-bold !text-[#020617]">
            {title}
          </Title>
          <Text className="!text-[30px] !text-[#6b7289]">{subtitle}</Text>
        </div>
        {children}
      </div>
    </div>
  );
}

export default AuthLayout;
