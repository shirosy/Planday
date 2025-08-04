import React from 'react';
import { motion } from 'framer-motion';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface ErrorMessageProps {
  message: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  return (
    <motion.div
      className="flex justify-start mb-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-start space-x-2 max-w-xs lg:max-w-md">
        {/* Error Icon */}
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
        </div>

        {/* Error Content */}
        <div className="bg-red-50 border border-red-200 rounded-2xl rounded-bl-md px-4 py-3">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-medium text-red-800">出现错误</span>
          </div>
          <p className="text-sm text-red-700">{message}</p>
          <button className="text-xs text-red-600 hover:text-red-800 mt-2 underline">
            重试
          </button>
        </div>
      </div>
    </motion.div>
  );
};