import { useCallback, useEffect, useState } from 'react'

function readSet(key: string, fallback: string[]): Set<string> {
  try {
    const raw = localStorage.getItem(key)
    return new Set(raw ? (JSON.parse(raw) as string[]) : fallback)
  } catch {
    return new Set(fallback)
  }
}

function useIdSet(key: string, fallback: string[]) {
  const [ids, setIds] = useState<Set<string>>(() => readSet(key, fallback))

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify([...ids]))
  }, [key, ids])

  const toggle = useCallback((id: string) => {
    setIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const add = useCallback((id: string) => {
    setIds((prev) => new Set(prev).add(id))
  }, [])

  return { ids, toggle, add }
}

export function useJobInteractions(
  defaultLikedIds: string[],
  defaultAppliedIds: string[],
) {
  const liked = useIdSet('jobnova:liked', defaultLikedIds)
  const applied = useIdSet('jobnova:applied', defaultAppliedIds)

  return {
    likedIds: liked.ids,
    toggleLiked: liked.toggle,
    appliedIds: applied.ids,
    markApplied: applied.add,
  }
}
