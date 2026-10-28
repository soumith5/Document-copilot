import { createContext } from 'react'

export interface PageTitleContextValue {
  setPageTitle: (title: string | null) => void
}

export const PageTitleContext = createContext<PageTitleContextValue>({
  setPageTitle: () => {},
})