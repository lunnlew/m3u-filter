from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any, Dict

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