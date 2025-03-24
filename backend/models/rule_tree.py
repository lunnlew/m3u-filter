from typing import List, Dict, Optional, Union, Any
from .rules import FilterRule

class RuleNode:
    """规则树节点，可以是单个规则或规则集合"""
    def __init__(self, logic_type: str = 'AND'):
        self.logic_type = logic_type  # 'AND' 或 'OR'
        self.rules: List[FilterRule] = []  # 单个规则列表
        self.children: List['RuleNode'] = []  # 子节点（规则集合）列表
    
    def add_rule(self, rule: FilterRule):
        """添加单个规则"""
        self.rules.append(rule)
    
    def add_child(self, child: 'RuleNode'):
        """添加子节点（规则集合）"""
        self.children.append(child)
    
    def evaluate(self, channel: Dict[str, Any]) -> bool:
        """评估当前节点对频道的匹配结果"""
        # 如果没有规则和子节点，默认返回True
        if not self.rules and not self.children:
            return True

        # 评估所有规则
        rule_results = [self._evaluate_rule(rule, channel) for rule in self.rules]
        
        # 评估所有子节点
        child_results = [child.evaluate(channel) for child in self.children]
        
        # 合并所有结果
        all_results = rule_results + child_results

        # 如果没有结果，返回True
        if not all_results:
            return True
        
        # 根据逻辑类型合并结果
        if self.logic_type == 'AND':
            return all(all_results)
        else:  # 'OR'
            return any(all_results)
    
    def _evaluate_rule(self, rule: FilterRule, channel: Dict[str, Any]) -> bool:
        """评估单个规则对频道的匹配结果"""
        # 根据规则类型进行匹配
        field = None
        value = None

        if rule.type == 'name':
            field = 'display_name'
        elif rule.type == 'group':
            field = 'group_title'
        elif rule.type == 'source_name':
            field = 'source_name'
        elif rule.type == 'resolution':
            field = 'resolution'
        elif rule.type == 'bitrate':
            field = 'bitrate'
        elif rule.type == 'keyword':
            # 关键字可以匹配多个字段
            fields = ['display_name', 'group_title', 'source_name', 'stream_url']
            for f in fields:
                if f in channel and self._match_pattern(rule, channel.get(f, '')):
                    return rule.action == 'include'
            return rule.action != 'include'
        
        if field and field in channel:
            value = channel[field]
            if self._match_pattern(rule, value):
                return rule.action == 'include'
        
        return rule.action != 'include'

    def _match_pattern(self, rule: FilterRule, value) -> bool:
        """根据规则的模式匹配值"""
        if value is None:
            return False
        
        # 转换为字符串进行匹配
        str_value = str(value)
        pattern = rule.pattern
        
        # 处理大小写敏感
        if not rule.case_sensitive:
            str_value = str_value.lower()
            pattern = pattern.lower()
        
        # 处理分辨率匹配
        if rule.type == 'resolution':
            resolution_options = ['4k', '2k', '1080p', '720p', '576p', '480p']
            # 确保值在选项列表中
            return str_value.lower() in resolution_options and str_value.lower() == pattern.lower()
        elif rule.type == 'bitrate' and hasattr(rule, 'min_value') and hasattr(rule, 'max_value'):
            try:
                num_value = float(str_value)
                if rule.min_value is not None and num_value < rule.min_value:
                    return False
                if rule.max_value is not None and num_value > rule.max_value:
                    return False
                return True
            except (ValueError, TypeError):
                return False
        
        # 处理正则表达式匹配
        if rule.regex_mode:
            import re
            try:
                return bool(re.search(pattern, str_value))
            except re.error:
                return False
        
        # 普通字符串匹配
        return pattern in str_value

class RuleTree:
    """规则树，用于管理和评估规则"""
    def __init__(self):
        self.root = RuleNode(logic_type='AND')  # 根节点默认使用AND逻辑
    
    def build_from_rule_set(self, rule_set_id: int, conn):
        """从数据库中的规则集合构建规则树"""
        cursor = conn.cursor()
        # 递归构建规则树
        self.root = self._build_node_from_rule_set(rule_set_id, cursor)
    
    def _build_node_from_rule_set(self, rule_set_id: int, cursor) -> RuleNode:
        """从规则集合ID构建节点"""
        # 获取规则集合信息
        cursor.execute(
            "SELECT id, name, enabled, logic_type FROM filter_rule_sets WHERE id = ?", 
            (rule_set_id,)
        )
        rule_set = cursor.fetchone()
        if not rule_set or not rule_set[2]:  # 如果规则集合不存在或未启用
            return RuleNode()
        
        # 创建节点
        node = RuleNode(logic_type=rule_set[3] or 'AND')
        
        # 添加规则
        cursor.execute("""
            SELECT fr.* 
            FROM filter_rules fr
            INNER JOIN filter_rule_set_mappings frsm ON fr.id = frsm.rule_id
            WHERE frsm.rule_set_id = ? AND fr.enabled = 1
        """, (rule_set_id,))
        rules = cursor.fetchall()
        for rule in rules:
            # 假设有一个函数可以将数据库行转换为FilterRule对象
            filter_rule = self._row_to_filter_rule(rule)
            node.add_rule(filter_rule)
        
        # 添加子规则集合
        cursor.execute("""
            SELECT child_set_id 
            FROM filter_rule_set_children 
            WHERE parent_set_id = ?
        """, (rule_set_id,))
        child_ids = [row[0] for row in cursor.fetchall()]
        for child_id in child_ids:
            child_node = self._build_node_from_rule_set(child_id, cursor)
            node.add_child(child_node)
        
        return node
    
    def _row_to_filter_rule(self, row) -> FilterRule:
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
    
    def filter_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用规则树过滤频道列表"""
        return [channel for channel in channels if self.root.evaluate(channel)]