import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FilterRule, FilterRuleSet, GenerateM3UResponse } from '../types/filter';
import request, { ApiResponse } from '../utils/request';

// 获取规则集合列表
export const useFilterRuleSets = () => {
  return useQuery<FilterRuleSet[]>({
    queryKey: ['filter-rule-sets'],
    queryFn: async () => {
      return await request.get('/filter-rule-sets').then((res) => res.data);
    },
  });
};

// 添加或更新规则集合
export const useFilterRuleSetMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (values: FilterRuleSet) => {
      if (values.id) {
        return await request.put(`/filter-rule-sets/${values.id}`, values);
      }
      return await request.post('/filter-rule-sets', values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
    },
  });
};

// 删除规则集合
export const useFilterRuleSetDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<FilterRuleSet>, unknown, number>({
    mutationFn: (id: number) => request.delete(`/filter-rule-sets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
    }
  });
};

// 切换规则集合状态
export const useFilterRuleSetToggle = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<FilterRuleSet>, unknown, number>({
    mutationFn: (id: number) => request.patch(`/filter-rule-sets/${id}/toggle`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
    }
  });
};

// 添加规则到集合
export const useAddRuleToSet = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ setId, ruleId, isRuleSet }: { setId: number; ruleId: number, isRuleSet: boolean }) => {
      return await request.post(`/filter-rule-sets/${setId}/${isRuleSet ? 'rule-sets' : 'rules'}/${ruleId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
    }
  });
};

// 从集合中移除规则
export const useRemoveRuleFromSet = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ setId, ruleId, isRuleSet }: { setId: number; ruleId: number, isRuleSet: boolean }) => {
      return await request.delete(`/filter-rule-sets/${setId}/${isRuleSet ? 'rule-sets' : 'rules'}/${ruleId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
    }
  });
};

// 生成M3U文件
export const useGenerateM3U = () => {
  return useMutation<ApiResponse<GenerateM3UResponse>, unknown, number>({
    mutationFn: async (id: number) => {
      return await request.post(`/filter-rule-sets/${id}/generate-m3u`);
    }
  });
};