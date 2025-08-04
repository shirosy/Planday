import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { 
  PaperAirplaneIcon, 
  PhotoIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { UploadedImage } from '../types';

interface MessageInputProps {
  onSendMessage: (content: string, image?: File) => void;
  isLoading: boolean;
  placeholder?: string;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  isLoading,
  placeholder = "输入消息..."
}) => {
  const [message, setMessage] = useState('');
  const [uploadedImage, setUploadedImage] = useState<UploadedImage | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (file) {
        const preview = URL.createObjectURL(file);
        setUploadedImage({
          file,
          preview,
          id: Math.random().toString(36).substring(7)
        });
      }
    },
    noClick: true, // 禁用点击上传，只允许拖拽
    noKeyboard: true // 禁用键盘上传
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if ((!message.trim() && !uploadedImage) || isLoading) return;

    const content = message.trim() || (uploadedImage ? '📷 已上传图片' : '');
    onSendMessage(content, uploadedImage?.file);
    
    setMessage('');
    setUploadedImage(null);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    const scrollHeight = Math.min(textarea.scrollHeight, 120); // Max height
    textarea.style.height = `${scrollHeight}px`;
  };

  const removeImage = () => {
    if (uploadedImage) {
      URL.revokeObjectURL(uploadedImage.preview);
      setUploadedImage(null);
    }
  };

  const suggestedPrompts = [
    "明天下午3-5点安排团队会议",
    "创建高优先级任务：完成季度报告",
    "找出本周2小时的空闲时间",
    "我今天应该优先处理什么？"
  ];

  return (
    <div className="w-full">
      {/* Suggested Prompts (show when input is empty) */}
      {!message && !uploadedImage && (
        <motion.div 
          className="mb-3"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((prompt, index) => (
              <motion.button
                key={index}
                onClick={() => setMessage(prompt)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {prompt}
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Image Preview */}
      {uploadedImage && (
        <motion.div 
          className="mb-3 relative inline-block"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
        >
          <img
            src={uploadedImage.preview}
            alt="Preview"
            className="w-24 h-24 object-cover rounded-lg border border-gray-200"
          />
          <button
            onClick={removeImage}
            className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div 
          {...getRootProps()}
          className={`relative border rounded-2xl transition-all duration-200 ${
            isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-gray-300 hover:border-gray-400 focus-within:border-primary-500'
          }`}
        >
          <input {...getInputProps()} />
          
          <div className="flex items-end space-x-3 p-3">
            {/* Image Upload Button */}
            <motion.label
              htmlFor="image-upload"
              className="flex-shrink-0 p-2 text-gray-500 hover:text-primary-500 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <PhotoIcon className="w-5 h-5" />
              <input
                id="image-upload"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    const preview = URL.createObjectURL(file);
                    setUploadedImage({
                      file,
                      preview,
                      id: Math.random().toString(36).substring(7)
                    });
                  }
                }}
                disabled={isLoading}
              />
            </motion.label>

            {/* Text Input */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyPress={handleKeyPress}
              placeholder={isDragActive ? "释放以上传图片..." : placeholder}
              className="flex-1 resize-none border-0 outline-none bg-transparent min-h-[24px] max-h-[120px] placeholder-gray-500"
              rows={1}
              disabled={isLoading}
              onClick={(e) => e.stopPropagation()} // 防止触发拖拽上传
            />

            {/* Send Button */}
            <motion.button
              type="submit"
              disabled={(!message.trim() && !uploadedImage) || isLoading}
              className={`flex-shrink-0 p-2 rounded-lg transition-all ${
                (!message.trim() && !uploadedImage) || isLoading
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-white bg-primary-500 hover:bg-primary-600 shadow-md hover:shadow-lg'
              }`}
              whileHover={(!message.trim() && !uploadedImage) || isLoading ? {} : { scale: 1.05 }}
              whileTap={(!message.trim() && !uploadedImage) || isLoading ? {} : { scale: 0.95 }}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
            </motion.button>
          </div>
        </div>

        {/* Drag Overlay */}
        {isDragActive && (
          <motion.div
            className="absolute inset-0 bg-primary-500 bg-opacity-10 border-2 border-dashed border-primary-500 rounded-2xl flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="text-center">
              <PhotoIcon className="w-8 h-8 text-primary-500 mx-auto mb-2" />
              <p className="text-primary-600 font-medium">释放以上传图片</p>
            </div>
          </motion.div>
        )}
      </form>

      {/* Input Help Text */}
      <p className="text-xs text-gray-500 mt-2 text-center">
        按 Enter 发送，Shift + Enter 换行 • 支持拖拽上传图片
      </p>
    </div>
  );
};