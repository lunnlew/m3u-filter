import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PaginatedStreamTracks, StreamTrack } from '../types/streamTrack';
import request, { ApiResponse } from '../utils/request';

// 获取直播源列表
export const useStreamTracks = (params?: {
  group_title?: string;
  name?: string;
  source_id?: number;
  test_status?: string;
}) => {
  return useQuery<PaginatedStreamTracks[]>({
    queryKey: ['stream-tracks', params],
    queryFn: async () => {
      return await request.get(`/stream-tracks`, {
        params,
      }).then((res) => res.data);
    },
  });
};

// 获取直播源详情
export const useStreamTrack = (id: number) => {
  return useQuery<StreamTrack>({
    queryKey: ['stream-track', id],
    queryFn: async () => {
      return await request.get(`/stream-tracks/${id}`);
    },
  });
};

// 更新直播源
export const useStreamTrackMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<StreamTrack>, unknown, { id: number; track: StreamTrack }>({
    mutationFn: async ({ id, track }: { id: number; track: StreamTrack }) => {
      return await request.put(`/stream-tracks/${id}`, track);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
      queryClient.invalidateQueries({ queryKey: ['stream-track'] });
    },
  });
};

// 删除直播源
export const useStreamTrackDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<StreamTrack>, unknown, number>({  // 修改泛型参数，只需要id参数
    mutationFn: (id: number) => request.delete(`/stream-tracks/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
      queryClient.invalidateQueries({ queryKey: ['stream-track'] });
    },
  });
};

// 测试单个直播源
export const useStreamTrackTest = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<StreamTrack>, unknown, number>({  // 修改泛型参数，只需要id参数
    mutationFn: (id: number) => request.post(`/stream-tracks/${id}/test`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
      queryClient.invalidateQueries({ queryKey: ['stream-track'] });
    },
  });
};

// 批量测试所有直播源
export const useStreamTrackTestAll = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<StreamTrack>, unknown, void>({  // 修改泛型参数，不需要参数
    mutationFn: () => request.post('/stream-tracks/test-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
    },
  });
};