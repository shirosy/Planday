import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChatHeader } from './components/ChatHeader';
import { MessageList } from './components/MessageList';
import { MessageInput } from './components/MessageInput';
import { WelcomeMessage } from './components/WelcomeMessage';
import { useChat } from './hooks/useChat';
import { generateSessionId } from './utils/sessionUtils';

function App() {
  const [sessionId] = useState(() => generateSessionId());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const {
    messages,
    isLoading,
    sendMessage,
    error
  } = useChat(sessionId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string, image?: File) => {
    await sendMessage(content, image);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <ChatHeader />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        <motion.div 
          className="flex-1 flex flex-col bg-white rounded-t-xl shadow-sm overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Messages Container */}
          <div className="flex-1 overflow-hidden relative">
            {messages.length === 0 ? (
              <WelcomeMessage onSendMessage={handleSendMessage} />
            ) : (
              <MessageList 
                messages={messages} 
                isLoading={isLoading}
                error={error}
              />
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 bg-white p-4">
            <MessageInput 
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              placeholder="输入消息，比如：'明天3-5点安排团队会议' 或上传图片..."
            />
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="text-center py-3 text-xs text-gray-500">
        PlanDay - AI 智能日程助手 | Powered by LangGraph
      </div>
    </div>
  );
}

export default App;