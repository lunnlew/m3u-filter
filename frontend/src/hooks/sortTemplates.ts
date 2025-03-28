import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import {
  fetchSortTemplates,
  createOrUpdateSortTemplate,
  deleteSortTemplate
} from '../api/sortTemplates';
import type { SortTemplate } from '../types/sortTemplate';

// 获取所有排序模板
export const useSortTemplates = () => {
  return useQuery<SortTemplate[]>({
    queryKey: ['sort-templates'],
    queryFn: fetchSortTemplates,
  });
};

// 创建或更新排序模板
export const useSortTemplateMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateSortTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sort-templates'] });
      message.success('操作成功');
    },
    onError: (error: Error) => {
      message.error(`操作失败: ${error.message}`);
    },
  });
};

// 删除排序模板
export const useSortTemplateDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSortTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sort-templates'] });
      message.success('删除成功');
    },
    onError: (error: Error) => {
      message.error(`删除失败: ${error.message}`);
    },
  });
};