package com.shelfwise;

import jakarta.persistence.*;
import java.time.Instant;
import java.math.BigDecimal;
import java.util.UUID;

enum Role { ADMIN, MANAGER, CLERK }
enum MovementType { STOCK_IN, STOCK_OUT, ADJUSTMENT, STOCKTAKE }
enum WarningType { LOW, OUT, RESTOCKED }
enum WarningState { OPEN, RESOLVED }
enum ReviewStage { PENDING, CONFIRMED, PROCESSING, RECOVERED }

@Entity @Table(name="users") class UserAccount {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(nullable=false, unique=true, length=80) String username;
    @Column(nullable=false, length=100) String displayName;
    @Column(nullable=false, length=100) String passwordHash;
    @Enumerated(EnumType.STRING) @Column(nullable=false, length=20) Role role;
    @Column(nullable=false) boolean enabled=true;
    @Column(nullable=false) Instant createdAt=Instant.now();
    protected UserAccount() {}
    UserAccount(String username,String displayName,String hash,Role role){this.username=username;this.displayName=displayName;this.passwordHash=hash;this.role=role;}
}

@Entity @Table(name="categories") class Category {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(nullable=false,unique=true,length=100) String name;
    @Column(length=500) String description;
    @Column(nullable=false) boolean active=true;
    protected Category(){}
    Category(String name,String description){this.name=name;this.description=description;}
}

@Entity @Table(name="suppliers") class Supplier {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(nullable=false,length=120) String name;
    @Column(length=120) String contactName;
    @Column(length=120) String email;
    @Column(length=40) String phone;
    @Column(nullable=false) boolean active=true;
    protected Supplier(){}
}

@Entity @Table(name="products", indexes={@Index(name="idx_product_name",columnList="name"),@Index(name="idx_product_category",columnList="category_id"),@Index(name="idx_product_quantity",columnList="quantity")}) class Product {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(nullable=false,unique=true,length=64) String sku;
    @Column(unique=true,length=64) String barcode;
    @Column(nullable=false,length=180) String name;
    @Column(nullable=false,length=40) String unit="pcs";
    @Column(nullable=false,precision=12,scale=2) BigDecimal price=BigDecimal.ZERO;
    @Column(nullable=false) long quantity=0;
    @Column(nullable=false) long sellableQuantity=0;
    @Column(nullable=false) long safetyStock=0;
    @Column(nullable=false) long reorderThreshold=0;
    @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="category_id") Category category;
    @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="supplier_id") Supplier supplier;
    @Column(nullable=false) boolean active=true;
    @Version long version;
    @Column(nullable=false) Instant updatedAt=Instant.now();
    protected Product(){}
}

@Entity @Table(name="inventory_transactions",uniqueConstraints=@UniqueConstraint(name="uk_tx_actor_key",columnNames={"actor_id","idempotency_key"}),indexes=@Index(name="idx_tx_product_time",columnList="product_id,created_at")) class InventoryTransaction {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="product_id",nullable=false) Product product;
    @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="actor_id",nullable=false) UserAccount actor;
    @Enumerated(EnumType.STRING) @Column(nullable=false,length=20) MovementType type;
    @Column(nullable=false) long delta;
    @Column(nullable=false) long quantityBefore;
    @Column(nullable=false) long quantityAfter;
    @Column(nullable=false,length=300) String reason;
    @Column(name="idempotency_key",nullable=false,length=80) String idempotencyKey;
    @Column(nullable=false,length=500) String requestMetadata="";
    @Column(nullable=false) Instant createdAt=Instant.now();
    protected InventoryTransaction(){}
}

@Entity @Table(name="warnings",indexes=@Index(name="idx_warning_state_time",columnList="state,created_at")) class WarningEpisode {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="product_id",nullable=false) Product product;
    @Enumerated(EnumType.STRING) @Column(nullable=false,length=20) WarningType type;
    @Enumerated(EnumType.STRING) @Column(nullable=false,length=20) WarningState state=WarningState.OPEN;
    @Column(nullable=false) long observedQuantity;
    @Column(nullable=false) long threshold;
    @Column(nullable=false) Instant createdAt=Instant.now();
    @Column(nullable=false) Instant expiresAt;
    @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="acknowledged_by") UserAccount acknowledgedBy;
    Instant acknowledgedAt;
    @Enumerated(EnumType.STRING) @Column(nullable=false,length=20) ReviewStage reviewStage=ReviewStage.PENDING;
    @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="assigned_to") UserAccount assignedTo;
    Instant recoveredAt;
    Long previousId;
    protected WarningEpisode(){}
}

@Entity @Table(name="warning_actions") class WarningAction {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="warning_id") WarningEpisode warning;
    @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="actor_id") UserAccount actor;
    @Column(nullable=false,length=30) String action;
    @Column(nullable=false,length=1000) String note;
    @Column(nullable=false) Instant createdAt=Instant.now();
}

@Entity @Table(name="app_settings") class AppSetting {
    @Id @Column(length=80) String settingKey;
    @Column(nullable=false,length=240) String settingValue;
    protected AppSetting(){}
}

@Entity @Table(name="cache_revision") class CacheRevision {
    @Id Long id=1L;
    @Column(nullable=false) long revision=0;
    protected CacheRevision(){}
    CacheRevision(long revision){this.revision=revision;}
}
