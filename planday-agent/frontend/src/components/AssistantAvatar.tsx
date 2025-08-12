import React from 'react';
import { motion } from 'framer-motion';

export const AssistantAvatar: React.FC = () => {
  return (
    <motion.div 
      className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-sm"
      animate={{ 
        boxShadow: [
          '0 0 0 0 rgba(147, 51, 234, 0.7)',
          '0 0 0 10px rgba(147, 51, 234, 0)',
          '0 0 0 0 rgba(147, 51, 234, 0)'
        ]
      }}
      transition={{ 
        duration: 2,
        repeat: Infinity,
        repeatType: 'loop'
      }}
    >
      <svg 
        className="w-5 h-5 text-white" 
        fill="currentColor" 
        viewBox="0 0 24 24"
      >
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        <circle cx="12" cy="8" r="2"/>
        <path d="M12 14c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
      </svg>
    </motion.div>
  );
};