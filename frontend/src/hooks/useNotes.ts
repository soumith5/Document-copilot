import { useEffect, useState } from 'react'
import { api, type Note } from '@/lib/api'
import { getFriendlyErrorMessage } from '@/lib/errors'

export function useNotes() {
  const [notes, setNotes] = useState<Note[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    api
      .listNotes()
      .then(setNotes)
      .catch((err) => setError(getFriendlyErrorMessage(err)))
      .finally(() => setIsLoading(false))
  }, [])

  async function createNote(): Promise<Note | null> {
    setIsCreating(true)
    try {
      const note = await api.createNote()
      setNotes((prev) => [note, ...prev])
      return note
    } catch (err) {
      setError(getFriendlyErrorMessage(err))
      return null
    } finally {
      setIsCreating(false)
    }
  }

  async function updateNote(noteId: number, body: { title?: string; content?: string }): Promise<Note | null> {
    try {
      const updated = await api.updateNote(noteId, body)
      setNotes((prev) =>
        [...prev.filter((n) => n.id !== noteId), updated].sort(
          (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )
      )
      return updated
    } catch (err) {
      setError(getFriendlyErrorMessage(err))
      return null
    }
  }

  async function deleteNote(noteId: number): Promise<boolean> {
    try {
      await api.deleteNote(noteId)
      setNotes((prev) => prev.filter((n) => n.id !== noteId))
      return true
    } catch (err) {
      setError(getFriendlyErrorMessage(err))
      return false
    }
  }

  return { notes, isLoading, error, isCreating, createNote, updateNote, deleteNote }
}