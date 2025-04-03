import { ApiResponse } from '@/types/api';
import type { ChannelLogo } from '../types/channel';
import request from '@/utils/request';

export interface ChannelLogoFilters {
  channel_name?: string;
  priority?: number;
}

export const fetchChannelLogos = async (filters?: ChannelLogoFilters): Promise<ChannelLogo[]> => {
  const response = await request<ApiResponse<ChannelLogo[]>>({
    method: 'get',
    url: '/default-channel-logos',
    params: filters
  });
  return response.data.data;
};

export const deleteChannelLogo = async (id: number): Promise<void> => {
  const response = await request<ApiResponse<void>>({
    method: 'delete',
    url: `/default-channel-logos/${id}`
  });
  return response.data.data;
};

export interface ChannelLogoInput {
  id?: number;
  channel_name: string;
  logo_url: string;
  priority: number;
}

export const createOrUpdateChannelLogo = async (data: ChannelLogoInput): Promise<ChannelLogo> => {
  const response = await request<ApiResponse<ChannelLogo>>({
    method: data.id ? 'put' : 'post',
    url: data.id ? `/default-channel-logos/${data.id}` : '/default-channel-logos',
    data
  });
  return response.data.data;
};