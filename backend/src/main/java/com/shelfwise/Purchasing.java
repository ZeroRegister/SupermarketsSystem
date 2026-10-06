package com.shelfwise;
import jakarta.persistence.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.*;
import java.util.*;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

enum PurchaseState { DRAFT, SUBMITTED, REJECTED, APPROVED, PARTIAL, COMPLETED, CANCELLED }
@Entity @Table(name="purchase_orders") class PurchaseOrder {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="supplier_id",nullable=false) Supplier supplier;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="created_by",nullable=false) UserAccount createdBy;
 @Enumerated(EnumType.STRING) @Column(nullable=false,length=20) PurchaseState state=PurchaseState.DRAFT;
 @Column(nullable=false,length=300) String reason;
 @Column(length=300) String reviewNote;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="reviewed_by") UserAccount reviewedBy;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="warning_id") WarningEpisode warning;
 @Column(nullable=false) Instant createdAt=Instant.now();
 @Column(nullable=false) Instant updatedAt=Instant.now();
}
@Entity @Table(name="purchase_lines") class PurchaseLine {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="order_id",nullable=false) PurchaseOrder order;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="product_id",nullable=false) Product product;
 @Column(nullable=false) long quantity;
 @Column(nullable=false) long received;
}
@Entity @Table(name="purchase_receipts") class PurchaseReceipt {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="order_id",nullable=false) PurchaseOrder order;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="line_id",nullable=false) PurchaseLine line;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="transaction_id",nullable=false) InventoryTransaction transaction;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="actor_id",nullable=false) UserAccount actor;
 @Column(nullable=false,length=80) String requestKey;
 @Column(nullable=false,length=600) String payload;
 @Column(nullable=false) Instant createdAt=Instant.now();
}
@Entity @Table(name="purchase_actions") class PurchaseAction {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="order_id",nullable=false) PurchaseOrder order;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="actor_id",nullable=false) UserAccount actor;
 @Column(nullable=false,length=30) String action;
 @Column(nullable=false,length=300) String note;
 @Column(nullable=false) Instant createdAt=Instant.now();
}
interface PurchaseOrderRepository extends JpaRepository<PurchaseOrder,Long> {
 @Lock(LockModeType.PESSIMISTIC_WRITE) @Query("select o from PurchaseOrder o where o.id=:id") Optional<PurchaseOrder> locked(@Param("id")Long id);
}
interface PurchaseLineRepository extends JpaRepository<PurchaseLine,Long> {
 List<PurchaseLine> findByOrderIdOrderByProductId(Long id);
 @Query("select coalesce(sum(l.quantity-l.received),0) from PurchaseLine l where l.product.id=:id and l.order.state in (com.shelfwise.PurchaseState.APPROVED,com.shelfwise.PurchaseState.PARTIAL)") long pending(@Param("id")Long id);
}
interface PurchaseReceiptRepository extends JpaRepository<PurchaseReceipt,Long> {
 Optional<PurchaseReceipt> findByActorIdAndRequestKey(Long actorId,String requestKey);
 List<PurchaseReceipt> findByOrderIdOrderByIdDesc(Long id);
}
interface PurchaseActionRepository extends JpaRepository<PurchaseAction,Long> { List<PurchaseAction> findByOrderIdOrderByIdDesc(Long id); }
record PurchaseLineInput(@NotNull @Positive Long productId,@Min(1) @Max(1000000000) long quantity) {}
record PurchaseInput(@NotNull @Positive Long supplierId,@NotEmpty @Size(max=50) List<@Valid PurchaseLineInput> lines,@NotBlank @Size(max=300) String reason,Long warningId) {}
record PurchaseActionInput(@NotBlank @Pattern(regexp="SUBMIT|APPROVE|REJECT|CANCEL") String action,@NotBlank @Size(max=300) String note) {}
record ReceiptInput(@NotNull @Positive Long lineId,@Min(1) @Max(1000000000) long quantity,@Size(max=80) String batchNumber,LocalDate productionDate,LocalDate expiryDate,@NotBlank @Size(max=80) String idempotencyKey) {}
record ReplenishmentInput(@Min(1) @Max(1000000000) long targetStock) {}
record Suggestion(Long productId,String productName,String sku,long sellable,long pending,long position,long trigger,long target,long suggested,Long supplierId,String supplier,int leadTimeDays) {}
record PurchaseLineView(Long id,Long productId,String productName,long quantity,long received,long remaining) {}
record PurchaseView(Long id,String supplier,PurchaseState state,String createdBy,String reviewedBy,String reason,String reviewNote,Long warningId,Instant createdAt,List<PurchaseLineView> lines) {}
record ReceiptView(Long id,Long lineId,long quantity,Long transactionId,String actor,Instant createdAt) {}
record PurchaseActionView(String action,String note,String actor,Instant createdAt) {}

@Service class Purchasing {
 private final PurchaseOrderRepository orders;private final PurchaseLineRepository lines;private final PurchaseReceiptRepository receipts;private final PurchaseActionRepository actions;private final ProductRepository products;private final SupplierRepository suppliers;private final UserRepository users;private final InventoryService inventory;private final WarningRepository warnings;private final Clock clock;
 Purchasing(PurchaseOrderRepository o,PurchaseLineRepository l,PurchaseReceiptRepository r,PurchaseActionRepository a,ProductRepository p,SupplierRepository s,UserRepository u,InventoryService i,WarningRepository w,Clock c){orders=o;lines=l;receipts=r;actions=a;products=p;suppliers=s;users=u;inventory=i;warnings=w;clock=c;}
 @org.springframework.beans.factory.annotation.Autowired private TransactionRepository transactions;
 @PersistenceContext private EntityManager em;
 @Transactional(readOnly=true) List<Suggestion> suggestions(){return products.findAllByActiveTrue().stream().map(this::suggestion).filter(s->s.suggested()>0).toList();}
 private Suggestion suggestion(Product p){long pending=lines.pending(p.id),position=p.sellableQuantity+pending;return new Suggestion(p.id,p.name,p.sku,p.sellableQuantity,pending,position,p.reorderThreshold,p.targetStock,position<=p.reorderThreshold?Math.max(0,p.targetStock-position):0,p.supplier==null?null:p.supplier.id,p.supplier==null?null:p.supplier.name,p.supplier==null?0:p.supplier.leadTimeDays);}
 @Transactional Suggestion target(long id,ReplenishmentInput in){Product p=products.lockById(id).orElseThrow(()->error("Product not found",404));if(in.targetStock()<=p.reorderThreshold)throw error("Target stock must exceed reorder threshold",400);p.targetStock=in.targetStock();return suggestion(p);}
 @Transactional PurchaseView save(Long id,PurchaseInput in,String username){
  PurchaseOrder o=id==null?new PurchaseOrder():orders.locked(id).orElseThrow(()->error("Purchase not found",404));
  if(id!=null&&o.state!=PurchaseState.DRAFT&&o.state!=PurchaseState.REJECTED)throw error("Only draft or rejected purchases can be edited",409);
  o.supplier=suppliers.findById(in.supplierId()).filter(s->s.active).orElseThrow(()->error("Active supplier required",400));
  if(id==null)o.createdBy=actor(username);o.reason=in.reason().trim();o.state=PurchaseState.DRAFT;o.updatedAt=clock.instant();
  if(in.warningId()!=null)o.warning=warnings.findById(in.warningId()).orElseThrow(()->error("Warning not found",404));else o.warning=null;
  Set<Long> ids=new HashSet<>();List<Product> selected=new ArrayList<>();for(var item:in.lines()){if(!ids.add(item.productId()))throw error("Duplicate product in purchase",400);Product p=products.findById(item.productId()).filter(x->x.active).orElseThrow(()->error("Active product required",400));if(p.supplier!=null&&!p.supplier.id.equals(o.supplier.id))throw error("Supplier does not match product",400);selected.add(p);}
  if(o.warning!=null&&!ids.contains(o.warning.product.id))throw error("Linked warning product must be included",400);
  orders.saveAndFlush(o);if(id!=null){lines.deleteAll(lines.findByOrderIdOrderByProductId(id));lines.flush();}
  for(int i=0;i<in.lines().size();i++){PurchaseLine l=new PurchaseLine();l.order=o;l.product=selected.get(i);l.quantity=in.lines().get(i).quantity();lines.save(l);}lines.flush();log(o,username,"DRAFT","Purchase draft saved");return view(o);
 }
 @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) PurchaseView act(long id,PurchaseActionInput in,String username){
  PurchaseOrder o=orders.locked(id).orElseThrow(()->error("Purchase not found",404));var items=lines.findByOrderIdOrderByProductId(id);
  // Product locks are ordered, and serialize approval against other approvals and receipts.
  for(PurchaseLine l:items){var p=products.lockById(l.product.id).orElseThrow();em.refresh(p);}
  switch(in.action()){
   case "SUBMIT" -> {if(o.state==PurchaseState.SUBMITTED)return view(o);if(o.state!=PurchaseState.DRAFT&&o.state!=PurchaseState.REJECTED)throw error("Purchase cannot be submitted in this state",409);o.state=PurchaseState.SUBMITTED;}
   case "APPROVE" -> {if(o.state==PurchaseState.APPROVED)return view(o);if(o.state!=PurchaseState.SUBMITTED)throw error("Only submitted purchases can be approved",409);for(PurchaseLine l:items){Product p=l.product;inventory.refreshWarning(p.id);Suggestion s=suggestion(p);if(!p.active||l.quantity>s.suggested()||s.suggested()==0)throw error("Recheck replenishment: requested quantity exceeds current recommendation for "+p.name,409);}o.state=PurchaseState.APPROVED;o.reviewedBy=actor(username);o.reviewNote=in.note().trim();}
   case "REJECT" -> {if(o.state==PurchaseState.REJECTED)return view(o);if(o.state!=PurchaseState.SUBMITTED)throw error("Only submitted purchases can be rejected",409);o.state=PurchaseState.REJECTED;o.reviewedBy=actor(username);o.reviewNote=in.note().trim();}
   case "CANCEL" -> {if(o.state==PurchaseState.CANCELLED)return view(o);if(o.state==PurchaseState.COMPLETED)throw error("Completed purchases cannot be cancelled",409);o.state=PurchaseState.CANCELLED;}
   default -> throw error("Unknown purchase action",400);
  }o.updatedAt=clock.instant();log(o,username,in.action(),in.note().trim());return view(o);
 }
 @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) ReceiptView receive(long id,ReceiptInput in,String username){
  PurchaseOrder o=orders.locked(id).orElseThrow(()->error("Purchase not found",404));UserAccount actor=actor(username);String payload=id+"|"+in.lineId()+"|"+in.quantity()+"|"+Objects.toString(in.batchNumber(),"")+"|"+in.productionDate()+"|"+in.expiryDate();
  var prior=receipts.findByActorIdAndRequestKey(actor.id,in.idempotencyKey());if(prior.isPresent()){if(!prior.get().payload.equals(payload))throw error("Receipt key used with a different payload",409);return receiptView(prior.get());}
  if(o.state!=PurchaseState.APPROVED&&o.state!=PurchaseState.PARTIAL)throw error("Only approved purchases can receive stock",409);
  var items=lines.findByOrderIdOrderByProductId(id);for(var l:items){var p=products.lockById(l.product.id).orElseThrow();em.refresh(p);}
  PurchaseLine l=items.stream().filter(x->x.id.equals(in.lineId())).findFirst().orElseThrow(()->error("Purchase line not found",404));if(in.quantity()>l.quantity-l.received)throw error("Receipt exceeds remaining approved quantity",400);
  var movement=inventory.move(new TransactionInput(l.product.id,MovementType.STOCK_IN,in.quantity(),"Purchase #"+id+" receipt", "po:"+UUID.nameUUIDFromBytes(in.idempotencyKey().getBytes(java.nio.charset.StandardCharsets.UTF_8)),in.batchNumber(),in.productionDate(),in.expiryDate(),null),username);
  l.received+=in.quantity();o.state=items.stream().allMatch(x->x.received==x.quantity)?PurchaseState.COMPLETED:PurchaseState.PARTIAL;o.updatedAt=clock.instant();
  PurchaseReceipt r=new PurchaseReceipt();r.order=o;r.line=l;r.actor=actor;r.requestKey=in.idempotencyKey();r.payload=payload;r.createdAt=clock.instant();r.transaction=transactions.findById(movement.id()).orElseThrow();receipts.saveAndFlush(r);log(o,username,"RECEIVE","Received "+in.quantity()+" units of "+l.product.name);return receiptView(r);
 }
 @Transactional(readOnly=true) PageResult<PurchaseView> list(int page,int size){return PageResult.of(orders.findAll(PageRequest.of(Math.max(0,page),Math.min(100,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"id"))).map(this::view));}
 @Transactional(readOnly=true) PurchaseView get(long id){return view(orders.findById(id).orElseThrow(()->error("Purchase not found",404)));}
 @Transactional(readOnly=true) List<ReceiptView> receipts(long id){return receipts.findByOrderIdOrderByIdDesc(id).stream().map(this::receiptView).toList();}
 @Transactional(readOnly=true) List<PurchaseActionView> history(long id){return actions.findByOrderIdOrderByIdDesc(id).stream().map(a->new PurchaseActionView(a.action,a.note,a.actor.displayName,a.createdAt)).toList();}
 private PurchaseView view(PurchaseOrder o){return new PurchaseView(o.id,o.supplier.name,o.state,o.createdBy.displayName,o.reviewedBy==null?null:o.reviewedBy.displayName,o.reason,o.reviewNote,o.warning==null?null:o.warning.id,o.createdAt,lines.findByOrderIdOrderByProductId(o.id).stream().map(l->new PurchaseLineView(l.id,l.product.id,l.product.name,l.quantity,l.received,o.state==PurchaseState.CANCELLED?0:l.quantity-l.received)).toList());}
 private ReceiptView receiptView(PurchaseReceipt r){return new ReceiptView(r.id,r.line.id,r.transaction.delta,r.transaction.id,r.actor.displayName,r.createdAt);}
 private void log(PurchaseOrder o,String username,String action,String note){PurchaseAction a=new PurchaseAction();a.order=o;a.actor=actor(username);a.action=action;a.note=note;a.createdAt=clock.instant();actions.save(a);}
 private UserAccount actor(String username){return users.findByUsername(username).filter(u->u.enabled).orElseThrow(()->error("User not found",404));}
 private DomainException error(String m,int status){return new DomainException(status==409?"CONFLICT":status==404?"NOT_FOUND":"VALIDATION",m,status);}
}

@RestController @RequestMapping("/api") class PurchasingController {
 private final Purchasing purchasing;PurchasingController(Purchasing p){purchasing=p;}
 @GetMapping("/replenishment") List<Suggestion> suggestions(){return purchasing.suggestions();}
 @PatchMapping("/products/{id}/target") Suggestion target(@PathVariable long id,@Valid @RequestBody ReplenishmentInput in){return purchasing.target(id,in);}
 @GetMapping("/purchases") PageResult<PurchaseView> list(@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="20")int size){return purchasing.list(page,size);}
 @GetMapping("/purchases/{id}") PurchaseView get(@PathVariable long id){return purchasing.get(id);}
 @PostMapping("/purchases") PurchaseView create(@Valid @RequestBody PurchaseInput in,org.springframework.security.core.Authentication auth){return purchasing.save(null,in,auth.getName());}
 @PutMapping("/purchases/{id}") PurchaseView edit(@PathVariable long id,@Valid @RequestBody PurchaseInput in,org.springframework.security.core.Authentication auth){return purchasing.save(id,in,auth.getName());}
 @PostMapping("/purchases/{id}/actions") PurchaseView act(@PathVariable long id,@Valid @RequestBody PurchaseActionInput in,org.springframework.security.core.Authentication auth){if(Set.of("APPROVE","REJECT","CANCEL").contains(in.action())&&auth.getAuthorities().stream().noneMatch(a->Set.of("ROLE_ADMIN","ROLE_MANAGER").contains(a.getAuthority())))throw new DomainException("FORBIDDEN","Manager approval required",403);return purchasing.act(id,in,auth.getName());}
 @PostMapping("/purchases/{id}/receipts") ReceiptView receipt(@PathVariable long id,@Valid @RequestBody ReceiptInput in,org.springframework.security.core.Authentication auth){return purchasing.receive(id,in,auth.getName());}
 @GetMapping("/purchases/{id}/receipts") List<ReceiptView> receipts(@PathVariable long id){return purchasing.receipts(id);}
 @GetMapping("/purchases/{id}/history") List<PurchaseActionView> history(@PathVariable long id){return purchasing.history(id);}
}
