import request from '@/utils/request';
import type { LoginFormValues } from '../hooks/useLogin';
import { ApiResponse } from '@/types/api';

export const loginUser = async (data: LoginFormValues): Promise<{ token: string }> => {
  try {
    const response = await request<ApiResponse<{ token: string }>>({
      method: 'post',
      url: '/login',
      data
    });
    return response.data.data;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.message || '登录失败，请检查账号密码',
    );
  }
};
