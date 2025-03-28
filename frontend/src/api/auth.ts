import type { LoginFormValues } from '../hooks/useLogin';
import { request } from '../utils/request';

export const loginUser = async (data: LoginFormValues): Promise<string> => {
  try {
    const response = await request<{ token: string }>({
      method: 'post',
      url: '/login',
      data
    });
    return response.data.token;
  } catch (error: any) {
    throw new Error(
      error.response?.data?.message || '登录失败，请检查账号密码',
    );
  }
};
