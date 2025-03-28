import React, { useState } from 'react';
import { Table, Button, Modal, App, Input, Space } from 'antd';
import type { TableProps } from 'antd';
import { EPGChannelForm } from './EPGChannelForm';
import { useEPGChannels, useEPGChannelMutation, useEPGChannelDelete, useClearAllData, useGenerateEPG } from '../hooks/epgChannels';
import { useSiteConfig } from '../hooks/siteConfig';

interface EPGChannel {
  id?: number;
  channel_id: string;
  display_name: string;
  language: string;
  category?: string;
  logo_url?: string;
}

export const EPGChannelList: React.FC = () => {
  const { message } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingChannel, setEditingChannel] = useState<EPGChannel | null>(null);
  const [searchText, setSearchText] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  const { data: channels, isLoading } = useEPGChannels();
  const { data: siteConfig = { base_url: '', static_url_prefix: '' } } = useSiteConfig();
  const { mutateAsync: generateEPG } = useGenerateEPG();

  const getLogoUrl = (url: string) => {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return `${siteConfig.base_url}${siteConfig.static_url_prefix}${url}`;
  };
  const channelMutation = useEPGChannelMutation();
  const deleteMutation = useEPGChannelDelete();
  const clearDataMutation = useClearAllData();

  const handleDelete = async (id: number) => {
    try {
      const { message: successMsg } = await deleteMutation.mutateAsync(id);
      message.success(successMsg || '删除EPG频道成功');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除EPG频道时发生错误');
    }
  };

  const handleAddOrUpdate = async (values: EPGChannel) => {
    try {
      const { message: successMsg } = await channelMutation.mutateAsync(values);
      message.success(successMsg || (values.id ? 'EPG频道更新成功' : 'EPG频道添加成功'));
      setIsModalVisible(false);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作EPG频道时发生错误');
    }
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  const handleClearData = async () => {
    Modal.confirm({
      title: '确认清空数据',
      content: '确定要清空所有频道数据吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const { message: successMsg } = await clearDataMutation.mutateAsync();
          message.success(successMsg || '数据已清空');
        } catch (err) {
          message.error(err instanceof Error ? err.message : '清空数据时发生错误');
        }
      }
    });
  };

  const handleExportEPG = async () => {
    try {
      setIsExporting(true);
      const result = await generateEPG();
      const fullUrl = `${siteConfig.base_url}${siteConfig.static_url_prefix}${result.url_path}`;
      Modal.success({
        title: 'EPG文件生成成功',
        content: (
          <div style={{ margin: '16px 0' }}>
            <p style={{ marginBottom: '8px' }}>访问地址：</p>
            <p style={{ wordBreak: 'break-all', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>{fullUrl}</p>
          </div>
        )
      });
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'EPG导出失败');
    } finally {
      setIsExporting(false);
    }
  };

  const filteredChannels = channels?.filter((channel: EPGChannel) =>
    searchText ? channel.display_name.toLowerCase().includes(searchText.toLowerCase()) : true
  ) || [];

  const columns: TableProps<EPGChannel>['columns'] = [
    { title: '频道名称', dataIndex: 'display_name', key: 'display_name' },
    { title: '订阅源', dataIndex: 'source_name', key: 'source_name' },
    { title: '语言', dataIndex: 'language', key: 'language' },
    { title: '分类', dataIndex: 'category', key: 'category' },
    {
      title: '台标',
      dataIndex: 'logo_url',
      key: 'logo_url',
      render: (url: string, record: EPGChannel) => {
        if (record.display_name === 'noepg' || !url) return '无';
        return <img src={getLogoUrl(url)} alt="channel logo" style={{ maxHeight: '30px' }} />;
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: EPGChannel) => (
        <Space>
          <Button
            type="link"
            onClick={() => {
              setEditingChannel(record);
              setIsModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            onClick={() => record.id && handleDelete(record.id)}
            loading={deleteMutation.isPending}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Space style={{ marginBottom: '20px' }}>
        <Button
          type="primary"
          onClick={() => {
            setEditingChannel(null);
            setIsModalVisible(true);
          }}
        >
          添加频道
        </Button>
        <Button
          type="primary"
          onClick={handleExportEPG}
          loading={isExporting}
        >
          导出EPG
        </Button>
        <Button
          danger
          onClick={handleClearData}
          loading={clearDataMutation.isPending}
        >
          清空数据
        </Button>
        <Input.Search
          placeholder="搜索频道名称"
          onSearch={handleSearch}
          onChange={(e) => handleSearch(e.target.value)}
          style={{ width: 200 }}
        />
      </Space>

      <Table
        dataSource={filteredChannels}
        columns={columns}
        rowKey="id"
        loading={isLoading}
      />

      <Modal
        title={editingChannel ? '编辑频道' : '添加频道'}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <EPGChannelForm
          initialValues={editingChannel || undefined}
          onSubmit={handleAddOrUpdate}
          onCancel={() => setIsModalVisible(false)}
        />
      </Modal>
    </div>
  );
};