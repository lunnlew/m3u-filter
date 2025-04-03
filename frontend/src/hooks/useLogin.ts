import { useMutation } from '@tanstack/react-query';
import { type NavigateFunction, useNavigate } from 'react-router-dom';
import { loginUser } from '../api/auth';
import type { ApiResponse } from '../types/api';

export interface LoginFormValues {
  username: string;
  password: string;
}

export const useLogin = (): {
  mutate: (data: LoginFormValues) => void;
  error: Error | null;
  isPending: boolean;
} => {
  const navigate: NavigateFunction = useNavigate();
  return useMutation<{ token: string }, Error, LoginFormValues>({
    mutationFn: loginUser,
    onSuccess: (result) => {
      localStorage.setItem('authToken', result.token);
      navigate('/', { replace: true });
    },
    onError: (error) => {
      console.error('Login error:', error);
      navigate('/login', { replace: true });
    },
  });
};
