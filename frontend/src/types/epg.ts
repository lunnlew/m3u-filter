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
  last_update: string | null;
  active: boolean;
  proxy?: ProxyConfig;
  sync_interval?: number;
}