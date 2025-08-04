import React from 'react';
import { Task } from '../types';
import { 
  CheckCircleIcon,
  ClockIcon,
  CalendarDaysIcon,
  TagIcon
} from '@heroicons/react/24/outline';

interface TaskCardProps {
  task: Task;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
  const getPriorityColor = (priority: string) => {
    const colors = {
      urgent: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-green-100 text-green-800 border-green-200',
    };
    return colors[priority as keyof typeof colors] || colors.medium;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'text-gray-600',
      in_progress: 'text-blue-600',
      completed: 'text-green-600',
      cancelled: 'text-red-600',
    };
    return colors[status as keyof typeof colors] || colors.pending;
  };

  const formatDuration = (task: Task) => {
    // 支持两种数据结构
    const minutes = task.estimated_duration_minutes || task.estimated_duration;
    if (!minutes) return null;
    
    if (minutes < 60) {
      return `${minutes}分钟`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    if (remainingMinutes === 0) {
      return `${hours}小时`;
    }
    
    return `${hours}小时${remainingMinutes}分钟`;
  };

  const formatDueDate = (dateString?: string) => {
    if (!dateString) return null;
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return '今天到期';
      if (diffDays === 1) return '明天到期';
      if (diffDays === -1) return '昨天到期';
      if (diffDays < 0) return `${Math.abs(diffDays)}天前到期`;
      if (diffDays <= 7) return `${diffDays}天后到期`;
      
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const isDueSoon = (dateString?: string) => {
    if (!dateString) return false;
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return diffDays <= 1 && diffDays >= 0;
    } catch {
      return false;
    }
  };

  const isOverdue = (dateString?: string) => {
    if (!dateString) return false;
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      return date.getTime() < now.getTime();
    } catch {
      return false;
    }
  };

  return (
    <div className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
      isOverdue(task.due_date) ? 'border-red-200 bg-red-50' : 
      isDueSoon(task.due_date) ? 'border-orange-200 bg-orange-50' : 
      'border-gray-200'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Task Title and Status */}
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircleIcon className={`w-5 h-5 ${getStatusColor(task.status)}`} />
            <h4 className="font-medium text-gray-900">{task.title}</h4>
          </div>

          {/* Task Details */}
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
            {/* Priority */}
            <span className={`px-2 py-1 rounded-full text-xs border ${getPriorityColor(task.priority)}`}>
              {task.priority === 'urgent' ? '紧急' :
               task.priority === 'high' ? '高' :
               task.priority === 'medium' ? '中' : '低'}优先级
            </span>

            {/* Duration */}
            {(task.estimated_duration_minutes || task.estimated_duration) && (
              <div className="flex items-center space-x-1">
                <ClockIcon className="w-4 h-4" />
                <span>{formatDuration(task)}</span>
              </div>
            )}

            {/* Due Date */}
            {task.due_date && (
              <div className={`flex items-center space-x-1 ${
                isOverdue(task.due_date) ? 'text-red-600' :
                isDueSoon(task.due_date) ? 'text-orange-600' : ''
              }`}>
                <CalendarDaysIcon className="w-4 h-4" />
                <span>{formatDueDate(task.due_date)}</span>
              </div>
            )}
          </div>

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <div className="flex items-center space-x-1 mb-2">
              <TagIcon className="w-4 h-4 text-gray-400" />
              <div className="flex flex-wrap gap-1">
                {task.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          {task.description && (
            <p className="text-sm text-gray-600 mt-2">{task.description}</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex flex-col space-y-1 ml-4">
          <button className="text-xs text-blue-600 hover:text-blue-800">编辑</button>
          <button className="text-xs text-green-600 hover:text-green-800">完成</button>
          <button className="text-xs text-red-600 hover:text-red-800">删除</button>
        </div>
      </div>
    </div>
  );
};