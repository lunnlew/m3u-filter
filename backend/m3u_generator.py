from typing import List, Dict
from config import BASE_URL, STATIC_URL_PREFIX


class M3UGenerator:
    def _deduplicate_channels(self, channels: List[Dict]) -> List[Dict]:
        """去除重复的URL，优先保留具有catchup或catchup_source的记录"""
        url_map = {}
        for channel in channels:
            url = channel.get('stream_url')
            if not url:
                continue

            if url not in url_map:
                url_map[url] = channel
            else:
                # 如果新的channel有catchup或catchup_source，而现有的没有，则替换
                existing = url_map[url]
                new_has_catchup = channel.get('catchup') or channel.get('catchup_source')
                existing_has_catchup = existing.get('catchup') or existing.get('catchup_source')
                
                if new_has_catchup and not existing_has_catchup:
                    url_map[url] = channel

        return list(url_map.values())

    def _sort_and_group_channels(self, channels: List[Dict], sort_by: str = 'display_name', group_order: List[str] = []) -> List[Dict]:
        """对频道进行排序和分组处理
        
        Args:
            channels: 频道列表
            sort_by: 排序字段，默认按display_name排序
            group_order: 分组顺序列表，如果提供则按照指定顺序排列分组
        """
        # 首先按照频道名称排序
        sorted_channels = sorted(channels, key=lambda x: x.get(sort_by, '').lower())
        
        if not group_order or len(group_order) == 0:
            # 如果没有指定分组顺序，直接返回排序后的结果
            return sorted_channels
        
        # 按照指定的分组顺序重新组织频道
        grouped_channels = []
        # 首先处理指定顺序的分组
        for group in group_order:
            group_channels = [ch for ch in sorted_channels if ch.get('group_title') == group]
            grouped_channels.extend(group_channels)
        
        # 处理未在指定顺序中的分组
        remaining_channels = [ch for ch in sorted_channels if ch.get('group_title') not in group_order]
        grouped_channels.extend(remaining_channels)
        
        return grouped_channels

    def generate_m3u(self, channels: List[Dict], rule_names: List[str] = [], header_info: dict = {}, 
                    sort_by: str = 'display_name', group_order: List[str] = []) -> tuple[str, str]:
        """生成M3U格式的播放列表
        
        Args:
            channels: 频道列表
            rule_names: 规则名称列表
            header_info: 头部信息
            sort_by: 排序字段
            group_order: 分组顺序列表
        """
        # 去重处理
        filtered_channels = self._deduplicate_channels(channels)
        
        # 排序和分组处理
        filtered_channels = self._sort_and_group_channels(filtered_channels, sort_by, group_order)
        
        # 确保每个频道都包含必要的字段
        for channel in filtered_channels:
            if 'stream_url' not in channel or not channel['stream_url']:
                continue
            if 'group_title' not in channel:
                channel['group_title'] = '未分类'

        # 初始化M3U文件内容
        lines = [f'#EXTM3U x-tvg-url="{BASE_URL}{STATIC_URL_PREFIX}/m3u/epg.xml"']

        # 添加header_info中的信息
        if 'generated_at' in header_info:
            lines.append(f"# Generated at: {header_info['generated_at']}")
        if 'provider' in header_info:
            lines.append(f"# Provider: {header_info['provider']}")
        
        for channel in filtered_channels:
            # 构建EXTINF行
            extinf = '#EXTINF:-1'
            
            # 添加TVG信息
            for attr in ['tvg-id', 'tvg-name', 'tvg-logo', 'tvg-language']:
                if attr in channel:
                    extinf += f' {attr}="{channel[attr]}"'
            
            # 添加x-tvg-url信息
            if 'x_tvg_url' in channel and channel['x_tvg_url']:
                extinf += f' tvg-url="{channel["x_tvg_url"]}"'
            
            if 'logo_url' in channel and channel["logo_url"]:
                extinf += f' tvg-logo="{BASE_URL}{STATIC_URL_PREFIX}{channel["logo_url"]}"'

            if 'display_name' in channel and channel["display_name"]:
                extinf += f' tvg-name="{channel["display_name"]}"'
            
            # 添加catchup和catchup_source信息
            if 'catchup' in channel and channel['catchup']:
                extinf += f' catchup="{channel["catchup"]}"'
            if 'catchup_source' in channel and channel['catchup_source']:
                extinf += f' catchup-source="{channel["catchup_source"]}"'
            
            # 添加分组信息
            if 'group_title' in channel:
                extinf += f' group-title="{channel["group_title"]}"'
            
            # 添加频道名称
            extinf += f',{channel["display_name"]}'
            
            # 添加EXTINF行和URL行
            lines.append(extinf)

            if 'stream_url' in channel:
                lines.append(channel['stream_url'])
        
        m3u_content = '\n'.join(lines)

        # 生成文件名
        if rule_names:
            filename = '_'.join(rule_names) + '.m3u'
            # 确保文件名合法
            filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        else:
            filename = 'filtered.m3u'
        
        return m3u_content, filename