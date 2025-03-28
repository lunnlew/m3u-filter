import { request } from '../utils/request';
import type { EPGProgram, EPGProgramsResponse, FetchProgramsParams } from '../types/epg';

export const fetchEPGPrograms = async (params: FetchProgramsParams): Promise<EPGProgramsResponse> => {
  const response = await request<EPGProgramsResponse>({
    method: 'get',
    url: '/epg-programs',
    params
  });
  return response.data;
};

export const syncAllEPG = async (): Promise<void> => {
  const response = await request<void>({
    method: 'post',
    url: '/epg-sources/sync-all'
  });
  return response.data;
};

export const clearAllEPGPrograms = async (): Promise<void> => {
  const response = await request<void>({
    method: 'delete',
    url: '/epg-programs-clear-all'
  });
  return response.data;
};