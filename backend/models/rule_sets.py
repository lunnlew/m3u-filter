from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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