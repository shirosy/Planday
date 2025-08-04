import React from 'react';
import { motion } from 'framer-motion';
import { Message } from '../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { ErrorMessage } from './ErrorMessage';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  error?: string;
}

export const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  isLoading, 
  error 
}) => {
  return (
    <div className="message-container custom-scrollbar">
      {messages.map((message, index) => (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ 
            duration: 0.3, 
            delay: index * 0.1 
          }}
        >
          <MessageBubble message={message} />
        </motion.div>
      ))}
      
      {isLoading && <TypingIndicator />}
      
      {error && <ErrorMessage message={error} />}
    </div>
  );
};