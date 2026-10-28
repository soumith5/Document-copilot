import { http } from '@/lib/http'

export interface Thread {
  id: number
  title: string | null
  created_at: string
}

export interface Citation {
  chunk_id: number
  ticker: string | null
  company: string | null
  filing_type: string | null
  filing_date: string | null
  item: string | null
  item_title: string | null
  page_start: number | null
  page_end: number | null
  excerpt: string
}

export interface Message {
  id: number
  thread_id: number
  role: string
  content: string
  created_at: string
  citations: Citation[]
}

export interface Note {
  id: number
  title: string | null
  content: string
  created_at: string
  updated_at: string
}

export const api = {
  listThreads: () => http.get<Thread[]>('/threads'),
  createThread: (title?: string) => http.post<Thread>('/threads', { title }),
  renameThread: (threadId: number, title: string) =>
    http.patch<Thread>(`/threads/${threadId}`, { title }),
  deleteThread: (threadId: number) => http.delete(`/threads/${threadId}`),
  getThreadMessages: (threadId: number) =>
    http.get<Message[]>(`/threads/${threadId}/messages`),

  listNotes: () => http.get<Note[]>('/notes'),
  createNote: (title?: string) => http.post<Note>('/notes', { title }),
  updateNote: (noteId: number, body: { title?: string; content?: string }) =>
    http.patch<Note>(`/notes/${noteId}`, body),
  deleteNote: (noteId: number) => http.delete(`/notes/${noteId}`),
}