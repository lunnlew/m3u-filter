import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getGroupMappingTemplates,
  createGroupMappingTemplate,
  updateGroupMappingTemplate,
  deleteGroupMappingTemplate,
  applyGroupMappingTemplate,
  type GroupMappingTemplate,
  type CreateGroupMappingTemplateRequest,
  type UpdateGroupMappingTemplateRequest
} from '@/api/groupMappingTemplates';

// 获取所有分组映射模板
export const useGroupMappingTemplates = () => {
  return useQuery<GroupMappingTemplate[]>({
    queryKey: ['groupMappingTemplates'],
    queryFn: () => getGroupMappingTemplates()
  });
};

// 创建分组映射模板
export const useCreateGroupMappingTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateGroupMappingTemplateRequest) => createGroupMappingTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groupMappingTemplates'] });
    }
  });
};

// 更新分组映射模板
export const useUpdateGroupMappingTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateGroupMappingTemplateRequest) => updateGroupMappingTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groupMappingTemplates'] });
    }
  });
};

// 删除分组映射模板
export const useDeleteGroupMappingTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteGroupMappingTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groupMappingTemplates'] });
    }
  });
};

// 应用分组映射模板到规则集
export const useApplyGroupMappingTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ templateIds, ruleSetId }: { templateIds: number[]; ruleSetId: number }) =>
      applyGroupMappingTemplate(templateIds, ruleSetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groupMappings'] });
    }
  });
};