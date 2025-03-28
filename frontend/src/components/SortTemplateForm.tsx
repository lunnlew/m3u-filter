import React, { useEffect } from 'react';
import { Form, Input, Button, App } from 'antd';
import { SortTemplate } from '../types/sortTemplate';
import { useSortTemplateMutation } from '../hooks/sortTemplates';

interface SortTemplateFormProps {
  template?: SortTemplate;
  onSuccess?: () => void;
}

const SortTemplateForm: React.FC<SortTemplateFormProps> = ({ template, onSuccess }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const mutation = useSortTemplateMutation();

  useEffect(() => {
    if (template) {
      form.setFieldsValue(template);
    }
  }, [template, form]);

  const handleSubmit = async (values: any) => {
    try {
      // 将group_orders字符串转换为JSON对象
      const groupOrders = values.group_orders
        .split('\n\n')
        .filter(Boolean)
        .reduce((acc: Record<string, string[]>, groupBlock: string) => {
          const [groupName, ...channels] = groupBlock.split('\n').filter(Boolean);
          acc[groupName] = channels;
          return acc;
        }, {});

      await mutation.mutateAsync({
        ...values,
        id: template?.id,
        group_orders: groupOrders,
      });
      message.success(template ? '排序模板更新成功' : '排序模板创建成功');
      form.resetFields();
      onSuccess?.();
    } catch (error) {
      message.error('操作失败：' + error);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{ group_orders: '' }}
    >
      <Form.Item
        name="name"
        label="模板名称"
        rules={[{ required: true, message: '请输入模板名称' }]}
      >
        <Input placeholder="请输入模板名称" />
      </Form.Item>

      <Form.Item
        name="description"
        label="描述"
      >
        <Input.TextArea placeholder="请输入模板描述" />
      </Form.Item>

      <Form.Item
        name="group_orders"
        label="分组顺序"
        rules={[{ required: true, message: '请输入频道顺序' }]}
      >
        <Input.TextArea
          placeholder="请输入分组及频道列表，每个分组用空行分隔。\n格式示例：\n央视频道\nCCTV1\nCCTV2\nCCTV3\n\n卫视频道\n湖南卫视\n浙江卫视\n江苏卫视"
          autoSize={{ minRows: 3, maxRows: 10 }}
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" loading={mutation.isPending}>
          {template ? '更新' : '创建'}
        </Button>
      </Form.Item>
    </Form>
  );
};

export default SortTemplateForm;