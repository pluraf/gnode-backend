from pydantic import BaseModel
from typing import Optional


class AuthbundleListResponse(BaseModel):
    authbundle_id: str
    connector_type: str
    auth_type: str
    description: Optional[str] = ""
