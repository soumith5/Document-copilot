import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useChat } from '@ai-sdk/react'
import { TextStreamChatTransport } from 'ai'
import { supabase } from '@/lib/supabase'
import { env } from '@/lib/env'
import { api, type Message } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getFriendlyErrorMessage } from '@/lib/errors'
import { Skeleton } from '@/components/Skeleton'
import { ChatBubble } from '@/components/ChatBubble'
import { usePageTitle } from '@/lib/use-page-title'
import { ArrowDown, Sparkle } from 'lucide-react'

function toUIMessage(message: Message) {
  return {
    id: String(message.id),
    role: message.role as 'user' | 'assistant',
    parts: [{ type: 'text' as const, text: message.content }],
  }
}

function ThinkingIndicator({ status }: { status: 'submitted' | 'streaming' }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-foreground text-background">
        <Sparkle size={14} className="animate-pulse" />
      </div>
      <span className="text-sm text-muted-foreground">
        {status === 'submitted' ? 'Searching filings…' : 'Writing the answer…'}
      </span>
    </div>
  )
}

const SUGGESTED_QUESTIONS = [
  "Across Apple's 2021–2025 10-Ks, how did the revenue mix between iPhone, Services, Mac, iPad, and Wearables change?",
  'For Amazon, compare AWS operating income and margin against North America and International from 2021–2025.',
  'How did NVIDIA describe demand drivers, customer concentration, and supply constraints for its Data Center business?',
  'Across Microsoft filings, what changed in how the company describes Azure, AI infrastructure, and cloud capacity constraints?',
]

const NEAR_BOTTOM_THRESHOLD = 80
const AUTO_TITLE_MAX_LENGTH = 60

function truncateForTitle(text: string): string {
  const trimmed = text.trim()
  if (trimmed.length <= AUTO_TITLE_MAX_LENGTH) return trimmed
  return trimmed.slice(0, AUTO_TITLE_MAX_LENGTH).trimEnd() + '…'
}

export default function ChatThreadPage() {
  const { threadId } = useParams<{ threadId: string }>()
  const [input, setInput] = useState('')
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [citationsByMessageId, setCitationsByMessageId] = useState<Record<string, Message['citations']>>({})
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)
  const [threadTitle, setThreadTitle] = useState<string | null>(null)
  // Tracks whether this chat had a real (non-null) title when it was
  // loaded, so auto-titling only fires for genuinely untitled chats and
  // never overwrites a title the user (or a previous auto-title) already set.
  const hadTitleOnLoad = useRef(false)

  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const previousMessageCount = useRef(0)

  const transport = useMemo(
    () =>
      new TextStreamChatTransport({
        api: `${env.apiBaseUrl}/chat/stream`,
        headers: async () => {
          const { data } = await supabase.auth.getSession()
          return {
            Authorization: `Bearer ${data.session?.access_token ?? ''}`,
          }
        },
        prepareSendMessagesRequest: ({ messages: outgoingMessages }) => ({
          body: {
            thread_id: Number(threadId),
            messages: outgoingMessages,
          },
        }),
      }),
    [threadId]
  )

  const { messages, sendMessage, status, error, setMessages } = useChat({ transport })

  useEffect(() => {
    if (!threadId) return

    setIsLoadingHistory(true)
    setHistoryError(null)

    api
      .getThreadMessages(Number(threadId))
      .then((history) => {
        setMessages(history.map(toUIMessage))
        const citationMap: Record<string, Message['citations']> = {}
        for (const message of history) {
          citationMap[String(message.id)] = message.citations
        }
        setCitationsByMessageId(citationMap)
      })
      .catch((err) => {
        setHistoryError(getFriendlyErrorMessage(err))
      })
      .finally(() => setIsLoadingHistory(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId])

  useEffect(() => {
    if (!threadId) return
    api
      .listThreads()
      .then((threads) => {
        const match = threads.find((t) => t.id === Number(threadId))
        hadTitleOnLoad.current = Boolean(match?.title)
        setThreadTitle(match?.title ?? 'New Chat')
      })
      .catch(() => setThreadTitle('New Chat'))
  }, [threadId])

  usePageTitle(threadTitle)

  useEffect(() => {
    if (messages.length === 0) return
    const isInitialLoad = previousMessageCount.current === 0
    bottomRef.current?.scrollIntoView({ behavior: isInitialLoad ? 'auto' : 'smooth' })
    previousMessageCount.current = messages.length
  }, [messages.length, isLoadingHistory])

  function handleScroll() {
    const container = scrollContainerRef.current
    if (!container) return
    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight
    setShowScrollToBottom(distanceFromBottom > NEAR_BOTTOM_THRESHOLD)
  }

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  async function submitQuestion(text: string) {
    if (!text.trim()) return
    if (status !== 'ready') return
    if (!threadId) return

    // Auto-title: only for a chat that had no title when this page loaded
    // and has no messages yet (i.e. this is genuinely the first question).
    // Fire-and-forget — a failure here shouldn't block sending the message.
    if (!hadTitleOnLoad.current && messages.length === 0) {
      const newTitle = truncateForTitle(text)
      api
        .renameThread(Number(threadId), newTitle)
        .then(() => {
          setThreadTitle(newTitle)
          hadTitleOnLoad.current = true
        })
        .catch(() => {
          // Non-critical — chat still works, just keeps "New Chat" as its name.
        })
    }

    sendMessage({ text })
    setInput('')
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    submitQuestion(input)
  }

  const isBusy = status === 'submitted' || status === 'streaming'
  const isEmpty = !isLoadingHistory && messages.length === 0

  return (
    <div className="relative flex h-full flex-col">
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="relative flex-1 overflow-y-auto px-6 py-4"
      >
        {isLoadingHistory && (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-10 w-2/3 self-end" />
            <Skeleton className="h-10 w-3/4" />
          </div>
        )}
        {historyError && <p className="text-destructive">{historyError}</p>}

        {isEmpty && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <div>
              <h2 className="text-lg font-semibold">Ask about SEC filings</h2>
              <p className="text-sm text-muted-foreground">
                Every answer is grounded in source documents with citations.
              </p>
            </div>
            <div className="flex max-w-2xl flex-col gap-2">
              {SUGGESTED_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => submitQuestion(question)}
                  className="rounded-full border px-4 py-2 text-left text-sm hover:bg-muted"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-3">
          {messages
            .filter((message) => message.role === 'user' || message.role === 'assistant')
            .map((message) => {
              const citations = citationsByMessageId[message.id] ?? []
              const text = message.parts
                .filter((part) => part.type === 'text')
                .map((part) => part.text)
                .join('')

              return (
                <ChatBubble
                  key={message.id}
                  role={message.role as 'user' | 'assistant'}
                  text={text}
                  citations={citations}
                />
              )
            })}

          {isBusy && <ThinkingIndicator status={status as 'submitted' | 'streaming'} />}

          {status === 'error' && (
            <p className="text-destructive">
              {error?.message ?? 'Something went wrong generating a response. Please try again.'}
            </p>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {showScrollToBottom && (
        <button
          type="button"
          onClick={scrollToBottom}
          aria-label="Scroll to bottom"
          className="absolute bottom-24 left-1/2 flex h-9 w-9 -translate-x-1/2 items-center justify-center rounded-full border bg-background shadow-md hover:bg-muted"
        >
          <ArrowDown size={16} />
        </button>
      )}

      <form onSubmit={handleSubmit} className="flex shrink-0 gap-2 border-t p-4">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isBusy}
          placeholder={isBusy ? 'Waiting for a response…' : 'Ask a question...'}
        />
        <Button type="submit" disabled={isBusy || !input.trim()}>
          {isBusy ? 'Thinking…' : 'Send'}
        </Button>
      </form>
    </div>
  )
}