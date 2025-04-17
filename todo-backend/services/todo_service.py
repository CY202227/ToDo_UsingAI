from typing import List, Optional
from datetime import datetime
from schemas.todo import TodoCreate, TodoResponse, TodoAnalysis, TodoStep
import openai
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置OpenAI API密钥
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE')

async def generate_todo_suggestions(todo: TodoCreate) -> TodoAnalysis:
    try:
        prompt = """分析以下待办事项并提供建议：
        任务：{}
        截止日期：{}
        
        请提供以下信息：
        1. 任务类别
        2. 优先级（高/中/低）及原因
        3. 预计所需时间（小时）
        4. AI建议笔记
        5. 详细的任务步骤（最多5步）
        
        请以JSON格式返回，包含以下字段：
        - category: 任务类别（工作/生活/学习等）
        - priority: 优先级（高/中/低）
        - estimated_hours: 预计所需时间（数字）
        - ai_notes: AI建议内容
        - priority_reasoning: 优先级判断原因
        - steps: 任务步骤列表
        """.format(
            todo.text,
            todo.due_date if todo.due_date else '未设置'
        )

        response = await openai.ChatCompletion.acreate(
            model=os.getenv('OPENAI_MODEL'),
            messages=[
                {"role": "system", "content": "你是一个任务管理助手，帮助用户分析和规划任务。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # 解析AI响应
        result = json.loads(response.choices[0].message.content)
        
        # 创建任务步骤
        steps = [
            TodoStep(
                description=step,
                order=idx + 1,
                completed=False
            ) for idx, step in enumerate(result["steps"])
        ]

        return TodoAnalysis(
            category=result["category"],
            priority=result["priority"],
            estimated_hours=float(result["estimated_hours"]),
            ai_notes=result["ai_notes"],
            priority_reasoning=result["priority_reasoning"],
            steps=steps
        )
    except Exception as e:
        print(f"生成AI建议时出错: {str(e)}")
        # 返回一个基本的分析结果作为后备方案
        return TodoAnalysis(
            category="未分类",
            priority="中",
            estimated_hours=1.0,
            ai_notes="无法获取AI建议",
            priority_reasoning="系统默认设置",
            steps=[
                TodoStep(description="规划任务", order=1, completed=False),
                TodoStep(description="执行任务", order=2, completed=False),
                TodoStep(description="检查完成情况", order=3, completed=False)
            ]
        ) 