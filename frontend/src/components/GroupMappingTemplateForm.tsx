import React, { useEffect } from 'react';
import { Form, Input, Button, App, Space } from 'antd';
import { GroupMappingTemplate } from '@/api/groupMappingTemplates';
import './GroupMappingTemplateForm.css';

interface GroupMappingTemplateFormProps {
  initialValues?: GroupMappingTemplate;
  onSubmit: (values: any) => void;
  onCancel?: () => void;
}

export const GroupMappingTemplateForm: React.FC<GroupMappingTemplateFormProps> = ({
  initialValues,
  onSubmit,
  onCancel
}) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();

  useEffect(() => {
    if (initialValues) {
      const formValues = {
        name: initialValues.name,
        description: initialValues.description,
        mappings: initialValues.mappings instanceof Array
          ? initialValues.mappings.map(item => ({
            channel: item.channel_name,
            group: item.custom_group,
            display_name: item.display_name
          }))
          : Object.entries(initialValues.mappings || {}).map(([channel, group]) => ({
            channel,
            group,
            display_name: ''
          }))
      };
      form.setFieldsValue(formValues);
    } else {
      form.resetFields();
      form.setFieldsValue({ mappings: [] });
    }
  }, [form, initialValues]);

  const handleSubmit = (values: any) => {
    try {
      const mappings = (values.mappings || []).map((item: { channel: string; group: string; display_name?: string }) => ({
        channel_name: item.channel,
        custom_group: item.group,
        display_name: item.display_name
      }));

      onSubmit({
        name: values.name,
        description: values.description,
        mappings
      })
    } catch (error) {
      message.error('表单数据处理失败');
      console.error('Form submission error:', error);
    }
  };

  return (
    <Form form={form} onFinish={handleSubmit} layout="vertical">
      <Form.Item
        name="name"
        label="模板名称"
        rules={[{ required: true, message: '请输入模板名称' }]}
      >
        <Input placeholder="请输入模板名称" />
      </Form.Item>

      <Form.Item
        name="description"
        label="模板描述"
      >
        <Input.TextArea placeholder="请输入模板描述" />
      </Form.Item>

      <Form.List name="mappings">
        {(fields, { add, remove }) => (
          <div className="mappings-container">
            {fields.map(({ key, name, ...restField }) => (
              <div key={key} className="group-mapping-row">
                <Form.Item
                  {...restField}
                  name={[name, 'channel']}
                  rules={[{ required: true, message: '请输入频道名称' }]}
                  className="group-mapping-input"
                >
                  <Input placeholder="频道名称" />
                </Form.Item>
                <Form.Item
                  {...restField}
                  name={[name, 'group']}
                  rules={[{ required: true, message: '请输入分组名称' }]}
                  className="group-mapping-input"
                >
                  <Input placeholder="自定义分组名称" />
                </Form.Item>
                <Form.Item
                  {...restField}
                  name={[name, 'display_name']}
                  className="group-mapping-input"
                >
                  <Input placeholder="自定义显示名称（可选）" />
                </Form.Item>
                <Button danger onClick={() => remove(name)}>删除</Button>
              </div>
            ))}
            <Form.Item>
              <Button 
                type="dashed" 
                onClick={() => {
                  const templateName = form.getFieldValue('name');
                  add({ group: templateName || '' });
                }} 
                block
              >
                添加映射
              </Button>
            </Form.Item>
          </div>
        )}
      </Form.List>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit">保存</Button>
          {onCancel && <Button onClick={onCancel}>取消</Button>}
        </Space>
      </Form.Item>
    </Form>
  );
};