import { http, HttpResponse } from 'msw';
import type { LoginFormValues } from '../hooks/useLogin';

export const handlers = [
  http.post('/api/login', async ({ request }) => {
    const body = (await request.json()) as LoginFormValues;

    if (!body) {
      return HttpResponse.json(
        {
          code: 401,
          message: '用户名或密码错误',
          data: null,
        },
        { status: 401 },
      );
    }

    // 模拟验证逻辑
    if (body.username === 'admin' && body.password === 'admin123') {
      return HttpResponse.json({
        code: 200,
        message: '登录成功',
        data: {
          token: 'mock-jwt-token',
        },
      });
    }

    return HttpResponse.json(
      {
        code: 401,
        message: '用户名或密码错误',
        data: null,
      },
      { status: 401 },
    );
  }),
];
