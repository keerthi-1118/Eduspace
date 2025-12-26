export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

export interface Note {
  id: number;
  title: string;
  content: string;
  type: 'PDF' | 'DOCX' | 'LINK' | 'IMAGE' | 'TEXT';
  subject: string;
  uploader: User;
  rating: number;
  userRating?: number;
  tags: string[];
  url?: string;
  fileSize?: string;
  uploadDate: string;
  summary?: string;
}

export type Resource = Note;

export const MOCK_RESOURCES: Resource[] = [
  {
    id: 1,
    title: 'React Hooks Cheatsheet',
    type: 'PDF',
    subject: 'Web Development',
    content: 'React Hooks are functions that let you use state and other React features without writing classes.',
    uploader: { id: '1', name: 'Jane Doe', email: 'jane@example.com' },
    rating: 4.8,
    tags: ['react', 'frontend', 'javascript'],
    fileSize: '2.4 MB',
    uploadDate: '2023-05-15',
  },
  {
    id: 2,
    title: 'Data Structures in Python',
    type: 'DOCX',
    subject: 'Computer Science',
    content: 'Common data structures implemented in Python with examples and complexity analysis.',
    uploader: { id: '2', name: 'John Smith', email: 'john@example.com' },
    rating: 4.5,
    tags: ['python', 'algorithms', 'data-structures'],
    fileSize: '1.8 MB',
    uploadDate: '2023-06-20',
  },
  {
    id: 3,
    title: 'Machine Learning Basics',
    type: 'LINK',
    subject: 'Artificial Intelligence',
    content: 'A comprehensive guide to machine learning concepts and algorithms.',
    uploader: { id: '3', name: 'Alice Johnson', email: 'alice@example.com' },
    rating: 4.7,
    tags: ['ml', 'ai', 'data-science'],
    url: 'https://example.com/ml-basics',
    uploadDate: '2023-07-10',
  },
];
