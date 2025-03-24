import React from 'react';
import { Form, Input, Switch, Button, Select, InputNumber } from 'antd';
import { StreamSource } from '../types/stream';

interface StreamSourceFormProps {
  initialValues?: StreamSource;
  onSubmit: (values: StreamSource) => void;
  onCancel: () => void;
}

export const StreamSourceForm: React.FC<StreamSourceFormProps> = ({
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
      initialValues={{ active: true, type: 'm3u', sync_interval: 6 }}
    >
      <Form.Item name="id" hidden>
        <Input />
      </Form.Item>
      <Form.Item
        name="name"
        label="名称"
        rules={[{ required: true, message: '请输入直播源名称' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="url"
        label="URL"
        rules={[{ required: true, message: '请输入直播源URL' }]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="type"
        label="类型"
        rules={[{ required: true, message: '请选择直播源类型' }]}
      >
        <Select>
          <Select.Option value="m3u">M3U</Select.Option>
          <Select.Option value="txt">TXT</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item name="active" label="启用" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item
        name="sync_interval"
        label="同步间隔（小时）"
        rules={[{ required: true, message: '请输入同步间隔' }]}
      >
        <InputNumber min={1} max={24} />
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