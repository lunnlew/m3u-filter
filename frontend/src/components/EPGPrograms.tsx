import { useState } from 'react';
import { Table, DatePicker, Input, Space, Button, Modal, App } from 'antd';
import type { TableProps } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useClearAllData, useEPGPrograms, useEPGSync } from '../hooks/epgPrograms';

interface EPGProgram {
  id: number;
  channel_id: string;
  channel_name: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  source_id: number;
}

const { RangePicker } = DatePicker;

const EPGPrograms = () => {
  const { message } = App.useApp();
  const [channel, setChannel] = useState('');
  const [timeRange, setTimeRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null]>([null, null]);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedProgram, setSelectedProgram] = useState<EPGProgram | null>(null);
  const clearDataMutation = useClearAllData();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
  });

  // 重置筛选条件
  const handleReset = () => {
    setChannel('');
    setTimeRange([null, null]);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const params = {
    page: pagination.current,
    page_size: pagination.pageSize,
    ...(channel ? { channel_name: channel } : {}),
    ...(timeRange && timeRange[0] && timeRange[1] ? {
      start_time: timeRange[0].format('YYYYMMDDHHmmss'),
      end_time: timeRange[1].format('YYYYMMDDHHmmss')
    } : {})
  };

  const { data, isLoading } = useEPGPrograms(params);
  const syncMutation = useEPGSync();

  const handleSync = () => {
    syncMutation.mutate();
  };

  const handleClearData = async () => {
    Modal.confirm({
      title: '确认清空数据',
      content: '确定要清空所有节目数据吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await clearDataMutation.mutateAsync();
          message.success('数据已清空');
        } catch (err) {
          message.error(err instanceof Error ? err.message : '清空数据时发生错误');
        }
      }
    });
  };

  const columns: TableProps<EPGProgram>['columns'] = [
    {
      title: '频道',
      dataIndex: 'channel_name',
      key: 'channel_name',
    },
    {
      title: '节目名称',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '订阅源',
      dataIndex: 'source_name',
      key: 'source_name',
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (text: string) => dayjs(text, 'YYYYMMDDHHmmss').format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      render: (text: string) => dayjs(text, 'YYYYMMDDHHmmss').format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          onClick={() => {
            setSelectedProgram(record);
            setDetailModalVisible(true);
          }}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="输入频道名称"
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          style={{ width: 200 }}
        />
        <RangePicker
          showTime
          value={timeRange}
          onChange={(dates) => setTimeRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null])}
        />
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
        >
          重置筛选
        </Button>
        <Button onClick={handleSync} loading={syncMutation.isPending}>同步EPG订阅数据</Button>
        <Button
          danger
          onClick={handleClearData}
          loading={clearDataMutation.isPending}
        >
          清空数据
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data?.data}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: data?.total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (page, pageSize) => {
            setPagination({
              current: page,
              pageSize: pageSize || 10
            });
          }
        }}
      />

      <Modal
        title="节目详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
      >
        {selectedProgram && (
          <div>
            <p><strong>频道：</strong>{selectedProgram.channel_name}</p>
            <p><strong>节目名称：</strong>{selectedProgram.title}</p>
            <p><strong>开始时间：</strong>
              {dayjs(selectedProgram.start_time, 'YYYYMMDDHHmmss').format('YYYY-MM-DD HH:mm:ss')}
            </p>
            <p><strong>结束时间：</strong>
              {dayjs(selectedProgram.end_time, 'YYYYMMDDHHmmss').format('YYYY-MM-DD HH:mm:ss')}
            </p>
            {selectedProgram.description && (
              <p><strong>节目描述：</strong>{selectedProgram.description}</p>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default EPGPrograms;