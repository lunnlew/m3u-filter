import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import {
  fetchFilterRuleSets,
  createOrUpdateFilterRuleSet,
  deleteFilterRuleSet,
  toggleFilterRuleSet,
  addRuleToSet,
  removeRuleFromSet,
  generateM3U,
  generateTXT
} from '../api/filterRuleSets';
import type { FilterRuleSet } from '../types/filter';

interface FilterParams {
  name?: string;
  enabled?: boolean;
  logic_type?: string;
}

export const useFilterRuleSets = (params?: FilterParams) => {
  return useQuery<FilterRuleSet[]>({
    queryKey: ['filter-rule-sets', params],
    queryFn: () => fetchFilterRuleSets(params),
  });
};

export const useFilterRuleSetMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateFilterRuleSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
      message.success('操作成功');
    },
    onError: (error: Error) => {
      message.error(`操作失败: ${error.message}`);
    },
  });
};

export const useFilterRuleSetDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteFilterRuleSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
      message.success('删除成功');
    },
    onError: (error: Error) => {
      message.error(`删除失败: ${error.message}`);
    },
  });
};

export const useFilterRuleSetToggle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleFilterRuleSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
      message.success('状态更新成功');
    },
    onError: (error: Error) => {
      message.error(`状态更新失败: ${error.message}`);
    },
  });
};

export const useAddRuleToSet = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addRuleToSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
      message.success('规则添加成功');
    },
    onError: (error: Error) => {
      message.error(`规则添加失败: ${error.message}`);
    },
  });
};

export const useRemoveRuleFromSet = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeRuleFromSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rule-sets'] });
      message.success('规则移除成功');
    },
    onError: (error: Error) => {
      message.error(`规则移除失败: ${error.message}`);
    },
  });
};

export const useGenerateM3U = () => {
  return useMutation({
    mutationFn: generateM3U,
    onSuccess: () => {
      message.success('M3U文件生成成功');
    },
    onError: (error: Error) => {
      message.error(`M3U文件生成失败: ${error.message}`);
    },
  });
};

export const useGenerateTXT = () => {
  return useMutation({
    mutationFn: generateTXT,
    onSuccess: () => {
      message.success('TXT文件生成成功');
    },
    onError: (error: Error) => {
      message.error(`TXT文件生成失败: ${error.message}`);
    },
  });
};
