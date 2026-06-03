from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    status: str = "success"
    message: Optional[str] = "Operation successful"
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    code: Optional[str] = None
    errors: Optional[Any] = None

class TimestampsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
