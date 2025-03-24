import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import request, { ApiResponse } from '../utils/request';

export interface ProxyConfig {
  enabled: boolean;
  proxy_type: 'http' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
}

export const useProxyConfig = () => {
  return useQuery<ProxyConfig>({
    queryKey: ['proxy-config'],
    queryFn: async () => {
      return await request.get('/proxy-config').then((res) => res.data);
    },
  });
};

export const useUpdateProxyConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (config: ProxyConfig) => {
      return await request.put<ApiResponse<ProxyConfig>>('/proxy-config', config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxy-config'] });
    },
  });
};