from pydantic import BaseModel


class AuthbundleListResponse(BaseModel):
    authbundle_id: str
    connector_type: str
    auth_type: str
    description: str
