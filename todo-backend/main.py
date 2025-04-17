from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import todo, auth
from database.database import engine
from models.todo import Base as TodoBase
from models.user import Base as UserBase

# 创建 FastAPI 应用
app = FastAPI(title="Todo API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # 预检请求的缓存时间
)

# 创建数据库表
TodoBase.metadata.create_all(bind=engine)
UserBase.metadata.create_all(bind=engine)

# 包含路由
app.include_router(auth.router)
app.include_router(todo.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)