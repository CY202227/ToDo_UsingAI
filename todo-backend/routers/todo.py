from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from models.todo import TodoModel
from models.user import User
from schemas.todo import Todo, TodoCreate, TodoUpdate, TodoAnalysis, TodoResponse, TodoStep
from auth.utils import get_current_user
from services.ai_service import generate_todo_suggestions
from services.ml_service import ml_service
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

def train_ml_model(db: Session, user_id: int):
    """后台训练机器学习模型"""
    todos = db.query(TodoModel).filter(
        TodoModel.user_id == user_id,
        TodoModel.completed == True
    ).all()
    if todos:
        ml_service.train_model(todos)

@router.get("/", response_model=List[Todo])
async def get_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: str = None,
    priority: str = None
):
    query = db.query(TodoModel).filter(TodoModel.user_id == current_user.id)
    
    if category:
        query = query.filter(TodoModel.category == category)
    if priority:
        query = query.filter(TodoModel.priority == priority)
        
    return query.all()

@router.post("/", response_model=TodoResponse)
async def create_todo(
    todo: TodoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新的待办事项，包含AI分析"""
    logger.info(f"收到待办事项创建请求: text={todo.text}, user={current_user.username}")
    
    try:
        # 生成AI建议
        analysis = generate_todo_suggestions(todo.text, todo.due_date)
        logger.info(f"AI分析完成: category={analysis.get('category')}, priority={analysis.get('priority')}")
        
        # 创建新的todo记录
        db_todo = TodoModel(
            text=todo.text,
            user_id=current_user.id,
            category=todo.category or analysis.get("category", "未分类"),
            priority=todo.priority or analysis.get("priority", "medium"),
            due_date=todo.due_date,
            ai_generated_notes=analysis.get("suggestions", ""),
            estimated_hours=float(analysis.get("estimated_hours", 1.0)),
            priority_reasoning=analysis.get("reasoning", ""),
            created_at=datetime.now(),
            completed=False
        )
        
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)
        
        # 在后台训练模型
        background_tasks.add_task(train_ml_model, db, current_user.id)
        
        logger.info(f"待办事项已创建: id={db_todo.id}")
        
        # 构建完整的响应
        todo_analysis = TodoAnalysis(
            category=analysis.get('category', '未分类'),
            priority=analysis.get('priority', 'medium'),
            estimated_hours=float(analysis.get('estimated_hours', 1.0)),
            ai_notes=analysis.get('suggestions', '无建议'),
            priority_reasoning=analysis.get('reasoning', '无详细原因'),
            steps=[
                TodoStep(description=step, order=idx+1, completed=False)
                for idx, step in enumerate([
                    "分析任务需求",
                    "制定执行计划",
                    "执行任务",
                    "检查完成情况"
                ])
            ]
        )
        
        return TodoResponse(
            id=db_todo.id,  # 不再需要转换为字符串
            text=db_todo.text,
            completed=db_todo.completed,
            created_at=db_todo.created_at,
            due_date=db_todo.due_date,
            category=db_todo.category,
            priority=db_todo.priority,
            estimated_hours=db_todo.estimated_hours,
            ai_generated_notes=db_todo.ai_generated_notes,
            priority_reasoning=db_todo.priority_reasoning,
            actual_completion_time=db_todo.actual_completion_time,
            completed_at=db_todo.completed_at,
            steps=todo_analysis.steps,
            analysis=todo_analysis
        )
        
    except Exception as e:
        logger.error(f"创建待办事项时发生错误: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "创建待办事项时发生错误",
                "error": str(e)
            }
        )

@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    todo = db.query(TodoModel).filter(
        TodoModel.id == todo_id,
        TodoModel.user_id == current_user.id
    ).first()
    
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # 更新基本字段
    update_data = todo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(todo, field):
            setattr(todo, field, value)
    
    # 特殊处理完成状态
    if todo_update.completed is not None:
        todo.completed = todo_update.completed
        if todo.completed:
            todo.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(todo)
    
    # 如果任务完成，在后台训练模型
    if todo.completed:
        background_tasks.add_task(train_ml_model, db, current_user.id)
    
    # 构建响应
    todo_analysis = TodoAnalysis(
        category=todo.category,
        priority=todo.priority,
        estimated_hours=todo.estimated_hours,
        ai_notes=todo.ai_generated_notes or "无建议",
        priority_reasoning=todo.priority_reasoning or "无详细原因",
        steps=todo_update.steps or [
            TodoStep(description=step, order=idx+1, completed=False)
            for idx, step in enumerate([
                "分析任务需求",
                "制定执行计划",
                "执行任务",
                "检查完成情况"
            ])
        ]
    )
    
    return TodoResponse(
        id=todo.id,
        text=todo.text,
        completed=todo.completed,
        created_at=todo.created_at,
        due_date=todo.due_date,
        category=todo.category,
        priority=todo.priority,
        estimated_hours=todo.estimated_hours,
        ai_generated_notes=todo.ai_generated_notes,
        priority_reasoning=todo.priority_reasoning,
        actual_completion_time=todo.actual_completion_time,
        completed_at=todo.completed_at,
        steps=todo_analysis.steps,
        analysis=todo_analysis
    )

@router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    todo = db.query(TodoModel).filter(
        TodoModel.id == todo_id,
        TodoModel.user_id == current_user.id
    ).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}

@router.get("/categories")
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(TodoModel.category).filter(
        TodoModel.user_id == current_user.id
    ).distinct().all()
    return [cat[0] for cat in categories if cat[0]]

@router.get("/model-stats")
def get_model_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模型统计信息"""
    completed_todos = db.query(TodoModel).filter(
        TodoModel.user_id == current_user.id,
        TodoModel.completed == True
    ).count()
    
    return {
        "completed_todos": completed_todos,
        "min_samples_needed": ml_service.min_samples_for_training,
        "model_ready": completed_todos >= ml_service.min_samples_for_training
    } 