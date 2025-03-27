from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional, Dict, List

Base = declarative_base()

class SortTemplate(BaseModel):
    id: Optional[int] = None
    name: str  # 模板名称
    description: Optional[str] = None  # 模板描述
    group_orders: Dict[str, List[str]]  # 分组下的频道排序配置，格式：{"分组名": ["频道1", "频道2", ...]}

class SortTemplateModel(Base):
    __tablename__ = 'sort_templates'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # 模板名称
    description = Column(String, nullable=True)  # 模板描述
    group_orders = Column(JSON)  # 分组下的频道排序配置，格式：{"分组名": ["频道1", "频道2", ...]}