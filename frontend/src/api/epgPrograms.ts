import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import request, { ApiResponse } from '../utils/request';
import dayjs from 'dayjs';

interface EPGProgram {
  id: number;
  channel_id: string;
  channel_name: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  source_id: number;
}

interface EPGProgramsResponse {
  data: EPGProgram[];
  total: number;
}

interface FetchProgramsParams {
  page: number;
  page_size: number;
  channel_name?: string;
  start_time?: string;
  end_time?: string;
}

const fetchEPGPrograms = (params: FetchProgramsParams): Promise<EPGProgramsResponse> => {
  return request.get('/epg-programs', { params }).then(response => response.data);
};


export const useEPGPrograms = (params: FetchProgramsParams) => {
  return useQuery<EPGProgramsResponse>({
    queryKey: ['epg-programs', params],
    queryFn: () => fetchEPGPrograms(params),
  });
};

export const useEPGSync = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGProgramsResponse>>({
    mutationFn: () => request.post('/epg-sources/sync-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-programs'] });
    },
  });
};

// 清空所有数据
export const useClearAllData = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGProgramsResponse>>({
    mutationFn: () => request.delete('/epg-programs-clear-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-programs'] });
    }
  });
};