import React from 'react';
import { Recommendation } from '../types';
import { 
  LightBulbIcon,
  StarIcon,
  ClockIcon,
  TrophyIcon
} from '@heroicons/react/24/outline';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const getConfidenceColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-600';
    
    if (score >= 0.8) return 'bg-green-100 text-green-700';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  const getConfidenceText = (score?: number) => {
    if (!score) return '未知';
    
    if (score >= 0.8) return '高置信度';
    if (score >= 0.6) return '中等置信度';
    return '低置信度';
  };

  const getPriorityStars = (score?: number) => {
    if (!score) return 3;
    
    if (score >= 8) return 5;
    if (score >= 6) return 4;
    if (score >= 4) return 3;
    if (score >= 2) return 2;
    return 1;
  };

  const formatTimeSlot = (slot: any) => {
    if (!slot) return null;
    
    try {
      const start = new Date(slot.start_time);
      const end = new Date(slot.end_time);
      
      return `${start.toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })} - ${end.toLocaleString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })}`;
    } catch {
      return '时间解析错误';
    }
  };

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className="flex-shrink-0">
          <div className="p-2 bg-purple-100 rounded-lg">
            <LightBulbIcon className="w-5 h-5 text-purple-600" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            {recommendation.task_title && (
              <h4 className="font-medium text-gray-900 flex items-center space-x-2">
                <TrophyIcon className="w-4 h-4 text-purple-600" />
                <span>{recommendation.task_title}</span>
              </h4>
            )}
            
            {/* Priority Score */}
            {recommendation.priority_score && (
              <div className="flex items-center space-x-1">
                {Array.from({ length: 5 }, (_, i) => (
                  <StarIcon
                    key={i}
                    className={`w-4 h-4 ${
                      i < getPriorityStars(recommendation.priority_score)
                        ? 'text-yellow-400 fill-current'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
                <span className="text-sm text-gray-600 ml-1">
                  {recommendation.priority_score?.toFixed(1)}
                </span>
              </div>
            )}
          </div>

          {/* Reasoning */}
          <p className="text-sm text-gray-700 mb-3">{recommendation.reasoning}</p>

          {/* Recommended Time Slot */}
          {recommendation.recommended_slot && (
            <div className="flex items-center space-x-2 text-sm text-gray-600 mb-2">
              <ClockIcon className="w-4 h-4" />
              <span className="font-medium">推荐时间：</span>
              <span>{formatTimeSlot(recommendation.recommended_slot)}</span>
            </div>
          )}

          {/* Confidence Score */}
          {recommendation.confidence_score && (
            <div className="flex items-center justify-between">
              <span className={`px-2 py-1 rounded-full text-xs ${getConfidenceColor(recommendation.confidence_score)}`}>
                {getConfidenceText(recommendation.confidence_score)}
              </span>
              <button className="text-xs text-purple-600 hover:text-purple-800 font-medium">
                采纳建议
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};