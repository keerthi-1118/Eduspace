import React from 'react';
import HomeIcon from './icons/HomeIcon';
import BookOpenIcon from './icons/BookOpenIcon';
import ProjectIcon from './icons/ProjectIcon';
import TaskIcon from './icons/TaskIcon';
import BrainCircuitIcon from './icons/BrainCircuitIcon';
import type { View } from '../types';

interface SidebarProps {
  currentView: View;
  onNavigate: (view: View) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onNavigate }) => {
  const navItems = [
    { id: 'home', icon: HomeIcon, label: 'Home' },
    { id: 'notes', icon: BookOpenIcon, label: 'Notes' },
    { id: 'projects', icon: ProjectIcon, label: 'Projects' },
    { id: 'tasks', icon: TaskIcon, label: 'Tasks' },
  ];

  return (
    <aside className="bg-secondary/30 border-r border-gray-700/50 p-4 flex flex-col items-center space-y-8 h-full">
      <div className="h-12 flex items-center">
        <h1 className="text-2xl font-semibold tracking-wide uppercase title-gradient">
            EduNex
        </h1>
      </div>
      <nav className="flex flex-col items-center space-y-6">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id as View)}
            className={`p-3 rounded-xl transition-all duration-300 relative group ${
              currentView === item.id
                ? 'bg-accent-blue text-white shadow-lg shadow-accent-blue/30'
                : 'text-gray-400 hover:bg-secondary hover:text-accent-blue'
            }`}
            aria-label={item.label}
          >
            <item.icon className="w-6 h-6" />
            <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
              {item.label}
            </span>
          </button>
        ))}
      </nav>
      <div className="mt-auto">
         <button className="p-3 rounded-xl text-gray-400 hover:bg-secondary hover:text-accent-blue relative group" aria-label="AI Mentor">
            <BrainCircuitIcon className="w-6 h-6" />
            <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
              AI Mentor
            </span>
          </button>
      </div>
    </aside>
  );
};

export default Sidebar;