import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { remarkCitationRefs } from '@/lib/citation-markdown-plugin'

interface MessageContentProps {
  text: string
  /** Maps a 1-based citation number (as emitted by the LLM, e.g. "[1]") to
   * a click handler — see ChatBubble.tsx, which builds this from the
   * message's citations list deduplicated by chunk_id. */
  onCitationClick?: (citationNumber: number) => void
}

export function MessageContent({ text, onCitationClick }: MessageContentProps) {
  return (
    <div className="flex flex-col gap-2 text-sm [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:font-semibold [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-muted-foreground/30 [&_th]:px-2 [&_th]:py-1 [&_td]:border [&_td]:border-muted-foreground/30 [&_td]:px-2 [&_td]:py-1 [&_h3]:font-semibold [&_h3]:mt-2">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkCitationRefs]}
        components={{
          // @ts-expect-error — custom element from the citation-ref plugin, not a standard HTML tag
          'citation-ref': ({ 'data-citation-number': num }: { 'data-citation-number': string }) => (
            <button
              type="button"
              onClick={() => onCitationClick?.(Number(num))}
              className="mx-0.5 inline-flex h-4 w-4 items-center justify-center rounded-full bg-foreground/10 align-super text-[0.6rem] font-medium leading-none hover:bg-foreground/20"
            >
              {num}
            </button>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}