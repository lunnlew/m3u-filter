import { useState } from 'react';
import { message } from 'antd';
import { BlockedDomain, fetchBlockedDomains, removeBlockedDomain } from '../api/blockedDomains';

interface BlockedDomainsHook {
  domains: BlockedDomain[];
  loading: boolean;
  total: number;
  fetchDomains: (page?: number, pageSize?: number) => Promise<void>;
  removeDomain: (domain: string) => Promise<void>;
}

export const useBlockedDomains = (): BlockedDomainsHook => {
  const [domains, setDomains] = useState<BlockedDomain[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const fetchDomains = async (page: number = 1, pageSize: number = 10) => {
    setLoading(true);
    try {
      const response = await fetchBlockedDomains(page, pageSize);
      setDomains(response.items);
      setTotal(response.total);
    } catch (error) {
      message.error('获取黑名单失败');
    } finally {
      setLoading(false);
    }
  };

  const removeDomain = async (domain: string) => {
    try {
      await removeBlockedDomain(domain);
      message.success('移除成功');
      await fetchDomains();
    } catch (error) {
      message.error('移除失败');
    }
  };

  return {
    domains,
    loading,
    total,
    fetchDomains,
    removeDomain
  };
};