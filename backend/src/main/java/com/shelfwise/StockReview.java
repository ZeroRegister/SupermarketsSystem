package com.shelfwise;
import jakarta.persistence.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.*;
import java.util.*;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Entity @Table(name="stock_reviews") class StockReview {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="product_id",nullable=false) Product product;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="batch_id") InventoryBatch batch;
 @Column(nullable=false,length=20) String kind;
 @Column(nullable=false,length=20) String state="SUBMITTED";
 @Column(nullable=false) long quantity;
 @Column(nullable=false) long snapshotQuantity;
 @Column(nullable=false) long snapshotVersion;
 @Column(nullable=false,length=300) String reason;
 @Column(length=300) String reviewNote;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="created_by",nullable=false) UserAccount createdBy;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="reviewed_by") UserAccount reviewedBy;
 @ManyToOne(fetch=FetchType.EAGER) @JoinColumn(name="transaction_id") InventoryTransaction transaction;
 @Column(nullable=false) Instant createdAt;
 Instant reviewedAt;
}
interface StockReviewRepository extends JpaRepository<StockReview,Long> {
 @Lock(LockModeType.PESSIMISTIC_WRITE) @Query("select r from StockReview r where r.id=:id") Optional<StockReview> locked(@org.springframework.data.repository.query.Param("id")Long id);
}
record StockReviewInput(@NotBlank @Pattern(regexp="COUNT|DISPOSAL|ADJUSTMENT") String kind,@NotNull @Positive Long productId,Long batchId,@Min(-1000000000) @Max(1000000000) long quantity,@NotBlank @Size(max=300) String reason) {}
record StockReviewAction(@NotBlank @Pattern(regexp="APPROVE|REJECT") String action,@NotBlank @Size(max=300) String note) {}
record StockReviewView(Long id,String kind,String state,Long productId,String productName,String batchNumber,long quantity,long snapshotQuantity,String reason,String reviewNote,String createdBy,String reviewedBy,Long transactionId,Instant createdAt) {}
@Service class StockReviews {
 private final StockReviewRepository reviews;private final ProductRepository products;private final BatchRepository batches;private final UserRepository users;private final TransactionRepository transactions;private final InventoryService inventory;private final Clock clock;
 @PersistenceContext private EntityManager em;
 StockReviews(StockReviewRepository r,ProductRepository p,BatchRepository b,UserRepository u,TransactionRepository t,InventoryService i,Clock c){reviews=r;products=p;batches=b;users=u;transactions=t;inventory=i;clock=c;}
 @Transactional StockReviewView submit(StockReviewInput in,String username){
  Product p=products.lockById(in.productId()).filter(x->x.active).orElseThrow(()->error("Active product required",400));
  StockReview r=new StockReview();r.product=p;r.kind=in.kind();r.quantity=in.quantity();r.reason=in.reason().trim();r.createdBy=users.findByUsername(username).orElseThrow();r.createdAt=clock.instant();r.snapshotQuantity=p.quantity;r.snapshotVersion=p.version;
  if("DISPOSAL".equals(in.kind())){if(in.batchId()==null||in.quantity()<=0)throw error("Disposal requires a batch and positive quantity",400);r.batch=batches.findById(in.batchId()).filter(b->b.product.id.equals(p.id)).orElseThrow(()->error("Batch does not belong to product",400));if(in.quantity()>r.batch.quantity)throw error("Disposal exceeds batch remainder",400);}
  else if(in.batchId()!=null)throw error("Batch selection is only used for disposal",400);
  if("COUNT".equals(in.kind())&&in.quantity()<0)throw error("Count must be non-negative",400);
  if("ADJUSTMENT".equals(in.kind())&&in.quantity()==0)throw error("Adjustment must be non-zero",400);
  reviews.save(r);return view(r);
 }
 @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) StockReviewView act(long id,StockReviewAction in,String username){
  StockReview r=reviews.locked(id).orElseThrow(()->error("Review not found",404));if(r.state.equals("APPROVED")&&in.action().equals("APPROVE")||r.state.equals("REJECTED")&&in.action().equals("REJECT"))return view(r);
  if(!r.state.equals("SUBMITTED"))throw error("Review already completed",409);
  Product p=products.lockById(r.product.id).orElseThrow();em.refresh(p);
  if(in.action().equals("APPROVE")){
   if(!p.active)throw error("Archived product cannot be adjusted",409);
   if(r.kind.equals("COUNT")&&(p.version!=r.snapshotVersion||p.quantity!=r.snapshotQuantity))throw error("Inventory changed since count snapshot; recount before approval",409);
   if(r.batch!=null){em.refresh(r.batch);if(r.quantity>r.batch.quantity)throw error("Disposal exceeds current batch remainder",409);}
   MovementType type=r.kind.equals("COUNT")?MovementType.STOCKTAKE:MovementType.ADJUSTMENT;
   long qty=r.kind.equals("DISPOSAL")?-r.quantity:r.quantity;
   var t=inventory.move(new TransactionInput(p.id,type,qty,"Review #"+r.id+": "+r.reason,"review:"+r.id,null,null,null,r.batch==null?null:r.batch.id),username);
   r.transaction=transactions.findById(t.id()).orElseThrow();r.state="APPROVED";
  }else r.state="REJECTED";
  r.reviewedBy=users.findByUsername(username).orElseThrow();r.reviewNote=in.note().trim();r.reviewedAt=clock.instant();return view(r);
 }
 @Transactional(readOnly=true) PageResult<StockReviewView> list(int page,int size){return PageResult.of(reviews.findAll(PageRequest.of(Math.max(0,page),Math.min(100,Math.max(1,size)),Sort.by(Sort.Direction.DESC,"id"))).map(this::view));}
 private StockReviewView view(StockReview r){return new StockReviewView(r.id,r.kind,r.state,r.product.id,r.product.name,r.batch==null?null:r.batch.batchNumber,r.quantity,r.snapshotQuantity,r.reason,r.reviewNote,r.createdBy.displayName,r.reviewedBy==null?null:r.reviewedBy.displayName,r.transaction==null?null:r.transaction.id,r.createdAt);}
 private DomainException error(String m,int status){return new DomainException(status==409?"CONFLICT":status==404?"NOT_FOUND":"VALIDATION",m,status);}
}
@RestController @RequestMapping("/api/stock-reviews") class StockReviewController {
 private final StockReviews reviews;StockReviewController(StockReviews r){reviews=r;}
 @GetMapping PageResult<StockReviewView> list(@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="20")int size){return reviews.list(page,size);}
 @PostMapping StockReviewView submit(@Valid @RequestBody StockReviewInput in,org.springframework.security.core.Authentication auth){return reviews.submit(in,auth.getName());}
 @PostMapping("/{id}/actions") StockReviewView act(@PathVariable long id,@Valid @RequestBody StockReviewAction in,org.springframework.security.core.Authentication auth){return reviews.act(id,in,auth.getName());}
}
