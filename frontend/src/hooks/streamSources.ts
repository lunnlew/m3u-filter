import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchStreamSources, createOrUpdateStreamSource, deleteStreamSource, syncStreamSource } from '../api/streamSources';
import type { StreamSource } from '../types/stream';

export const useStreamSources = () => {
  return useQuery<StreamSource[]>({
    queryKey: ['stream-sources'],
    queryFn: fetchStreamSources,
  });
};

export const useStreamSourceMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrUpdateStreamSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-sources'] });
    },
  });
};

export const useStreamSourceDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteStreamSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-sources'] });
    }
  });
};

export const useStreamSourceSync = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncStreamSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-sources'] });
    }
  });
};