import './App.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App as AntApp, ConfigProvider } from 'antd';
import { RouterProvider } from 'react-router-dom';
import router from './router';
const queryClient = new QueryClient();
const App = () => {
  return (
    <AntApp>
      <ConfigProvider
        theme={{
          cssVar: true,
          hashed: false,
          token: { colorPrimary: '#00b96b' },
        }}
      >
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </ConfigProvider>
    </AntApp>
  );
};

export default App;
