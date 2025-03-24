from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FilterRule(BaseModel):
    id: Optional[int] = None
    name: str
    type: str  # 匹配类型：name, keyword, resolution, group, bitrate, source_name
    pattern: str  # 匹配模式
    action: str  # 动作：include或exclude
    priority: int = 0  # 优先级
    enabled: bool = True  # 是否启用
    case_sensitive: bool = False  # 是否区分大小写
    regex_mode: bool = False  # 是否使用正则表达式
    min_value: Optional[int] = None
    max_value: Optional[int] = None

class FilterRuleModel(Base):
    __tablename__ = 'filter_rules'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # 匹配类型：name, keyword, resolution, group, bitrate, source_name
    pattern = Column(String)  # 匹配模式
    action = Column(String)  # 动作：include或exclude
    priority = Column(Integer, default=0)  # 优先级
    enabled = Column(Boolean, default=True)  # 是否启用
    case_sensitive = Column(Boolean, default=False)  # 是否区分大小写
    regex_mode = Column(Boolean, default=False)  # 是否使用正则表达式

class FilterRuleSet(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    enabled: bool = True
    logic_type: str = 'AND'
    rules: Optional[List[FilterRule]] = None
    children: Optional[List[int]] = None
    sync_interval: int = 6  # 同步间隔（小时）

class FilterRuleSetModel(Base):
    __tablename__ = 'filter_rule_sets'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # 规则集合名称
    description = Column(String, nullable=True)  # 规则集合描述
    enabled = Column(Boolean, default=True)  # 是否启用
    logic_type = Column(String, default='AND')  # 逻辑运算类型：AND/OR

class FilterRuleSetChildren(Base):
    __tablename__ = 'filter_rule_set_children'

    id = Column(Integer, primary_key=True, index=True)
    parent_set_id = Column(Integer)  # 父规则集合ID
    child_set_id = Column(Integer)  # 子规则集合ID

class FilterRuleSetMapping(Base):
    __tablename__ = 'filter_rule_set_mappings'

    id = Column(Integer, primary_key=True, index=True)
    rule_set_id = Column(Integer)  # 规则集合ID
    rule_id = Column(Integer)  # 规则ID