import { useState } from 'react';
import { Menu, ConfigProvider } from 'antd';
import zhCN from 'antd/es/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';
import EPGPrograms from './components/EPGPrograms';
import { EPGChannelList } from './components/EPGChannelList';
import { EPGSourceList } from './components/EPGSourceList';
import { ProxyConfigForm } from './components/ProxyConfigForm';
import { ChannelLogoList } from './components/ChannelLogoList';
import { StreamSourceList } from './components/StreamSourceList';
import StreamTrackList from './components/StreamTrackList';
import FilterRuleList from './components/FilterRuleList';
import { FilterRuleSetList } from './components/FilterRuleSetList';
import SortTemplateList from './components/SortTemplateList';

const queryClient = new QueryClient();

const App = () => {
  const [activeTab, setActiveTab] = useState('sources');

  return (
    <ConfigProvider locale={zhCN}>
      <QueryClientProvider client={queryClient}>
        <div className="content">
          <Menu
            mode="horizontal"
            selectedKeys={[activeTab]}
            onClick={({ key }) => setActiveTab(key)}
            items={[
              { key: 'sources', label: 'EPG订阅管理' },
              { key: 'channels', label: 'EPG频道管理' },
              { key: 'programs', label: 'EPG节目表' },
              { key: 'logos', label: 'EPG台标管理' },
              { key: 'streams', label: '直播订阅管理' },
              { key: 'tracks', label: '直播源管理' },
              { key: 'filters', label: '过滤规则管理' },
              { key: 'filter-sets', label: '筛选合集管理' },
              { key: 'sort-templates', label: '排序模板管理' },
              { key: 'settings', label: '代理设置' },
            ]}
            style={{ marginBottom: '20px' }}
          />
          {activeTab === 'sources' ? <EPGSourceList /> :
            activeTab === 'programs' ? <EPGPrograms /> :
              activeTab === 'channels' ? <EPGChannelList /> :
                activeTab === 'logos' ? <ChannelLogoList /> :
                  activeTab === 'streams' ? <StreamSourceList /> :
                    activeTab === 'tracks' ? <StreamTrackList /> :
                      activeTab === 'filters' ? <FilterRuleList /> :
                        activeTab === 'filter-sets' ? <FilterRuleSetList /> :
                          activeTab === 'sort-templates' ? <SortTemplateList /> :
                            <ProxyConfigForm />}
        </div>
      </QueryClientProvider>
    </ConfigProvider>
  );
};

export default App;
