import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { chatAPI } from '../services/api';
import { Message, ChatResponse, MessageData } from '../types';

export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | undefined>();

  const mutation = useMutation({
    mutationFn: ({ message, image }: { message: string; image?: File }) =>
      chatAPI.sendMessage(message, sessionId, image),
    onSuccess: (response: ChatResponse) => {
      setError(undefined);
      
      // Add assistant response
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        content: response.response,
        role: 'assistant',
        timestamp: new Date(),
        data: {
          events: response.events,
          tasks: response.tasks,
          recommendations: response.recommendations,
          type: determineMessageType(response)
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
    },
    onError: (error: any) => {
      console.error('Chat error:', error);
      setError(error.response?.data?.error || error.message || '发送消息失败');
    }
  });

  const sendMessage = useCallback(async (content: string, image?: File) => {
    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      role: 'user',
      timestamp: new Date(),
      image: image ? URL.createObjectURL(image) : undefined
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Send to API
    await mutation.mutateAsync({ message: content, image });
  }, [mutation]);

  const determineMessageType = (response: ChatResponse): MessageData['type'] => {
    if (response.events && response.events.length > 0) return 'schedule';
    if (response.tasks && response.tasks.length > 0) return 'tasks';
    if (response.recommendations && response.recommendations.length > 0) return 'recommendations';
    return 'general';
  };

  return {
    messages,
    isLoading: mutation.isPending,
    sendMessage,
    error
  };
};