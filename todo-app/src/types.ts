export interface TodoStep {
  id: number;
  content: string;
  completed: boolean;
  estimated_minutes: number;
  dependencies: number[];
}

export interface TodoItem {
  id: number;
  text: string;
  completed: boolean;
  category?: string;
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  ai_generated_notes?: string;
  estimated_hours?: number;
  priority_reasoning?: string;
  actual_completion_time?: number;
  completed_at?: string;
  created_at: string;
  steps?: TodoStep[];
  current_step?: number;
}

export interface ModelStats {
  completed_todos: number;
  min_samples_needed: number;
  model_ready: boolean;
  accuracy: number;
  total_predictions: number;
  successful_predictions: number;
  recent_predictions: {
    input: string;
    output: string;
    timestamp: string;
  }[];
} 