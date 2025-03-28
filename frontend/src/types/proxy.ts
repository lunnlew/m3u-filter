export interface ProxyConfig {
  enabled: boolean;
  proxy_type: 'http' | 'socks5';
  host: string;
  port: number;
  username?: string;
  password?: string;
}