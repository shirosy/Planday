import React from 'react';
import { motion } from 'framer-motion';
import { 
  CalendarIcon, 
  ListBulletIcon, 
  LightBulbIcon,
  PhotoIcon 
} from '@heroicons/react/24/outline';

interface WelcomeMessageProps {
  onSendMessage: (content: string) => void;
}

export const WelcomeMessage: React.FC<WelcomeMessageProps> = ({ onSendMessage }) => {
  const suggestions = [
    {
      icon: CalendarIcon,
      title: "安排会议",
      description: "明天下午3-5点安排团队会议",
      color: "text-blue-600",
      bgColor: "bg-blue-50"
    },
    {
      icon: ListBulletIcon,
      title: "创建任务",
      description: "创建高优先级任务：完成季度报告",
      color: "text-green-600",
      bgColor: "bg-green-50"
    },
    {
      icon: LightBulbIcon,
      title: "获取建议",
      description: "我今天应该优先处理什么？",
      color: "text-purple-600",
      bgColor: "bg-purple-50"
    },
    {
      icon: PhotoIcon,
      title: "解析内容",
      description: "上传图片或解析邮件内容",
      color: "text-orange-600",
      bgColor: "bg-orange-50"
    }
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <motion.div
        className="text-center max-w-2xl"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Welcome Header */}
        <div className="mb-8">
          <motion.div
            className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4"
            animate={{ 
              scale: [1, 1.1, 1],
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              repeatType: 'loop'
            }}
          >
            <CalendarIcon className="w-8 h-8 text-white" />
          </motion.div>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            欢迎使用 PlanDay
          </h1>
          <p className="text-lg text-gray-600">
            您的 AI 智能日程和任务管理助手
          </p>
        </div>

        {/* Features */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">我可以帮您:</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestions.map((suggestion, index) => (
              <motion.button
                key={index}
                onClick={() => onSendMessage(suggestion.description)}
                className={`p-4 rounded-xl border border-gray-200 hover:border-gray-300 ${suggestion.bgColor} text-left transition-all hover:shadow-md`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-start space-x-3">
                  <suggestion.icon className={`w-6 h-6 ${suggestion.color} flex-shrink-0 mt-0.5`} />
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">{suggestion.title}</h3>
                    <p className="text-sm text-gray-600">{suggestion.description}</p>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Quick Start Tips */}
        <motion.div
          className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <h3 className="font-semibold text-gray-800 mb-3">💡 使用技巧</h3>
          <div className="text-sm text-gray-600 space-y-2">
            <p>• 使用自然语言描述您的需求，比如"明天3点开会"</p>
            <p>• 支持拖拽上传图片，AI 会智能解析内容</p>
            <p>• 可以询问优先级建议和时间安排推荐</p>
            <p>• 复杂任务会自动分解为可执行的子任务</p>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};