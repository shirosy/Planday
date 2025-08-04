import React from 'react';
import { motion } from 'framer-motion';
import { CalendarIcon, SparklesIcon } from '@heroicons/react/24/outline';

export const ChatHeader: React.FC = () => {
  return (
    <motion.header 
      className="bg-white border-b border-gray-200 px-6 py-4"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-500 rounded-lg">
            <CalendarIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">PlanDay</h1>
            <p className="text-sm text-gray-500">AI 智能日程和任务管理助手</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <SparklesIcon className="w-4 h-4" />
          <span>由 LangGraph 驱动</span>
        </div>
      </div>
    </motion.header>
  );
};