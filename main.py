from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import health, products, orders, inventory, reports,categories

app = FastAPI(title = "SSP POS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origin.split(",")],
    allow_credentials = True,
    allow_methods = ["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers = ["Authorization", "Content-Type"]
)

app.include_router(health.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(products.router)
app.include_router(reports.router)
app.include_router(categories.router)