import request from '@/utils/request';
import type { StreamTrack, PaginatedStreamTracks } from '../types/stream';
import { ApiResponse } from '@/types/api';

interface StreamTracksParams {
  group_title?: string;
  name?: string;
  source_id?: number;
  test_status?: string;
}

export const fetchStreamTracks = async (params?: StreamTracksParams): Promise<PaginatedStreamTracks[]> => {
  const response = await request<ApiResponse<PaginatedStreamTracks[]>>({
    method: 'get',
    url: '/stream-tracks',
    params
  });
  return response.data.data;
};

export const fetchStreamTrack = async (id: number): Promise<StreamTrack> => {
  const response = await request<ApiResponse<StreamTrack>>({
    method: 'get',
    url: `/stream-tracks/${id}`
  });
  return response.data.data;
};

export const deleteStreamTrack = async (id: number): Promise<any> => {
  const response = await request<ApiResponse<any>>({
    method: 'delete',
    url: `/stream-tracks/${id}`
  });
  return response.data.data;
};

export interface TestResponse {
  message: string;
}

export const testAllStreamTracks = async (): Promise<TestResponse> => {
  const response = await request<ApiResponse<TestResponse>>({
    method: 'post',
    url: '/stream-tracks/test-all'
  });
  return response.data;
};

export interface StreamTrackTestResponse {
  data: StreamTrack;
  message: string;
}

export const testStreamTrack = async (id: number): Promise<ApiResponse> => {
  const response = await request<ApiResponse>({
    method: 'post',
    url: `/stream-tracks/${id}/test`
  });
  return response.data;
};