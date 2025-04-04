import { useState } from 'react';
import { Table, Button, Modal, App, Space, Select } from 'antd';
import { GroupMappingTemplate } from '@/api/groupMappingTemplates';
import {
  useGroupMappingTemplates,
  useCreateGroupMappingTemplate,
  useUpdateGroupMappingTemplate,
  useDeleteGroupMappingTemplate,
  useApplyGroupMappingTemplate
} from '@/hooks/groupMappingTemplates';
import { GroupMappingTemplateForm } from './GroupMappingTemplateForm';
import { useFilterRuleSets } from '@/hooks/filterRuleSets';

export const GroupMappingTemplateList = () => {
  const { message } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<GroupMappingTemplate | null>(null);

  const { data: templates = [], isLoading } = useGroupMappingTemplates();
  const createMutation = useCreateGroupMappingTemplate();
  const updateMutation = useUpdateGroupMappingTemplate();
  const deleteMutation = useDeleteGroupMappingTemplate();
  const applyMutation = useApplyGroupMappingTemplate();

  const handleEdit = (template: GroupMappingTemplate) => {
    setEditingTemplate(template);
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个分组映射模板吗？',
      onOk: () => {
        deleteMutation.mutate(id, {
          onSuccess: () => message.success('模板删除成功'),
          onError: () => message.error('模板删除失败')
        });
      }
    });
  };

  const handleSubmit = (values: any) => {
    try {
      const submitData = editingTemplate
        ? { id: editingTemplate.id, ...values }
        : values;

      const mutation = editingTemplate ? updateMutation : createMutation;
      mutation.mutate(submitData, {
        onSuccess: () => {
          message.success(editingTemplate ? '模板更新成功' : '模板创建成功');
          setIsModalVisible(false);
          setEditingTemplate(null);
        },
        onError: () => message.error(editingTemplate ? '模板更新失败' : '模板创建失败')
      });
    } catch (error) {
      message.error('提交数据处理失败');
      console.error('Submit error:', error);
    }
  };

  const [selectedRuleSetId, setSelectedRuleSetId] = useState<number | null>(null);
  const { data: ruleSets = [] } = useFilterRuleSets();

  const handleApplyTemplate = (templateId: number) => {
    let tempSelectedRuleSetId: number | null = null;
    
    Modal.confirm({
      title: '选择规则集',
      content: (
        <div>
          <p>请选择要应用模板的规则集：</p>
          <Select
            style={{ width: '100%' }}
            placeholder="选择规则集"
            onChange={(value) => {
              tempSelectedRuleSetId = value;
              setSelectedRuleSetId(value);
            }}
          >
            {ruleSets.map(set => (
              <Select.Option key={set.id} value={set.id}>{set.name}</Select.Option>
            ))}
          </Select>
        </div>
      ),
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        if (!tempSelectedRuleSetId) {
          message.error('请选择规则集');
          return Promise.reject();
        }
        return applyMutation.mutate({ templateIds: [templateId], ruleSetId: tempSelectedRuleSetId }, {
          onSuccess: () => {
            message.success('模板应用成功');
            setSelectedRuleSetId(null);
          },
          onError: () => message.error('模板应用失败')
        });
      },
      afterClose: () => {
        setSelectedRuleSetId(null);
      }
    });
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description' },
    {
      title: '映射数量',
      key: 'mappingsCount',
      render: (record: GroupMappingTemplate) => {
        return record.mappings && typeof record.mappings === 'object' ? Object.keys(record.mappings).length : 0;
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: GroupMappingTemplate) => (
        <Space>
          <Button type="link" onClick={() => handleEdit(record)}>编辑</Button>
          <Button
            type="link"
            onClick={() => handleApplyTemplate(record.id)}
          >
            应用到规则集
          </Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Button
        type="primary"
        onClick={() => {
          setEditingTemplate(null);
          setIsModalVisible(true);
        }}
        style={{ marginBottom: 16 }}
      >
        创建模板
      </Button>

      <Table
        columns={columns}
        dataSource={templates}
        rowKey="id"
        loading={isLoading}
      />

      <Modal
        title={editingTemplate ? '编辑分组映射模板' : '创建分组映射模板'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingTemplate(null);
        }}
        footer={null}
        width={800}
        destroyOnClose
      >
        <GroupMappingTemplateForm
          initialValues={editingTemplate || undefined}
          onSubmit={handleSubmit}
          onCancel={() => {
            setIsModalVisible(false);
            setEditingTemplate(null);
          }}
        />
      </Modal>
    </div>
  );
};

export default GroupMappingTemplateList;