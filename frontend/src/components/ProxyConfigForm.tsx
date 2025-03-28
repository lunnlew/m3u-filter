import React from 'react';
import { Form, Input, Switch, Select, InputNumber, Button, App } from 'antd';
import { useProxyConfig, useUpdateProxyConfig } from '../hooks/proxyConfig';

interface ProxyConfig {
  enabled: boolean;
  proxy_type: 'http' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
}

export const ProxyConfigForm: React.FC = () => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { data: proxyConfig, isLoading: isLoadingConfig } = useProxyConfig();
  const { mutate: updateConfig, isPending: isUpdating } = useUpdateProxyConfig();

  React.useEffect(() => {
    if (proxyConfig) {
      form.setFieldsValue(proxyConfig);
    }
  }, [form, proxyConfig]);

  const handleSubmit = (values: ProxyConfig) => {
    updateConfig(values, {
      onSuccess: () => {
        message.success('代理配置已更新');
      },
    });
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '20px' }}>
      <h2>代理服务器设置</h2>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          enabled: false,
          proxy_type: 'http',
        }}
      >
        <Form.Item
          name="enabled"
          label="启用代理"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="proxy_type"
          label="代理类型"
          rules={[{ required: true, message: '请选择代理类型' }]}
        >
          <Select>
            <Select.Option value="http">HTTP</Select.Option>
            <Select.Option value="socks5">SOCKS5</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="host"
          label="主机地址"
          rules={[{ required: true, message: '请输入代理服务器地址' }]}
        >
          <Input placeholder="例如：127.0.0.1" />
        </Form.Item>

        <Form.Item
          name="port"
          label="端口"
          rules={[{ required: true, message: '请输入端口号' }]}
        >
          <InputNumber min={1} max={65535} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="username"
          label="用户名（可选）"
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="password"
          label="密码（可选）"
        >
          <Input.Password />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={isUpdating || isLoadingConfig}>
            保存设置
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};