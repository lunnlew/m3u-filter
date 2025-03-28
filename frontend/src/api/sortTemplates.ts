import { request } from '../utils/request';
import type { SortTemplate } from '../types/sortTemplate';
import { ApiResponse } from '@/types/api';

export const fetchSortTemplates = async (): Promise<SortTemplate[]> => {
  const response = await request<SortTemplate[]>({
    method: 'get',
    url: '/sort-templates'
  });
  return response.data;
};

export const createOrUpdateSortTemplate = async (values: Omit<SortTemplate, 'id'> & { id?: number }): Promise<ApiResponse<SortTemplate>> => {
  const response = await request<ApiResponse<SortTemplate>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/sort-templates/${values.id}` : '/sort-templates',
    data: values
  });
  return response.data;
};

export const deleteSortTemplate = async (id: number): Promise<ApiResponse<void>> => {
  const response = await request<ApiResponse<void>>({
    method: 'delete',
    url: `/sort-templates/${id}`
  });
  return response.data;
};