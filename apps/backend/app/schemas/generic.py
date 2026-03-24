from typing import Any
from pydantic import BaseModel


class JSONResponse(BaseModel):
    status: int
    message: Any
    data: Any = None
