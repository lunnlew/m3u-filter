import React, { useState } from 'react';
import { Table, Button, Input, Space, Modal, Form, InputNumber, App, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { useChannelLogos, useChannelLogoMutation, useChannelLogoDelete } from '../hooks/channelLogo';
import { useSiteConfig } from '../hooks/siteConfig';
import { ChannelLogo } from '@/types/channel';

export const ChannelLogoList: React.FC = () => {
  const { message } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingLogo, setEditingLogo] = useState<ChannelLogo | null>(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({
    channel_name: '',
    priority: undefined as number | undefined
  });
  const [priorityOptions, setPriorityOptions] = useState<number[]>([]);
  const { data: siteConfig = { base_url: '', resource_url_prefix: '' } } = useSiteConfig();

  // 处理logo URL
  const getLogoUrl = (url: string) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    // 处理相对路径
    return `${siteConfig.base_url}${siteConfig.resource_url_prefix}${url}`;
  };

  // 使用封装的hooks获取数据
  const { data: logos, isLoading } = useChannelLogos(filters);
  const mutation = useChannelLogoMutation();
  const deleteMutation = useChannelLogoDelete();
  
  // 提取所有可用的优先级，用于筛选
  React.useEffect(() => {
    if (logos) {
      const uniquePriorities = Array.from(new Set(logos
        .map((logo) => logo.priority)
        .filter(Boolean)));
      setPriorityOptions(uniquePriorities as number[]);
    }
  }, [logos]);
  
  const handleFilterChange = (field: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleSearch = (value: string) => {
    setSearchText(value);
    handleFilterChange('channel_name', value);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingLogo(null);
    form.resetFields();
  };

  const handleEdit = (record: ChannelLogo) => {
    setEditingLogo(record);
    form.setFieldsValue({
      channel_name: record.channel_name,
      logo_url: record.logo_url,
      priority: record.priority
    });
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个Logo吗？',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('删除成功');
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const columns = [
    {
      title: '台标',
      dataIndex: 'logo_url',
      key: 'logo_url',
      render: (url: string, record: ChannelLogo) => {
        if (record.channel_name === 'noepg' || !url) return '无';
        return <img src={getLogoUrl(url)} alt="channel logo" style={{ width: 50, height: 50, objectFit: 'contain' }} />;
      },
    },
    {
      title: '频道名称',
      dataIndex: 'channel_name',
      key: 'channel_name',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      sorter: (a: ChannelLogo, b: ChannelLogo) => b.priority - a.priority,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ChannelLogo) => (
        <Space size="middle">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space style={{ marginBottom: 16 }} wrap>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalVisible(true)}
        >
          添加台标
        </Button>
        <Input
          placeholder="筛选频道名称"
          value={filters.channel_name}
          onChange={(e) => handleFilterChange('channel_name', e.target.value)}
          style={{ width: 180 }}
          prefix={<SearchOutlined />}
          allowClear
        />
        <Select
          placeholder="筛选优先级"
          value={filters.priority}
          onChange={(value) => handleFilterChange('priority', value)}
          style={{ width: 150 }}
          allowClear
        >
          {priorityOptions.map(priority => (
            <Select.Option key={priority} value={priority}>{priority}</Select.Option>
          ))}
        </Select>
      </Space>

      <Table
        columns={columns}
        dataSource={logos}
        rowKey="id"
        loading={isLoading}
      />

      <Modal
        title={editingLogo ? '编辑台标' : '添加台标'}
        open={isModalVisible}
        onCancel={handleModalClose}
        onOk={() => form.submit()}
        confirmLoading={mutation.isPending}
        okText={editingLogo? '保存' : '添加'}
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            try {
              await mutation.mutateAsync({ ...values, id: editingLogo?.id });
              message.success(editingLogo ? '编辑成功' : '添加成功');
              handleModalClose();
            } catch (error) {
              message.error(editingLogo ? '编辑失败' : '添加失败');
            }
          }}
        >
          <Form.Item
            name="channel_name"
            label="频道名称"
            rules={[{ required: true, message: '请输入频道名称' }]}
          >
            <Input placeholder="请输入频道名称" />
          </Form.Item>
          <Form.Item
            name="logo_url"
            label="台标地址"
            rules={[{ required: true, message: '请输入台标地址' }]}
          >
            <Input placeholder="请输入台标地址（支持相对路径）" />
          </Form.Item>
          <Form.Item
            name="priority"
            label="优先级"
            initialValue={0}
            rules={[{ type: 'number', message: '请输入有效的数字' }]}
          >
            <InputNumber min={0} placeholder="请输入优先级" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};