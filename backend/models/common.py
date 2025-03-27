from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any, Dict, List
from database import get_db_connection
from .rules import FilterRule, FilterRuleSet

class ProxyConfig(BaseModel):
    enabled: bool = False
    proxy_type: str = 'http'  # 'http' or 'socks5'
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

T = TypeVar('T')

class BaseResponse(Generic[T]):
    """统一的API响应模型"""
    def __init__(self, data: Optional[T] = None, message: str = "", code: int = 200):
        self.data = data
        self.message = message
        self.code = code

    def dict(self) -> Dict:
        return {
            "data": self.data,
            "message": self.message,
            "code": self.code
        }

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "操作成功") -> Dict:
        return cls(data=data, message=message, code=200).dict()

    @classmethod
    def error(cls, message: str = "操作失败", code: int = 400) -> Dict:
        return cls(data=None, message=message, code=code).dict()

def get_rules_for_set(cursor, set_id: int) -> List[dict]:
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

def row_to_filter_rule(row) -> FilterRule:
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
        min_value=row[9] if len(row) > 9 else None,
        max_value=row[10] if len(row) > 10 else None
    )

def validate_rule_set_name(cursor, name: str, set_id: Optional[int] = None) -> bool:
    """验证规则集合名称是否重复"""
    if set_id:
        cursor.execute("SELECT id FROM filter_rule_sets WHERE name = ? AND id != ?", (name, set_id))
    else:
        cursor.execute("SELECT id FROM filter_rule_sets WHERE name = ?", (name,))
    return cursor.fetchone() is None

def update_rule_set_children(cursor, set_id: int, children: List[int]):
    """更新规则集合的子规则集合关系"""
    # 获取现有子规则集合
    cursor.execute("SELECT child_set_id FROM filter_rule_set_children WHERE parent_set_id=?", (set_id,))
    existing_children = set(row[0] for row in cursor.fetchall())
    new_children = set(children)
    
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