import request from '@/utils/request';
import type { FilterRuleSet, GenerateM3UResponse } from '../types/filter';
import { ApiResponse } from '@/types/api';
import type { GroupMapping } from '../types/filter';

interface FilterParams {
  name?: string;
  enabled?: boolean;
  logic_type?: string;
}

export const fetchFilterRuleSets = async (params?: FilterParams): Promise<FilterRuleSet[]> => {
  const response = await request<ApiResponse<FilterRuleSet[]>>({
    method: 'get',
    url: '/filter-rule-sets',
    params
  });
  return response.data.data;
};

export const createOrUpdateFilterRuleSet = async (values: FilterRuleSet): Promise<FilterRuleSet> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/filter-rule-sets/${values.id}` : '/filter-rule-sets',
    data: values
  });
  return response.data.data;
};

export const deleteFilterRuleSet = async (id: number): Promise<FilterRuleSet> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'delete',
    url: `/filter-rule-sets/${id}`
  });
  return response.data.data;
};

export const toggleFilterRuleSet = async (id: number): Promise<FilterRuleSet> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'patch',
    url: `/filter-rule-sets/${id}/toggle`
  });
  return response.data.data;
};

interface AddRemoveRuleParams {
  setId: number;
  ruleId: number;
  isRuleSet: boolean;
}

export const addRuleToSet = async ({ setId, ruleId, isRuleSet }: AddRemoveRuleParams): Promise<FilterRuleSet> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'post',
    url: `/filter-rule-sets/${setId}/${isRuleSet ? 'rule-sets' : 'rules'}/${ruleId}`
  });
  return response.data.data;
};

export const removeRuleFromSet = async ({ setId, ruleId, isRuleSet }: AddRemoveRuleParams): Promise<FilterRuleSet> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'delete',
    url: `/filter-rule-sets/${setId}/${isRuleSet ? 'rule-sets' : 'rules'}/${ruleId}`
  });
  return response.data.data;
};

export const generateM3U = async (id: number): Promise<GenerateM3UResponse> => {
  const response = await request<ApiResponse<GenerateM3UResponse>>({
    method: 'post',
    url: `/filter-rule-sets/${id}/generate-m3u`
  });
  return response.data.data;
};

export const generateTXT = async (id: number): Promise<GenerateM3UResponse> => {
  const response = await request<ApiResponse<GenerateM3UResponse>>({
    method: 'post',
    url: `/filter-rule-sets/${id}/generate-txt`
  });
  return response.data.data;
};

export const fetchGroupMappings = async (ruleSetId?: number): Promise<Record<string, string>> => {
  const response = await request<ApiResponse<Record<string, string>>>({
    method: 'get',
    url: '/group-mappings',
    params: { rule_set_id: ruleSetId }
  });
  return response.data.data;
};

export const updateGroupMapping = async (mapping: GroupMapping): Promise<void> => {
  await request<ApiResponse<void>>({
    method: 'post',
    url: '/group-mappings',
    data: mapping
  });
};

export const deleteGroupMapping = async (mapping: GroupMapping): Promise<void> => {
  await request<ApiResponse<void>>({
    method: 'delete',
    url: '/group-mappings',
    data: mapping
  });
};

export const batchUpdateGroupMappings = async (mappings: GroupMapping[]): Promise<void> => {
  await request<ApiResponse<void>>({
    method: 'post',
    url: '/group-mappings/batch',
    data: mappings
  });
};

export const batchDeleteGroupMappings = async (mappings: GroupMapping[]): Promise<void> => {
  await request<ApiResponse<void>>({
    method: 'delete',
    url: '/group-mappings/batch',
    data: mappings
  });
};


export const testRuleSet = async (ruleSetId: number) => {
  return await request({
    method: 'post',
    url: `/filter-rule-sets/${ruleSetId}/test-rules`
  });
};