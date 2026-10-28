import { useMemo, useState } from 'react'
import type { Citation } from '@/lib/api'
import { CitationFootnote } from '@/components/CitationFootnote'
import { MessageContent } from '@/components/MessageContent'
import { Sparkle, Copy, Check } from 'lucide-react'

interface ChatBubbleProps {
  role: 'user' | 'assistant'
  text: string
  citations: Citation[]
}

function AssistantAvatar() {
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-foreground text-background">
      <Sparkle size={14} />
    </div>
  )
}

export function ChatBubble({ role, text, citations }: ChatBubbleProps) {
  const isUser = role === 'user'
  const [copied, setCopied] = useState(false)
  const [openNumber, setOpenNumber] = useState<number | null>(null)

  // Deduplicate citations by chunk_id, preserving first-appearance order —
  // this is what makes "[1]" always mean the same source even if the LLM
  // cites the same chunk more than once, matching real footnote behavior.
  const numberedCitations = useMemo(() => {
    const seen = new Map<number, Citation>()
    for (const citation of citations) {
      if (!seen.has(citation.chunk_id)) seen.set(citation.chunk_id, citation)
    }
    return Array.from(seen.values()).map((citation, i) => ({ number: i + 1, citation }))
  }, [citations])

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  function handleCitationClick(number: number) {
    setOpenNumber((current) => (current === number ? null : number))
  }

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl bg-primary px-4 py-2 text-primary-foreground">
          <p className="text-sm">{text}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2">
      <AssistantAvatar />
      <div className="flex max-w-[75%] flex-col gap-2 rounded-2xl bg-muted px-4 py-2">
        <MessageContent text={text} onCitationClick={handleCitationClick} />

        {numberedCitations.length > 0 && (
          <div className="flex flex-col gap-0.5 border-t pt-2">
            {numberedCitations.map(({ number, citation }) => (
              <CitationFootnote
                key={citation.chunk_id}
                number={number}
                citation={citation}
                isOpen={openNumber === number}
                onToggle={() => setOpenNumber((cur) => (cur === number ? null : number))}
              />
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={handleCopy}
          className="flex w-fit items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </div>
  )
}