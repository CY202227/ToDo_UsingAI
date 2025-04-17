from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Float, JSON
from sqlalchemy.orm import relationship
from database.database import Base
import enum
from datetime import datetime

class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TodoModel(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String, index=True)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ai_generated_notes = Column(String, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    priority_reasoning = Column(String, nullable=True)
    actual_completion_time = Column(Float, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    steps = Column(JSON, nullable=True)  # 存储任务步骤
    current_step = Column(Integer, default=0)  # 当前完成到哪个步骤

    user = relationship("User", back_populates="todos") 