import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import request, { ApiResponse } from '../utils/request';

export interface ChannelLogo {
  id: number;
  channel_name: string;
  logo_url: string;
  priority: number;
}

// 获取Logo列表
export const useChannelLogos = () => {
  return useQuery<ChannelLogo[]>({
    queryKey: ['channelLogos'],
    queryFn: () => request.get('/default-channel-logos').then((res) => res.data),
  });
};

// 添加或更新Logo
export const useChannelLogoMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<ChannelLogo>, Error, Partial<ChannelLogo>>({    
    mutationFn: ({ id, ...values }: Partial<ChannelLogo>) => {
      const data = {
        channel_name: values.channel_name,
        logo_url: values.logo_url,
        priority: values.priority || 0
      };
      if (id) {
        return request.put(`/default-channel-logos/${id}`, data);
      }
      return request.post('/default-channel-logos', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channelLogos'] });
      message.success('操作成功');
    },
    onError: (error: Error) => {
      message.error(`操作失败: ${error.message}`);
    },
  });
};

// 删除Logo
export const useChannelLogoDelete = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<ChannelLogo>, Error, number>({    
    mutationFn: (id: number) => request.delete(`/default-channel-logos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channelLogos'] });
      message.success('删除成功');
    },
    onError: (error: Error) => {
      message.error(`删除失败: ${error.message}`);
    },
  });
};