import React from 'react';
import Sidebar from './Sidebar';
import MentorBotIcon from './icons/MentorBotIcon';
import type { View } from '../types';

interface LayoutProps {
  children: React.ReactNode;
  currentView: View;
  onNavigate: (view: View) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, currentView, onNavigate }) => {
  return (
    <div className="flex h-screen overflow-hidden">
        <Sidebar currentView={currentView} onNavigate={onNavigate} />
        <div className="flex-1 flex flex-col relative">
            <button className="absolute top-6 sm:top-8 right-6 sm:right-8 z-20 flex items-center space-x-2 bg-secondary/50 border border-gray-700 text-gray-300 font-semibold py-2 px-4 rounded-full transition-all duration-300 transform hover:bg-accent-blue hover:text-white hover:shadow-glow-blue hover:border-accent-blue">
                <span>Mentor Bot</span>
                <MentorBotIcon className="w-6 h-6" />
            </button>
            <main className="flex-1 overflow-y-auto">
                {children}
            </main>
        </div>
    </div>
  );
};

export default Layout;