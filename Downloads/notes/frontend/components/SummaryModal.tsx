import React from 'react';
import SparklesIcon from './icons/SparklesIcon';

interface SummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: string;
  isLoading: boolean;
  error: string | null;
  noteTitle: string;
}

const LoadingSpinner: React.FC = () => (
    <div className="flex flex-col items-center justify-center space-y-4">
        <div className="w-16 h-16 border-4 border-t-transparent border-accent-blue rounded-full animate-spin"></div>
        <p className="text-light-text animate-pulse">AI is thinking...</p>
    </div>
);


const SummaryModal: React.FC<SummaryModalProps> = ({
  isOpen,
  onClose,
  summary,
  isLoading,
  error,
  noteTitle,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="glassmorphism w-full max-w-2xl rounded-2xl p-6 md:p-8 flex flex-col max-h-[90vh] relative animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-gradient-to-br from-accent-blue to-accent-blue-light rounded-lg">
            <SparklesIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-light-text">AI StudyFlow Summary</h2>
            <p className="text-gray-400 text-sm">For: "{noteTitle}"</p>
          </div>
        </div>

        <div className="flex-grow overflow-y-auto pr-4 -mr-4 custom-scrollbar">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
                <LoadingSpinner />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64 bg-red-500/10 text-red-300 p-4 rounded-lg">
              <p>{error}</p>
            </div>
          ) : (
            <div className="prose prose-invert prose-p:text-gray-300 prose-headings:text-light-text prose-strong:text-accent-blue">
                <pre className="whitespace-pre-wrap font-sans text-base leading-relaxed">
                    {summary}
                </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SummaryModal;