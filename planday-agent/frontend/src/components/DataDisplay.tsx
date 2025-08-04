import React from 'react';
import { motion } from 'framer-motion';
import { MessageData } from '../types';
import { EventCard } from './EventCard';
import { TaskCard } from './TaskCard';
import { RecommendationCard } from './RecommendationCard';

interface DataDisplayProps {
  data: MessageData;
}

export const DataDisplay: React.FC<DataDisplayProps> = ({ data }) => {
  const { events, tasks, recommendations } = data;

  if (!events?.length && !tasks?.length && !recommendations?.length) {
    return null;
  }

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      {/* Events */}
      {events && events.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            📅 日程安排
            <span className="ml-2 bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">
              {events.length}
            </span>
          </h3>
          <div className="space-y-2">
            {events.map((event, index) => (
              <motion.div
                key={event.id || index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <EventCard event={event} />
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Tasks */}
      {tasks && tasks.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            📝 任务清单
            <span className="ml-2 bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full">
              {tasks.length}
            </span>
          </h3>
          <div className="space-y-2">
            {tasks.map((task, index) => (
              <motion.div
                key={task.id || index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <TaskCard task={task} />
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            💡 智能建议
            <span className="ml-2 bg-purple-100 text-purple-800 text-xs px-2 py-0.5 rounded-full">
              {recommendations.length}
            </span>
          </h3>
          <div className="space-y-2">
            {recommendations.map((rec, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <RecommendationCard recommendation={rec} />
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
};