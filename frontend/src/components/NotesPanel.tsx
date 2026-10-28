import { useEffect, useRef, useState } from 'react'
import { useNotes } from '@/hooks/useNotes'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/Skeleton'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { StickyNote, Plus, Trash2, Download, ArrowLeft } from 'lucide-react'

const AUTOSAVE_DELAY_MS = 1000

function downloadNote(title: string | null, content: string) {
  const filename = `${(title ?? 'Untitled note').replace(/[^\w\- ]/g, '')}.txt`
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function NotesPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [activeNoteId, setActiveNoteId] = useState<number | null>(null)
  const [draftTitle, setDraftTitle] = useState('')
  const [draftContent, setDraftContent] = useState('')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')
  const { notes, isLoading, error, isCreating, createNote, updateNote, deleteNote } = useNotes()

  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const activeNote = notes.find((n) => n.id === activeNoteId) ?? null

  useEffect(() => {
    if (!activeNote) return
    setDraftTitle(activeNote.title ?? '')
    setDraftContent(activeNote.content)
  }, [activeNoteId]) // eslint-disable-line react-hooks/exhaustive-deps

  function scheduleAutosave(title: string, content: string) {
    if (!activeNoteId) return
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current)
    setSaveStatus('saving')
    saveTimeoutRef.current = setTimeout(async () => {
      await updateNote(activeNoteId, { title: title || 'Untitled note', content })
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 1200)
    }, AUTOSAVE_DELAY_MS)
  }

  function handleTitleChange(value: string) {
    setDraftTitle(value)
    scheduleAutosave(value, draftContent)
  }

  function handleContentChange(value: string) {
    setDraftContent(value)
    scheduleAutosave(draftTitle, value)
  }

  async function handleNewNote() {
    const note = await createNote()
    if (note) setActiveNoteId(note.id)
  }

  async function handleDelete(noteId: number) {
    const confirmed = window.confirm('Delete this note? This cannot be undone.')
    if (!confirmed) return
    const deleted = await deleteNote(noteId)
    if (deleted && activeNoteId === noteId) setActiveNoteId(null)
  }

  return (
    <Sheet open={isOpen} onOpenChange={(open) => { setIsOpen(open); if (!open) setActiveNoteId(null) }}>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
        aria-label="Notes"
      >
        <StickyNote size={18} />
      </button>
      <SheetContent side="right" className="flex w-96 flex-col gap-0 p-0 sm:max-w-96">
        {activeNote ? (
          <>
            <SheetHeader className="flex-row items-center gap-2 space-y-0 border-b px-4 py-3">
              <button
                type="button"
                onClick={() => setActiveNoteId(null)}
                className="flex h-7 w-7 items-center justify-center rounded-md hover:bg-muted"
                aria-label="Back to notes list"
              >
                <ArrowLeft size={16} />
              </button>
              <SheetTitle className="sr-only">Edit note</SheetTitle>
              <Input
                value={draftTitle}
                onChange={(e) => handleTitleChange(e.target.value)}
                placeholder="Untitled note"
                className="h-8 flex-1 border-none px-0 text-base font-medium shadow-none focus-visible:ring-0"
              />
              <button
                type="button"
                onClick={() => downloadNote(draftTitle, draftContent)}
                className="flex h-7 w-7 items-center justify-center rounded-md hover:bg-muted"
                aria-label="Download note"
              >
                <Download size={16} />
              </button>
            </SheetHeader>
            <Textarea
              value={draftContent}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleContentChange(e.target.value)}
              placeholder="Write anything you want to remember while researching..."
              className="flex-1 resize-none rounded-none border-none p-4 shadow-none focus-visible:ring-0"
            />
            <div className="border-t px-4 py-2 text-xs text-muted-foreground">
              {saveStatus === 'saving' && 'Saving…'}
              {saveStatus === 'saved' && 'Saved'}
            </div>
          </>
        ) : (
          <>
            <SheetHeader className="flex-row items-center justify-between space-y-0 border-b px-4 py-3">
              <SheetTitle>Notes</SheetTitle>
              <Button size="sm" onClick={handleNewNote} disabled={isCreating}>
                <Plus size={14} className="mr-1" />
                New
              </Button>
            </SheetHeader>
            <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-4">
              {isLoading && (
                <div className="flex flex-col gap-2">
                  <Skeleton className="h-14 w-full" />
                  <Skeleton className="h-14 w-full" />
                </div>
              )}
              {error && <p className="text-sm text-destructive">{error}</p>}
              {!isLoading && !error && notes.length === 0 && (
                <p className="text-sm text-muted-foreground">No notes yet.</p>
              )}
              {notes.map((note) => (
                <div
                  key={note.id}
                  className="group flex items-center gap-1 rounded-lg border px-3 py-2 hover:bg-muted/50"
                >
                  <button
                    type="button"
                    onClick={() => setActiveNoteId(note.id)}
                    className="flex-1 truncate text-left text-sm font-medium"
                  >
                    {note.title || 'Untitled note'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(note.id)}
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md opacity-0 hover:bg-muted group-hover:opacity-100"
                    aria-label="Delete note"
                  >
                    <Trash2 size={14} className="text-destructive" />
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}