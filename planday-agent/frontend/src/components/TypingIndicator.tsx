import React from 'react';
import { motion } from 'framer-motion';

export const TypingIndicator: React.FC = () => {
  return (
    <motion.div
      className="flex justify-start mb-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="flex items-start space-x-2">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>

        {/* Typing Animation */}
        <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
          <div className="typing-indicator">
            <div 
              className="typing-dot"
              style={{ '--delay': '0s' } as React.CSSProperties}
            />
            <div 
              className="typing-dot"
              style={{ '--delay': '0.2s' } as React.CSSProperties}
            />
            <div 
              className="typing-dot"
              style={{ '--delay': '0.4s' } as React.CSSProperties}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};