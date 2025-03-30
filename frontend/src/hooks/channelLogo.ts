import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { fetchChannelLogos, deleteChannelLogo, createOrUpdateChannelLogo, type ChannelLogoInput } from '../api/channelLogo';
import type { ChannelLogo } from '../types/channel';

import { ChannelLogoFilters } from '../api/channelLogo';

export const useChannelLogos = (filters?: ChannelLogoFilters) => {
  return useQuery<ChannelLogo[]>({
    queryKey: ['channelLogos', filters],
    queryFn: () => fetchChannelLogos(filters),
  });
};

export const useChannelLogoMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateChannelLogo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channelLogos'] });
    },
  });
};

export const useChannelLogoDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteChannelLogo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channelLogos'] });
      message.success('删除成功');
    },
    onError: (error: Error) => {
      message.error(`删除失败: ${error.message}`);
    },
  });
};