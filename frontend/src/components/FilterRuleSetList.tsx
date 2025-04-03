import { useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, App, Space, Select, Row, Col } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import {
    useFilterRuleSets, useFilterRuleSetMutation, useFilterRuleSetDelete, useAddRuleToSet, useRemoveRuleFromSet, useGenerateM3U, useGenerateTXT  // 新增TXT生成钩子
} from '../hooks/filterRuleSets';
import { useFilterRules } from '../hooks/filterRules';
import { FilterRuleSet, FilterRule } from '../types/filter';
import { useSiteConfig } from '../hooks/siteConfig';
import { FilterRuleSetForm } from './FilterRuleSetForm';
import './FilterRuleSetList.css';
import { RuleSetRulesForm } from './RuleSetRulesForm';
import { GroupMappingForm } from './GroupMappingForm';

export const FilterRuleSetList = () => {
    const { message } = App.useApp();
    const [form] = Form.useForm<FilterRuleSet>();
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isRuleModalVisible, setIsRuleModalVisible] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [selectedRuleSetId, setSelectedRuleSetId] = useState<number | null>(null);
    const [searchName, setSearchName] = useState('');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [filterLogicType, setFilterLogicType] = useState<string>('all');
    const { data: siteConfig = { base_url: '', resource_url_prefix: '' } } = useSiteConfig();

    // 构建API筛选参数
    const getFilterParams = () => {
        const params: any = {};

        if (searchName) {
            params.name = searchName;
        }

        if (filterStatus !== 'all') {
            params.enabled = filterStatus === 'enabled';
        }

        if (filterLogicType !== 'all') {
            params.logic_type = filterLogicType;
        }

        return Object.keys(params).length > 0 ? params : undefined;
    };

    const { data: ruleSets = [], isLoading } = useFilterRuleSets(getFilterParams());
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
            const fullUrl = `${siteConfig.base_url}${siteConfig.resource_url_prefix}${result.url_path}`;
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
            const fullUrl = `${siteConfig.base_url}${siteConfig.resource_url_prefix}${result.url_path}`;
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

    // 新增状态控制分组映射Modal
    const [isGroupMappingModalVisible, setIsGroupMappingModalVisible] = useState(false);
    
    // 修改操作列中的分组映射按钮点击事件
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
                    {/* 新增分组映射按钮 */}
                    <Button 
                        type="link" 
                        onClick={() => {
                            setSelectedRuleSetId(record.id);
                            setIsGroupMappingModalVisible(true);
                        }}
                    >
                        分组映射
                    </Button>
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

    // 处理数据源，为children元素添加_parentId属性并应用筛选条件
    const processDataSource = (data: FilterRuleSet[]) => {
        // 先应用筛选条件
        const filteredData = data.filter(item => {
            // 按名称筛选
            const nameMatch = searchName ? item.name.toLowerCase().includes(searchName.toLowerCase()) : true;

            // 按状态筛选
            const statusMatch = filterStatus === 'all' ? true :
                filterStatus === 'enabled' ? item.enabled :
                    !item.enabled;

            // 按逻辑运算符筛选
            const logicMatch = filterLogicType === 'all' ? true :
                item.logic_type === filterLogicType;

            return nameMatch && statusMatch && logicMatch;
        });

        // 然后处理children
        return filteredData.map(item => {
            const newItem = { ...item };
            if (newItem.children && newItem.children.length > 0) {
                newItem.children = newItem.children.map(child => ({
                    ...child,
                    _parentId: newItem.id
                }));
            }
            return newItem;
        });
    };

    // 重置筛选条件
    const resetFilters = () => {
        setSearchName('');
        setFilterStatus('all');
        setFilterLogicType('all');
    };

    return (
        <div style={{ padding: '20px' }}>
            <Space style={{ marginBottom: 16 }}>
                <Input
                    placeholder="按名称搜索"
                    value={searchName}
                    onChange={e => setSearchName(e.target.value)}
                    prefix={<SearchOutlined />}
                    allowClear
                />
                <Select
                    style={{ width: '100%' }}
                    placeholder="筛选状态"
                    value={filterStatus}
                    onChange={value => setFilterStatus(value)}
                >
                    <Select.Option value="all">全部状态</Select.Option>
                    <Select.Option value="enabled">已启用</Select.Option>
                    <Select.Option value="disabled">已禁用</Select.Option>
                </Select>
                <Select
                    style={{ width: '100%' }}
                    placeholder="筛选逻辑运算符"
                    value={filterLogicType}
                    onChange={value => setFilterLogicType(value)}
                >
                    <Select.Option value="all">全部运算符</Select.Option>
                    <Select.Option value="AND">与(AND)</Select.Option>
                    <Select.Option value="OR">或(OR)</Select.Option>
                </Select>
                <Button onClick={resetFilters}>重置筛选</Button>
                <Button
                    type="primary"
                    onClick={() => {
                        setEditingId(null);
                        form.resetFields();
                        setIsModalVisible(true);
                    }}
                >
                    创建筛选合集
                </Button>
            </Space>

            <Table
                columns={columns}
                dataSource={processDataSource(ruleSets)}
                rowKey={(record) => {
                    // 为每个行生成唯一的key
                    // 如果是子元素，使用父id和子id的组合作为唯一标识
                    return record._parentId ? `${record._parentId}-${record.id}` : `${record.id}`;
                }}
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
            
            {/* 分组映射Modal */}
            <Modal
                title="分组映射配置"
                open={isGroupMappingModalVisible}
                onCancel={() => setIsGroupMappingModalVisible(false)}
                footer={null}
                width={800}
                destroyOnClose
            >
                {selectedRuleSetId && (
                    <div className="group-mapping-container">
                        <GroupMappingForm 
                            ruleSetId={selectedRuleSetId}
                            onCancel={() => setIsGroupMappingModalVisible(false)}
                        />
                    </div>
                )}
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