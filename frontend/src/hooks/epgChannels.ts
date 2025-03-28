import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import {
  fetchEPGChannels,
  createOrUpdateEPGChannel,
  deleteEPGChannel,
  clearAllEPGChannels,
  generateEPGXML
} from '../api/epgChannels';
import type { EPGChannel } from '../types/epg';

export interface GenerateEPGResponse {
  url_path: string;
}

export const useEPGChannels = () => {
  return useQuery<EPGChannel[]>({
    queryKey: ['epg-channels'],
    queryFn: fetchEPGChannels,
  });
};

export const useEPGChannelMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateEPGChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
      message.success('操作成功');
    },
    onError: (error: Error) => {
      message.error(`操作失败: ${error.message}`);
    },
  });
};

export const useEPGChannelDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteEPGChannel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
      message.success('删除成功');
    },
    onError: (error: Error) => {
      message.error(`删除失败: ${error.message}`);
    },
  });
};

export const useClearAllData = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearAllEPGChannels,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
      message.success('清空成功');
    },
    onError: (error: Error) => {
      message.error(`清空失败: ${error.message}`);
    },
  });
};

export const useGenerateEPG = () => {
  return useMutation({
    mutationFn: generateEPGXML,
    onSuccess: () => {
      message.success('生成成功');
    },
    onError: (error: Error) => {
      message.error(`生成失败: ${error.message}`);
    },
  });
};