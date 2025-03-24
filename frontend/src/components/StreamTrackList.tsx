import React, { useState } from 'react';
import { Table, Input, Select, Button, Space, message, Popconfirm } from 'antd';
import { useStreamTracks, useStreamTrackDelete, useStreamTrackTest, useStreamTrackTestAll } from '../api/streamTracks';
import { StreamTrack, PaginatedStreamTracks } from '../types/streamTrack';

const { Option } = Select;

export default function StreamTrackList() {
  const [searchName, setSearchName] = useState('');
  const [searchGroup, setSearchGroup] = useState('');
  const [searchStatus, setSearchStatus] = useState();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchParams, setSearchParams] = useState<{
    name?: string;
    group_title?: string;
    page?: number;
    page_size?: number;
  }>({ page: 1, page_size: 10 });

  const { data, isLoading } = useStreamTracks(searchParams) as { data: PaginatedStreamTracks | undefined, isLoading: boolean };
  const tracks = data?.items || [];
  const total = data?.total || 0;
  const deleteMutation = useStreamTrackDelete();
  const testMutation = useStreamTrackTest();
  const testAllMutation = useStreamTrackTestAll();

  // 提取所有不重复的分组
  const groups = Array.from(new Set(tracks.map((track: StreamTrack) => track.group_title).filter(Boolean))) as string[];

  const handleSearch = () => {
    const newParams = {
      name: searchName || undefined,
      group_title: searchGroup || undefined,
      test_status: searchStatus,
      page: 1,
      page_size: pageSize
    };
    setCurrentPage(1);
    setSearchParams(newParams);
  };

  const handleTableChange = (pagination: any) => {
    const newParams = {
      ...searchParams,
      page: pagination.current,
      page_size: pagination.pageSize
    };
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    setSearchParams(newParams);
  };

  const handleTest = async (id: number) => {
    try {
      const { data, message: successMsg } = await testMutation.mutateAsync(id);
      message.success(successMsg || '测试成功');
    } catch (error: any) {
      message.error(error.message || '测试失败');
    }
  };

  const handleTestAll = async () => {
    try {
      const { data, message: successMsg } = await testAllMutation.mutateAsync();
      message.success(successMsg || '全部测试成功');
    } catch (error: any) {
      message.error(error.message || '测试失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      const { message: successMsg } = await deleteMutation.mutateAsync(id);
      message.success(successMsg || '删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '直播源名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '分组',
      dataIndex: 'group_title',
      key: 'group_title',
    },
    {
      title: '订阅源',
      dataIndex: 'source_name',
      key: 'source_name',
    },
    {
      title: '资源地址',
      dataIndex: 'url',
      key: 'url',
    },
    {
      title: '视频编码',
      dataIndex: 'video_codec',
      key: 'video_codec',
      render: (codec: string | null) => codec || '-'
    },
    {
      title: '音频编码',
      dataIndex: 'audio_codec',
      key: 'audio_codec',
      render: (codec: string | null) => codec || '-'
    },
    {
      title: '分辨率',
      dataIndex: 'resolution',
      key: 'resolution',
      render: (resolution: string | null) => resolution || '-'
    },
    {
      title: '码率',
      dataIndex: 'bitrate',
      key: 'bitrate',
      render: (bitrate: number | null) => bitrate ? `${bitrate}Kbps` : '-'
    },
    {
      title: '帧率',
      dataIndex: 'frame_rate',
      key: 'frame_rate',
      render: (frameRate: number | null) => frameRate ? `${frameRate}fps` : '-'
    },
    {
      title: '测试状态',
      dataIndex: 'test_status',
      key: 'test_status',
      render: (status: boolean | null) => {
        if (status === null) return '未测试';
        return status ? '可用' : '不可用';
      }
    },
    {
      title: '测试延迟',
      dataIndex: 'test_latency',
      key: 'test_latency',
      render: (latency: number | null) => {
        if (latency === null) return '-';
        return `${latency.toFixed(2)}秒`;
      }
    },
    {
      title: 'Ping时间',
      dataIndex: 'ping_time',
      key: 'ping_time',
      render: (latency: number | null) => {
        if (latency === null) return '-';
        return `${latency.toFixed(2)}毫秒`;
      }
    },
    {
      title: '最后测试时间',
      dataIndex: 'last_test_time',
      key: 'last_test_time',
      render: (time: string | null) => {
        if (!time) return '-';
        return new Date(time).toLocaleString();
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StreamTrack) => (
        <Space size="middle">
          <Button type="link" onClick={() => record.id && handleTest(record.id)}>测试</Button>
          <Popconfirm
            title="确定要删除这个直播源吗？"
            onConfirm={() => record.id && handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleTestAll}>全部测试</Button>
        <Input
          placeholder="搜索直播源名称"
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
          style={{ width: 200 }}
        />
        <Select
          style={{ width: 200 }}
          placeholder="选择分组"
          value={searchGroup}
          onChange={setSearchGroup}
          allowClear
        >
          {groups.map((group) => (
            <Option key={group} value={group}>{group}</Option>
          ))}
        </Select>
        <Select
          style={{ width: 200 }}
          placeholder="选择状态"
          value={searchStatus}
          onChange={setSearchStatus}
          allowClear
        >
          <Option value={null}>全部</Option>
          <Option value={true}>可用</Option>
          <Option value={false}>不可用</Option>
        </Select>
        <Button type="primary" onClick={handleSearch}>搜索</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={tracks}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
        onChange={handleTableChange}
      />
    </div>
  );
}