from fastapi import APIRouter
from pathlib import Path
from database import get_db_connection
from models import BaseResponse
from m3u_generator import M3UGenerator
from models import FilterRule
import logging
logger = logging.getLogger(__name__)
from config import RESOURCE_ROOT

router = APIRouter()


def _row_to_filter_rule(row) -> FilterRule:
    """将数据库行转换为FilterRule对象"""
    return FilterRule(
        id=row[0],
        name=row[1],
        type=row[2],
        pattern=row[3],
        action=row[4],
        priority=row[5],
        enabled=bool(row[6]),
        case_sensitive=bool(row[7]),
        regex_mode=bool(row[8]),
        min_value=row[9],
        max_value=row[10]
    )

@router.get("/filter-rules")
def get_filter_rules():
    """获取所有过滤规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM filter_rules")
        rules = cursor.fetchall()
        return BaseResponse.success(data=[_row_to_filter_rule(rule) for rule in rules])

@router.post("/filter-rules")
def create_filter_rule(rule: FilterRule):
    """创建新的过滤规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO filter_rules (name, type, pattern, action, priority, enabled, case_sensitive, regex_mode, min_value, max_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (rule.name, rule.type, rule.pattern, rule.action, rule.priority, rule.enabled, rule.case_sensitive, rule.regex_mode, rule.min_value, rule.max_value)
        )
        conn.commit()
        rule_id = cursor.lastrowid
        rule_dict = rule.__dict__.copy()
        rule_dict.pop('id', None)
        return BaseResponse.success(data=FilterRule(id=rule_id, **rule_dict))

@router.put("/filter-rules/{rule_id}")
def update_filter_rule(rule_id: int, rule: FilterRule):
    """更新过滤规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE filter_rules SET name=?, type=?, pattern=?, action=?, priority=?, enabled=?, case_sensitive=?, regex_mode=?, min_value=?, max_value=? WHERE id=?",
            (rule.name, rule.type, rule.pattern, rule.action, rule.priority, rule.enabled, rule.case_sensitive, rule.regex_mode, rule.min_value, rule.max_value, rule_id)
        )
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Rule not found", code=404)
        conn.commit()
        rule_dict = rule.__dict__.copy()
        rule_dict.pop('id', None)
        return BaseResponse.success(data=FilterRule(id=rule_id, **rule_dict))

@router.delete("/filter-rules/{rule_id}")
def delete_filter_rule(rule_id: int):
    """删除过滤规则"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filter_rules WHERE id=?", (rule_id,))
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Rule not found", code=404)
        conn.commit()
        return BaseResponse.success(message="Rule deleted successfully")

@router.post("/filter-rules/apply")
def apply_filter_rules():
    """应用过滤规则到频道列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 获取所有启用的规则
        cursor.execute("SELECT * FROM filter_rules WHERE enabled = 1 ORDER BY priority DESC")
        rules = [_row_to_filter_rule(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT
                stream_tracks.id,
                stream_tracks.name as display_name,
                stream_tracks.url as stream_url,
                stream_tracks.group_title,
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
    
    # 依次应用每个规则进行过滤
    filtered_channels = channels
    for rule in rules:
        if rule.action == "include":
            filtered_channels = [ch for ch in filtered_channels if _match_rule(rule, ch)]
        elif rule.action == "exclude":
            filtered_channels = [ch for ch in filtered_channels if not _match_rule(rule, ch)]

    return {"channels": filtered_channels}

def _match_rule(rule: FilterRule, channel: dict) -> bool:
    """检查频道是否匹配规则"""
    if not rule.enabled:
        return False

    value = channel.get(rule.type)
    if value is None:
        return False

    if rule.type in ['min_value', 'max_value']:
        try:
            value = float(value)
            if rule.type == 'min_value' and value < rule.min_value:
                return False
            if rule.type == 'max_value' and value > rule.max_value:
                return False
            return True
        except (ValueError, TypeError):
            return False

    pattern = rule.pattern
    if not rule.case_sensitive:
        value = str(value).lower()
        pattern = pattern.lower()

    if rule.regex_mode:
        import re
        try:
            return bool(re.search(pattern, str(value)))
        except re.error:
            return False
    else:
        return pattern in str(value)

@router.post("/filter-rules/generate-m3u")
def generate_m3u_file():
    """生成过滤后的M3U文件"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 获取所有启用的规则
        cursor.execute("SELECT * FROM filter_rules WHERE enabled = 1 ORDER BY priority DESC")
        rules = [_row_to_filter_rule(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT
                stream_tracks.id,
                stream_tracks.name as display_name,
                stream_tracks.url as stream_url,
                stream_tracks.group_title,
                stream_tracks.catchup,
                stream_tracks.catchup_source,
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
        
        # 依次应用每个规则进行过滤
        filtered_channels = channels
        for rule in rules:
            if rule.action == "include":
                filtered_channels = [ch for ch in filtered_channels if _match_rule(rule, ch)]
            elif rule.action == "exclude":
                filtered_channels = [ch for ch in filtered_channels if not _match_rule(rule, ch)]
    
    # 使用M3UGenerator生成M3U文件
    generator = M3UGenerator()
    m3u_content, filename = generator.generate_m3u(filtered_channels, rule_names=[rule.name for rule in rules])
    
    # 保存到m3u文件夹
    m3u_dir = Path(RESOURCE_ROOT) / 'm3u'
    # 确保静态文件目录存在
    if not m3u_dir.exists():
        m3u_dir.mkdir(parents=True)

    file_path = m3u_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    return BaseResponse.success({"url_path": f"/m3u/{filename}"})