import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchEPGPrograms, syncAllEPG, clearAllEPGPrograms } from '../api/epgPrograms';
import type { EPGProgramsResponse, FetchProgramsParams } from '../types/epg';

export const useEPGPrograms = (params: FetchProgramsParams) => {
  return useQuery<EPGProgramsResponse>({
    queryKey: ['epg-programs', params],
    queryFn: () => fetchEPGPrograms(params),
  });
};

export const useEPGSync = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncAllEPG,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-programs'] });
    },
  });
};

export const useClearAllData = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clearAllEPGPrograms,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epg-programs'] });
    }
  });
};