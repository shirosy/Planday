import React from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';

export const UserAvatar: React.FC = () => {
  return (
    <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
      <UserCircleIcon className="w-6 h-6 text-white" />
    </div>
  );
};