import { request } from '../utils/request';
import type { FilterRuleSet, GenerateM3UResponse } from '../types/filter';
import { ApiResponse } from '@/types/api';

interface FilterParams {
  name?: string;
  enabled?: boolean;
  logic_type?: string;
}

export const fetchFilterRuleSets = async (params?: FilterParams): Promise<FilterRuleSet[]> => {
  const response = await request<FilterRuleSet[]>({
    method: 'get',
    url: '/filter-rule-sets',
    params
  });
  return response.data;
};

export const createOrUpdateFilterRuleSet = async (values: FilterRuleSet): Promise<ApiResponse<FilterRuleSet>> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/filter-rule-sets/${values.id}` : '/filter-rule-sets',
    data: values
  });
  return response.data;
};

export const deleteFilterRuleSet = async (id: number): Promise<ApiResponse<FilterRuleSet>> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'delete',
    url: `/filter-rule-sets/${id}`
  });
  return response.data;
};

export const toggleFilterRuleSet = async (id: number): Promise<ApiResponse<FilterRuleSet>> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'patch',
    url: `/filter-rule-sets/${id}/toggle`
  });
  return response.data;
};

interface AddRemoveRuleParams {
  setId: number;
  ruleId: number;
  isRuleSet: boolean;
}

export const addRuleToSet = async ({ setId, ruleId, isRuleSet }: AddRemoveRuleParams): Promise<ApiResponse<FilterRuleSet>> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'post',
    url: `/filter-rule-sets/${setId}/${isRuleSet ? 'rule-sets' : 'rules'}/${ruleId}`
  });
  return response.data;
};

export const removeRuleFromSet = async ({ setId, ruleId, isRuleSet }: AddRemoveRuleParams): Promise<ApiResponse<FilterRuleSet>> => {
  const response = await request<ApiResponse<FilterRuleSet>>({
    method: 'delete',
    url: `/filter-rule-sets/${setId}/${isRuleSet ? 'rule-sets' : 'rules'}/${ruleId}`
  });
  return response.data;
};

export const generateM3U = async (id: number): Promise<GenerateM3UResponse> => {
  const response = await request<GenerateM3UResponse>({
    method: 'post',
    url: `/filter-rule-sets/${id}/generate-m3u`
  });
  return response.data;
};

export const generateTXT = async (id: number): Promise<GenerateM3UResponse> => {
  const response = await request<GenerateM3UResponse>({
    method: 'post',
    url: `/filter-rule-sets/${id}/generate-txt`
  });
  return response.data;
};