import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchStreamTracks, fetchStreamTrack, deleteStreamTrack } from '../api/streamTracks';
import type { StreamTrack, PaginatedStreamTracks } from '../types/stream';
import { testAllStreamTracks, type TestResponse } from '../api/streamTracks';
import { testStreamTrack, type StreamTrackTestResponse } from '../api/streamTracks';

export const useStreamTracks = (params?: {
  group_title?: string;
  name?: string;
  source_id?: number;
  test_status?: string;
}) => {
  return useQuery<PaginatedStreamTracks[]>({
    queryKey: ['stream-tracks', params],
    queryFn: () => fetchStreamTracks(params),
  });
};

export const useStreamTrack = (id: number) => {
  return useQuery<StreamTrack>({
    queryKey: ['stream-track', id],
    queryFn: () => fetchStreamTrack(id),
  });
};

export const useStreamTrackDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteStreamTrack,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
      queryClient.invalidateQueries({ queryKey: ['stream-track'] });
    },
  });
};

export const useStreamTrackTestAll = () => {
  const queryClient = useQueryClient();

  return useMutation<TestResponse, Error>({
    mutationFn: testAllStreamTracks,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
    },
  });
};

export const useStreamTrackTest = () => {
  const queryClient = useQueryClient();

  return useMutation<StreamTrackTestResponse, Error, number>({
    mutationFn: testStreamTrack,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stream-tracks'] });
    },
  });
};