import request from '@/utils/request';
import type { EPGSource } from '../types/epg';
import { ApiResponse } from '@/types/api';

export const fetchEPGSources = async (params?: Record<string, unknown>): Promise<EPGSource[]> => {
  const response = await request<ApiResponse<EPGSource[]>>({
    method: 'get',
    url: '/epg-sources',
    params
  });
  return response.data.data;
};

export const createOrUpdateEPGSource = async (values: EPGSource): Promise<ApiResponse<EPGSource>> => {
  const response = await request<ApiResponse<EPGSource>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/epg-sources/${values.id}` : '/epg-sources',
    data: values
  });
  return response.data;
};

export const deleteEPGSource = async (id: number): Promise<void> => {
  const response = await request<ApiResponse<void>>({
    method: 'delete',
    url: `/epg-sources/${id}`
  });
  return response.data.data;
};

export const syncEPGSource = async (id: number): Promise<void> => {
  const response = await request<ApiResponse<void>>({
    method: 'post',
    url: `/epg-sources/${id}/sync`
  });
  return response.data;
};