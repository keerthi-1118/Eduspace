// frontend/components/KnowledgeHub.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Link as LinkIcon, File, Star, Tag, Plus, Sparkles, Search } from 'lucide-react';
import { uploadFile } from '../services/uploadService';
import { getNotes, generateSummary, searchResources } from '../services/api';
import { summarizeText } from '../services/geminiService';
import { toast } from 'react-hot-toast';
import SummaryModal from './SummaryModal';

interface Note {
  id: string;
  title: string;
  type: 'pdf' | 'docx' | 'image' | 'url' | 'other';
  url: string;
  tags: string[];
  uploadDate: string;
  rating: number;
  size?: string;
  uploader: {
    name: string;
    avatarUrl?: string;
  };
  content?: string;
  summary?: string;
}

const KnowledgeHub: React.FC<{ onSummarize?: (note: Note) => void }> = ({ onSummarize }) => {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
  const [summary, setSummary] = useState('');
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newNote, setNewNote] = useState<{
    title: string;
    content: string;
    type: 'TEXT' | 'LINK' | 'FILE';
    subject: string;
    tags: string[];
    file: File | null;
    is_public: boolean;
  }>({
    title: '',
    content: '',
    type: 'TEXT',
    subject: '',
    tags: [],
    file: null,
    is_public: false,
  });

  const availableTags = ['Algorithms', 'Mathematics', 'Physics', 'AI', 'ML', 'CSE', 'BBA'];
  const subjects = ['B.Tech CSE', 'B.Tech ECE', 'B.Tech ME', 'MBA', 'BBA', 'BCA'];
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getFileTypeFromUrl = (url: string): 'pdf' | 'docx' | 'image' | 'url' | 'other' => {
    if (!url) return 'other';
    if (url.includes('.pdf')) return 'pdf';
    if (url.includes('.docx') || url.includes('.doc')) return 'docx';
    if (url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return 'image';
    if (url.startsWith('http')) return 'url';
    return 'other';
  };

  // Helper function to convert backend note to frontend format
  const convertBackendNoteToFrontend = (note: any): Note => {
    // Determine note type from file_url and summary
    let noteType: 'pdf' | 'docx' | 'image' | 'url' | 'other' = 'other';
    const fileUrl = note.file_url || '';
    
    // Check if file_url is None, null, or empty - indicates TEXT note
    if (!fileUrl || fileUrl === '' || fileUrl === 'None' || fileUrl === null) {
      // If no file_url but has summary, it's a text note
      if (note.summary) {
        noteType = 'other'; // TEXT note
      }
    } else if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
      // Check if it's a link (URL) or a file URL
      if (fileUrl.includes('.pdf')) {
        noteType = 'pdf';
      } else if (fileUrl.includes('.docx') || fileUrl.includes('.doc')) {
        noteType = 'docx';
      } else if (fileUrl.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
        noteType = 'image';
      } else if (!fileUrl.includes('/uploads/') && !fileUrl.includes('cloudinary') && !fileUrl.includes('res.cloudinary.com')) {
        // If it's a URL but not a file URL, it's a link
        noteType = 'url';
      } else {
        noteType = getFileTypeFromUrl(fileUrl);
      }
    } else {
      noteType = getFileTypeFromUrl(fileUrl);
    }
    
    return {
      id: note.id.toString(),
      title: note.title,
      type: noteType,
      url: fileUrl && fileUrl !== 'None' && fileUrl !== null ? fileUrl : (noteType === 'url' && note.summary ? note.summary : (noteType === 'other' ? '#' : '#')),
      tags: [], // Backend doesn't store tags yet, can be extended
      uploadDate: note.created_at || new Date().toISOString(),
      rating: 0,
      size: '', // Can be calculated if needed
      uploader: {
        name: 'You',
        avatarUrl: ''
      },
      content: note.extracted_content || note.summary || '', // Use extracted_content for files, summary for TEXT/LINK
      summary: note.summary || ''
    };
  };

  // Fetch notes from backend
  useEffect(() => {
    const fetchNotes = async () => {
      try {
        setIsLoading(true);
        const backendNotes = await getNotes();
        // Convert backend notes to frontend format using helper function
        const formattedNotes: Note[] = backendNotes.map((note: any) => convertBackendNoteToFrontend(note));
        setNotes(formattedNotes);
      } catch (error) {
        console.error('Error fetching notes:', error);
        toast.error('Failed to load notes');
      } finally {
        setIsLoading(false);
      }
    };

    fetchNotes();
  }, []);

  // Handle search
  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.trim().length < 2) {
      // Reset to all notes if search is too short
      try {
        const backendNotes = await getNotes();
        const formattedNotes: Note[] = backendNotes.map((note: any) => convertBackendNoteToFrontend(note));
        setNotes(formattedNotes);
        setIsSearching(false);
      } catch (error) {
        console.error('Error fetching notes:', error);
      }
      return;
    }

    try {
      setIsSearching(true);
      const results = await searchResources(query);
      const formattedNotes: Note[] = results.map((note: any) => convertBackendNoteToFrontend(note));
      setNotes(formattedNotes);
    } catch (error) {
      console.error('Error searching notes:', error);
      toast.error('Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const handleGenerateSummary = async (note: Note) => {
    setSelectedNote(note);
    setIsSummaryModalOpen(true);
    setIsGeneratingSummary(true);
    setSummaryError(null);
    setSummary('');

    try {
      // Use note content or generate from note ID
      const noteId = parseInt(note.id);
      const text = note.content || note.summary || `Summarize the document: ${note.title}`;
      
      const result = await summarizeText(text, noteId);
      setSummary(result);
    } catch (err: any) {
      setSummaryError(err.message || 'Failed to generate summary. Please try again.');
      console.error(err);
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FileText className="text-red-500 w-5 h-5" />;
      case 'docx':
        return <File className="text-blue-500 w-5 h-5" />;
      case 'image':
        return <File className="text-green-500 w-5 h-5" />;
      default:
        return <File className="text-gray-500 w-5 h-5" />;
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size should be less than 10MB');
        return;
      }
      setNewNote(prev => ({
        ...prev,
        file,
        title: prev.title || file.name.split('.')[0]
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted!', { newNote, isSubmitting });

    // Validation
    if (!newNote.title.trim()) {
      console.error('Validation failed: No title');
      toast.error('Please enter a title');
      return;
    }

    if (newNote.type === 'LINK' && (!newNote.content || !newNote.content.trim().startsWith('http'))) {
      console.error('Validation failed: Invalid URL for LINK type', newNote.content);
      toast.error('Please enter a valid URL');
      return;
    }

    if (newNote.type === 'TEXT' && !newNote.content.trim()) {
      console.error('Validation failed: No content for TEXT type');
      toast.error('Please enter text content');
      return;
    }

    if (newNote.type === 'FILE' && !newNote.file) {
      console.error('Validation failed: No file for FILE type');
      toast.error('Please upload a file');
      return;
    }

    console.log('Validation passed, starting upload...');
    setIsSubmitting(true);
    
    try {
      const formData = new FormData();
      formData.append('title', newNote.title.trim());
      formData.append('type', newNote.type);
      
      // Always send subject, even if empty
      formData.append('subject', newNote.subject || '');
      formData.append('is_public', String(newNote.is_public));
      
      // Send tags as comma-separated string for easier backend handling
      if (newNote.tags.length > 0) {
        formData.append('tags', newNote.tags.join(','));
      }
      
      // Append file only if it exists (FILE type)
      if (newNote.type === 'FILE' && newNote.file) {
        formData.append('file', newNote.file);
      }
      
      // Append content for TEXT and LINK types
      if (newNote.type === 'TEXT' || newNote.type === 'LINK') {
        if (newNote.content && newNote.content.trim()) {
          formData.append('content', newNote.content.trim());
        }
      } else if (newNote.type === 'FILE' && newNote.content && newNote.content.trim()) {
        // Optional description for files
        formData.append('content', newNote.content.trim());
      }

      console.log('Submitting form data:', {
        title: newNote.title,
        type: newNote.type,
        hasFile: newNote.file !== null,
        contentLength: newNote.content?.length || 0,
        subject: newNote.subject,
        tags: newNote.tags,
      });

      // Log FormData contents
      console.log('FormData contents:');
      for (const [key, value] of formData.entries()) {
        // Check if value is a File object (more reliable check)
        if (value && typeof value === 'object' && 'name' in value && 'size' in value && 'type' in value) {
          const file = value as File;
          console.log(`  ${key}: File(${file.name}, ${file.size} bytes, ${file.type})`);
        } else {
          console.log(`  ${key}: ${value}`);
        }
      }

      console.log('Calling uploadFile service...');
      const response = await uploadFile(formData);
      console.log('Upload successful:', response);

      // Immediately add the uploaded note to the list (optimistic update)
      const uploadedNote: Note = {
        id: response.id,
        title: response.title,
        type: response.type === 'text' ? 'other' : (response.type === 'link' ? 'url' : getFileTypeFromUrl(response.url || '')),
        url: response.url || '#',
        tags: response.tags || [],
        uploadDate: response.uploadDate || new Date().toISOString(),
        rating: 0,
        size: response.size,
        uploader: {
          name: 'You',
          avatarUrl: ''
        },
        content: response.content || '',
        summary: response.content || ''
      };
      
      // Add to beginning of list for immediate feedback
      setNotes(prevNotes => [uploadedNote, ...prevNotes]);

      // Refresh notes list from backend to ensure consistency
      try {
        const backendNotes = await getNotes();
        // Convert backend notes to frontend format using helper function
        const formattedNotes: Note[] = backendNotes.map((note: any) => convertBackendNoteToFrontend(note));
        setNotes(formattedNotes);
      } catch (error) {
        console.error('Error refreshing notes:', error);
        // If refresh fails, keep the optimistic update
      }

      setIsUploadModalOpen(false);
      setNewNote({
        title: '',
        content: '',
        type: 'TEXT',
        subject: '',
        tags: [],
        file: null,
        is_public: false,
      });
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      toast.success(response.message || 'Note saved successfully!');
    } catch (error: any) {
      console.error('=== UPLOAD ERROR IN COMPONENT ===');
      console.error('Error:', error);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      const errorMessage = error.message || 'Failed to upload note. Please try again.';
      toast.error(errorMessage);
      // Don't close modal on error so user can try again
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-blue-900">Knowledge Hub</h1>
        <button
          onClick={() => setIsUploadModalOpen(true)}
          className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          Upload Notes
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search notes by title, content, or summary..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">Upload New Note</h2>
              <button 
                onClick={() => !isSubmitting && setIsUploadModalOpen(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Note Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Note Type</label>
                <div className="grid grid-cols-3 gap-2">
                  {['TEXT', 'LINK', 'FILE'].map(type => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => {
                        setNewNote(prev => ({ 
                          ...prev, 
                          type: type as any,
                          // Clear file and content when switching types to avoid confusion
                          file: type !== 'FILE' ? null : prev.file,
                          content: type === 'FILE' ? '' : prev.content
                        }));
                        // Reset file input if switching away from FILE type
                        if (type !== 'FILE' && fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                      className={`flex flex-col items-center justify-center p-3 border rounded-lg ${
                        newNote.type === type
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {type === 'TEXT' && <FileText className="h-5 w-5 text-blue-600" />}
                      {type === 'LINK' && <LinkIcon className="h-5 w-5 text-blue-600" />}
                      {type === 'FILE' && <File className="h-5 w-5 text-blue-600" />}
                      <span className="mt-1 text-sm">{type}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-1">Title *</label>
                <input
                  type="text"
                  value={newNote.title}
                  onChange={(e) => setNewNote(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
                  required
                />
              </div>

              {/* Type-dependent Input */}
              {newNote.type === 'LINK' && (
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-1">URL *</label>
                  <input
                    type="url"
                    value={newNote.content}
                    onChange={(e) => setNewNote(prev => ({ ...prev, content: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="https://example.com"
                    required
                  />
                </div>
              )}
              {newNote.type === 'FILE' && (
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-1">Upload File *</label>
                  <div className="flex items-center justify-center border-2 border-dashed border-gray-300 p-4 rounded-lg">
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      onChange={handleFileUpload}
                      accept=".pdf,.docx,.jpg,.png"
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Select File
                    </button>
                  </div>
                  {newNote.file && (
                    <p className="mt-2 text-sm text-gray-700">{newNote.file.name}</p>
                  )}
                </div>
              )}
              {newNote.type === 'TEXT' && (
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-1">Content *</label>
                  <textarea
                    value={newNote.content}
                    onChange={(e) => setNewNote(prev => ({ ...prev, content: e.target.value }))}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
                    placeholder="Write your note content here..."
                  />
                </div>
              )}

              {/* Subject */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-1">Subject</label>
                <select
                  value={newNote.subject}
                  onChange={(e) => setNewNote(prev => ({ ...prev, subject: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
                >
                  <option value="">Select subject</option>
                  {subjects.map(subject => (
                    <option key={subject} value={subject}>{subject}</option>
                  ))}
                </select>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-1">Tags</label>
                <div className="flex flex-wrap gap-2">
                  {availableTags.map(tag => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => {
                        setNewNote(prev => ({
                          ...prev,
                          tags: prev.tags.includes(tag)
                            ? prev.tags.filter(t => t !== tag)
                            : [...prev.tags, tag],
                        }));
                      }}
                      className={`px-3 py-1 rounded-full text-sm ${
                        newNote.tags.includes(tag)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      <Tag className="inline w-3 h-3 mr-1" /> {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* Public Toggle */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={newNote.is_public}
                  onChange={(e) => setNewNote(prev => ({ ...prev, is_public: e.target.checked }))}
                  className="mr-2"
                />
                <label className="text-sm text-gray-900">Make this note public</label>
              </div>

              {/* Submit */}
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsUploadModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {isSubmitting ? 'Uploading...' : 'Upload Note'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Notes Grid */}
      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-gray-600">Loading notes...</p>
        </div>
      ) : notes.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600">
            {isSearching ? 'No notes found matching your search.' : 'No notes yet. Upload your first note to get started!'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {notes.map(note => (
          <div
            key={note.id}
            className="border rounded-lg shadow-sm p-4 hover:shadow-md transition"
          >
            <div className="flex items-center mb-3">
              {getFileIcon(note.type)}
              <h3 className="ml-3 font-semibold text-lg text-white-900 truncate" title={note.title}>
                {note.title}
              </h3>
            </div>
            <p className="text-sm text-gray-600 mb-2">{note.size} • {new Date(note.uploadDate).toLocaleDateString()}</p>
            <div className="flex flex-wrap gap-2 mb-3">
              {note.tags.map(tag => (
                <span key={tag} className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">{tag}</span>
              ))}
            </div>
            <div className="flex flex-col space-y-2 mt-4">
              {(note.type === 'url' || note.type === 'pdf' || note.type === 'docx' || note.type === 'image') && note.url && note.url !== '#' ? (
                <button 
                  onClick={() => window.open(note.url, '_blank')}
                  className="w-full py-2 px-3 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm font-medium flex items-center justify-center"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  {note.type === 'url' ? 'Open Link' : 'Open File'}
                </button>
              ) : note.type === 'other' && note.content ? (
                <button 
                  onClick={() => setSelectedNote(note)}
                  className="w-full py-2 px-3 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm font-medium flex items-center justify-center"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  View Content
                </button>
              ) : null}
              {note.content && (
                <button 
                  onClick={() => handleGenerateSummary(note)}
                  className="w-full py-2 px-3 bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors text-sm font-medium flex items-center justify-center"
                  disabled={isGeneratingSummary}
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  {isGeneratingSummary ? 'Generating...' : 'AI Summary'}
                </button>
              )}
            </div>
          </div>
        ))}
        </div>
      )}

      {/* Note Detail Modal */}
      {selectedNote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">{selectedNote.title}</h2>
              <button 
                onClick={() => setSelectedNote(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                &times;
              </button>
            </div>
            
            <div className="mb-4">
              <div className="flex items-center text-sm text-gray-600 mb-2">
                <span className="mr-4">Type: {selectedNote.type.toUpperCase()}</span>
                {selectedNote.size && <span className="mr-4">Size: {selectedNote.size}</span>}
                <span>Uploaded: {new Date(selectedNote.uploadDate).toLocaleDateString()}</span>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-4">
                {selectedNote.tags.map(tag => (
                  <span key={tag} className="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                {selectedNote.type === 'url' ? (
                  <div>
                    <a 
                      href={selectedNote.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline break-all"
                    >
                      {selectedNote.url}
                    </a>
                    {selectedNote.summary && selectedNote.summary !== selectedNote.url && (
                      <p className="mt-2 text-gray-700">{selectedNote.summary}</p>
                    )}
                  </div>
                ) : selectedNote.type === 'other' && selectedNote.content ? (
                  <div className="p-4 bg-white rounded border">
                    <p className="text-gray-800 whitespace-pre-wrap">{selectedNote.content}</p>
                  </div>
                ) : selectedNote.url && selectedNote.url !== '#' ? (
                  <div className="p-4 bg-white rounded border">
                    <p className="text-blue-800">File: {selectedNote.title}</p>
                    <a 
                      href={selectedNote.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-block mt-2 text-blue-600 hover:underline"
                    >
                      View/Download File
                    </a>
                  </div>
                ) : (
                  <div className="p-4 bg-white rounded border">
                    <p className="text-gray-600">No content available</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between text-sm text-gray-600 pt-4 border-t">
              <div className="flex items-center">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium mr-2">
                  {selectedNote.uploader.name.charAt(0).toUpperCase()}
                </div>
                <span className="text-gray-900">{selectedNote.uploader.name}</span>
              </div>
              <div className="flex items-center">
                <Star className="w-4 h-4 text-yellow-400 mr-1" />
                <span className="text-gray-900">{selectedNote.rating.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Modal */}
      {isSummaryModalOpen && selectedNote && (
        <SummaryModal
          isOpen={isSummaryModalOpen}
          onClose={() => {
            setIsSummaryModalOpen(false);
            setSelectedNote(null);
            setSummary('');
            setSummaryError(null);
          }}
          summary={summary}
          isLoading={isGeneratingSummary}
          error={summaryError}
          noteTitle={selectedNote.title}
        />
      )}
    </div>
  );
};

export default KnowledgeHub;
