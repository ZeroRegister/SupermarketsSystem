package com.shelfwise;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;

record ProductInput(@NotBlank @Size(max=64) String sku,@Size(max=64) String barcode,@NotBlank @Size(max=180) String name,
 @NotBlank @Size(max=40) String unit,@NotNull @DecimalMin("0.00") @Digits(integer=10,fraction=2) BigDecimal price,
 @NotNull @PositiveOrZero Long safetyStock,@NotNull @PositiveOrZero Long reorderThreshold,@Positive Long categoryId,@Positive Long supplierId) {}
record TransactionInput(@NotNull Long productId,@NotNull MovementType type,@NotNull @Min(-1000000000) @Max(1000000000) Long quantity,
 @NotBlank @Size(max=300) String reason,@NotBlank @Size(max=80) String idempotencyKey) {}
record PageResult<T>(List<T> items,int page,int size,long totalElements,int totalPages) {
 static <T> PageResult<T> of(org.springframework.data.domain.Page<T> p){return new PageResult<>(p.getContent(),p.getNumber(),p.getSize(),p.getTotalElements(),p.getTotalPages());}
}
record ProductView(Long id,String sku,String barcode,String name,String unit,BigDecimal price,long quantity,long safetyStock,long reorderThreshold,String category,String supplier,boolean active,Instant updatedAt) {
 static ProductView of(Product p){return new ProductView(p.id,p.sku,p.barcode,p.name,p.unit,p.price,p.quantity,p.safetyStock,p.reorderThreshold,p.category==null?null:p.category.name,p.supplier==null?null:p.supplier.name,p.active,p.updatedAt);}
}
record TransactionView(Long id,Long productId,String productName,MovementType type,long delta,long quantityBefore,long quantityAfter,String reason,String actor,Instant createdAt) {
 static TransactionView of(InventoryTransaction t){return new TransactionView(t.id,t.product.id,t.product.name,t.type,t.delta,t.quantityBefore,t.quantityAfter,t.reason,t.actor.displayName,t.createdAt);}
}
record WarningView(Long id,Long productId,String sku,String productName,WarningType type,WarningState state,long quantity,long threshold,String acknowledgedBy,Instant acknowledgedAt,Instant createdAt,Instant expiresAt) {
 static WarningView of(WarningEpisode w){return new WarningView(w.id,w.product.id,w.product.sku,w.product.name,w.type,w.state,w.observedQuantity,w.threshold,w.acknowledgedBy==null?null:w.acknowledgedBy.displayName,w.acknowledgedAt,w.createdAt,w.expiresAt);}
}
record UserView(Long id,String username,String displayName,Role role,boolean enabled,Instant createdAt) {
 static UserView of(UserAccount u){return new UserView(u.id,u.username,u.displayName,u.role,u.enabled,u.createdAt);}
}
record CategoryInput(@NotBlank @Size(max=100) String name,@Size(max=500) String description) {}
record SupplierInput(@NotBlank @Size(max=120) String name,@Size(max=120) String contactName,@Email @Size(max=120) String email,@Size(max=40) String phone) {}
record UserInput(@NotBlank @Size(max=80) String username,@NotBlank @Size(max=100) String displayName,@NotBlank @Size(min=12,max=100) String password,@NotNull Role role) {}
record SettingInput(@NotBlank @Size(max=120) String businessName,@NotBlank @Pattern(regexp="[A-Z]{3}") String currency) {}
record ThresholdInput(@NotNull @Min(0) @Max(1000000000) Long safetyStock,@NotNull @Min(0) @Max(1000000000) Long reorderThreshold) {}
record UserAccessInput(@NotNull Role role,@NotNull Boolean enabled) {}
record CategoryMetric(String name,long quantity,long productCount) {}
record DashboardView(long productCount,long lowStock,long outOfStock,BigDecimal inventoryValue,long transactionCount,List<String> activityDates,List<Long> activityCounts,List<CategoryMetric> categoryMix,List<ProductView> urgentProducts,List<WarningView> warnings) {}
record ReportView(long activeProducts,long lowStock,long outOfStock,BigDecimal inventoryValue,long movementsToday,List<Map<String,Object>> topMovements,List<Map<String,Object>> categorySummary) {}
record ErrorView(String code,String message,Instant timestamp) {}
