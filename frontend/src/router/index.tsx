import { Navigate, Outlet, createBrowserRouter } from 'react-router-dom';
import HomePage from '../pages/home/IndexPage';
import LoginPage from '../pages/login/LoginPage';

const AuthLayout = () => {
  const token = localStorage.getItem('authToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
};

const router = createBrowserRouter([
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      {
        path: '',
        element: <HomePage />,
      },
      // 其他需要鉴权的路由都放在这里
    ],
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '*',
    element: <div>404</div>,
  },
]);

export default router;
