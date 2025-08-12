export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  typing?: boolean;
  data?: MessageData;
  image?: string;
}

export interface MessageData {
  events?: CalendarEvent[];
  tasks?: Task[];
  recommendations?: Recommendation[];
  type?: 'schedule' | 'tasks' | 'recommendations' | 'general';
}

export interface CalendarEvent {
  id?: string;
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  location?: string;
  attendees?: string[];
  event_type?: string;
}

export interface Task {
  id?: string;
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  due_date?: string;
  estimated_duration_minutes?: number;
  estimated_duration?: number; // 保持向后兼容
  tags?: string[];
}

export interface Recommendation {
  task_id?: string;
  task_title?: string;
  priority_score?: number;
  reasoning: string;
  recommended_slot?: TimeSlot;
  confidence_score?: number;
}

export interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

export interface ChatResponse {
  response: string;
  events?: CalendarEvent[];
  tasks?: Task[];
  recommendations?: Recommendation[];
  session_id: string;
  success: boolean;
  error?: string;
}

export interface UploadedImage {
  file: File;
  preview: string;
  id: string;
}