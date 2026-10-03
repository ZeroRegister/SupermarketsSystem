export type StockHealth = 'healthy' | 'low' | 'out'

export function stockHealth(quantity: number, reorderThreshold: number): StockHealth {
  if (quantity <= 0) return 'out'
  if (quantity <= reorderThreshold) return 'low'
  return 'healthy'
}

export function stockStatusLabel(quantity: number, reorderThreshold: number): string {
  const state = stockHealth(quantity, reorderThreshold)
  return state === 'out' ? 'Out of stock' : state === 'low' ? 'Low stock' : 'In stock'
}
