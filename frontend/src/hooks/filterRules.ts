import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import {
  fetchFilterRules,
  createOrUpdateFilterRule,
  deleteFilterRule,
  toggleFilterRule,
  applyFilterRules,
  generateM3U
} from '../api/filterRules';
import type { FilterRule, GenerateM3UResponse } from '../types/filter';

export const useFilterRules = () => {
  return useQuery<FilterRule[]>({
    queryKey: ['filter-rules'],
    queryFn: fetchFilterRules,
  });
};

export const useFilterRuleMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateFilterRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
      message.success('操作成功');
    },
    onError: (error: Error) => {
      message.error(`操作失败: ${error.message}`);
    },
  });
};

export const useFilterRuleDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteFilterRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
      message.success('删除成功');
    },
    onError: (error: Error) => {
      message.error(`删除失败: ${error.message}`);
    },
  });
};

export const useFilterRuleToggle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleFilterRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filter-rules'] });
      message.success('状态更新成功');
    },
    onError: (error: Error) => {
      message.error(`状态更新失败: ${error.message}`);
    },
  });
};

export const useApplyFilterRules = () => {
  return useMutation({
    mutationFn: applyFilterRules,
    onSuccess: () => {
      message.success('规则应用成功');
    },
    onError: (error: Error) => {
      message.error(`规则应用失败: ${error.message}`);
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