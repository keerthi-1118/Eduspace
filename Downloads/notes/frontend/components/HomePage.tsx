import React from 'react';
import type { View } from '../types';
import BookOpenIcon from './icons/BookOpenIcon';
import ProjectIcon from './icons/ProjectIcon';
import TaskIcon from './icons/TaskIcon';
import PreviewIcon from './icons/PreviewIcon';

interface HomePageProps {
    onNavigate: (view: View) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
    const features = [
        {
            icon: <BookOpenIcon className="w-10 h-10 text-accent-blue-light" />,
            title: 'Knowledge Exchange Hub',
            description: 'Dive into a collaborative pool of knowledge. Upload your study materials, discover notes from peers, and leverage our \'AI StudyFlow\' to get instant, insightful summaries of complex documents. Learning together has never been more efficient.',
            buttonText: 'Explore the Hub',
            targetView: 'notes' as View,
        },
        {
            icon: <ProjectIcon className="w-10 h-10 text-accent-blue-light" />,
            title: 'Project Collaboration',
            description: 'Bring your ideas to life. Start or join projects, manage your codebase in a shared environment, and collaborate with your team in real-time. Perfect for group assignments and hackathons.',
            buttonText: 'Manage Projects',
            targetView: 'projects' as View,
        },
        {
            icon: <TaskIcon className="w-10 h-10 text-accent-blue-light" />,
            title: 'Task Dashboard',
            description: 'Stay organized and on track. Create to-do lists, assign tasks, and monitor your project\'s progress with our intuitive dashboard. Never miss a deadline again and keep your team perfectly in sync.',
            buttonText: 'View Tasks',
            targetView: 'tasks' as View,
        },
        {
            icon: <PreviewIcon className="w-10 h-10 text-accent-blue-light" />,
            title: 'Real-Time Preview',
            description: 'See your code in action instantly. Our platform provides a live preview environment for your web projects, allowing you to iterate faster, get immediate feedback, and showcase your work effortlessly.',
            buttonText: 'Launch Preview',
            targetView: 'projects' as View,
        }
    ];

    return (
        <div className="p-6 sm:p-8">
            <div className="text-center mb-16 animate-fade-in">
                 <h2 className="text-3xl lg:text-4xl font-medium text-light-text mb-3">Welcome to Your Dashboard</h2>
                <p className="text-muted-text max-w-3xl mx-auto">
                    This is your central hub for learning, collaboration, and building. Explore the features below to get started on your next big project.
                </p>
            </div>

            <div className="space-y-16 max-w-5xl mx-auto">
                {features.map((feature, index) => (
                    <div key={feature.title} 
                         className="flex flex-col md:flex-row items-center gap-8 animate-fade-in-up" 
                         style={{ animationDelay: `${index * 0.15}s` }}>
                        
                        <div className="flex-shrink-0 p-5 bg-secondary/40 rounded-2xl ring-1 ring-accent-blue/20">
                            {feature.icon}
                        </div>
                        <div className="flex-grow text-center md:text-left">
                            <h3 className="text-2xl font-semibold text-light-text mb-2">{feature.title}</h3>
                            <p className="text-muted-text mb-5 leading-relaxed">{feature.description}</p>
                            <button
                                onClick={() => onNavigate(feature.targetView)}
                                className="bg-secondary/50 border border-gray-700 text-gray-300 font-semibold py-2 px-5 rounded-lg transition-all duration-300 transform hover:bg-accent-blue hover:text-white hover:shadow-glow-blue hover:border-accent-blue"
                            >
                                {feature.buttonText}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default HomePage;