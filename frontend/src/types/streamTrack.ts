export interface StreamTrack {
  id?: number;
  name: string;
  url: string;
  group_title?: string;
  tvg_id?: string;
  tvg_name?: string;
  tvg_logo?: string;
  tvg_language?: string;
  source_id: number;
  test_status?: boolean;
  test_speed?: number;
  video_codec?: string;
  audio_codec?: string;
  resolution?: string;
  bitrate?: number;
  frame_rate?: number;
  last_test_time?: string;
  created_at?: string;
  updated_at?: string;
  probe_failure_count?: number;
  last_failure_time?: string;
}

export interface PaginatedStreamTracks {
  items: StreamTrack[];
  total: number;
  isLoading: boolean;
}