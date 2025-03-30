import { request } from '../utils/request';
import type { ChannelLogo } from '../types/channel';

export interface ChannelLogoFilters {
  channel_name?: string;
  priority?: number;
}

export const fetchChannelLogos = async (filters?: ChannelLogoFilters): Promise<ChannelLogo[]> => {
  const response = await request<ChannelLogo[]>({
    method: 'get',
    url: '/default-channel-logos',
    params: filters
  });
  return response.data;
};

export const deleteChannelLogo = async (id: number): Promise<void> => {
  const response = await request<void>({
    method: 'delete',
    url: `/default-channel-logos/${id}`
  });
  return response.data;
};

export interface ChannelLogoInput {
  id?: number;
  channel_name: string;
  logo_url: string;
  priority: number;
}

export const createOrUpdateChannelLogo = async (data: ChannelLogoInput): Promise<ChannelLogo> => {
  const response = await request<ChannelLogo>({
    method: data.id ? 'put' : 'post',
    url: data.id ? `/default-channel-logos/${data.id}` : '/default-channel-logos',
    data
  });
  return response.data;
};