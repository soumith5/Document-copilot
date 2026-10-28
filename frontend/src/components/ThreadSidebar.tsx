import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useThreads } from '@/hooks/useThreads'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/Skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreVertical, Pencil, Trash2 } from 'lucide-react'

export function ThreadSidebar() {
  const navigate = useNavigate()
  const { threadId: activeThreadId } = useParams<{ threadId: string }>()
  const { threads, isLoading, error, isCreating, createThread, renameThread, deleteThread } =
    useThreads()
  const [renamingId, setRenamingId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')

  async function handleNewThread() {
    const thread = await createThread()
    if (thread) navigate(`/chat/${thread.id}`)
  }

  function startRename(threadId: number, currentTitle: string | null) {
    setRenamingId(threadId)
    setRenameValue(currentTitle ?? 'New Chat')
  }

  async function confirmRename(threadId: number) {
    const trimmed = renameValue.trim()
    if (trimmed) await renameThread(threadId, trimmed)
    setRenamingId(null)
  }

  async function handleDelete(threadId: number) {
    const confirmed = window.confirm('Delete this chat and all its messages? This cannot be undone.')
    if (!confirmed) return

    const wasActive = String(threadId) === activeThreadId
    const deleted = await deleteThread(threadId)
    if (deleted && wasActive) navigate('/chat')
  }

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
      <Button onClick={handleNewThread} disabled={isCreating} size="sm">
        {isCreating ? 'Creating…' : 'New Chat'}
      </Button>

      {isLoading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {!isLoading && !error && threads.length === 0 && (
        <p className="text-sm text-muted-foreground">No chats yet.</p>
      )}

      <ul className="flex flex-col gap-2">
        {threads.map((thread) => {
          const isActive = String(thread.id) === activeThreadId
          const isRenaming = renamingId === thread.id

          return (
            <li
              key={thread.id}
              className={`group flex items-center gap-1 rounded-lg border px-3 py-2 ${
                isActive ? 'border-foreground/30 bg-muted' : 'border-transparent hover:bg-muted/50'
              }`}
            >
              {isRenaming ? (
                <Input
                  autoFocus
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  onBlur={() => confirmRename(thread.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') confirmRename(thread.id)
                    if (e.key === 'Escape') setRenamingId(null)
                  }}
                  className="h-7 flex-1 text-sm"
                />
              ) : (
                <Link to={`/chat/${thread.id}`} className="flex-1 truncate text-sm font-medium">
                  {thread.title ?? 'New Chat'}
                </Link>
              )}

              {!isRenaming && (
                <DropdownMenu>
                  <DropdownMenuTrigger
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md opacity-0 hover:bg-muted group-hover:opacity-100"
                    aria-label="Chat options"
                  >
                    <MoreVertical size={14} />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => startRename(thread.id, thread.title)}>
                      <Pencil size={14} className="mr-2" />
                      Rename
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => handleDelete(thread.id)}
                      className="text-destructive"
                    >
                      <Trash2 size={14} className="mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}