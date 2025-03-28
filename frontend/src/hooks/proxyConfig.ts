import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchProxyConfig, updateProxyConfig } from '../api/proxyConfig';
import type { ProxyConfig } from '../types/proxy';

export const useProxyConfig = () => {
  return useQuery<ProxyConfig>({
    queryKey: ['proxy-config'],
    queryFn: fetchProxyConfig,
  });
};

export const useUpdateProxyConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateProxyConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxy-config'] });
    },
  });
};