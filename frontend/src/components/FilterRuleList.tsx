import React, { useState } from 'react';
import { Table, Button, Switch, Space, Modal, App } from 'antd';
import { FilterRuleForm } from './FilterRuleForm';
import type { FilterRule } from '../types/filter';
import { useFilterRules, useFilterRuleMutation, useFilterRuleDelete, useFilterRuleToggle, useApplyFilterRules, useGenerateM3U } from '../hooks/filterRules';
import { useSiteConfig } from '../hooks/siteConfig';

interface FilterRuleListProps { }

const FilterRuleList: React.FC<FilterRuleListProps> = () => {
  const { message } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<FilterRule | null>(null);
  const { data: rules = [], isLoading } = useFilterRules();
  const { data: siteConfig = { base_url: '', static_url_prefix: '' } } = useSiteConfig();
  const { mutateAsync: deleteRuleMutate } = useFilterRuleDelete();
  const { mutateAsync: toggleRuleMutate } = useFilterRuleToggle();
  const filterRuleMutation = useFilterRuleMutation();

  const handleAddOrUpdate = async (values: FilterRule) => {
    try {
      await filterRuleMutation.mutateAsync(values);
      message.success(values.id ? '规则更新成功' : '规则添加成功');
      setIsModalVisible(false);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作规则时发生错误');
    }
  };

  // 切换规则启用状态
  const toggleRuleEnabled = async (rule: FilterRule) => {
    try {
      const { message: successMsg } = await toggleRuleMutate(rule);
      message.success(successMsg || `规则${rule.enabled ? '禁用' : '启用'}成功`);
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 删除规则
  const deleteRule = async (id: number) => {
    try {
      const { message: successMsg } = await deleteRuleMutate(id);
      message.success(successMsg || '删除规则成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '规则类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          'name': '名称匹配',
          'keyword': '关键词匹配',
          'resolution': '分辨率匹配',
          'group': '分组匹配',
          'source_name': '来源名称匹配',
          'bitrate': '码率匹配'
        };
        return typeMap[type] || type;
      }
    },
    {
      title: '动作',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => action === 'include' ? '包含' : '排除'
    },
    {
      title: '匹配模式',
      dataIndex: 'pattern',
      key: 'pattern',
    },
    {
      title: '区分大小写',
      dataIndex: 'case_sensitive',
      key: 'case_sensitive',
      render: (case_sensitive: boolean) => case_sensitive ? '是' : '否'
    },
    {
      title: '正则',
      dataIndex: 'regex_mode',
      key: 'regex_mode',
      render: (regex_mode: boolean) => regex_mode ? '是' : '否'
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      sorter: (a: FilterRule, b: FilterRule) => (a.priority || 0) - (b.priority || 0)
    },
    {
      title: '启用状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (_: any, record: FilterRule) => (
        <Switch checked={record.enabled} onChange={() => toggleRuleEnabled(record)} />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: FilterRule) => (
        <Space size="middle">
          <Button type="link" onClick={() => {
            setEditingRule(record);
            setIsModalVisible(true);
          }}>编辑</Button>
          <Button type="link" danger onClick={() => deleteRule(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  const { mutateAsync: applyRules } = useApplyFilterRules();
  const { mutateAsync: generateM3U } = useGenerateM3U();

  // 应用过滤规则
  const handleApplyRules = async () => {
    try {
      const result = await applyRules([]);
      message.success('过滤规则应用成功');
    } catch (error) {
      message.error('应用过滤规则失败');
    }
  };

  // 生成M3U文件
  const handleGenerateM3U = async () => {
    try {
      const { data: result } = await generateM3U([]);
      const fullUrl = `${siteConfig.base_url}${siteConfig.static_url_prefix}${result.url_path}`;
      Modal.success({
        title: 'M3U文件生成成功',
        content: (
          <div style={{ margin: '16px 0' }}>
            <p style={{ marginBottom: '8px' }}>访问地址：</p>
            <p style={{ wordBreak: 'break-all', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>{fullUrl}</p>
          </div>
        )
      });
    } catch (error) {
      message.error('生成M3U文件失败');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" onClick={() => {
            setEditingRule(null);
            setIsModalVisible(true);
          }}>新建规则</Button>
          {/* <Button onClick={handleApplyRules}>应用规则</Button>
          <Button onClick={handleGenerateM3U}>生成M3U</Button> */}
        </Space>
      </div>

      <Table
        loading={isLoading}
        columns={columns}
        dataSource={rules}
        rowKey="id"
      />

      <Modal
        title={`${editingRule ? '编辑' : '新建'}规则`}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        {isModalVisible && (
          <FilterRuleForm
            initialValues={editingRule || undefined}
            onSubmit={handleAddOrUpdate}
            onCancel={() => setIsModalVisible(false)}
          />
        )}
      </Modal>
    </div>
  );
};

export default FilterRuleList;