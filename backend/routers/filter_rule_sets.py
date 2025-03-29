from fastapi import APIRouter, HTTPException, Path
from typing import List, Optional
from database import get_db_connection
from models import FilterRuleSet, FilterRuleSetMapping, RuleTree
import os
from m3u_generator import M3UGenerator
from models import BaseResponse
from datetime import datetime
from config import RESOURCE_ROOT
import json
import logging
logger = logging.getLogger(__name__)
router = APIRouter()


from pydantic import BaseModel


class FilterRuleSetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    logic_type: Optional[str] = "AND"
    rules: List[dict]  # 修改为接收字典列表
    children: Optional[List[dict]] = None
    sync_interval: Optional[int] = None  # 新增字段，单位：分钟

@router.get("/filter-rule-sets")
def get_filter_rule_sets():
    """获取所有规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, enabled, logic_type, sync_interval FROM filter_rule_sets")
        columns = [column[0] for column in cursor.description]
        rule_sets = [dict(zip(columns, row)) for row in cursor.fetchall()]
        data = []
        for rule_set in rule_sets:
            # 获取子规则集合
            cursor.execute("""
                SELECT rs.id, rs.name, rs.description, rs.enabled, rs.sync_interval, rs.logic_type
                FROM filter_rule_sets rs
                INNER JOIN filter_rule_set_children rsc ON rs.id = rsc.child_set_id
                WHERE rsc.parent_set_id = ?
            """, (rule_set['id'],))
            children = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
            
            data.append(
                FilterRuleSetResponse(
                    id=rule_set['id'],
                    name=rule_set['name'],
                    description=rule_set['description'],
                    enabled=bool(rule_set['enabled']),
                    logic_type=rule_set['logic_type'],
                    sync_interval=rule_set['sync_interval'],
                    rules=_get_rules_for_set(cursor, rule_set['id']),
                    children=[{
                        'id': child['id'],
                        'name': child['name'],
                        'description': child['description'],
                        'enabled': bool(child['enabled']),
                        'logic_type': child['logic_type'],
                        'sync_interval': child['sync_interval'],
                        'rules': _get_rules_for_set(cursor, child['id'])
                    } for child in children]
                )
            )
        return BaseResponse.success(data=data)

def _get_rules_for_set(cursor, set_id: int) -> List[dict]:
    """获取规则集合中的所有规则"""
    cursor.execute("""
        SELECT fr.id, fr.name, fr.type, fr.pattern, fr.action, fr.priority, fr.enabled, fr.case_sensitive, fr.regex_mode 
        FROM filter_rules fr
        INNER JOIN filter_rule_set_mappings frsm ON fr.id = frsm.rule_id
        WHERE frsm.rule_set_id = ?
    """, (set_id,))
    columns = [column[0] for column in cursor.description]
    rules = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return [{
        'id': rule['id'],
        'name': rule['name'],
        'type': rule['type'],
        'pattern': rule['pattern'],
        'action': rule['action'],
        'priority': rule['priority'],
        'enabled': bool(rule['enabled']),
        'case_sensitive': bool(rule['case_sensitive']),
        'regex_mode': bool(rule['regex_mode'])
    } for rule in rules]

@router.post("/filter-rule-sets")
def create_filter_rule_set(rule_set: FilterRuleSet):
    """创建新的规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 检查名称是否重复
        cursor.execute("SELECT id FROM filter_rule_sets WHERE name = ?", (rule_set.name,))
        if cursor.fetchone():
            return BaseResponse.error(message="Rule set name already exists", code=400)
        
        cursor.execute(
            "INSERT INTO filter_rule_sets (name, description, enabled, logic_type, sync_interval) VALUES (?, ?, ?, ?, ?)",
            (rule_set.name, rule_set.description, rule_set.enabled, rule_set.logic_type, rule_set.sync_interval)
        )
        set_id = cursor.lastrowid
        
        # 添加子规则集合关系
        if rule_set.children:
            for child_id in rule_set.children:
                cursor.execute(
                    "INSERT INTO filter_rule_set_children (parent_set_id, child_set_id) VALUES (?, ?)",
                    (set_id, child_id)
                )
        
        conn.commit()
        return BaseResponse.success(data={"id": set_id})

@router.put("/filter-rule-sets/{set_id}")
def update_filter_rule_set(set_id: int, rule_set: FilterRuleSet):
    """更新规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 检查规则集合是否存在
        cursor.execute("SELECT id FROM filter_rule_sets WHERE id = ?", (set_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Rule set not found", code=404)
        
        # 检查名称是否与其他规则集合重复
        cursor.execute("SELECT id FROM filter_rule_sets WHERE name = ? AND id != ?", (rule_set.name, set_id))
        if cursor.fetchone():
            return BaseResponse.error(message="Rule set name already exists", code=400)
        
        cursor.execute(
            "UPDATE filter_rule_sets SET name=?, description=?, enabled=?, logic_type=?, sync_interval=? WHERE id=?",
            (rule_set.name, rule_set.description, rule_set.enabled, rule_set.logic_type, rule_set.sync_interval, set_id)
        )
        
        # 更新子规则集合关系
        if rule_set.children:
            # 获取现有子规则集合
            cursor.execute("SELECT child_set_id FROM filter_rule_set_children WHERE parent_set_id=?", (set_id,))
            existing_children = set(row[0] for row in cursor.fetchall())
            new_children = set(rule_set.children)
            
            # 删除不再需要的子规则集合
            for child_id in existing_children - new_children:
                cursor.execute(
                    "DELETE FROM filter_rule_set_children WHERE parent_set_id=? AND child_set_id=?",
                    (set_id, child_id)
                )
            
            # 添加新的子规则集合
            for child_id in new_children - existing_children:
                cursor.execute(
                    "INSERT INTO filter_rule_set_children (parent_set_id, child_set_id) VALUES (?, ?)",
                    (set_id, child_id)
                )
        
        conn.commit()
        return BaseResponse.success()

@router.patch("/filter-rule-sets/{set_id}/toggle")
def toggle_filter_rule_set(set_id: int):
    """切换规则集合的启用状态"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT enabled FROM filter_rule_sets WHERE id = ?", (set_id,))
        result = cursor.fetchone()
        if not result:
            return BaseResponse.error(message="Rule set not found", code=404)
        
        new_status = not bool(result[0])
        cursor.execute(
            "UPDATE filter_rule_sets SET enabled = ? WHERE id = ?",
            (new_status, set_id)
        )
        conn.commit()
        return BaseResponse.success(data={"enabled": new_status})

@router.delete("/filter-rule-sets/{set_id}")
def delete_filter_rule_set(set_id: int):
    """删除规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 首先删除规则集合与规则的关联关系
        cursor.execute("DELETE FROM filter_rule_set_mappings WHERE rule_set_id=?", (set_id,))
        # 删除子规则集合关系
        cursor.execute("DELETE FROM filter_rule_set_children WHERE parent_set_id=? OR child_set_id=?", (set_id, set_id))
        # 然后删除规则集合
        cursor.execute("DELETE FROM filter_rule_sets WHERE id=?", (set_id,))
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Rule set not found", code=404)
        conn.commit()
        return BaseResponse.success()

@router.post("/filter-rule-sets/{parent_set_id}/rule-sets/{child_set_id}")
def add_child_set(parent_set_id: int, child_set_id: int):
    """向规则集合中添加子规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查父子集合是否存在
        cursor.execute("SELECT id FROM filter_rule_sets WHERE id IN (?, ?)", (parent_set_id, child_set_id))
        existing = cursor.fetchall()
        if len(existing) != 2:
            return BaseResponse.error(message="Parent or child set not found", code=404)
        
        # 检查是否会产生循环依赖
        cursor.execute("""
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_set_id 
                FROM filter_rule_set_children 
                WHERE child_set_id = ?
                UNION
                SELECT c.parent_set_id 
                FROM filter_rule_set_children c, ancestors a
                WHERE c.child_set_id = a.id
            )
            SELECT id FROM ancestors WHERE id = ?
        """, (parent_set_id, child_set_id))
        if cursor.fetchone():
            return BaseResponse.error(message="Adding child would create cyclic dependency", code=400)
        
        # 检查是否已存在关联
        cursor.execute("""
            SELECT 1 FROM filter_rule_set_children 
            WHERE parent_set_id = ? AND child_set_id = ?
        """, (parent_set_id, child_set_id))
        if cursor.fetchone():
            return BaseResponse.error(message="Child set already exists", code=400)
        
        cursor.execute("""
            INSERT INTO filter_rule_set_children (parent_set_id, child_set_id)
            VALUES (?, ?)
        """, (parent_set_id, child_set_id))
        
        conn.commit()
        return BaseResponse.success()

@router.post("/filter-rule-sets/{set_id}/rules/{rule_id}")
def add_rule_to_set(set_id: int, rule_id: int):
    """向规则集合中添加规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 检查规则集合和规则是否存在
        cursor.execute("SELECT id FROM filter_rule_sets WHERE id=?", (set_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Rule set not found", code=404)
        
        cursor.execute("SELECT id FROM filter_rules WHERE id=?", (rule_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Rule not found", code=404)
        
        # 检查规则是否已经在集合中
        cursor.execute(
            "SELECT 1 FROM filter_rule_set_mappings WHERE rule_set_id=? AND rule_id=?",
            (set_id, rule_id)
        )
        if cursor.fetchone():
            return BaseResponse.error(message="Rule already exists in set", code=400)
        
        # 添加关联关系
        cursor.execute(
            "INSERT INTO filter_rule_set_mappings (rule_set_id, rule_id) VALUES (?, ?)",
            (set_id, rule_id)
        )
        conn.commit()
        return BaseResponse.success()

@router.delete("/filter-rule-sets/{set_id}/rules/{rule_id}")
def remove_rule_from_set(set_id: int, rule_id: int):
    """从规则集合中移除规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM filter_rule_set_mappings WHERE rule_set_id=? AND rule_id=?",
            (set_id, rule_id)
        )
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Rule not found in set", code=404)
        conn.commit()
        return BaseResponse.success()

@router.delete("/filter-rule-sets/{parent_set_id}/rule-sets/{child_set_id}")
def remove_child_set(parent_set_id: int, child_set_id: int):
    """从规则集合中移除子规则集合"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM filter_rule_set_children 
            WHERE parent_set_id=? AND child_set_id=?
            """,
            (parent_set_id, child_set_id)
        )
        if cursor.rowcount == 0:
            return BaseResponse.error(message="RuleSet not found", code=404)
        conn.commit()
        return BaseResponse.success()

@router.post("/filter-rule-sets/{set_id}/generate-m3u")
async def generate_m3u_file(
    set_id: int,
    sort_by: str = 'display_name',
    group_order: List[str] = []
):
    """根据规则集合生成M3U文件"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 获取规则集合
        cursor.execute("SELECT id, name, enabled, logic_type FROM filter_rule_sets WHERE id = ?", (set_id,))
        rule_set = cursor.fetchone()
        if not rule_set:
            return BaseResponse.error(message="规则集合不存在", code=404)
        
        if not rule_set[2]:  # enabled
            raise HTTPException(status_code=400, detail="Rule set is disabled")
        
        # 获取所有频道
        # 修改获取频道的SQL查询，添加download_speed字段
        cursor.execute("""
            SELECT
                stream_tracks.id,
                stream_tracks.name as display_name,
                stream_tracks.url as stream_url,
                stream_tracks.group_title,
                stream_tracks.catchup,
                stream_tracks.catchup_source,
                stream_tracks.download_speed,
                epg_channels.channel_id,
                epg_channels.language,
                epg_channels.category,
                COALESCE(
                    epg_channels.local_logo_path,
                    epg_channels.logo_url,
                    (SELECT local_logo_path FROM default_channel_logos 
                    WHERE channel_name = stream_tracks.name 
                    ORDER BY priority DESC LIMIT 1),
                    (SELECT logo_url FROM default_channel_logos 
                    WHERE channel_name = stream_tracks.name 
                    ORDER BY priority DESC LIMIT 1)
                ) as logo_url,
                epg_sources.name AS source_name,
                epg_sources.id AS source_id
            FROM stream_tracks
            LEFT JOIN epg_channels ON stream_tracks.name = epg_channels.display_name
            LEFT JOIN epg_sources ON epg_channels.source_id = epg_sources.id
            WHERE stream_tracks.test_status = 1
        """)
        columns = [description[0] for description in cursor.description]
        channels = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # 获取规则树
        rule_tree = RuleTree()
        rule_tree.build_from_rule_set(set_id, conn)


        # 使用规则树过滤频道
        filtered_channels = rule_tree.filter_channels(channels)

        # 按分组和频道名称对频道进行分组
        grouped_channels = {}
        for channel in filtered_channels:
            group = channel.get('group_title', 'Unknown')
            name = channel.get('display_name', '')
            key = (group, name)  # 使用分组和名称的元组作为键
            if key not in grouped_channels:
                grouped_channels[key] = []
            grouped_channels[key].append(channel)

        # 对每个分组下的同名频道按download_speed排序并只保留前2个
        final_channels = []
        for (group, name), channels in grouped_channels.items():
            sorted_channels = sorted(
                channels, 
                key=lambda x: float(x.get('download_speed', 0) or 0), 
                reverse=True
            )
            final_channels.extend(sorted_channels[:2])


        # 使用规则集合名称作为文件名
        filename = f"{rule_set[1]}"
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        # 获取排序模板
        cursor.execute("""
            SELECT name, group_orders
            FROM sort_templates
        """)
        sort_templates_raw = cursor.fetchall()
        sort_templates = {}

        for template_name, group_orders in sort_templates_raw:
            try:
                # 解析JSON格式的group_orders
                orders = json.loads(group_orders)
                # 合并到sort_templates中
                for group_name, channels in orders.items():
                    if group_name not in sort_templates:
                        sort_templates[group_name] = []
                    sort_templates[group_name].extend(channels)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in sort template: {template_name}")
                continue
        
        # 使用M3UGenerator生成m3u文件
        header_info = {
            "generated_at": datetime.now().isoformat(),
            "provider": "M3U Filter"
        }

        generator = M3UGenerator()
        m3u_content, filename = generator.generate_m3u(
            final_channels,
            [filename], 
            header_info,
            sort_by=sort_by,
            group_order=group_order,
            sort_templates=sort_templates  # 使用合并后的排序模板
        )
        
        # 保存到m3u文件夹
        m3u_dir = Path(RESOURCE_ROOT) / 'm3u'
        # 确保静态文件目录存在
        if not m3u_dir.exists():
            m3u_dir.mkdir(parents=True)

        file_path = m3u_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        return BaseResponse.success({"url_path": f"/m3u/{filename}"})

@router.post("/filter-rule-sets/{set_id}/generate-txt")
async def generate_txt_file(
    set_id: int,
    sort_by: str = 'display_name',
    group_order: List[str] = []
):
    """根据规则集合生成TXT风格文件"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 获取规则集合
        cursor.execute("SELECT id, name, enabled, logic_type FROM filter_rule_sets WHERE id = ?", (set_id,))
        rule_set = cursor.fetchone()
        if not rule_set:
            return BaseResponse.error(message="规则集合不存在", code=404)
        
        if not rule_set[2]:  # enabled
            raise HTTPException(status_code=400, detail="Rule set is disabled")
        
        # 获取所有频道
        # 修改获取频道的SQL查询，添加download_speed字段
        cursor.execute("""
            SELECT
                stream_tracks.id,
                stream_tracks.name as display_name,
                stream_tracks.url as stream_url,
                stream_tracks.group_title,
                stream_tracks.catchup,
                stream_tracks.catchup_source,
                stream_tracks.download_speed,
                epg_channels.channel_id,
                epg_channels.language,
                epg_channels.category,
                COALESCE(
                    epg_channels.local_logo_path,
                    epg_channels.logo_url,
                    (SELECT local_logo_path FROM default_channel_logos 
                    WHERE channel_name = stream_tracks.name 
                    ORDER BY priority DESC LIMIT 1),
                    (SELECT logo_url FROM default_channel_logos 
                    WHERE channel_name = stream_tracks.name 
                    ORDER BY priority DESC LIMIT 1)
                ) as logo_url,
                epg_sources.name AS source_name,
                epg_sources.id AS source_id
            FROM stream_tracks
            LEFT JOIN epg_channels ON stream_tracks.name = epg_channels.display_name
            LEFT JOIN epg_sources ON epg_channels.source_id = epg_sources.id
            WHERE stream_tracks.test_status = 1
        """)
        columns = [description[0] for description in cursor.description]
        channels = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # 获取规则树
        rule_tree = RuleTree()
        rule_tree.build_from_rule_set(set_id, conn)


        # 使用规则树过滤频道
        filtered_channels = rule_tree.filter_channels(channels)

        # 按分组和频道名称对频道进行分组
        grouped_channels = {}
        for channel in filtered_channels:
            group = channel.get('group_title', 'Unknown')
            name = channel.get('display_name', '')
            key = (group, name)  # 使用分组和名称的元组作为键
            if key not in grouped_channels:
                grouped_channels[key] = []
            grouped_channels[key].append(channel)

        # 对每个分组下的同名频道按download_speed排序并只保留前2个
        final_channels = []
        for (group, name), channels in grouped_channels.items():
            sorted_channels = sorted(
                channels, 
                key=lambda x: float(x.get('download_speed', 0) or 0), 
                reverse=True
            )
            final_channels.extend(sorted_channels[:2])


        # 使用规则集合名称作为文件名
        filename = f"{rule_set[1]}"
        filename = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        # 获取排序模板
        cursor.execute("""
            SELECT name, group_orders
            FROM sort_templates
        """)
        sort_templates_raw = cursor.fetchall()
        sort_templates = {}

        for template_name, group_orders in sort_templates_raw:
            try:
                # 解析JSON格式的group_orders
                orders = json.loads(group_orders)
                # 合并到sort_templates中
                for group_name, channels in orders.items():
                    if group_name not in sort_templates:
                        sort_templates[group_name] = []
                    sort_templates[group_name].extend(channels)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in sort template: {template_name}")
                continue
        
        # 使用M3UGenerator生成TXT文件
        generator = M3UGenerator()
        txt_content, filename = generator.generate_txt(final_channels, [filename], sort_by, group_order, sort_templates)
        
        # 保存到m3u文件夹
        m3u_dir = Path(RESOURCE_ROOT) / 'm3u'
        if not m3u_dir.exists():
            m3u_dir.mkdir(parents=True)

        file_path = m3u_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return BaseResponse.success({"url_path": f"/m3u/{filename}"})