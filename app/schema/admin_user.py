from pydantic import BaseModel

class AdminUser(BaseModel):
    username: str
    is_active: bool = True
    is_superuser: bool = True
    full_name: str | None = None