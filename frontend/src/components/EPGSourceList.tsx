import React, { useState } from 'react';
import { Table, Button, Modal, message } from 'antd';
import { EPGSourceForm } from './EPGSourceForm';
import { EPGSource } from '../types/epg';
import { useEPGSources, useEPGSourceMutation, useEPGSourceDelete, useEPGSourceSync } from '../api/epgSources';

export const EPGSourceList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingSource, setEditingSource] = useState<EPGSource | null>(null);

  const { data: sources, isLoading } = useEPGSources();
  const sourceMutation = useEPGSourceMutation();
  const deleteMutation = useEPGSourceDelete();
  const syncMutation = useEPGSourceSync();

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      message.success('删除EPG源成功');
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除EPG源时发生错误');
    }
  };

  const handleSync = async (id: number) => {
    try {
      const { message: successMsg } = await syncMutation.mutateAsync(id);
      message.success(successMsg);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '同步EPG源时发生错误');
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: 'URL', dataIndex: 'url', key: 'url' },
    {
      title: '最后更新时间',
      dataIndex: 'last_update',
      key: 'last_update',
      render: (text: string | null) => text ? new Date(text).toLocaleString() : '从未更新',
    },
    {
        title: '同步周期',
        key: 'sync_interval',
        render: (_: any, record: EPGSource) => record.sync_interval + '小时'
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
      render: (_: any, record: EPGSource) => (
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

  const handleAddOrUpdate = async (values: EPGSource) => {
    try {
      const { data: result, message: successMsg } = await sourceMutation.mutateAsync(values);
      message.success(successMsg || (values.id ? 'EPG源更新成功' : 'EPG源添加成功'));
      setIsModalVisible(false);

      // 如果是新添加的EPG源且返回的数据中包含id，则触发同步
      if (!values.id && result && result.id) {
        handleSync(result.id);
      }
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作EPG源时发生错误');
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
        添加EPG源
      </Button>

      <Table
        dataSource={sources}
        columns={columns}
        rowKey="id"
        loading={isLoading}
      />

      <Modal
        title={editingSource ? '编辑EPG源' : '添加EPG源'}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <EPGSourceForm
          initialValues={editingSource || undefined}
          onSubmit={handleAddOrUpdate}
          onCancel={() => setIsModalVisible(false)}
        />
      </Modal>
    </div>
  );
};