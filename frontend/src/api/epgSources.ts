import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { EPGSource } from '../types/epg';
import request, { ApiResponse } from '../utils/request';

// 获取EPG源列表
export const useEPGSources = () => {
  return useQuery<EPGSource[]>({
    queryKey: ['epg-sources'],
    queryFn: async () => {
      return await request.get('/epg-sources').then((res) => res.data);
    },
  });
};

// 添加或更新EPG源
export const useEPGSourceMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGSource>, unknown, EPGSource>({    
    mutationFn: async (values: EPGSource) => {
      const response = values.id
        ? await request.put<ApiResponse<EPGSource>>(`/epg-sources/${values.id}`, values)
        : await request.post<ApiResponse<EPGSource>>('/epg-sources', values);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    },
  });
};

// 删除EPG源
export const useEPGSourceDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGSource>, unknown, number>({
    mutationFn: async (id: number) => {
      return await request.delete(`/epg-sources/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    }
  });
};

interface SyncResponse {
  message: string;
}

// 同步EPG源
export const useEPGSourceSync = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<SyncResponse>, unknown, number>({
    mutationFn: async (id: number) => {
      return await request.post(`/epg-sources/${id}/sync`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    }
  });
};