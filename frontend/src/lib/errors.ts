import { ApiError } from '@/lib/http'

/**
 * Turns a raw error (from an API call, or a network/fetch failure) into
 * a consistent, user-friendly message. One place to own this copy so it
 * doesn't drift between pages — e.g. ChatListPage and ChatThreadPage both
 * use this instead of each writing their own guess at friendly wording.
 */
export function getFriendlyErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isNetworkError) {
      return "Can't reach the server. Check that the backend is running and try again."
    }

    switch (error.status) {
      case 401:
        return 'Your session has expired. Please sign in again.'
      case 403:
        return "You don't have permission to do that."
      case 404:
        return "That couldn't be found — it may have been deleted or never existed."
      case 422:
        return 'Something about that request was invalid. Please try again.'
      default:
        if (error.status >= 500) {
          return 'Something went wrong on our end. Please try again in a moment.'
        }
        return 'Something went wrong. Please try again.'
    }
  }

  return 'Something unexpected went wrong. Please try again.'
}