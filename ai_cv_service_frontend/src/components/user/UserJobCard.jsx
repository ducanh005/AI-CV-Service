import { DollarOutlined, EnvironmentOutlined, GiftOutlined } from '@ant-design/icons';
import { Button } from 'antd';

function UserJobCard({ job, onApply, compact = false }) {
  return (
    <div className="panel-card p-5">
      <div className="mb-2 flex items-start justify-between gap-3">
        <h3 className="m-0 text-[16px] font-semibold text-[#020617]">{job.title}</h3>
        <GiftOutlined className="text-[20px] text-[#111827]" />
      </div>
      <p className="mb-4 text-[20px] text-[#6b7289]">{job.company}</p>

      <div className="mb-4 space-y-1 text-[20px] text-[#6b7289]">
        <p className="m-0 flex items-center gap-2"><EnvironmentOutlined /> {job.location}</p>
        <p className="m-0 flex items-center gap-2"><DollarOutlined /> {job.salary}</p>
        <p className="m-0 flex items-center gap-2"><GiftOutlined /> {job.type}</p>
      </div>

      {!compact && <p className="mb-4 text-[20px] text-[#6b7289]">{job.description}</p>}

      <Button
        block
        className="!h-[56px] !rounded-[14px] !border-0 !bg-[#00011f] !text-[20px] !font-semibold !text-white"
        onClick={() => onApply(job)}
      >
        Ứng tuyển ngay
      </Button>
    </div>
  );
}

export default UserJobCard;
