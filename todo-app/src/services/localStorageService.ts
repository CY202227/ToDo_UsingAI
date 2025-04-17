import { TodoItem, ModelStats } from '@/types';
import Cookies from 'js-cookie';

const API_URL = 'http://localhost:8000';

// 存储键名
const STORAGE_KEYS = {
  TODOS: 'guest_todos',
  MODEL_STATS: 'guest_model_stats',
  IS_GUEST: 'guest_mode'
} as const;

let nextId = 1;

// 生成新的待办事项ID
export const generateId = (): number => {
  return nextId++;
};

// 设置游客模式
export const setGuestMode = (value: boolean) => {
  if (value) {
    localStorage.setItem(STORAGE_KEYS.IS_GUEST, 'true');
    Cookies.set('guest_mode', 'true', { path: '/' });
  } else {
    localStorage.removeItem(STORAGE_KEYS.IS_GUEST);
    Cookies.remove('guest_mode', { path: '/' });
    clearGuestData();
  }
};

// 检查是否为游客模式
export const isGuestMode = (): boolean => {
  return localStorage.getItem(STORAGE_KEYS.IS_GUEST) === 'true';
};

// 清除游客数据
export const clearGuestData = () => {
  localStorage.removeItem(STORAGE_KEYS.TODOS);
  localStorage.removeItem(STORAGE_KEYS.MODEL_STATS);
  localStorage.removeItem(STORAGE_KEYS.IS_GUEST);
};

// 保存游客的待办事项
export const saveTodos = (todos: TodoItem[]) => {
  if (isGuestMode()) {
    localStorage.setItem(STORAGE_KEYS.TODOS, JSON.stringify(todos));
  }
};

// 获取游客的待办事项
export const getTodos = (): TodoItem[] => {
  const todos = localStorage.getItem(STORAGE_KEYS.TODOS);
  return todos ? JSON.parse(todos) : [];
};

// 保存游客的模型统计数据
export const saveModelStats = (stats: ModelStats | null) => {
  if (isGuestMode()) {
    localStorage.setItem(STORAGE_KEYS.MODEL_STATS, JSON.stringify(stats));
  }
};

// 获取游客的模型统计数据
export const getModelStats = (): ModelStats => {
  const savedStats = localStorage.getItem(STORAGE_KEYS.MODEL_STATS);
  if (savedStats) {
    return JSON.parse(savedStats);
  }
  
  // 如果没有保存的统计数据，返回默认值
  const todos = getTodos();
  const completedTodos = todos.filter(todo => todo.completed).length;
  return {
    completed_todos: completedTodos,
    min_samples_needed: 10,
    model_ready: false,
    accuracy: 0,
    total_predictions: 0,
    successful_predictions: 0,
    recent_predictions: []
  };
};

// 从本地存储获取下一个可用的ID
const getNextId = (): number => {
  const todos = getTodos();
  if (todos.length === 0) return 1;
  return Math.max(...todos.map(todo => todo.id)) + 1;
};

// 获取AI分析结果
const getAIAnalysis = async (text: string, dueDate?: string) => {
  try {
    const response = await fetch(`${API_URL}/todos/guest-analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        text,
        due_date: dueDate
      }),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('AI分析失败');
    }

    const data = await response.json();
    return {
      category: data.category || '未分类',
      priority: data.priority || 'medium',
      estimated_hours: data.estimated_hours || 1,
      ai_generated_notes: data.ai_notes || '无AI建议',
      priority_reasoning: data.priority_reasoning || '无优先级说明',
      steps: data.steps || [],
    };
  } catch (error) {
    console.error('AI分析失败:', error);
    // 在AI分析失败时，生成一些基本的任务步骤
    const basicSteps = [
      {
        id: 1,
        content: '规划任务',
        estimated_minutes: 15,
        dependencies: [],
        completed: false
      },
      {
        id: 2,
        content: '执行任务',
        estimated_minutes: 30,
        dependencies: [1],
        completed: false
      },
      {
        id: 3,
        content: '检查完成情况',
        estimated_minutes: 15,
        dependencies: [2],
        completed: false
      }
    ];

    // 根据文本内容设置基本优先级
    let priority = 'medium';
    const text_lower = text.toLowerCase();
    if (text_lower.includes('紧急') || text_lower.includes('立即') || text_lower.includes('马上')) {
      priority = 'high';
    } else if (text_lower.includes('不急') || text_lower.includes('随时')) {
      priority = 'low';
    }

    return {
      category: '未分类',
      priority,
      estimated_hours: 1,
      ai_generated_notes: '离线模式：根据任务描述生成基本建议',
      priority_reasoning: `离线模式：根据任务描述"${text}"自动判断优先级`,
      steps: basicSteps,
    };
  }
};

// 添加待办事项
export const addTodo = async (text: string, dueDate?: string): Promise<TodoItem> => {
  const aiAnalysis = await getAIAnalysis(text, dueDate);
  
  const newTodo: TodoItem = {
    id: getNextId(),
    text: text,
    completed: false,
    category: aiAnalysis.category,
    priority: aiAnalysis.priority as 'low' | 'medium' | 'high',
    created_at: new Date().toISOString(),
    due_date: dueDate ?? null,
    ai_generated_notes: aiAnalysis.ai_generated_notes,
    estimated_hours: aiAnalysis.estimated_hours,
    priority_reasoning: aiAnalysis.priority_reasoning,
    steps: aiAnalysis.steps,
    current_step: 0
  };
  
  const todos = getTodos();
  todos.push(newTodo);
  saveTodos(todos);
  return newTodo;
};

// 更新待办事项
export const updateTodo = (id: number, updates: Partial<TodoItem>): TodoItem | null => {
  const todos = getTodos();
  const index = todos.findIndex(todo => todo.id === id);
  if (index === -1) return null;

  const updatedTodo = { ...todos[index], ...updates };
  if (updates.completed) {
    updatedTodo.completed_at = new Date().toISOString();
  }
  todos[index] = updatedTodo;
  saveTodos(todos);
  return updatedTodo;
};

// 删除待办事项
export const deleteTodo = (id: number): boolean => {
  const todos = getTodos();
  const newTodos = todos.filter(todo => todo.id !== id);
  if (newTodos.length === todos.length) return false;
  saveTodos(newTodos);
  return true;
}; 