from fastapi import APIRouter, HTTPException
from typing import List
import json

from database import get_db_connection
from models.sort_templates import SortTemplate
from models.common import BaseResponse

router = APIRouter(prefix="/sort-templates", tags=["sort_templates"])

@router.get("")
def get_sort_templates():
    """获取所有排序模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, group_orders FROM sort_templates")
        columns = [column[0] for column in cursor.description]
        templates = []
        for row in cursor.fetchall():
            template = dict(zip(columns, row))
            template['group_orders'] = json.loads(template['group_orders'])
            templates.append(template)
        return BaseResponse.success(data=templates)

@router.get("/{template_id}")
def get_sort_template(template_id: int):
    """获取指定排序模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, group_orders FROM sort_templates WHERE id = ?", (template_id,))
        template = cursor.fetchone()
        if not template:
            return BaseResponse.error(message="Sort template not found", code=404)
        columns = [column[0] for column in cursor.description]
        template_dict = dict(zip(columns, template))
        template_dict['group_orders'] = json.loads(template_dict['group_orders'])
        return BaseResponse.success(data=template_dict)

@router.post("")
def create_sort_template(template: SortTemplate):
    """创建排序模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sort_templates (name, description, group_orders) VALUES (?, ?, ?)",
            (template.name, template.description, json.dumps(template.group_orders))
        )
        template_id = cursor.lastrowid
        conn.commit()
        return BaseResponse.success(data={"id": template_id})

@router.put("/{template_id}")
def update_sort_template(template_id: int, template: SortTemplate):
    """更新排序模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sort_templates WHERE id = ?", (template_id,))
        if not cursor.fetchone():
            return BaseResponse.error(message="Sort template not found", code=404)
        
        cursor.execute(
            "UPDATE sort_templates SET name = ?, description = ?, group_orders = ? WHERE id = ?",
            (template.name, template.description, json.dumps(template.group_orders), template_id)
        )
        conn.commit()
        return BaseResponse.success()

@router.delete("/{template_id}")
def delete_sort_template(template_id: int):
    """删除排序模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sort_templates WHERE id = ?", (template_id,))
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Sort template not found", code=404)
        conn.commit()
        return BaseResponse.success(message="Sort template deleted successfully")