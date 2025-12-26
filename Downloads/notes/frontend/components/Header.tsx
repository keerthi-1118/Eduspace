import React from 'react';
import MentorBotIcon from './icons/MentorBotIcon';
import type { View } from '../types';

interface HeaderProps {
  currentView: View;
}

const viewTitles: Record<View, string> = {
  home: 'Dashboard',
  notes: 'Knowledge Exchange Hub',
  projects: 'Projects',
  tasks: 'Tasks',
};

const Header: React.FC<HeaderProps> = ({ currentView }) => {
  const title = viewTitles[currentView];

  return (
    <header className="flex items-center justify-between p-6 sm:p-8 flex-shrink-0 bg-primary/80 backdrop-filter backdrop-blur-lg border-b border-secondary sticky top-0 z-20">
      <h1 className="text-2xl font-semibold text-light-text">{title}</h1>
      <button className="flex items-center space-x-2 bg-secondary/50 border border-gray-700 text-gray-300 font-semibold py-2 px-4 rounded-full transition-all duration-300 transform hover:bg-accent-blue hover:text-white hover:shadow-glow-blue hover:border-accent-blue">
        <span>Mentor Bot</span>
        <MentorBotIcon className="w-6 h-6" />
      </button>
    </header>
  );
};

export default Header;