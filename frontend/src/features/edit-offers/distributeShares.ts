export type EditableOffer = {
  id: number
  name: string
  share: number
  pinned: boolean
  removed: boolean
}

export function distributeShares(offers: EditableOffer[]): EditableOffer[] {
  const pinnedSum = offers
    .filter((o) => o.pinned && !o.removed)
    .reduce((sum, o) => sum + o.share, 0)

  if (pinnedSum > 100) {
    throw new Error('sum of pinned shares exceeds 100')
  }

  const remainder = 100 - pinnedSum
  const eligible = offers
    .map((o, i) => ({ o, i }))
    .filter(({ o }) => !o.removed && !o.pinned)
    .map(({ i }) => i)

  const distributed: Record<number, number> = {}
  if (eligible.length > 0) {
    const base = Math.floor(remainder / eligible.length)
    const extra = remainder % eligible.length
    eligible.forEach((idx, j) => {
      distributed[idx] = base + (j < extra ? 1 : 0)
    })
  }

  return offers.map((o, i) => {
    let share: number
    if (o.removed) {
      share = 0
    } else if (o.pinned) {
      share = o.share
    } else {
      share = distributed[i] ?? 0
    }
    return { ...o, share }
  })
}

export function sortOffers(offers: EditableOffer[]): EditableOffer[] {
  const active = offers.filter((o) => !o.removed)
  const removed = offers.filter((o) => o.removed)
  return [...active, ...removed]
}