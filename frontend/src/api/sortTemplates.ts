import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { SortTemplate } from '../types/sortTemplate';
import request, { ApiResponse } from '../utils/request';

// 获取所有排序模板
export const useSortTemplates = () => {
  return useQuery<SortTemplate[]>({
    queryKey: ['sort-templates'],
    queryFn: async () => {
      return await request.get('/sort-templates').then((res) => res.data);
    },
  });
};

// 创建或更新排序模板
export const useSortTemplateMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (values: Omit<SortTemplate, 'id'> & { id?: number }) => {
      if (values.id) {
        return await request.put(`/sort-templates/${values.id}`, values);
      }
      return await request.post('/sort-templates', values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sort-templates'] });
    },
  });
};

// 删除排序模板
export const useSortTemplateDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<void>, unknown, number>({
    mutationFn: (id: number) => request.delete(`/sort-templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sort-templates'] });
    }
  });
};