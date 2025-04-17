from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models.todo import PriorityEnum

class TodoStep(BaseModel):
    description: str
    order: int
    completed: bool = False

class TodoAnalysis(BaseModel):
    category: str
    priority: str
    estimated_hours: float
    ai_notes: str
    priority_reasoning: str
    steps: List[TodoStep]

class TodoBase(BaseModel):
    text: str
    due_date: Optional[datetime] = None
    category: Optional[str] = None
    priority: Optional[str] = None

class TodoCreate(TodoBase):
    pass

class TodoUpdate(TodoBase):
    completed: Optional[bool] = None
    steps: Optional[List[TodoStep]] = None
    actual_completion_time: Optional[float] = None

class TodoResponse(BaseModel):
    id: int
    text: str
    completed: bool = False
    created_at: datetime
    due_date: Optional[datetime] = None
    category: str
    priority: str
    estimated_hours: float
    ai_generated_notes: Optional[str] = None
    priority_reasoning: Optional[str] = None
    actual_completion_time: Optional[float] = None
    completed_at: Optional[datetime] = None
    steps: List[TodoStep]
    analysis: Optional[TodoAnalysis] = None

    class Config:
        from_attributes = True

class Todo(BaseModel):
    id: int
    text: str
    completed: bool
    user_id: int
    category: str
    priority: str
    due_date: Optional[datetime]
    created_at: datetime
    ai_generated_notes: Optional[str]
    estimated_hours: Optional[float]
    priority_reasoning: Optional[str]
    actual_completion_time: Optional[float]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True 