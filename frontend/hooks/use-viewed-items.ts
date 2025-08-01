import { useState, useEffect } from 'react'

const STORAGE_KEYS = {
  VIEWED_ITEMS: 'churchable-viewed-items'
} as const

const loadViewedItems = (): Set<string> => {
  if (typeof window === 'undefined') return new Set()
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.VIEWED_ITEMS)
    return stored ? new Set(JSON.parse(stored)) : new Set()
  } catch {
    return new Set()
  }
}

export function useViewedItems() {
  const [viewedItems, setViewedItems] = useState<Set<string>>(new Set())

  // Load viewed items on mount and listen for changes
  useEffect(() => {
    setViewedItems(loadViewedItems())

    // Listen for storage changes (when content-library updates viewed items)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEYS.VIEWED_ITEMS) {
        setViewedItems(loadViewedItems())
      }
    }

    // Listen for custom events from same tab (localStorage events only fire for other tabs)
    const handleViewedItemsUpdate = () => {
      setViewedItems(loadViewedItems())
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('viewed-items-updated', handleViewedItemsUpdate)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('viewed-items-updated', handleViewedItemsUpdate)
    }
  }, [])

  return viewedItems
}