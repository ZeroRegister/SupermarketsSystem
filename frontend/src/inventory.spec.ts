import { describe, expect, it } from 'vitest'
import { stockHealth, stockStatusLabel } from './inventory'

describe('inventory threshold boundaries', () => {
  it('marks zero as out of stock, including a zero threshold', () => {
    expect(stockHealth(0, 0)).toBe('out')
    expect(stockStatusLabel(0, 4)).toBe('Out of stock')
  })

  it('includes equality at the reorder threshold in the low-stock state', () => {
    expect(stockHealth(4, 4)).toBe('low')
    expect(stockStatusLabel(4, 4)).toBe('Low stock')
  })

  it('keeps positive stock above the threshold healthy', () => {
    expect(stockHealth(5, 4)).toBe('healthy')
    expect(stockHealth(1, 0)).toBe('healthy')
  })
})
