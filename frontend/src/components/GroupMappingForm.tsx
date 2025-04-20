import React, { useEffect, useState } from 'react';
import { Form, Input, Button, App, Space, Modal, Select } from 'antd';
import { useGroupMappings, useUpdateGroupMapping } from '../hooks/filterRuleSets';
import { useDeleteGroupMapping } from '../hooks/filterRuleSets';
import { useBatchUpdateGroupMappings, useBatchDeleteGroupMappings } from '../hooks/filterRuleSets';
import { useGroupMappingTemplates, useCreateGroupMappingTemplate, useApplyGroupMappingTemplate } from '../hooks/groupMappingTemplates';

interface GroupMappingFormProps {
  ruleSetId?: number;
  onCancel?: () => void;
}

export const GroupMappingForm: React.FC<GroupMappingFormProps> = ({ ruleSetId, onCancel }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { data: mappings, isLoading, refetch } = useGroupMappings(ruleSetId);
  const { mutate: updateMapping, isPending } = useUpdateGroupMapping();
  const { mutate: deleteMapping } = useDeleteGroupMapping();
  const { mutate: batchUpdateMappings } = useBatchUpdateGroupMappings();
  const { mutate: batchDeleteMappings } = useBatchDeleteGroupMappings();

  // 模板相关状态和钩子
  const [isTemplateModalVisible, setIsTemplateModalVisible] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [selectedTemplateIds, setSelectedTemplateIds] = useState<number[]>([]);
  const { data: templates = [] } = useGroupMappingTemplates();
  const createTemplateMutation = useCreateGroupMappingTemplate();
  const applyTemplateMutation = useApplyGroupMappingTemplate();

  // 每次ruleSetId变化时重新加载数据
  useEffect(() => {
    if (ruleSetId) {
      refetch();
    }
  }, [ruleSetId, refetch]);

  useEffect(() => {
    if (mappings) {
      const initialValues = Object.entries(mappings).map(([channel, mapping]) => ({
        channel,
        group: mapping.custom_group,
        display_name: mapping.display_name
      }));
      form.setFieldsValue({ mappings: initialValues });
    } else {
      form.setFieldsValue({ mappings: [] });
    }
  }, [form, mappings]);

  const handleSubmit = (values: { mappings: Array<{ channel: string; group: string; display_name?: string }> }) => {
    const updatePayload = values.mappings.map(({ channel, group, display_name }) => ({
      channel_name: channel,
      custom_group: group,
      display_name: display_name,
      rule_set_id: ruleSetId
    }));

    batchUpdateMappings(updatePayload);
    message.success('分组映射已更新');
  };

  // 保存为模板
  const handleSaveAsTemplate = () => {
    const currentMappings = form.getFieldValue('mappings');
    if (!currentMappings || currentMappings.length === 0) {
      message.error('请先添加映射规则');
      return;
    }
    setIsTemplateModalVisible(true);
  };

  // 确认保存模板
  const handleConfirmSaveTemplate = () => {
    if (!templateName.trim()) {
      message.error('请输入模板名称');
      return;
    }
    const currentMappings = form.getFieldValue('mappings');
    const mappingsArray = currentMappings.map((mapping: { channel: string; group: string; display_name?: string }) => ({
      channel_name: mapping.channel,
      custom_group: mapping.group,
      display_name: mapping.display_name
    }));

    createTemplateMutation.mutate({
      name: templateName,
      description: templateDescription,
      mappings: mappingsArray
    }, {
      onSuccess: () => {
        message.success('模板保存成功');
        setIsTemplateModalVisible(false);
        setTemplateName('');
        setTemplateDescription('');
      },
      onError: () => message.error('模板保存失败')
    });
  };

  // 应用模板
  const handleApplyTemplate = (templateIds: number[]) => {
    if (!ruleSetId || templateIds.length === 0) return;

    applyTemplateMutation.mutate(
      { templateIds, ruleSetId },
      {
        onSuccess: () => {
          message.success('所有模板应用成功');
          refetch();
        },
        onError: () => {
          message.error('模板应用失败');
        }
      }
    );
  };

  return (
    <>
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Space style={{ marginBottom: 16 }}>
          <Button onClick={handleSaveAsTemplate}>保存为模板</Button>
          <Select
            mode="multiple"
            style={{ width: 200 }}
            placeholder="选择模板"
            value={selectedTemplateIds}
            onChange={setSelectedTemplateIds}
          >
            {templates.map(template => (
              <Select.Option key={template.id} value={template.id}>
                {template.name}
              </Select.Option>
            ))}
          </Select>
          <Button
            type="primary"
            onClick={() => {
              handleApplyTemplate(selectedTemplateIds);
              setSelectedTemplateIds([]);
            }}
            disabled={selectedTemplateIds.length === 0}
          >
            应用选中模板
          </Button>
        </Space>

        <Form.List name="mappings">
          {(fields, { add, remove }) => (
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
                    <Form.Item
                      {...restField}
                      name={[name, 'display_name']}
                      className="group-mapping-input"
                    >
                      <Input placeholder="自定义显示名称（可选）" />
                    </Form.Item>
                    <Button
                      danger
                      onClick={() => {
                        remove(name);
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

      <Modal
        title="保存为模板"
        open={isTemplateModalVisible}
        onOk={handleConfirmSaveTemplate}
        onCancel={() => {
          setIsTemplateModalVisible(false);
          setTemplateName('');
          setTemplateDescription('');
        }}
        destroyOnClose
      >
        <Form layout="vertical">
          <Form.Item label="模板名称" required>
            <Input
              value={templateName}
              onChange={e => setTemplateName(e.target.value)}
              placeholder="请输入模板名称"
            />
          </Form.Item>
          <Form.Item label="模板描述">
            <Input.TextArea
              value={templateDescription}
              onChange={e => setTemplateDescription(e.target.value)}
              placeholder="请输入模板描述"
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};