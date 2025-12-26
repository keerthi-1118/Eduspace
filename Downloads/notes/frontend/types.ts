export interface Note {
  id: number;
  title: string;
  type: 'PDF' | 'DOC' | 'LINK' | 'IMG';
  subject: string;
  content: string; // This will hold the text content for summarization
  uploader: {
    name: string;
    avatarUrl: string;
  };
  rating: number;
}

export type View = 'home' | 'notes' | 'projects' | 'tasks';
