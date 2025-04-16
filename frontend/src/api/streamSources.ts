import request from '@/utils/request';
import type { StreamSource } from '../types/stream';
import { ApiResponse } from '@/types/api';

export const fetchStreamSources = async (params?: { keyword?: string; type?: string; active?: boolean }): Promise<StreamSource[]> => {
  const response = await request<ApiResponse<StreamSource[]>>({
    method: 'get',
    url: '/stream-sources',
    params
  });
  return response.data.data;
};

export const createOrUpdateStreamSource = async (values: StreamSource): Promise<StreamSource> => {
  const response = await request<ApiResponse<StreamSource>>({
    method: values.id ? 'put' : 'post',
    url: values.id ? `/stream-sources/${values.id}` : '/stream-sources',
    data: values
  });
  return response.data.data;
};

export const deleteStreamSource = async (id: number): Promise<ApiResponse> => {
  const response = await request<ApiResponse>({
    method: 'delete',
    url: `/stream-sources/${id}`
  });
  return response.data;
};

export const syncStreamSource = async (id: number): Promise<ApiResponse> => {
  const response = await request<ApiResponse>({
    method: 'post',
    url: `/stream-sources/${id}/sync`
  });
  return response.data;
};

export const syncAllStreamSources = async (): Promise<ApiResponse> => {
  const response = await request<ApiResponse>({
    method: 'post',
    url: '/stream-sources/sync-all'
  });
  return response.data;
};