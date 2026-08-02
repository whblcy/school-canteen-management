"""
Result 类型 - 操作结果封装
用于服务层向 UI 层返回结构化结果，替代 (bool, str) 元组
"""
from dataclasses import dataclass
from typing import Any, TypeVar, Generic, Optional

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """操作结果封装"""
    success: bool
    message: str = ""
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: T = None, message: str = "操作成功") -> "Result[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, data: T = None) -> "Result[T]":
        return cls(success=False, message=message, data=data)

    def is_ok(self) -> bool:
        return self.success

    def __bool__(self):
        return self.success
