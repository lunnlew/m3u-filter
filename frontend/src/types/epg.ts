export interface ProxyConfig {
  type: 'HTTP' | 'SOCKS5';
  server: string;
  port: number;
  username?: string;
  password?: string;
}

export interface EPGSource {
  id?: number;
  name: string;
  url: string;
  enabled: boolean;
  last_sync?: string;
}

export interface EPGProgram {
  id: number;
  channel_id: string;
  channel_name: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  source_id: number;
}

export interface EPGProgramsResponse {
  data: EPGProgram[];
  total: number;
}

export interface FetchProgramsParams {
  page: number;
  page_size: number;
  channel_name?: string;
  start_time?: string;
  end_time?: string;
}

export interface EPGSource {
  id?: number;
  name: string;
  url: string;
  last_update: string | null;
  active: boolean;
  proxy?: ProxyConfig;
  sync_interval?: number;
}


export interface EPGChannel {
  id?: number;
  display_name: string;
  channel_id: string;
  language: string;
  category?: string;
  logo_url?: string;
}