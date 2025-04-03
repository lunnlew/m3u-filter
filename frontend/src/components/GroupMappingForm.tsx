import React, { useEffect } from 'react';
import { Form, Input, Button, App, Space } from 'antd';
import { useGroupMappings, useUpdateGroupMapping } from '../hooks/filterRuleSets';
import { useDeleteGroupMapping } from '../hooks/filterRuleSets';
import { useBatchUpdateGroupMappings, useBatchDeleteGroupMappings } from '../hooks/filterRuleSets';

interface GroupMappingFormProps {
  ruleSetId?: number;
  onCancel?: () => void;
}

export const GroupMappingForm: React.FC<GroupMappingFormProps> = ({ ruleSetId, onCancel }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { data: mappings, isLoading, refetch } = useGroupMappings(ruleSetId);
  const { mutate: updateMapping, isPending } = useUpdateGroupMapping();
  const { mutate: deleteMapping } = useDeleteGroupMapping(); // 需要先引入删除的API钩子
  const { mutate: batchUpdateMappings } = useBatchUpdateGroupMappings();
  const { mutate: batchDeleteMappings } = useBatchDeleteGroupMappings();

  // 每次ruleSetId变化时重新加载数据
  useEffect(() => {
    if (ruleSetId) {
      refetch();
    }
  }, [ruleSetId, refetch]);

  useEffect(() => {
    if (mappings) {
      const initialValues = Object.entries(mappings).map(([channel, group]) => ({
        channel,
        group
      }));
      form.setFieldsValue({ mappings: initialValues });
    } else {
      form.setFieldsValue({ mappings: [] });
    }
  }, [form, mappings]);

  const handleSubmit = (values: { mappings: Array<{ channel: string; group: string }> }) => {
    // 批量处理所有映射
    const updatePayload = values.mappings.map(({ channel, group }) => ({
      channel_name: channel,
      custom_group: group,
      rule_set_id: ruleSetId
    }));
    
    batchUpdateMappings(updatePayload);
    message.success('分组映射已更新');
  };
  return (
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Form.List name="mappings">
          {(fields, { add, remove }) => (  // 这里解构出remove函数
            <>
              {fields.map(({ key, name, ...restField }) => {
                const channel = form.getFieldValue(['mappings', name, 'channel']);
                return (
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
                    <Button 
                      danger 
                      onClick={() => {
                        remove(name);  // 现在可以正确使用remove函数
                        if (channel) {
                          deleteMapping({
                            channel_name: channel,
                            custom_group: '',
                            rule_set_id: ruleSetId
                          });
                        }
                      }}
                    >
                      删除
                    </Button>
                  </div>
                );
              })}
              <Button type="dashed" onClick={() => add()} block>
                添加映射
              </Button>
            </>
          )}
        </Form.List>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={isPending || isLoading}>
              保存设置
            </Button>
            {onCancel && (
              <Button onClick={onCancel}>关闭</Button>
            )}
          </Space>
        </Form.Item>
      </Form>
  );
};