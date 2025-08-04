import React from 'react';
import { motion } from 'framer-motion';
import { Message } from '../types';
import { UserAvatar } from './UserAvatar';
import { AssistantAvatar } from './AssistantAvatar';
import { DataDisplay } from './DataDisplay';
import { ImageDisplay } from './ImageDisplay';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const timestamp = new Date(message.timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-xs lg:max-w-md xl:max-w-lg ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
        {/* Avatar */}
        <div className="flex-shrink-0">
          {isUser ? <UserAvatar /> : <AssistantAvatar />}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          {/* Message Bubble */}
          <motion.div
            className={`px-4 py-3 rounded-2xl max-w-full ${
              isUser
                ? 'bg-primary-500 text-white rounded-br-md'
                : 'bg-gray-100 text-gray-900 rounded-bl-md'
            }`}
            whileHover={{ scale: 1.02 }}
            transition={{ type: 'spring', stiffness: 400, damping: 17 }}
          >
            {/* Image if present */}
            {message.image && (
              <ImageDisplay 
                src={message.image} 
                alt="Uploaded image" 
                className="mb-2 rounded-lg max-w-48"
              />
            )}

            {/* Text Content */}
            <div className={`prose prose-sm max-w-none ${isUser ? 'prose-invert' : ''}`}>
              <ReactMarkdown 
                className="whitespace-pre-wrap"
                components={{
                  p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                  em: ({ children }) => <em className="italic">{children}</em>,
                  ul: ({ children }) => <ul className="list-disc list-inside my-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside my-1">{children}</ol>,
                  li: ({ children }) => <li className="mb-0.5">{children}</li>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          </motion.div>

          {/* Timestamp */}
          <span className={`text-xs text-gray-500 mt-1 ${isUser ? 'mr-2' : 'ml-2'}`}>
            {timestamp}
          </span>

          {/* Structured Data Display */}
          {message.data && !isUser && (
            <div className="mt-3 w-full">
              <DataDisplay data={message.data} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};