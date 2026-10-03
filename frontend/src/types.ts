export type Role = 'ADMIN' | 'MANAGER' | 'CLERK'
export interface User { id: number; username: string; displayName: string; role: Role; enabled: boolean; createdAt: string }
export interface Product { id: number; sku: string; barcode: string | null; name: string; unit: string; price: number; quantity: number; safetyStock: number; reorderThreshold: number; category: string | null; supplier: string | null; active: boolean; updatedAt: string }
export interface Transaction { id: number; productId: number; productName: string; type: 'STOCK_IN' | 'STOCK_OUT' | 'ADJUSTMENT' | 'STOCKTAKE'; delta: number; quantityBefore: number; quantityAfter: number; reason: string; actor: string; createdAt: string }
export interface Warning { id: number; productId: number; sku: string; productName: string; type: 'LOW' | 'OUT' | 'RESTOCKED'; state: 'OPEN' | 'RESOLVED'; quantity: number; threshold: number; acknowledgedBy: string | null; acknowledgedAt: string | null; createdAt: string; expiresAt: string }
export interface Page<T> { items: T[]; page: number; size: number; totalElements: number; totalPages: number }
export interface Category { id: number; name: string; description: string; active: boolean }
export interface Supplier { id: number; name: string; contactName: string; email: string; phone: string; active: boolean }
export interface Dashboard { productCount: number; lowStock: number; outOfStock: number; inventoryValue: number; transactionCount: number; activityDates: string[]; activityCounts: number[]; categoryMix: { name: string; quantity: number; productCount: number }[]; urgentProducts: Product[]; warnings: Warning[] }
