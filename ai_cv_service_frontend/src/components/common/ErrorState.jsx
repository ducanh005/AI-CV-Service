import { Alert } from 'antd';

function ErrorState({ message }) {
  return <Alert type="error" showIcon message="Đã có lỗi xảy ra" description={message} />;
}

export default ErrorState;
