import React from 'react';
import { Form, Input, Button, Space } from 'antd';

interface EPGChannel {
  id?: number;
  display_name: string;
  channel_id: string;
  language: string;
  category?: string;
  logo_url?: string;
}

interface EPGChannelFormProps {
  initialValues?: EPGChannel;
  onSubmit: (values: EPGChannel) => void;
  onCancel: () => void;
}

export const EPGChannelForm: React.FC<EPGChannelFormProps> = ({
  initialValues,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm<EPGChannel>();

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
      initialValues={initialValues}
      onFinish={onSubmit}
    >
      <Form.Item name="id" hidden>
        <Input />
      </Form.Item>
      <Form.Item name="channel_id" hidden>
        <Input />
      </Form.Item>
      <Form.Item
        name="display_name"
        label="频道名称"
        rules={[{ required: true, message: '请输入频道名称' }]}
      >
        <Input placeholder="请输入频道名称" />
      </Form.Item>

      <Form.Item
        name="language"
        label="语言"
        rules={[{ required: true, message: '请输入语言' }]}
      >
        <Input placeholder="请输入语言" />
      </Form.Item>

      <Form.Item
        name="category"
        label="分类"
      >
        <Input placeholder="请输入分类" />
      </Form.Item>

      <Form.Item
        name="logo_url"
        label="台标地址"
      >
        <Input placeholder="请输入台标地址" />
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