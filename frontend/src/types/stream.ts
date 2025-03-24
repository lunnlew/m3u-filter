export interface StreamSource {
  id?: number;
  name: string;
  url: string;
  type: 'm3u' | 'txt';
  last_update: string | null;
  active: boolean;
  sync_interval?: number;
  proxy?: {
    type: 'HTTP' | 'SOCKS5';
    server: string;
    port: number;
    username?: string;
    password?: string;
  };
}