import { ApiResponse } from '@/types/api';
import request from '@/utils/request';

export interface GroupMappingTemplate {
    id: number;
    name: string;
    description: string;
    mappings: Record<string, string>;
}

export interface CreateGroupMappingTemplateRequest {
    name: string;
    description: string;
    mappings: Record<string, string>;
}

export interface UpdateGroupMappingTemplateRequest extends CreateGroupMappingTemplateRequest {
    id: number;
}

// 获取所有分组映射模板
export const getGroupMappingTemplates = async () => {
    const response = await request.get<ApiResponse<GroupMappingTemplate[]>>('/group-mapping-templates');
    return response.data.data;
};

// 创建分组映射模板
export const createGroupMappingTemplate = async (data: CreateGroupMappingTemplateRequest) => {
    const response = await request.post<ApiResponse<GroupMappingTemplate>>('/group-mapping-templates', data);
    return response.data.data;
};

// 更新分组映射模板
export const updateGroupMappingTemplate = async (data: UpdateGroupMappingTemplateRequest) => {
    const response = await  request.put<ApiResponse<GroupMappingTemplate>>(`/group-mapping-templates/${data.id}`, data);
    return response.data.data;
};

// 删除分组映射模板
export const deleteGroupMappingTemplate = async (id: number) => {
    const response = await  request.delete<ApiResponse<void>>(`/group-mapping-templates/${id}`);
    return response.data.data;
};

// 应用分组映射模板到规则集
export const applyGroupMappingTemplate = async (templateIds: number[], ruleSetId: number) => {
    const response = await request.post<ApiResponse<void>>(`/group-mapping-templates/batch-apply/${ruleSetId}`, { template_ids: templateIds });
    return response.data.data;
};