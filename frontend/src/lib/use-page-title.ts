import { useContext, useEffect } from 'react'
import { PageTitleContext } from '@/lib/page-title-context'

/**
 * Lets a page set the title shown in the header next to "Document Copilot"
 * (e.g. the active thread's name). Clears itself on unmount so navigating
 * away doesn't leave a stale title in the header.
 */
export function usePageTitle(title: string | null) {
  const { setPageTitle } = useContext(PageTitleContext)

  useEffect(() => {
    setPageTitle(title)
    return () => setPageTitle(null)
  }, [title, setPageTitle])
}