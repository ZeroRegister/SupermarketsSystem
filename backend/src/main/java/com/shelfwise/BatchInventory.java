package com.shelfwise;
import java.time.*;
import java.util.*;
import jakarta.validation.constraints.*;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

interface BatchRepository extends JpaRepository<InventoryBatch,Long> {
 @Query("select b.product.id from InventoryBatch b where b.id=:id") Optional<Long> productId(@org.springframework.data.repository.query.Param("id")Long id);
 List<InventoryBatch> findByProductId(Long productId);
 boolean existsByProductIdAndBatchNumber(Long productId,String number);
 Page<InventoryBatch> findByProductId(Long productId,Pageable page);
}
interface AllocationRepository extends JpaRepository<BatchAllocation,Long> {
 List<BatchAllocation> findByBatchIdOrderByIdDesc(Long batchId);
 List<BatchAllocation> findByTransactionId(Long transactionId);
}
interface BatchActionRepository extends JpaRepository<BatchAction,Long> { List<BatchAction> findByBatchIdOrderByIdDesc(Long batchId); }
record BatchView(Long id,Long productId,String productName,String sku,String batchNumber,LocalDate receivedDate,LocalDate productionDate,LocalDate expiryDate,long quantity,boolean quarantined,String status) {}
record BatchControlInput(@NotNull Boolean quarantined,@NotBlank @Size(max=300) String reason) {}
record AllocationView(Long transactionId,String type,long delta,String reason,String actor,Instant createdAt,String batchNumber) {}
record BatchActionView(boolean quarantined,String reason,String actor,Instant createdAt) {}

@Service class BatchInventory {
 private final BatchRepository batches;private final AllocationRepository allocations;private final BatchActionRepository actions;private final UserRepository users;private final ProductRepository products;private final Clock clock;
 BatchInventory(BatchRepository b,AllocationRepository a,BatchActionRepository h,UserRepository u,ProductRepository p,Clock c){batches=b;allocations=a;actions=h;users=u;products=p;clock=c;}
 @org.springframework.beans.factory.annotation.Autowired private WarningPolicyRepository policies;
 LocalDate today(){return clock.instant().atZone(ZoneId.of(policies.findById(1L).orElseThrow().businessTimezone)).toLocalDate();}
 boolean sellable(InventoryBatch b){return !b.quarantined&&(b.expiryDate==null||!b.expiryDate.isBefore(today()));}
 void recompute(Product p){p.sellableQuantity=batches.findByProductId(p.id).stream().filter(this::sellable).mapToLong(b->b.quantity).sum();}
 void seedBalance(Product p){if(p.quantity>0&&batches.findByProductId(p.id).isEmpty()){InventoryBatch b=new InventoryBatch();b.product=p;b.batchNumber="OPENING-"+p.id;b.receivedDate=today();b.quantity=p.quantity;batches.save(b);}recompute(p);}
 void apply(Product p,InventoryTransaction t,TransactionInput in){
  if(in.batchId()!=null&&(t.delta>=0||(in.type()==MovementType.STOCK_OUT||in.type()==MovementType.SALE)))throw error("Batch selection is only supported for negative adjustments",400);
  if(in.type()!=MovementType.STOCK_IN&&(in.batchNumber()!=null||in.expiryDate()!=null||in.productionDate()!=null))throw error("Batch dates are only supported for receipts",400);
  if(t.delta>0){
   if(in.productionDate()!=null&&in.productionDate().isAfter(today()))throw error("Production date cannot be in the future",400);
   if(in.expiryDate()!=null&&in.productionDate()!=null&&in.expiryDate().isBefore(in.productionDate()))throw error("Expiry date precedes production date",400);
   String number=in.batchNumber()==null||in.batchNumber().isBlank()?"RECEIPT-"+t.id:in.batchNumber().trim();
   if(batches.existsByProductIdAndBatchNumber(p.id,number))throw error("Batch number already exists for this product",409);
   InventoryBatch b=new InventoryBatch();b.product=p;b.batchNumber=number;b.receivedDate=today();b.productionDate=in.productionDate();b.expiryDate=in.expiryDate();b.quantity=t.delta;batches.save(b);allocate(t,b,t.delta);
  }else if(t.delta<0){
   List<InventoryBatch> candidates=new ArrayList<>(batches.findByProductId(p.id));
   candidates.removeIf(b->b.quantity==0||(in.batchId()!=null&&!in.batchId().equals(b.id))||((in.type()==MovementType.STOCK_OUT||in.type()==MovementType.SALE)&&!sellable(b)));
   candidates.sort(Comparator.comparing((InventoryBatch b)->b.expiryDate,Comparator.nullsLast(Comparator.naturalOrder())).thenComparing(b->b.receivedDate).thenComparing(b->b.id));
   long remaining=-t.delta;if(candidates.stream().mapToLong(b->b.quantity).sum()<remaining)throw error("Insufficient eligible batch stock",400);
   for(InventoryBatch b:candidates){long take=Math.min(remaining,b.quantity);if(take==0)break;b.quantity-=take;allocate(t,b,-take);remaining-=take;}
  }recompute(p);
 }
 private void allocate(InventoryTransaction t,InventoryBatch b,long delta){BatchAllocation a=new BatchAllocation();a.transaction=t;a.batch=b;a.delta=delta;allocations.save(a);}
 @Transactional(readOnly=true) PageResult<BatchView> list(Long productId,int page,int size){Pageable p=PageRequest.of(Math.max(0,page),Math.min(100,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"id"));return PageResult.of((productId==null?batches.findAll(p):batches.findByProductId(productId,p)).map(this::view));}
 @Transactional BatchView control(long id,BatchControlInput in,String username){
  Long productId=batches.productId(id).orElseThrow(()->error("Batch not found",404));Product p=products.lockById(productId).orElseThrow();
  InventoryBatch b=batches.findById(id).orElseThrow();b.quarantined=in.quarantined();BatchAction a=new BatchAction();a.batch=b;a.quarantined=b.quarantined;a.reason=in.reason().trim();a.actor=users.findByUsername(username).orElseThrow();actions.save(a);recompute(p);return view(b);
 }
 @Transactional(readOnly=true) List<AllocationView> history(long id){return allocations.findByBatchIdOrderByIdDesc(id).stream().map(this::allocationView).toList();}
 @Transactional(readOnly=true) List<AllocationView> transactionAllocations(long id){return allocations.findByTransactionId(id).stream().map(this::allocationView).toList();}
 private AllocationView allocationView(BatchAllocation a){return new AllocationView(a.transaction.id,a.transaction.type.name(),a.delta,a.transaction.reason,a.transaction.actor.displayName,a.transaction.createdAt,a.batch.batchNumber);}
 @Transactional(readOnly=true) List<BatchActionView> controls(long id){return actions.findByBatchIdOrderByIdDesc(id).stream().map(a->new BatchActionView(a.quarantined,a.reason,a.actor.displayName,a.createdAt)).toList();}
 BatchView view(InventoryBatch b){return new BatchView(b.id,b.product.id,b.product.name,b.product.sku,b.batchNumber,b.receivedDate,b.productionDate,b.expiryDate,b.quantity,b.quarantined,b.expiryDate!=null&&b.expiryDate.isBefore(today())?"EXPIRED":b.quarantined?"QUARANTINED":"SELLABLE");}
 private DomainException error(String m,int status){return new DomainException(status==409?"CONFLICT":status==404?"NOT_FOUND":"VALIDATION",m,status);}
}
