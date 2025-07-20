from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from databases import Database
from sqlalchemy import Table, Column, String, MetaData
import os
from dotenv import load_dotenv

# -------------------- Database Setup -------------------- #
# Please open your pgAdmin and RESTORE the file Logindatabase into your pgAdmin database
# Default database name is Logindatabase and password is password

load_dotenv()
DATABASE_URL = os.getenv(
    "LOGIN_DATABASE_URL",
    "postgresql://postgres:password@localhost/Logindatabase",
)
database = Database(DATABASE_URL)
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("username", String, primary_key=True),
    Column("password", String, nullable=False),
    Column("role", String, nullable=False),
)

# -------------------- FastAPI App -------------------- #

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

security = HTTPBearer()

# -------------------- Pydantic Models -------------------- #

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str

# -------------------- Auth Dependencies -------------------- #

async def auth_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    query = users.select().where(users.c.username == token)
    user = await database.fetch_one(query)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"username": user["username"], "role": user["role"]}

async def manager_dependency(user_info: dict = Depends(auth_dependency)):
    if user_info.get("role") != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return user_info

# -------------------- Routes -------------------- #

@app.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    query = users.select().where(users.c.username == data.username)
    user = await database.fetch_one(query)

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"token": user["username"], "role": user["role"]}

@app.get("/public")
async def public_endpoint():
    return {"message": "Public endpoint - no auth required"}

@app.get("/employee")
async def protected_endpoint(user_info: dict = Depends(auth_dependency)):
    return {
        "message": "Protected endpoint",
        "user": user_info["username"],
        "role": user_info["role"]
    }

@app.get("/manager")
async def manager_endpoint(user_info: dict = Depends(manager_dependency)):
    return {
        "message": "Manager-only endpoint",
        "user": user_info["username"],
        "role": user_info["role"]
    }
