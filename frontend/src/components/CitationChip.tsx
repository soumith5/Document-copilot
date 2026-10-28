import { useState } from 'react'
import type { Citation } from '@/lib/api'

function formatCitationLabel(citation: Citation): string {
  const parts = [citation.ticker, citation.item].filter(Boolean)
  return parts.length > 0 ? parts.join(' · ') : `Chunk ${citation.chunk_id}`
}

export function CitationChip({ citation }: { citation: Citation }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="inline-block">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="rounded-full border border-muted-foreground/30 bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground hover:bg-muted-foreground/10"
      >
        {formatCitationLabel(citation)}
      </button>

      {isOpen && (
        <div className="mt-2 max-w-md rounded-md border bg-background p-3 text-sm shadow-sm">
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