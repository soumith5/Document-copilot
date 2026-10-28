import type { Citation } from '@/lib/api'

interface CitationFootnoteProps {
  number: number
  citation: Citation
  isOpen: boolean
  onToggle: () => void
}

export function CitationFootnote({ number, citation, isOpen, onToggle }: CitationFootnoteProps) {
  const label = [citation.ticker, citation.filing_type, citation.filing_date]
    .filter(Boolean)
    .join(' · ')

  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs hover:bg-foreground/5"
      >
        <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-foreground text-background text-[0.6rem]">
          {number}
        </span>
        <span className="text-muted-foreground">{label || `Chunk ${citation.chunk_id}`}</span>
      </button>

      {isOpen && (
        <div className="ml-6 mt-1 max-w-md rounded-md border bg-background p-3 text-sm shadow-sm">
          <div className="mb-1 font-semibold">
            {citation.company ?? citation.ticker ?? 'Source'}
            {citation.item_title && ` — ${citation.item_title}`}
          </div>
          {(citation.page_start || citation.page_end) && (
            <div className="mb-2 text-xs text-muted-foreground">
              Page {citation.page_start}
              {citation.page_end && citation.page_end !== citation.page_start
                ? `–${citation.page_end}`
                : ''}
            </div>
          )}
          <p className="whitespace-pre-wrap text-muted-foreground">{citation.excerpt}</p>
        </div>
      )}
    </div>
  )
}