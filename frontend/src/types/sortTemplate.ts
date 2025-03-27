export interface SortTemplate {
  id: number;
  name: string;
  description?: string;
  group_orders: Record<string, string[]>;
  created_at?: string;
  updated_at?: string;
}