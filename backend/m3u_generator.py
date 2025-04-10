from typing import List, Dict
from config import BASE_URL, RESOURCE_URL_PREFIX


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

    def _basic_sort_channels(self, channels: List[Dict], sort_by: str = 'display_name') -> List[Dict]:
        """基础频道排序"""
        return sorted(channels, key=lambda x: x.get(sort_by, '').lower())

    def _sort_group_by_template(self, channels: List[Dict], channel_order: List[str]) -> List[Dict]:
        """按照模板对频道进行排序
        
        Args:
            channels: 同一分组下的频道列表
            channel_order: 该分组下的频道排序模板
        """
        if not channels or not channel_order:
            return channels

        # 创建排序映射，不区分大小写
        order_map = {name.lower(): idx for idx, name in enumerate(channel_order)}
        
        # 分离有序和无序频道
        ordered_channels = []
        unordered_channels = []
        
        for channel in channels:
            display_name = channel.get('display_name', '')
            if display_name.lower() in order_map:
                ordered_channels.append((order_map[display_name.lower()], channel))
            else:
                unordered_channels.append(channel)
        
        # 按模板顺序排序
        final_channels = []
        if ordered_channels:
            final_channels.extend(ch for _, ch in sorted(ordered_channels, key=lambda x: x[0]))
        if unordered_channels:
            final_channels.extend(sorted(unordered_channels, key=lambda x: x.get('display_name', '').lower()))
        
        return final_channels

    def _sort_channels_in_groups(self, grouped_channels: Dict[str, List[Dict]], 
                               sort_by: str, sort_templates: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """对每个分组内的频道进行排序"""
        sorted_groups = {}
        for group, channels in grouped_channels.items():
            if group in sort_templates and sort_templates[group]:
                # 使用模板排序
                sorted_groups[group] = self._sort_group_by_template(channels, sort_templates[group])
            else:
                # 使用基础排序
                sorted_groups[group] = self._basic_sort_channels(channels, sort_by)
        return sorted_groups

    def _group_channels(self, channels: List[Dict]) -> Dict[str, List[Dict]]:
        """将频道按分组归类"""
        grouped = {}
        for channel in channels:
            # 修改默认分组名称，避免出现 Undefined
            group = channel.get('group_title', '') or '未分类'
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(channel)
            # 确保 channel 中的 group_title 与分组一致
            channel['group_title'] = group
        return grouped

    def _sort_and_group_channels(self, channels: List[Dict], sort_by: str = 'display_name', 
                               group_order: List[str] = [], sort_templates: Dict[str, List[str]] = {}) -> List[Dict]:
        """对频道进行排序和分组处理"""
        # 1. 先按分组归类
        grouped_channels = self._group_channels(channels)
        
        # 2. 对每个分组内的频道进行排序
        sorted_groups = self._sort_channels_in_groups(grouped_channels, sort_by, sort_templates)
        
        # 3. 按照group_order组织最终顺序
        final_channels = []
        processed_groups = set()
        
        # 首先处理group_order中指定的分组
        for group in group_order:
            if group in sorted_groups:
                final_channels.extend(sorted_groups[group])
                processed_groups.add(group)
        
        # 处理剩余的分组（按字母顺序，确保None被转换为'未分类'）
        remaining_groups = sorted(
            (group for group in sorted_groups.keys() if group not in processed_groups),
            key=lambda x: str(x or '未分类')
        )
        for group in remaining_groups:
            final_channels.extend(sorted_groups[group])
        
        return final_channels

    def generate_txt(self, channels: List[Dict], rule_names: List[str] = [], sort_by: str = 'display_name', 
                    group_order: List[str] = [], sort_templates: Dict[str, List[str]] = {}) -> tuple[str, str]:
        # 去重处理
        filtered_channels = self._deduplicate_channels(channels)
        
        # 排序和分组处理
        filtered_channels = self._sort_and_group_channels(filtered_channels, sort_by, group_order, sort_templates)
        
        # 按分组重新组织频道（保持分组顺序）
        grouped_channels = self._group_channels(filtered_channels)
        
        # 生成TXT格式内容
        txt_lines = []
        
        # 按照group_order的顺序输出分组
        for group in group_order:
            if group in grouped_channels:
                txt_lines.append(f"{group},#genre#")
                for channel in grouped_channels[group]:
                    txt_lines.append(f"{channel['display_name']},{channel['stream_url']}")
                grouped_channels.pop(group)
        
        # 输出剩余的分组（按字母顺序）
        for group in sorted(grouped_channels.keys()):
            txt_lines.append(f"{group},#genre#")
            for channel in grouped_channels[group]:
                txt_lines.append(f"{channel['display_name']},{channel['stream_url']}")
        
        txt_content = "\n".join(txt_lines)
        
        # 生成文件名
        filename = '_'.join(rule_names) + '.txt' if rule_names else 'filtered.txt'
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        return txt_content, filename

    def generate_m3u(self, channels: List[Dict], rule_names: List[str] = [], header_info: dict = {}, 
                    sort_by: str = 'display_name', group_order: List[str] = [], 
                    sort_templates: Dict[str, List[str]] = {}) -> tuple[str, str]:
        # 去重处理
        filtered_channels = self._deduplicate_channels(channels)
        
        # 排序和分组处理
        filtered_channels = self._sort_and_group_channels(filtered_channels, sort_by, group_order, sort_templates)
        
        # 按分组重新组织频道（保持分组顺序）
        grouped_channels = self._group_channels(filtered_channels)
        
        # 初始化M3U文件内容
        lines = [f'#EXTM3U x-tvg-url="{BASE_URL}{RESOURCE_URL_PREFIX}/m3u/epg.xml"']
        
        # 添加header_info
        if 'generated_at' in header_info:
            lines.append(f"# Generated at: {header_info['generated_at']}")
        if 'provider' in header_info:
            lines.append(f"# Provider: {header_info['provider']}")
        
        def add_channel_to_lines(channel):
            if not channel.get('stream_url'):
                return
                
            extinf = '#EXTINF:-1'
            
            if channel.get('tvg-id'):
                extinf += f' tvg-id="{channel["tvg-id"]}"'
            elif channel.get('tvg-name'):
                extinf += f' tvg-id="{channel["tvg-name"]}"'
            elif channel.get('display_name'):
                extinf += f' tvg-id="{channel["display_name"]}"'

            if channel.get('tvg-name'):
                extinf += f' tvg-name="{channel["tvg-name"]}"'
            elif channel.get('display_name'):
                extinf += f' tvg-name="{channel["display_name"]}"'

            if channel.get('x_tvg_url'):
                extinf += f' tvg-url="{channel["x_tvg_url"]}"'

            if channel.get('logo_url'):
                extinf += f' tvg-logo="{BASE_URL}{RESOURCE_URL_PREFIX}{channel["logo_url"]}"'
            elif channel.get('tvg-logo'):
                extinf += f' tvg-logo="{channel["tvg-logo"]}"'
            
            if channel.get('tvg-language'):
                extinf += f' tvg-language="{channel["tvg-language"]}"'
            
            if channel.get('catchup'):
                extinf += f' catchup="{channel["catchup"]}"'

            if channel.get('catchup_source'):
                extinf += f' catchup-source="{channel["catchup_source"]}"'

            if channel.get('group_title'):
                extinf += f' group-title="{channel["group_title"]}"'
            
            extinf += f',{channel["display_name"]}'
            lines.extend([extinf, channel['stream_url']])
        
        # 按照group_order的顺序输出分组
        for group in group_order:
            if group in grouped_channels:
                for channel in grouped_channels[group]:
                    add_channel_to_lines(channel)
                grouped_channels.pop(group)
        
        # 输出剩余的分组（按字母顺序）
        for group in sorted(grouped_channels.keys()):
            for channel in grouped_channels[group]:
                add_channel_to_lines(channel)
        
        m3u_content = '\n'.join(lines)
        
        # 生成文件名
        filename = '_'.join(rule_names) + '.m3u' if rule_names else 'filtered.m3u'
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        return m3u_content, filename