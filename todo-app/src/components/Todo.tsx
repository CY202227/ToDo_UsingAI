'use client';
import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { TodoItem, ModelStats, TodoStep } from '@/types';
import * as localStorageService from '@/services/localStorageService';

const API_URL = 'http://localhost:8000';

export default function Todo() {
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [modelStats, setModelStats] = useState<ModelStats | null>(null);
  const [selectedTodo, setSelectedTodo] = useState<TodoItem | null>(null);
  const [showDetails, setShowDetails] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isGuest, setIsGuest] = useState(false);

  // 检查是否为游客模式
  useEffect(() => {
    const guestMode = localStorageService.isGuestMode();
    setIsGuest(guestMode);
    if (guestMode) {
      const savedTodos = localStorageService.getTodos();
      const savedStats = localStorageService.getModelStats();
      setTodos(savedTodos);
      setModelStats(savedStats);
      setLoading(false);
    } else {
      fetchTodos();
      fetchModelStats();
    }
  }, []);

  // 保存游客模式的数据
  useEffect(() => {
    if (isGuest) {
      localStorageService.saveTodos(todos);
      localStorageService.saveModelStats(modelStats);
    }
  }, [isGuest, todos, modelStats]);

  // 获取所有待办事项
  const fetchTodos = async () => {
    try {
      const response = await fetch(`${API_URL}/todos/`, {
        credentials: 'include',
      });
      if (response.status === 401) {
        setError('请先登录');
        setTodos([]);
        return;
      }
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      if (!Array.isArray(data)) {
        console.error('获取到的数据不是数组格式:', data);
        setTodos([]);
        return;
      }
      
      setTodos(data);
      setError(null);
    } catch (error) {
      console.error('获取待办事项失败:', error);
      setTodos([]);
      setError('获取待办事项失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取模型统计信息
  const fetchModelStats = async () => {
    try {
      const response = await fetch(`${API_URL}/todos/model-stats`, {
        credentials: 'include',
      });
      if (response.status === 401) {
        return;
      }
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setModelStats(data);
    } catch (error) {
      console.error('获取模型统计失败:', error);
    }
  };

  // 添加待办事项
  const addTodo = async () => {
    if (input.trim()) {
      try {
        if (isGuest) {
          const newTodo = await localStorageService.addTodo(input.trim());
          setTodos([...todos, newTodo]);
          setInput('');
          setModelStats(localStorageService.getModelStats());
        } else {
          const response = await fetch(`${API_URL}/todos/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ title: input.trim() }),
          });
          if (response.status === 401) {
            setError('请先登录');
            return;
          }
          const newTodo = await response.json();
          setTodos([...todos, newTodo]);
          setInput('');
          fetchModelStats();
        }
      } catch (error) {
        console.error('添加待办事项失败:', error);
        setError('添加待办事项失败');
      }
    }
  };

  // 更新任务步骤
  const updateStep = async (todoId: number, currentStep: number) => {
    try {
      if (isGuest) {
        const updatedTodo = localStorageService.updateTodo(todoId, { current_step: currentStep });
        if (updatedTodo) {
          setTodos(localStorageService.getTodos());
        }
      } else {
        const response = await fetch(`${API_URL}/todos/${todoId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ current_step: currentStep }),
        });
        if (response.status === 401) {
          setError('请先登录');
          return;
        }
        fetchTodos();
      }
    } catch (error) {
      console.error('更新步骤失败:', error);
      setError('更新步骤失败');
    }
  };

  // 完成待办事项
  const completeTodo = async (id: number, actualTime?: number) => {
    try {
      if (isGuest) {
        const updatedTodo = localStorageService.updateTodo(id, {
          completed: true,
          actual_completion_time: actualTime,
        });
        if (updatedTodo) {
          setTodos(localStorageService.getTodos());
          setModelStats(localStorageService.getModelStats());
        }
      } else {
        const response = await fetch(`${API_URL}/todos/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            completed: true,
            actual_completion_time: actualTime,
          }),
        });
        if (response.status === 401) {
          setError('请先登录');
          return;
        }
        fetchTodos();
        fetchModelStats();
      }
    } catch (error) {
      console.error('更新待办事项失败:', error);
      setError('更新待办事项失败');
    }
  };

  // 删除待办事项
  const deleteTodo = async (id: number) => {
    try {
      if (isGuest) {
        if (localStorageService.deleteTodo(id)) {
          setTodos(localStorageService.getTodos());
        }
      } else {
        const response = await fetch(`${API_URL}/todos/${id}`, {
          method: 'DELETE',
          credentials: 'include',
        });
        if (response.status === 401) {
          setError('请先登录');
          return;
        }
        setTodos(todos.filter(todo => todo.id !== id));
      }
    } catch (error) {
      console.error('删除待办事项失败:', error);
      setError('删除待办事项失败');
    }
  };

  // 登出功能
  const handleLogout = async () => {
    try {
      if (isGuest) {
        localStorageService.clearGuestData();
        window.location.href = '/login';
      } else {
        const response = await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('登出失败');
        }

        setTodos([]);
        setModelStats(null);
        setError('请先登录');
      }
    } catch (error) {
      console.error('登出失败:', error);
    }
  };

  // 优先级对应的颜色
  const priorityColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-lg">
        <p className="text-center text-gray-500">加载中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-lg">
        <div className="text-center text-red-500">
          <p>{error}</p>
          {error === '请先登录' && (
            <button
              onClick={() => window.location.href = '/login'}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              去登录
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">待办事项</h1>
          {isGuest && (
            <p className="text-sm text-gray-500 mt-1">
              游客模式 - 数据仅保存在本地
            </p>
          )}
        </div>
        <button
          onClick={handleLogout}
          className="px-4 py-2 text-sm text-red-600 hover:text-red-700 font-medium"
        >
          {isGuest ? '退出游客模式' : '退出登录'}
        </button>
      </div>
      
      {/* 模型状态显示 */}
      {modelStats && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">模型状态</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p>已完成任务数: {modelStats.completed_todos}</p>
              <p>训练所需样本: {modelStats.min_samples_needed}</p>
            </div>
            <div>
              <p>模型状态: {modelStats.model_ready ? '已就绪' : '训练中'}</p>
              <p>准确率: {(modelStats.accuracy * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}
      
      {/* 输入框 */}
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          placeholder="添加新的待办事项..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={addTodo}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          添加
        </button>
      </div>

      {/* 待办事项列表 */}
      <ul className="space-y-4">
        {Array.isArray(todos) && todos.map((todo) => (
          <li
            key={`todo-${todo.id}`}
            className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => completeTodo(todo.id)}
                  className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className={todo.completed ? 'line-through text-gray-500' : 'text-gray-800'}>
                  {todo.text}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs ${priorityColors[todo.priority]}`}>
                  {todo.priority}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowDetails(showDetails === todo.id ? null : todo.id)}
                  className="text-blue-500 hover:text-blue-600"
                >
                  {showDetails === todo.id ? '收起' : '详情'}
                </button>
                <button
                  onClick={() => deleteTodo(todo.id)}
                  className="text-red-500 hover:text-red-600"
                >
                  删除
                </button>
              </div>
            </div>

            {/* 详细信息 */}
            {showDetails === todo.id && (
              <div className="mt-4 space-y-3">
                {todo.category && (
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">类别：</span>
                    {todo.category}
                  </p>
                )}
                {todo.due_date && (
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">截止日期：</span>
                    {format(new Date(todo.due_date), 'yyyy-MM-dd HH:mm')}
                  </p>
                )}
                {todo.estimated_hours && (
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">预计用时：</span>
                    {todo.estimated_hours} 小时
                  </p>
                )}
                {todo.priority_reasoning && (
                  <div className="text-sm text-gray-600">
                    <span className="font-semibold">优先级说明：</span>
                    <p className="mt-1 ml-4">{todo.priority_reasoning}</p>
                  </div>
                )}
                {todo.ai_generated_notes && (
                  <div className="text-sm text-gray-600">
                    <span className="font-semibold">AI 建议：</span>
                    <p className="mt-1 ml-4">{todo.ai_generated_notes}</p>
                  </div>
                )}

                {/* 任务步骤 */}
                {todo.steps && todo.steps.length > 0 && (
                  <div className="mt-4">
                    <h3 className="font-semibold text-gray-700 mb-2">任务步骤</h3>
                    <div className="space-y-2">
                      {todo.steps.map((step, index) => (
                        <div
                          key={`todo-${todo.id}-step-${step.id}`}
                          className={`p-3 rounded ${
                            index === todo.current_step
                              ? 'bg-blue-100'
                              : index < todo.current_step
                              ? 'bg-green-100'
                              : 'bg-gray-100'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">步骤 {index + 1}</span>
                              <span className="text-sm text-gray-600">
                                ({step.estimated_minutes} 分钟)
                              </span>
                            </div>
                            {index === todo.current_step && !todo.completed && (
                              <button
                                onClick={() => updateStep(todo.id, index + 1)}
                                className="text-sm text-blue-500 hover:text-blue-600"
                              >
                                完成步骤
                              </button>
                            )}
                          </div>
                          <p className="mt-1 text-sm">{step.content}</p>
                          {step.dependencies.length > 0 && (
                            <p className="mt-1 text-xs text-gray-500">
                              依赖步骤: {step.dependencies.map(d => d + 1).join(', ')}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 完成时间 */}
                {todo.completed && todo.completed_at && (
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">完成时间：</span>
                    {format(new Date(todo.completed_at), 'yyyy-MM-dd HH:mm')}
                    {todo.actual_completion_time && (
                      <span className="ml-2">
                        (实际用时: {todo.actual_completion_time} 小时)
                      </span>
                    )}
                  </p>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>

      {todos.length === 0 && (
        <p className="text-center text-gray-500 mt-6">暂无待办事项</p>
      )}
    </div>
  );
} 