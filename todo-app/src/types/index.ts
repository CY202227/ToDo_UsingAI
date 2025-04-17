export interface TodoStep {
  description: string;
  order: number;
  completed: boolean;
}

export interface TodoItem {
  id: number;
  text: string;
  completed: boolean;
  category: string;
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  ai_generated_notes?: string;
  estimated_hours?: number;
  priority_reasoning?: string;
  actual_completion_time?: number;
  completed_at?: string;
  created_at: string;
  steps?: TodoStep[];
  current_step: number;
}

export interface ModelStats {
  completed_todos: number;
  min_samples_needed: number;
  model_ready: boolean;
  accuracy: number;
  recent_predictions?: Array<{ text: string; predicted: string }>;
} 