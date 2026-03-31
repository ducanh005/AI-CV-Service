import { Spin } from 'antd';

function LoadingState({ full = false }) {
  return (
    <div className={full ? 'flex min-h-screen items-center justify-center' : 'flex items-center justify-center py-8'}>
      <Spin size="large" />
    </div>
  );
}

export default LoadingState;
