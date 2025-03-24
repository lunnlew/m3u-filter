import React, { useState } from 'react';
import { Table, Button, Modal, message, Tooltip } from 'antd';
import { StreamSource } from '../types/stream';
import { useStreamSources, useStreamSourceMutation, useStreamSourceDelete, useStreamSourceSync } from '../api/streamSources';
import { StreamSourceForm } from './StreamSourceForm';

export const StreamSourceList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingSource, setEditingSource] = useState<StreamSource | null>(null);

  const { data: sources, isLoading } = useStreamSources();
  const sourceMutation = useStreamSourceMutation();
  const deleteMutation = useStreamSourceDelete();
  const syncMutation = useStreamSourceSync();

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      message.success('删除直播源成功');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除直播源时发生错误');
    }
  };

  const handleSync = async (id: number) => {
    try {
      await syncMutation.mutateAsync(id);
      message.success('同步直播源成功');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '同步直播源时发生错误');
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: 'URL', dataIndex: 'url', key: 'url', width: 200,
      ellipsis: {
        showTitle: false
      },
      render: (url: string) => (
        <Tooltip placement="topLeft" title={url}>
          <span>{url}</span>
        </Tooltip>
      )
    },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: 'EPG源', dataIndex: 'x_tvg_url', key: 'x_tvg_url' },
    {
      title: '回看标志',
      dataIndex: 'catchup',
      key: 'catchup',
    },
    {
      title: '回看源',
      dataIndex: 'catchup_source',
      key: 'catchup_source',
      render: (text: string | null) => text || '-',
    },
    {
      title: '最后更新时间',
      dataIndex: 'last_update',
      key: 'last_update',
      render: (text: string | null) => text ? new Date(text).toLocaleString() : '从未更新',
    },
    {
      title: '状态',
      dataIndex: 'active',
      key: 'active',
      render: (active: boolean) => active ? '启用' : '禁用',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StreamSource) => (
        <>
          <Button
            type="link"
            onClick={() => {
              setEditingSource(record);
              setIsModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            onClick={() => record.id && handleSync(record.id)}
            loading={syncMutation.isPending}
          >
            立即同步
          </Button>
          <Button
            type="link"
            danger
            onClick={() => record.id && handleDelete(record.id)}
            loading={deleteMutation.isPending}
          >
            删除
          </Button>
        </>
      ),
    },
  ];

  const handleAddOrUpdate = async (values: StreamSource) => {
    try {
      const result = await sourceMutation.mutateAsync(values);
      message.success(values.id ? '直播源更新成功' : '直播源添加成功');
      setIsModalVisible(false);
      setEditingSource(null);

      // 如果是新添加的直播源且返回的数据中包含id，则触发同步
      if (!values.id && result && result.id) {
        handleSync(result.id);
      }
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作直播源时发生错误');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Button
        type="primary"
        onClick={() => {
          setEditingSource(null);
          setIsModalVisible(true);
        }}
        style={{ marginBottom: '20px' }}
      >
        添加直播源
      </Button>

      <Table
        columns={columns}
        dataSource={sources}
        loading={isLoading}
        rowKey="id"
      />

      <Modal
        title={editingSource ? '编辑直播源' : '添加直播源'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingSource(null);
        }}
        footer={null}
      >
        <StreamSourceForm
          initialValues={editingSource || undefined}
          onSubmit={handleAddOrUpdate}
          onCancel={() => {
            setIsModalVisible(false);
            setEditingSource(null);
          }}
        />
      </Modal>
    </div>
  );
};