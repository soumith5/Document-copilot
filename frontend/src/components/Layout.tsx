import { useState } from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ThreadSidebar } from '@/components/ThreadSidebar'
import { AccountMenu } from '@/components/AccountMenu'
import { NotesPanel } from '@/components/NotesPanel'
import { PageTitleContext } from '@/lib/page-title-context'
import { useThreads } from '@/hooks/useThreads'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { PanelLeftClose, PanelLeftOpen, Search } from 'lucide-react'

export default function Layout() {
  const navigate = useNavigate()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [pageTitle, setPageTitle] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const { threads } = useThreads()

  const filteredThreads = threads.filter((t) =>
    (t.title ?? 'New Chat').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex h-screen overflow-hidden">
      {isSidebarOpen && (
        <div className="flex w-64 shrink-0 flex-col overflow-hidden border-r bg-muted/30">
          <div className="flex shrink-0 items-center gap-1 border-b px-4 py-2">
            <Link to="/chat" className="text-xl font-semibold">
              Document Copilot
            </Link>

            <DropdownMenu onOpenChange={(open) => !open && setSearch('')}>
              <DropdownMenuTrigger
                className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
                aria-label="Search chats"
              >
                <Search size={16} />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-64">
                <div className="p-2">
                  <Input
                    autoFocus
                    placeholder="Search chats..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
                {filteredThreads.length === 0 && (
                  <p className="px-3 py-2 text-sm text-muted-foreground">No chats found.</p>
                )}
                {filteredThreads.map((thread) => (
                  <DropdownMenuItem key={thread.id} onClick={() => navigate(`/chat/${thread.id}`)}>
                    {thread.title ?? 'New Chat'}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <ThreadSidebar />

          <div className="shrink-0 border-t p-3">
            <AccountMenu />
          </div>
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center justify-between px-6 py-2">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSidebarOpen((open) => !open)}
              aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
              {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
            </Button>

            {pageTitle && (
              <span className="text-[0.92rem] font-medium text-muted-foreground">
                {pageTitle}
              </span>
            )}
          </div>

          <NotesPanel />
        </header>
        <main className="flex flex-1 flex-col overflow-hidden">
          <PageTitleContext.Provider value={{ setPageTitle }}>
            <Outlet />
          </PageTitleContext.Provider>
        </main>
      </div>
    </div>
  )
}