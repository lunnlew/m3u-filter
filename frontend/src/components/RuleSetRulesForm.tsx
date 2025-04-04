import React from 'react';
import { Select, Table, Button } from 'antd';
import type { FilterRuleSet, FilterRule } from '../types/filter';

interface RuleSetRulesFormProps {
    selectedRuleSetId: number;
    ruleSets: FilterRuleSet[];
    rules: FilterRule[];
    handleAddRule: (itemId: number, isSet: boolean) => void;
    handleRemoveRule: (ruleSetId: number, ruleId: number, isSet: boolean) => void;
    isRuleInSet: (item: FilterRule | FilterRuleSet, ruleSetId: number) => boolean;
}

const typeMap: Record<string, string> = {
    'name': '名称匹配',
    'keyword': '关键词匹配',
    'resolution': '分辨率匹配',
    'group': '分组匹配',
    'source_name': '来源名称匹配',
    'bitrate': '码率匹配',
    'status': '可用状态匹配'
};

export const RuleSetRulesForm: React.FC<RuleSetRulesFormProps> = ({
    selectedRuleSetId,
    ruleSets,
    rules,
    handleAddRule,
    handleRemoveRule,
    isRuleInSet,
}) => {
    React.useEffect(() => {
        // 当selectedRuleSetId变化时重置组件状态
    }, [selectedRuleSetId]);
    return (
        <div>
            <div style={{ marginBottom: 16 }}>
                <Select
                    style={{ width: '100%' }}
                    placeholder="选择要添加的规则"
                    showSearch
                    filterOption={(input, option) => {
                        if (!option) return false;
                        const label = option.label?.toString().toLowerCase() || '';
                        return label.includes(input.toLowerCase());
                    }}
                    options={[
                        {
                            label: '规则',
                            options: rules
                                .filter(rule => !isRuleInSet(rule, selectedRuleSetId))
                                .map(rule => ({
                                    label: rule.name + ' - ' + (typeMap[rule.type] || rule.type),
                                    value: `rule_${rule.id}`,
                                    type: 'rule'
                                }))
                        },
                        {
                            label: '规则集合',
                            options: ruleSets
                                .filter(set => set.id !== selectedRuleSetId && !isRuleInSet(set, selectedRuleSetId) && !set.children?.some(c => c.id === selectedRuleSetId))
                                .map(set => ({
                                    label: set.name,
                                    value: `set_${set.id}`,
                                    type: 'set'
                                }))
                        }
                    ]}
                    onChange={(value) => {
                        const [type, id] = value.split('_');
                        handleAddRule(parseInt(id), type === 'set');
                    }}
                />
            </div>
            <Table
                columns={[
                    { title: '名称', dataIndex: 'name', key: 'name' },
                    {
                        title: '类型',
                        key: 'itemType',
                        render: (_, record: any) => (
                            <span>{record.pattern ? '规则' : '规则集合'}</span>
                        )
                    },
                    {
                        title: '详情',
                        key: 'details',
                        render: (_, record: any) => (
                            record.pattern ? (
                                <span>{`${typeMap[record.type]} - ${record.pattern}`}</span>
                            ) : (
                                <span>{`包含 ${record.rules?.length || 0} 个规则`}</span>
                            )
                        )
                    },
                    {
                        title: '操作',
                        key: 'action',
                        render: (_: any, record: any) => (
                            <Button
                                type="link"
                                danger
                                onClick={() => {
                                    const [type, id] = (record.id + '').split('_');
                                    handleRemoveRule(selectedRuleSetId, type === 'set' ? id as any : id || type, type === 'set')
                                }}
                            >
                                移除
                            </Button>
                        )
                    }
                ]}
                rowClassName={(record: any) => record.pattern ? '' : 'rule-set-row'}
                dataSource={[
                    ...(ruleSets.find(set => set.id === selectedRuleSetId)?.rules || []),
                    ...(ruleSets.find(set => set.id === selectedRuleSetId)?.children?.map(c => ({ ...c, id: `set_${c.id}` })) || [])
                ]}
                rowKey="id"
            />
        </div>
    );
};

export default RuleSetRulesForm;