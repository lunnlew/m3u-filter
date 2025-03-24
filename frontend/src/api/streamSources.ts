import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { StreamSource } from '../types/stream';
import request, { ApiResponse } from '../utils/request';

// 获取直播源列表
export const useStreamSources = () => {
  return useQuery<StreamSource[]>({
    queryKey: ['stream-sources'],
    queryFn: async () => {
      return await request.get('/stream-sources').then((res) => res.data);
    },
  });
};

// 添加或更新直播源
export const useStreamSourceMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (values: StreamSource) => {
      const response = values.id
        ? await request.put(`/stream-sources/${values.id}`, values)
        : await request.post('/stream-sources', values);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-sources'] });
    },
  });
};

// 删除直播源
export const useStreamSourceDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<StreamSource>, unknown, number>({
    mutationFn: (id: number) => request.delete(`/stream-sources/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-sources'] });
    }
  });
};

// 同步直播源
export const useStreamSourceSync = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<StreamSource>, unknown, number>({
    mutationFn: (id: number) => request.post(`/stream-sources/${id}/sync`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-sources'] });
    }
  });
};