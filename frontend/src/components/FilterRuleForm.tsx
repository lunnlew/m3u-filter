import React, { useEffect } from 'react';
import { Form, Input, InputNumber, Select, Switch, Button, Space } from 'antd';
import type { FilterRule } from '../types/filter';

const { Option } = Select;

interface FilterRuleFormProps {
  initialValues?: FilterRule;
  onSubmit: (values: FilterRule) => void;
  onCancel: () => void;
}

export const FilterRuleForm: React.FC<FilterRuleFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const typeValue = Form.useWatch('type', form);

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
      layout="vertical"
      onFinish={onSubmit}
      initialValues={{
        enabled: true,
        action: 'include',
        priority: 0,
        type: 'name',
        ...initialValues
      }}
    >
      <Form.Item name="id" hidden>
        <Input />
      </Form.Item>
      <Form.Item
        name="name"
        label="规则名称"
        rules={[{ required: true, message: '请输入规则名称' }]}
      >
        <Input />
      </Form.Item>

      <Form.Item
        name="type"
        label="规则类型"
        rules={[{ required: true, message: '请选择规则类型' }]}
      >
        <Select>
          <Option value="name">名称匹配</Option>
          <Option value="keyword">关键词匹配</Option>
          <Option value="resolution">分辨率匹配</Option>
          <Option value="group">分组匹配</Option>
          <Option value="bitrate">码率匹配</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="action"
        label="动作类型"
        rules={[{ required: true, message: '请选择动作类型' }]}
      >
        <Select>
          <Option value="include">包含</Option>
          <Option value="exclude">排除</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="priority"
        label="优先级"
        rules={[{ required: true, message: '请输入优先级' }]}
      >
        <InputNumber min={0} />
      </Form.Item>
      <Form.Item
        name="pattern"
        label="匹配模式"
        rules={[{ required: true, message: '请输入匹配模式' }]}
      >
        {
          typeValue === 'resolution' ? (
            <Select>
              <Option value="4k">4K</Option>
              <Option value="2k">2K</Option>
              <Option value="1080p">1080P</Option>
              <Option value="720p">720P</Option>
              <Option value="576p">576P</Option>
              <Option value="480p">480P</Option>
            </Select>
          ) : typeValue === 'bitrate' ? (
            <Space.Compact>
              <InputNumber
                style={{ width: '45%' }}
                min={0}
                placeholder="最小码率"
                onChange={value => {
                  const maxValue = form.getFieldValue('pattern')?.split('-')[1] || '';
                  form.setFieldValue('pattern', `${value || ''}-${maxValue}`);
                }}
              />
              <Input
                style={{ width: '10%', textAlign: 'center', pointerEvents: 'none' }}
                placeholder="-"
                disabled
              />
              <InputNumber
                style={{ width: '45%' }}
                min={0}
                placeholder="最大码率"
                onChange={value => {
                  const minValue = form.getFieldValue('pattern')?.split('-')[0] || '';
                  form.setFieldValue('pattern', `${minValue}-${value || ''}`);
                }}
              />
            </Space.Compact>
          ) : (
            <Input />
          )
        }
      </Form.Item>

      <Form.Item name="case_sensitive" valuePropName="checked" label="区分大小写">
        <Switch />
      </Form.Item>

      <Form.Item name="regex_mode" valuePropName="checked" label="使用正则表达式">
        <Switch />
      </Form.Item>

      <Form.Item name="enabled" valuePropName="checked" label="启用规则">
        <Switch />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit">
            确定
          </Button>
          <Button onClick={onCancel}>
            取消
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};