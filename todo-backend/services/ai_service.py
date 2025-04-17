import os
from openai import OpenAI
from dotenv import load_dotenv
from .ml_service import ml_service
import json
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIServiceConfig:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")
        if not self.api_base:
            raise ValueError("OPENAI_API_BASE 环境变量未设置")

class AIService:
    def __init__(self):
        self.config = AIServiceConfig()
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base
        )
    
    def _create_prompt(self, text: str, ml_priority: str) -> str:
        return f"""
        基于以下待办事项内容，请提供：
        1. 合适的分类
        2. 建议的优先级（high/medium/low）
        3. 补充说明或建议
        4. 预计所需时间（小时）
        
        待办事项：{text}
        机器学习模型建议的优先级：{ml_priority}
        
        请以JSON格式返回，包含以下字段：
        - category: 分类
        - priority: 优先级（请参考机器学习模型的建议）
        - suggestions: 补充说明或建议
        - estimated_hours: 预计完成所需时间（小时）
        - reasoning: 为什么选择这个优先级和分类的原因
        """
    
    def _get_default_response(self, ml_priority: str, error_msg: str = "无法获取AI建议") -> Dict:
        return {
            "category": "未分类",
            "priority": ml_priority,
            "suggestions": error_msg,
            "estimated_hours": 1,
            "reasoning": "使用机器学习模型的默认建议"
        }
    
    def generate_todo_suggestions(self, text: str, due_date: Optional[datetime] = None) -> Dict:
        """生成待办事项的建议，包括分类和补充内容"""
        try:
            # 首先使用ML模型预测优先级
            ml_priority = ml_service.predict_priority(text, due_date)
            
            # 准备并发送请求到OpenAI
            prompt = self._create_prompt(text, ml_priority)
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的任务管理助手，帮助用户更好地组织待办事项。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            # 提取生成的内容
            ai_response = response.choices[0].message.content
            try:
                suggestions_dict = json.loads(ai_response)
                # 确保优先级与枚举值匹配
                if suggestions_dict["priority"] not in ["low", "medium", "high"]:
                    suggestions_dict["priority"] = ml_priority
                logger.info(f"成功生成待办事项建议: {suggestions_dict}")
                return suggestions_dict
            except json.JSONDecodeError as e:
                logger.error(f"AI响应解析失败: {str(e)}")
                return self._get_default_response(ml_priority, "AI响应解析失败")
                
        except Exception as e:
            logger.error(f"生成待办事项建议时发生错误: {str(e)}", exc_info=True)
            return self._get_default_response(
                ml_service.predict_priority(text, due_date),
                f"生成建议时发生错误: {str(e)}"
            )

# 创建全局AI服务实例
ai_service = AIService()
generate_todo_suggestions = ai_service.generate_todo_suggestions 