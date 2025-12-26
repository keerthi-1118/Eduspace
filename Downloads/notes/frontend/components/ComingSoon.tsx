import React from 'react';
import BrainCircuitIcon from './icons/BrainCircuitIcon';

interface ComingSoonProps {
  pageName: string;
}

const ComingSoon: React.FC<ComingSoonProps> = ({ pageName }) => {
  return (
    <div className="flex flex-col flex-grow items-center justify-center text-center p-8 animate-fade-in">
      <div className="p-4 bg-secondary rounded-full mb-6 ring-2 ring-accent-blue/50 shadow-glow-blue">
        <BrainCircuitIcon className="w-16 h-16 text-accent-blue" />
      </div>
      <h2 className="text-3xl font-semibold text-light-text title-gradient mb-2">
        {pageName} - Coming Soon!
      </h2>
      <p className="text-muted-text max-w-md">
        We're hard at work building this feature. It will be available soon to enhance your collaborative learning experience on EduNex.
      </p>
    </div>
  );
};

export default ComingSoon;