import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FilterRule, GenerateM3UResponse } from '../types/filter';
import request, { ApiResponse } from '../utils/request';

// 获取过滤规则列表
export const useFilterRules = () => {
  return useQuery<FilterRule[]>({
    queryKey: ['filter-rules'],
    queryFn: async () => {
      return await request.get('/filter-rules').then((res) => res.data);
    },
  });
};

// 添加或更新过滤规则
export const useFilterRuleMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<FilterRule>, unknown, FilterRule>({
    mutationFn: async (values: FilterRule) => {
      if (values.id) {
        return await request.put(`/filter-rules/${values.id}`, values);
      }
      return await request.post('/filter-rules', values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
    },
  });
};

// 删除过滤规则
export const useFilterRuleDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<FilterRule>, unknown, number>({
    mutationFn: (id: number) => request.delete(`/filter-rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
    }
  });
};

// 切换规则启用状态
export const useFilterRuleToggle = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<FilterRule>, unknown, FilterRule>({
    mutationFn: async (rule: FilterRule) => {
      return (await request.put(`/filter-rules/${rule.id}`, { ...rule, enabled: !rule.enabled }));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
    }
  });
};

// 应用过滤规则
export const useApplyFilterRules = () => {
  return useMutation<ApiResponse<FilterRule>, unknown, any[]>({
    mutationFn: async (channels) => {
      return (await request.post('/filter-rules/apply', { channels }));
    },
  });
};

// 生成M3U文件
export const useGenerateM3U = () => {
  return useMutation<ApiResponse<GenerateM3UResponse>, unknown, any[]>({
    mutationFn: async (channels) => {
      return (await request.post('/filter-rules/generate-m3u', { channels }));
    },
  });
};