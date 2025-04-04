export interface FilterRule {
  id: number;
  name: string;
  type: string;  // 匹配类型：name, keyword, resolution, group, bitrate
  pattern: string;  // 统一的匹配模式
  action: string;  // include 或 exclude
  priority: number;
  enabled: boolean;
  case_sensitive: boolean;
  regex_mode: boolean;
}

export interface FilterRuleSet {
  id: number;
  name: string;
  description: string;
  enabled: boolean;
  rules?: any[];
  children?: any[];
  sync_interval: number;
  logic_type: string;
  _parentId?: string
}

export interface GenerateM3UResponse {
  url_path: string;
}

export interface GroupMapping {
  channel_name: string;
  custom_group: string;
  rule_set_id?: number;
}