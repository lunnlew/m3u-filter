import { useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, App, Space, Select } from 'antd';
import { useFilterRuleSets, useFilterRuleSetMutation, useFilterRuleSetDelete, useAddRuleToSet, useRemoveRuleFromSet, useGenerateM3U, useGenerateTXT  // 新增TXT生成钩子
} from '../hooks/filterRuleSets';
import { useFilterRules } from '../hooks/filterRules';
import { FilterRuleSet, FilterRule } from '../types/filter';
import { useSiteConfig } from '../hooks/siteConfig';
import { FilterRuleSetForm } from './FilterRuleSetForm';
import './FilterRuleSetList.css';
import { RuleSetRulesForm } from './RuleSetRulesForm';

export const FilterRuleSetList = () => {
    const { message } = App.useApp();
    const [form] = Form.useForm<FilterRuleSet>();
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isRuleModalVisible, setIsRuleModalVisible] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [selectedRuleSetId, setSelectedRuleSetId] = useState<number | null>(null);
    const { data: siteConfig = { base_url: '', static_url_prefix: '' } } = useSiteConfig();

    const { data: ruleSets = [], isLoading } = useFilterRuleSets();
    const { data: rules = [] } = useFilterRules();
    const mutation = useFilterRuleSetMutation();
    const deleteMutation = useFilterRuleSetDelete();
    const addRuleMutation = useAddRuleToSet();
    const removeRuleMutation = useRemoveRuleFromSet();
    const { mutateAsync: generateM3U } = useGenerateM3U();
    const { mutateAsync: generateTXT } = useGenerateTXT();  // 新增TXT生成mutation

    const handleEdit = (record: FilterRuleSet) => {
        setEditingId(record.id);
        // Remove form.setFieldsValue here as it's handled in FilterRuleSetForm
        setIsModalVisible(true);
    };

    const handleDelete = (id: number) => {
        Modal.confirm({
            title: '确认删除',
            content: '确定要删除这个筛选合集吗？',
            onOk: () => {
                deleteMutation.mutate(id, {
                    onSuccess: () => message.success('筛选合集删除成功'),
                    onError: () => message.error('筛选合集删除失败')
                });
            }
        });
    };

    const handleSubmit = (values: FilterRuleSet) => {
        const submitData = editingId ? { ...values, id: editingId } : values;
        mutation.mutate(submitData, {
            onSuccess: () => {
                message.success(editingId ? '筛选合集更新成功' : '筛选合集创建成功');
                setIsModalVisible(false);
                form.resetFields();
                setEditingId(null);
            },
            onError: () => message.error(editingId ? '筛选合集更新失败' : '筛选合集创建失败')
        });
    };

    const handleAddRule = (itemId: number, isSet: boolean = false) => {
        if (selectedRuleSetId) {
            addRuleMutation.mutate({
                setId: selectedRuleSetId,
                ruleId: itemId,
                isRuleSet: isSet
            }, {
                onSuccess: () => {
                    message.success(isSet ? '筛选合集添加成功' : '规则添加成功');
                    setIsRuleModalVisible(false);
                },
                onError: () => message.error(isSet ? '筛选合集添加失败' : '规则添加失败')
            });
        }
    };

    // 生成M3U文件
    const handleGenerateM3U = async (id: number) => {
        try {
            const result = await generateM3U(id);
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

    // 生成M3U文件
    const handleGenerateTXT = async (id: number) => {
        try {
            const result = await generateTXT(id);
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

    const handleRemoveRule = (ruleSetId: number, ruleId: number, isSet: boolean = false) => {
        removeRuleMutation.mutate({ setId: ruleSetId, ruleId, isRuleSet: isSet }, {
            onSuccess: () => {
                message.success(isSet ? '筛选合集删除成功' : '规则删除成功');
                setIsRuleModalVisible(false);
            },
            onError: () => message.error(isSet ? '筛选合集删除失败' : '规则删除失败')
        });
    };

    const columns = [
        { title: '名称', dataIndex: 'name', key: 'name' },
        { title: '描述', dataIndex: 'description', key: 'description' },
        {
            title: '状态',
            dataIndex: 'enabled',
            key: 'enabled',
            render: (enabled: boolean) => (
                <Switch checked={enabled} disabled />
            )
        },
        {
            title: '逻辑运算符',
            dataIndex: 'logic_type',
            key: 'logic_type',
            render: (logic_type: string) => logic_type === 'OR' ? '或(OR)' : '与(AND)'
        },
        {
            title: '规则数量',
            key: 'rulesCount',
            render: (_: any, record: FilterRuleSet) => (record.rules?.length || 0) + (record.children?.length || 0)
        },
        {
            title: '生成周期',
            key: 'sync_interval',
            render: (_: any, record: FilterRuleSet) => record.sync_interval + '小时'
        },
        {
            title: '操作',
            key: 'action',
            render: (_: any, record: FilterRuleSet) => (
                <Space>
                    <Button type="link" onClick={() => handleEdit(record)}>编辑</Button>
                    <Button
                        type="link"
                        onClick={() => {
                            setSelectedRuleSetId(record.id);
                            setIsRuleModalVisible(true);
                        }}
                    >
                        管理规则
                    </Button>
                    {/* 新增TXT生成按钮 */}
                    <Button type="link" onClick={() => handleGenerateM3U(record.id)}>生成M3U</Button>
                    <Button type="link" onClick={() => handleGenerateTXT(record.id)}>生成TXT</Button>
                    <Button type="link" danger onClick={() => handleDelete(record.id)}>删除</Button>
                </Space>
            )
        }
    ];

    const isRuleInSet = (item: FilterRule | FilterRuleSet, ruleSetId: number) => {
        const ruleSet = ruleSets.find(set => set.id === ruleSetId);
        if (!ruleSet) return false;
        return (
            (ruleSet.rules?.some(r => r.id === item.id) || false) ||
            (ruleSet.children?.some(c => c.id === item.id) || false)
        );
    };

    return (
        <div style={{ padding: '20px' }}>
            <Button
                type="primary"
                onClick={() => {
                    setEditingId(null);
                    form.resetFields();
                    setIsModalVisible(true);
                }}
                style={{ marginBottom: 16 }}
            >
                创建筛选合集
            </Button>

            <Table
                columns={columns}
                dataSource={ruleSets}
                rowKey="id"
                loading={isLoading}
            />

            <Modal
                title={editingId ? '编辑筛选合集' : '创建筛选合集'}
                open={isModalVisible}
                onCancel={() => {
                    setIsModalVisible(false);
                    form.resetFields(); // Reset form when closing modal
                }}
                onOk={() => form.submit()}
                okText="确认"
                cancelText="取消"
                destroyOnClose
                footer={null}
            >
                <FilterRuleSetForm
                    form={form}
                    onSubmit={handleSubmit}
                    onCancel={() => {
                        setIsModalVisible(false);
                        form.resetFields(); // Reset form when canceling
                    }}
                    initialValues={editingId ? ruleSets.find(set => set.id === editingId) : undefined}
                />
            </Modal>

            <Modal
                title="管理规则"
                open={isRuleModalVisible}
                onCancel={() => setIsRuleModalVisible(false)}
                footer={null}
                width={800}
            >
                {selectedRuleSetId && (
                    <RuleSetRulesForm
                        selectedRuleSetId={selectedRuleSetId}
                        ruleSets={ruleSets}
                        rules={rules}
                        handleAddRule={handleAddRule}
                        handleRemoveRule={handleRemoveRule}
                        isRuleInSet={isRuleInSet}
                    />
                )}
            </Modal>
        </div>
    );
};

export default FilterRuleSetList;