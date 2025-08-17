from fastapi import APIRouter
from app.schema.admin_user import AdminUser
from fastapi.responses import JSONResponse 


admin_router = APIRouter()

@admin_router.get("/admin")
async def admin_portal(AdminUser: AdminUser):
    admin_user = AdminUser.username
    return {"message": f"Welcome to the admin portal, {admin_user}!"}
