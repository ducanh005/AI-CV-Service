import { LogoutOutlined } from '@ant-design/icons';
import { Avatar, Button } from 'antd';

function TopBar({ userName, onLogout }) {
  const initial = userName ? userName.charAt(0).toUpperCase() : 'U';
  return (
    <header className="flex h-20 items-center justify-between border-b border-gray-200 bg-white px-9">
      <h1 className="m-0 text-[46px] font-bold text-[#030521]">SmartHire</h1>
      <div className="flex items-center gap-4">
        <Avatar className="bg-[#00011f]">{initial}</Avatar>
        <span className="text-[32px] text-[#1f2937]">{userName}</span>
        <Button type="text" icon={<LogoutOutlined className="text-[24px]" />} onClick={onLogout} />
      </div>
    </header>
  );
}

export default TopBar;
