import {
  ApartmentOutlined,
  MailOutlined,
  PhoneOutlined,
  SearchOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Avatar, Card, Col, Input, Row, Select, Typography } from 'antd';
import { useMemo, useState } from 'react';

import { employeeCards } from '../../utils/mockData';

const { Title, Text } = Typography;

function HRStaffPage() {
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('all');

  const items = useMemo(() => {
    return employeeCards.filter((person) => {
      const hitSearch = !search || person.name.toLowerCase().includes(search.toLowerCase());
      const hitDept = department === 'all' || person.department === department;
      return hitSearch && hitDept;
    });
  }, [search, department]);

  return (
    <div>
      <Title level={2} className="!mb-1 !text-[52px]">Danh bạ nhân viên</Title>
      <Text className="!text-[30px] !text-[#6b7289]">Quản lý thông tin nhân viên trong công ty</Text>

      <div className="mt-4 flex gap-3">
        <Input
          className="search-input"
          prefix={<SearchOutlined />}
          placeholder="Tìm kiếm nhân viên..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Select
          className="!min-w-[220px]"
          value={department}
          onChange={setDepartment}
          options={[{ value: 'all', label: 'Tất cả phòng ban' }, { value: 'Công nghệ', label: 'Công nghệ' }, { value: 'Marketing', label: 'Marketing' }, { value: 'Thiết kế', label: 'Thiết kế' }]}
        />
      </div>

      <Row gutter={[16, 16]} className="mt-5">
        {items.map((person) => (
          <Col xs={24} md={12} xl={6} key={person.email}>
            <Card className="panel-card !h-full">
              <div className="text-center">
                <Avatar size={88} className="!bg-[#00011f] !text-[22px]">{person.name[0]}</Avatar>
                <h3 className="mt-4 text-[40px]">{person.name}</h3>
                <p className="mt-0 text-[18px] text-[#6b7289]">{person.role}</p>
              </div>

              <div className="mt-4 space-y-2 border-t border-gray-200 pt-4 text-[16px] text-[#6b7289]">
                <p className="m-0 flex items-center gap-2"><ApartmentOutlined /> {person.department}</p>
                <p className="m-0 flex items-center gap-2"><MailOutlined /> {person.email}</p>
                <p className="m-0 flex items-center gap-2"><PhoneOutlined /> {person.phone}</p>
                <p className="m-0 flex items-center gap-2"><UserOutlined /> {person.since}</p>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}

export default HRStaffPage;
