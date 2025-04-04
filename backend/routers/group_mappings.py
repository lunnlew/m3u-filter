from fastapi import APIRouter, HTTPException
from typing import List, Optional, Union, Dict
from database import get_db_connection
from models import BaseResponse
from pydantic import BaseModel
import time
from sqlite3 import OperationalError


router = APIRouter()

class GroupMapping(BaseModel):
    channel_name: str
    custom_group: str
    rule_set_id: Optional[int] = None

class GroupMappingTemplate(BaseModel):
    name: str
    description: Optional[str] = None
    mappings: Union[List[GroupMapping], Dict[str, str]]

@router.get("/group-mappings")
def get_group_mappings(rule_set_id: Optional[int] = None):
    """获取分组映射列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT channel_name, custom_group, rule_set_id FROM group_mappings"
        params = []
        
        if rule_set_id is not None:
            query += " WHERE rule_set_id = ?"
            params.append(rule_set_id)
        
        cursor.execute(query, params)
        mappings = [{
            "channel_name": row[0],
            "custom_group": row[1],
            "rule_set_id": row[2]
        } for row in cursor.fetchall()]
        
        return BaseResponse.success(data=mappings)

@router.post("/group-mappings")
def create_group_mapping(mapping: GroupMapping):
    """创建分组映射"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO group_mappings (channel_name, custom_group, rule_set_id) VALUES (?, ?, ?)",
            (mapping.channel_name, mapping.custom_group, mapping.rule_set_id)
        )
        
        conn.commit()
        return BaseResponse.success()

@router.put("/group-mappings/{channel_name}")
def update_group_mapping(channel_name: str, mapping: GroupMapping):
    """更新分组映射"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE group_mappings SET custom_group = ?, rule_set_id = ? WHERE channel_name = ?",
            (mapping.custom_group, mapping.rule_set_id, channel_name)
        )
        
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Mapping not found", code=404)
        
        conn.commit()
        return BaseResponse.success()
@router.delete("/group-mappings/{channel_name}")
def delete_group_mapping(channel_name: str, rule_set_id: Optional[int] = None):
    """删除分组映射"""
    max_retries = 3
    retry_delay = 0.5  # 500ms
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as conn:
                # 设置超时时间为5秒
                conn.execute("PRAGMA busy_timeout = 5000")
                cursor = conn.cursor()
        
                query = "DELETE FROM group_mappings WHERE channel_name = ?"
                params = [channel_name]
                
                if rule_set_id is not None:
                    query += " AND rule_set_id = ?"
                    params.append(rule_set_id)
                
                cursor.execute(query, params)
                
                if cursor.rowcount == 0:
                    return BaseResponse.error(message="Mapping not found", code=404)
                
                conn.commit()
                return BaseResponse.success()
            
        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return BaseResponse.error(message="Database is busy, please try again later", code=503)
        except Exception as e:
            return BaseResponse.error(message=str(e), code=500)

@router.post("/group-mappings/batch")
def batch_create_group_mappings(mappings: List[GroupMapping]):
    """批量创建分组映射"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for mapping in mappings:
            cursor.execute(
                "INSERT INTO group_mappings (channel_name, custom_group, rule_set_id) VALUES (?, ?, ?)",
                (mapping.channel_name, mapping.custom_group, mapping.rule_set_id)
            )
        
        conn.commit()
        return BaseResponse.success()

@router.post("/group-mapping-templates")
def create_group_mapping_template(template: GroupMappingTemplate):
    """创建分组映射模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO group_mapping_templates (name, description) VALUES (?, ?)",
            (template.name, template.description)
        )
        template_id = cursor.lastrowid
        
        # 处理映射数据
        mappings = []
        if isinstance(template.mappings, dict):
            # 如果是字典格式，转换为GroupMapping对象列表
            mappings = [GroupMapping(channel_name=k, custom_group=v) for k, v in template.mappings.items()]
        else:
            # 如果已经是GroupMapping对象列表，直接使用
            mappings = template.mappings
        
        # 保存映射数据
        for mapping in mappings:
            cursor.execute(
                "INSERT INTO group_mapping_template_items (template_id, channel_name, custom_group) VALUES (?, ?, ?)",
                (template_id, mapping.channel_name, mapping.custom_group)
            )
        
        conn.commit()
        return BaseResponse.success(data={"id": template_id})

@router.get("/group-mapping-templates")
def get_group_mapping_templates():
    """获取分组映射模板列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT id, name, description FROM group_mapping_templates"
        
        cursor.execute(query)
        templates = []
        
        for row in cursor.fetchall():
            template_id = row[0]
            template = {
                "id": template_id,
                "name": row[1],
                "description": row[2],
                "mappings": []
            }
            
            cursor.execute(
                "SELECT channel_name, custom_group FROM group_mapping_template_items WHERE template_id = ?",
                (template_id,)
            )
            
            template["mappings"] = [{
                "channel_name": item[0],
                "custom_group": item[1]
            } for item in cursor.fetchall()]
            
            templates.append(template)
        
        return BaseResponse.success(data=templates)

@router.delete("/group-mapping-templates/{template_id}")
def delete_group_mapping_template(template_id: int):
    """删除分组映射模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM group_mapping_template_items WHERE template_id = ?", (template_id,))
        cursor.execute("DELETE FROM group_mapping_templates WHERE id = ?", (template_id,))
        
        if cursor.rowcount == 0:
            return BaseResponse.error(message="Template not found", code=404)
        
        conn.commit()
        return BaseResponse.success()

@router.post("/group-mapping-templates/{template_id}/apply/{rule_set_id}")
def apply_group_mapping_template(template_id: int, rule_set_id: int):
    """应用分组映射模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 获取模板信息
        cursor.execute(
            "SELECT id FROM group_mapping_templates WHERE id = ?",
            (template_id,)
        )
        if not cursor.fetchone():
            return BaseResponse.error(message="Template not found", code=404)
        
        # 获取模板中的映射项
        cursor.execute(
            "SELECT channel_name, custom_group FROM group_mapping_template_items WHERE template_id = ?",
            (template_id,)
        )
        mappings = cursor.fetchall()
        
        # 应用映射
        for channel_name, custom_group in mappings:
            cursor.execute(
                "INSERT OR REPLACE INTO group_mappings (channel_name, custom_group, rule_set_id) VALUES (?, ?, ?)",
                (channel_name, custom_group, rule_set_id)
            )
        
        conn.commit()
        return BaseResponse.success()

@router.put("/group-mapping-templates/{template_id}")
def update_group_mapping_template(template_id: int, template: GroupMappingTemplate):
    """更新分组映射模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查模板是否存在
        cursor.execute(
            "SELECT id FROM group_mapping_templates WHERE id = ?",
            (template_id,)
        )
        if not cursor.fetchone():
            return BaseResponse.error(message="Template not found", code=404)
        
        # 更新模板基本信息
        cursor.execute(
            "UPDATE group_mapping_templates SET name = ?, description = ? WHERE id = ?",
            (template.name, template.description, template_id)
        )
        
        # 删除原有的映射项
        cursor.execute("DELETE FROM group_mapping_template_items WHERE template_id = ?", (template_id,))
        
        # 处理新的映射数据
        mappings = []
        if isinstance(template.mappings, dict):
            # 如果是字典格式，转换为GroupMapping对象列表
            mappings = [GroupMapping(channel_name=k, custom_group=v) for k, v in template.mappings.items()]
        else:
            # 如果已经是GroupMapping对象列表，直接使用
            mappings = template.mappings
        
        # 保存新的映射数据
        for mapping in mappings:
            cursor.execute(
                "INSERT INTO group_mapping_template_items (template_id, channel_name, custom_group) VALUES (?, ?, ?)",
                (template_id, mapping.channel_name, mapping.custom_group)
            )
        
        conn.commit()
        return BaseResponse.success()

class BatchApplyTemplatesRequest(BaseModel):
    template_ids: List[int]

@router.post("/group-mapping-templates/batch-apply/{rule_set_id}")
def batch_apply_group_mapping_templates(rule_set_id: int, request: BatchApplyTemplatesRequest):
    """批量应用多个分组映射模板"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 验证所有模板是否存在
        template_ids_str = ','.join('?' * len(request.template_ids))
        cursor.execute(
            f"SELECT COUNT(*) FROM group_mapping_templates WHERE id IN ({template_ids_str})",
            request.template_ids
        )
        if cursor.fetchone()[0] != len(request.template_ids):
            return BaseResponse.error(message="Some templates not found", code=404)
        
        # 按照模板ID的顺序获取并应用映射
        for template_id in request.template_ids:
            cursor.execute(
                "SELECT channel_name, custom_group FROM group_mapping_template_items WHERE template_id = ?",
                (template_id,)
            )
            mappings = cursor.fetchall()
            
            # 应用映射
            for channel_name, custom_group in mappings:
                cursor.execute(
                    "INSERT OR REPLACE INTO group_mappings (channel_name, custom_group, rule_set_id) VALUES (?, ?, ?)",
                    (channel_name, custom_group, rule_set_id)
                )
        
        conn.commit()
        return BaseResponse.success()