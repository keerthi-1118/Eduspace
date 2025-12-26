import React, { useState, useCallback } from 'react';
import Layout from './components/Layout';
import SummaryModal from './components/SummaryModal';
import { summarizeText } from './services/geminiService';
import type { Note, View } from './types';
import LoginPage from './components/LoginPage';
import HomePage from './components/HomePage';
import KnowledgeHub from './components/KnowledgeHub';
import Projects from './components/Projects';
import Tasks from './components/Tasks';
import ComingSoon from './components/ComingSoon';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentView, setCurrentView] = useState<View>('home');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeNote, setActiveNote] = useState<Note | null>(null);

  const handleOpenSummary = useCallback(async (note: Note) => {
    setActiveNote(note);
    setIsModalOpen(true);
    setIsLoading(true);
    setError(null);
    setSummary('');

    try {
      const result = await summarizeText(note.content);
      setSummary(result);
    } catch (err) {
      setError('Failed to generate summary. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setActiveNote(null);
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleNavigate = (view: View) => {
    setCurrentView(view);
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-primary text-light-text">
      <div className="absolute inset-0 z-0 opacity-10">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-blue-light rounded-full filter blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-blue rounded-full filter blur-3xl animate-pulse animation-delay-4000"></div>
      </div>
      <div className="relative z-10">
        <Layout currentView={currentView} onNavigate={handleNavigate}>
          {currentView === 'home' && <HomePage onNavigate={handleNavigate} />}
          {currentView === 'notes' && <KnowledgeHub />}
          {currentView === 'projects' && <Projects />}
          {currentView === 'tasks' && <Tasks />}
        </Layout>
        {isModalOpen && (
          <SummaryModal
            isOpen={isModalOpen}
            onClose={handleCloseModal}
            summary={summary}
            isLoading={isLoading}
            error={error}
            noteTitle={activeNote?.title || ''}
          />
        )}
      </div>
    </div>
  );
};

export default App;