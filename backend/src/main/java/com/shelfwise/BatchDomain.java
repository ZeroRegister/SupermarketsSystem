package com.shelfwise;
import jakarta.persistence.*;
import java.time.*;

@Entity @Table(name="inventory_batches") class InventoryBatch {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="product_id") Product product;
 @Column(nullable=false,length=80) String batchNumber;
 @Column(nullable=false) LocalDate receivedDate;
 LocalDate productionDate;LocalDate expiryDate;
 @Column(nullable=false) long quantity;
 @Column(nullable=false) boolean quarantined;
 @Version long version;
}
@Entity @Table(name="batch_allocations") class BatchAllocation {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="transaction_id") InventoryTransaction transaction;
 @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="batch_id") InventoryBatch batch;
 @Column(nullable=false) long delta;
}
@Entity @Table(name="batch_actions") class BatchAction {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="batch_id") InventoryBatch batch;
 @ManyToOne(fetch=FetchType.EAGER,optional=false) @JoinColumn(name="actor_id") UserAccount actor;
 @Column(nullable=false) boolean quarantined;
 @Column(nullable=false,length=300) String reason;
 @Column(nullable=false) Instant createdAt=Instant.now();
}
