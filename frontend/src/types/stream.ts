export interface StreamSource {
  id?: number;
  name: string;
  url: string;
  enabled: boolean;
  last_sync?: string;
  sync_interval?: number;
}

export interface StreamTrack {
  id: number;
  name: string;
  url: string;
  group_title: string;
  logo?: string;
  source_id: number;
  test_status?: 'pending' | 'success' | 'failed';
}

export interface PaginatedStreamTracks {
  data: StreamTrack[];
  total: number;
}