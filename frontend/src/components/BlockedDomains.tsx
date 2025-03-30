import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, Input } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { useBlockedDomains } from '../hooks/useBlockedDomains';

interface BlockedDomain {
  domain: string;
  failure_count: number;
  last_failure_time: string;
  created_at: string;
  updated_at: string;
}

const BlockedDomains: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const { 
    domains, 
    loading, 
    total, 
    keyword,
    setKeyword,
    fetchDomains, 
    removeDomain 
  } = useBlockedDomains();

  const getFailureColor = (count: number) => {
    if (count >= 10) return 'red';
    if (count >= 5) return 'orange';
    return 'blue';
  };

  const columns: ColumnsType<BlockedDomain> = [
    {
      title: '域名',
      dataIndex: 'domain',
      key: 'domain',
    },
    {
      title: '失败次数',
      dataIndex: 'failure_count',
      key: 'failure_count',
      width: 100,
      render: (count: number) => (
        <Tag color={getFailureColor(count)}>
          {count}
        </Tag>
      ),
    },
    {
      title: '最后失败时间',
      dataIndex: 'last_failure_time',
      key: 'last_failure_time',
      width: 200,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleRemove(record.domain)}
        >
          移除
        </Button>
      ),
    },
  ];

  const handleRemove = async (domain: string) => {
    await removeDomain(domain);
    fetchDomains(currentPage, pageSize);
  };

  const handleTableChange = (pagination: any) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    fetchDomains(pagination.current, pagination.pageSize);
  };

  useEffect(() => {
    fetchDomains(currentPage, pageSize);
  }, []);

  const handleSearch = (value: string) => {
    setKeyword(value);
    setCurrentPage(1); // 重置页码
    fetchDomains(1, pageSize);
  };

  return (
    <Card
      title={
        <span>
          域名黑名单
          <Tag color="red">
            失败次数大于等于10的域名，对应直播源将跳过入库及测速
          </Tag>
        </span>
      }
      extra={
        <div style={{ display: 'flex', gap: '8px' }}>
          <Input.Search
            placeholder="搜索域名"
            allowClear
            onSearch={handleSearch}
            style={{ width: 200 }}
          />
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => fetchDomains(currentPage, pageSize)}
          >
            刷新
          </Button>
        </div>
      }
    >
      <Table
        columns={columns}
        dataSource={domains}
        loading={loading}
        rowKey="domain"
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
        onChange={handleTableChange}
      />
    </Card>
  );
};

export default BlockedDomains;