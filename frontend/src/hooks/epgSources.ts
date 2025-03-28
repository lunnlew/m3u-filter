import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchEPGSources, createOrUpdateEPGSource, deleteEPGSource, syncEPGSource } from '../api/epgSources';
import type { EPGSource } from '../types/epg';
import { ApiResponse } from '@/types/api';

export const useEPGSources = () => {
  return useQuery<EPGSource[]>({
    queryKey: ['epg-sources'],
    queryFn: fetchEPGSources,
  });
};

export const useEPGSourceMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateEPGSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    },
  });
};

export const useEPGSourceDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteEPGSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    }
  });
};

export const useEPGSourceSync = () => {
  const queryClient = useQueryClient();

  return useMutation<ApiResponse<any>, unknown, number>({
    mutationFn: syncEPGSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-sources'] });
    }
  });
};