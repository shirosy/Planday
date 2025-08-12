import React from 'react';
import { CalendarEvent } from '../types';
import { 
  CalendarIcon, 
  ClockIcon, 
  MapPinIcon,
  UserGroupIcon 
} from '@heroicons/react/24/outline';

interface EventCardProps {
  event: CalendarEvent;
}

export const EventCard: React.FC<EventCardProps> = ({ event }) => {
  const formatTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getEventTypeColor = (type?: string) => {
    const colors = {
      meeting: 'bg-blue-500',
      appointment: 'bg-green-500',
      personal: 'bg-purple-500',
      work: 'bg-orange-500',
      deadline: 'bg-red-500',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500';
  };

  const getDuration = () => {
    try {
      const start = new Date(event.start_time);
      const end = new Date(event.end_time);
      const diffMs = end.getTime() - start.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
      
      if (diffHours > 0) {
        return `${diffHours}小时${diffMinutes > 0 ? ` ${diffMinutes}分钟` : ''}`;
      }
      return `${diffMinutes}分钟`;
    } catch {
      return '';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Event Title */}
          <div className="flex items-center space-x-2 mb-2">
            <div className={`w-3 h-3 rounded-full ${getEventTypeColor(event.event_type)}`} />
            <h4 className="font-medium text-gray-900">{event.title}</h4>
          </div>

          {/* Time Info */}
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
            <div className="flex items-center space-x-1">
              <CalendarIcon className="w-4 h-4" />
              <span>{formatTime(event.start_time)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <ClockIcon className="w-4 h-4" />
              <span>{getDuration()}</span>
            </div>
          </div>

          {/* Location */}
          {event.location && (
            <div className="flex items-center space-x-1 text-sm text-gray-600 mb-2">
              <MapPinIcon className="w-4 h-4" />
              <span>{event.location}</span>
            </div>
          )}

          {/* Attendees */}
          {event.attendees && event.attendees.length > 0 && (
            <div className="flex items-center space-x-1 text-sm text-gray-600 mb-2">
              <UserGroupIcon className="w-4 h-4" />
              <span>{event.attendees.length} 位参与者</span>
            </div>
          )}

          {/* Description */}
          {event.description && (
            <p className="text-sm text-gray-600 mt-2">{event.description}</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex flex-col space-y-1 ml-4">
          <button className="text-xs text-blue-600 hover:text-blue-800">编辑</button>
          <button className="text-xs text-red-600 hover:text-red-800">删除</button>
        </div>
      </div>
    </div>
  );
};