import { useEffect, useState } from 'react'
import { api, type Thread } from '@/lib/api'
import { getFriendlyErrorMessage } from '@/lib/errors'

export function useThreads() {
  const [threads, setThreads] = useState<Thread[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    api
      .listThreads()
      .then(setThreads)
      .catch((err) => setError(getFriendlyErrorMessage(err)))
      .finally(() => setIsLoading(false))
  }, [])

  async function createThread(): Promise<Thread | null> {
    setIsCreating(true)
    try {
      const thread = await api.createThread()
      setThreads((prev) => [thread, ...prev])
      return thread
    } catch (err) {
      setError(getFriendlyErrorMessage(err))
      return null
    } finally {
      setIsCreating(false)
    }
  }

  async function renameThread(threadId: number, title: string): Promise<boolean> {
    try {
      const updated = await api.renameThread(threadId, title)
      setThreads((prev) => prev.map((t) => (t.id === threadId ? updated : t)))
      return true
    } catch (err) {
      setError(getFriendlyErrorMessage(err))
      return false
    }
  }

  async function deleteThread(threadId: number): Promise<boolean> {
    try {
      await api.deleteThread(threadId)
      setThreads((prev) => prev.filter((t) => t.id !== threadId))
      return true
    } catch (err) {
      setError(getFriendlyErrorMessage(err))
      return false
    }
  }

  return { threads, isLoading, error, isCreating, createThread, renameThread, deleteThread }
}