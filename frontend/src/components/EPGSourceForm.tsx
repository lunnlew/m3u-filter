import React from 'react';
import { Form, Input, Switch, Button, InputNumber } from 'antd';

import { EPGSource } from '../types/epg';

interface EPGSourceFormProps {
  initialValues?: EPGSource;
  onSubmit: (values: EPGSource) => void;
  onCancel: () => void;
}

export const EPGSourceForm: React.FC<EPGSourceFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();

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
      initialValues={{ active: true, sync_interval: 6 }}
    >
      <Form.Item name="id" hidden>
        <Input />
      </Form.Item>
      <Form.Item
        name="name"
        label="名称"
        rules={[{ required: true, message: '请输入EPG源名称' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="url"
        label="URL"
        rules={[{ required: true, message: '请输入EPG源URL' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="sync_interval"
        label="同步周期（小时）"
        rules={[{ required: true, message: '请输入同步周期' }]}
      >
        <InputNumber min={1} max={24} />
      </Form.Item>
      <Form.Item name="active" label="启用" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" style={{ marginRight: 8 }}>
          {initialValues ? '更新' : '添加'}
        </Button>
        <Button onClick={onCancel}>取消</Button>
      </Form.Item>
    </Form>
  );
};