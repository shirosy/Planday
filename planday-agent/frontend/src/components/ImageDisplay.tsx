import React from 'react';

interface ImageDisplayProps {
  src: string;
  alt: string;
  className?: string;
}

export const ImageDisplay: React.FC<ImageDisplayProps> = ({ 
  src, 
  alt, 
  className = '' 
}) => {
  return (
    <div className={`relative ${className}`}>
      <img
        src={src}
        alt={alt}
        className="w-full h-auto object-cover rounded-lg border border-gray-200"
        loading="lazy"
      />
    </div>
  );
};