import { ApiResponse } from '@/types/api';
import type { EPGProgram, EPGProgramsResponse, FetchProgramsParams } from '../types/epg';
import request from '@/utils/request';

export const fetchEPGPrograms = async (params: FetchProgramsParams): Promise<EPGProgramsResponse> => {
  const response = await request<ApiResponse<EPGProgramsResponse>>({
    method: 'get',
    url: '/epg-programs',
    params
  });
  return response.data.data;
};

export const syncAllEPG = async (): Promise<void> => {
  const response = await request<ApiResponse<void>>({
    method: 'post',
    url: '/epg-sources/sync-all'
  });
  return response.data.data;
};

export const clearAllEPGPrograms = async (): Promise<void> => {
  const response = await request<ApiResponse<void>>({
    method: 'delete',
    url: '/epg-programs-clear-all'
  });
  return response.data.data;
};