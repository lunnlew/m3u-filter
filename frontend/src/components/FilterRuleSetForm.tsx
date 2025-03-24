import React, { useEffect } from 'react';
import { Button, Form, Input, Space, Switch, Select } from 'antd';
import type { FilterRuleSet } from '../types/filter';

interface FilterRuleSetFormProps {
    initialValues?: FilterRuleSet;
    onSubmit: (values: FilterRuleSet) => void;
    onCancel: () => void;
    form: any;
}

export const FilterRuleSetForm: React.FC<FilterRuleSetFormProps> = ({
    initialValues,
    onSubmit,
    onCancel,
    form
}) => {

    React.useEffect(() => {
        if (initialValues) {
            form.setFieldsValue(initialValues);
        } else {
            form.resetFields();
        }
    }, [initialValues, form]);

    return (
        <Form
            form={form}
            onFinish={onSubmit}
            layout="vertical"
            initialValues={initialValues}
        >
            <Form.Item name="id" hidden>
                <Input />
            </Form.Item>
            <Form.Item
                name="name"
                label="名称"
                rules={[{ required: true, message: '请输入规则集合名称' }]}
            >
                <Input />
            </Form.Item>
            <Form.Item
                name="description"
                label="描述"
            >
                <Input.TextArea />
            </Form.Item>
            <Form.Item
                name="enabled"
                label="启用"
                valuePropName="checked"
                initialValue={true}
            >
                <Switch />
            </Form.Item>
            <Form.Item
                name="logic_type"
                label="逻辑运算符"
                initialValue="AND"
            >
                <Select
                    options={[
                        { label: '与(AND)', value: 'AND' },
                        { label: '或(OR)', value: 'OR' }
                    ]}
                />
            </Form.Item>
            <Form.Item>
                <Space>
                    <Button type="primary" htmlType="submit">
                        {initialValues ? '更新' : '添加'}
                    </Button>
                    <Button onClick={onCancel}>取消</Button>
                </Space>
            </Form.Item>
        </Form>
    );
};

export default FilterRuleSetForm;