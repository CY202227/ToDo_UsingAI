# Todo 后端项目

## 项目简介

这是一个使用 FastAPI 构建的 Todo 后端项目，提供了基本的任务管理功能。

## 技术栈

- **FastAPI**: 用于构建 API
- **SQLAlchemy**: 用于数据库操作
- **Pydantic**: 用于数据验证
- **Uvicorn**: 用于运行 ASGI 应用

## 安装与运行

1. 克隆仓库：
   ```bash
   git clone https://github.com/your-repo/todo-backend.git
   ```
2. 进入项目目录：
   ```bash
   cd todo-backend
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 运行项目：
   ```bash
   uvicorn main:app --reload
   ```

## 环境变量

项目使用 `.env` 文件来管理环境变量，请参考 `.env.example` 文件进行配置。

## 贡献

欢迎提交 Pull Request 或 Issue 来改进项目。
