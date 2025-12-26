import React from 'react';
import type { Note } from '../types';
import SparklesIcon from './icons/SparklesIcon';

interface NoteCardProps {
  note: Note;
  onSummarize: (note: Note) => void;
}

const NoteTypeBadge: React.FC<{ type: Note['type'] }> = ({ type }) => {
  const baseClasses = "px-2 py-1 text-xs font-semibold rounded-full";
  const typeStyles = {
    PDF: "bg-red-500/20 text-red-300",
    DOC: "bg-cyan-500/20 text-cyan-300",
    LINK: "bg-green-500/20 text-green-300",
    IMG: "bg-purple-500/20 text-purple-300",
  };
  return <span className={`${baseClasses} ${typeStyles[type]}`}>{type}</span>;
};

const NoteCard: React.FC<NoteCardProps> = ({ note, onSummarize }) => {
  return (
    <div className="glassmorphism rounded-xl p-5 flex flex-col h-full group transition-all duration-300 hover:transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-accent-blue/20">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-light-text pr-2 flex-1">{note.title}</h3>
        <NoteTypeBadge type={note.type} />
      </div>
      <p className="text-sm text-gray-400 mb-4">{note.subject}</p>
      
      <div className="flex-grow text-gray-400 text-sm mb-4 line-clamp-3">
        {note.content}
      </div>

      <div className="mt-auto">
        <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-2">
                <img src={note.uploader.avatarUrl} alt={note.uploader.name} className="w-8 h-8 rounded-full border-2 border-secondary" />
                <span className="text-xs text-gray-300">{note.uploader.name}</span>
            </div>
            <div className="flex items-center space-x-1 text-yellow-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                <span className="text-sm font-semibold">{note.rating}</span>
            </div>
        </div>
        <button
          onClick={() => onSummarize(note)}
          className="w-full bg-gradient-to-r from-accent-blue to-accent-blue-light text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all duration-300 transform hover:scale-105 hover:shadow-glow-blue"
        >
          <SparklesIcon className="w-5 h-5" />
          <span>AI StudyFlow</span>
        </button>
      </div>
    </div>
  );
};

export default NoteCard;