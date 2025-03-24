import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import request, { ApiResponse } from '../utils/request';

interface EPGChannel {
  id?: number;
  channel_id: string;
  display_name: string;
  language: string;
  category?: string;
  logo_url?: string;
}

// 获取EPG频道列表
export const useEPGChannels = () => {
  return useQuery<EPGChannel[]>({
    queryKey: ['epg-channels'],
    queryFn: async () => request.get('/epg-channels').then((res) => res.data),
  });
};

// 添加或更新EPG频道
export const useEPGChannelMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGChannel>, unknown, EPGChannel>({
    mutationFn: (values: EPGChannel) => {
      if (values.id) {
        return request.put(`/epg-channels/${values.id}`, values);
      }
      return request.post('/epg-channels', values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
    },
  });
};

// 删除EPG频道
export const useEPGChannelDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGChannel>, unknown, number>({
    mutationFn: (id: number) => request.delete(`/epg-channels/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
    }
  });
};

// 清空所有数据
export const useClearAllData = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<EPGChannel>>({
    mutationFn: () => request.delete('/epg-channels-clear-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
    }
  });
};

export interface GenerateEPGResponse {
  url_path: string;
}
// 生成EPG文件
export const useGenerateEPG = () => {
  return useMutation<ApiResponse<GenerateEPGResponse>, unknown>({
    mutationFn: async () => {
      return await request.post(`/epg-channels/export-xml`);
    }
  });
};