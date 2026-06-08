from fastapi import APIRouter

from app.api.routes import admin, auth
from app.api.routes.resources import orders_router, products_router, stores_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(stores_router)
