import React, { useState } from 'react';
import { Table, Button, Space, Popconfirm, App, Modal } from 'antd';
import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { SortTemplate } from '../types/sortTemplate';
import { useSortTemplates, useSortTemplateDelete } from '../hooks/sortTemplates';
import SortTemplateForm from './SortTemplateForm';

const SortTemplateList: React.FC = () => {
  const { message } = App.useApp();
  const [editingTemplate, setEditingTemplate] = useState<SortTemplate | undefined>();
  const [isModalVisible, setIsModalVisible] = useState(false);

  const { data: templates = [], isLoading } = useSortTemplates();
  const deleteMutation = useSortTemplateDelete();

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败：' + error);
    }
  };

  const handleEdit = (template: SortTemplate) => {
    setEditingTemplate({
      ...template,
      group_orders: Object.entries(template.group_orders)
        .map(([group, channels]) => `${group}\n${channels.join('\n')}`)
        .join('\n\n')
    } as any);
    setIsModalVisible(true);
  };

  const handleCreate = () => {
    setEditingTemplate(undefined);
    setIsModalVisible(true);
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setEditingTemplate(undefined);
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '分组顺序',
      dataIndex: 'group_orders',
      key: 'group_orders',
      render: (groupOrders: Record<string, string[]>) => {
        return Object.entries(groupOrders)
          .map(([group, channels]) => `${group}: ${channels.join(', ')}`)
          .join('\n');
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: SortTemplate) => (
        <Space size="middle">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个排序模板吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleCreate}>
          创建排序模板
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={templates}
        rowKey="id"
        loading={isLoading}
      />
      <Modal
        title={editingTemplate ? '编辑排序模板' : '创建排序模板'}
        open={isModalVisible}
        onCancel={handleModalClose}
        footer={null}
        destroyOnClose
      >
        <SortTemplateForm
          template={editingTemplate}
          onSuccess={handleModalClose}
        />
      </Modal>
    </div>
  );
};

export default SortTemplateList;