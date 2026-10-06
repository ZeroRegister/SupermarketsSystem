package com.shelfwise;
import jakarta.persistence.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.*;
import java.util.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@Entity @Table(name="warning_policy") class WarningPolicy {
 @Id Long id=1L;
 @Column(nullable=false) int nearExpiryDays=7;
 @Column(nullable=false,length=80) String businessTimezone="Asia/Shanghai";
 @Column(nullable=false) int slowStockDays=30;
 @Column(nullable=false) long slowStockMinimum=10;
 @Version long version;
}
interface WarningPolicyRepository extends JpaRepository<WarningPolicy,Long> {
 @Lock(LockModeType.PESSIMISTIC_WRITE) @Query("select p from WarningPolicy p where p.id=1") WarningPolicy locked();
}
record WarningPolicyInput(@Min(0) @Max(365) int nearExpiryDays,@NotBlank @Size(max=80) String businessTimezone,@Min(1) @Max(3650) int slowStockDays,@Min(1) @Max(1000000000) long slowStockMinimum) {
 WarningPolicyInput(int days,String zone){this(days,zone,30,10);}
}
record WarningPolicyView(int nearExpiryDays,String businessTimezone,long version,int slowStockDays,long slowStockMinimum) {}

@Service class WarningRules {
 private final WarningRepository warnings;private final BatchRepository batches;private final WarningWorkflow workflow;private final WarningPolicyRepository policies;private final CacheRevisionRepository revisions;private final Clock clock;
 WarningRules(WarningRepository w,BatchRepository b,WarningWorkflow f,WarningPolicyRepository p,CacheRevisionRepository r,Clock c){warnings=w;batches=b;workflow=f;policies=p;revisions=r;clock=c;}
 @org.springframework.beans.factory.annotation.Autowired private TransactionRepository transactions;
 @Transactional(readOnly=true) WarningPolicyView policy(){return view(policies.findById(1L).orElseThrow());}
 private WarningPolicyView view(WarningPolicy p){return new WarningPolicyView(p.nearExpiryDays,p.businessTimezone,p.version,p.slowStockDays,p.slowStockMinimum);}
 @Transactional WarningPolicyView configure(WarningPolicyInput in){try{ZoneId.of(in.businessTimezone());}catch(DateTimeException e){throw new DomainException("VALIDATION","Unknown business time zone",400);}WarningPolicy p=policies.locked();p.nearExpiryDays=in.nearExpiryDays();p.businessTimezone=in.businessTimezone();p.slowStockDays=in.slowStockDays();p.slowStockMinimum=in.slowStockMinimum();policies.flush();revisions.increment();return view(p);}
 LocalDate today(){return clock.instant().atZone(ZoneId.of(policy().businessTimezone())).toLocalDate();}
 void refresh(Product p){
  WarningPolicy policy=policies.findById(1L).orElseThrow();LocalDate today=clock.instant().atZone(ZoneId.of(policy.businessTimezone)).toLocalDate();
  for(InventoryBatch b:batches.findByProductId(p.id)){
   boolean remaining=p.active&&b.quantity>0&&b.expiryDate!=null;
   boolean expired=remaining&&b.expiryDate.isBefore(today);
   boolean near=remaining&&!expired&&!b.quarantined&&!b.expiryDate.isAfter(today.plusDays(policy.nearExpiryDays));
   evaluate(p,b,WarningType.EXPIRED,expired,b.quantity,0);evaluate(p,b,WarningType.EXPIRING,near,b.quantity,policy.nearExpiryDays);
  }
  Instant since=today.minusDays(policy.slowStockDays).atStartOfDay(ZoneId.of(policy.businessTimezone)).toInstant();
  boolean slow=p.active&&p.sellableQuantity>=policy.slowStockMinimum&&!p.createdAt.isAfter(since)&&!transactions.existsByProductIdAndTypeAndCreatedAtGreaterThanEqual(p.id,MovementType.SALE,since);
  evaluate(p,null,WarningType.SLOW,slow,p.sellableQuantity,policy.slowStockMinimum);
 }
 void evaluate(Product p,InventoryBatch batch,WarningType type,boolean condition,long quantity,long threshold){
  var events=warnings.findByProductIdAndState(p.id,WarningState.OPEN).stream().filter(w->w.type==type&&Objects.equals(w.batch==null?null:w.batch.id,batch==null?null:batch.id)).toList();
  if(!condition){events.forEach(workflow::recover);return;}
  if(!events.isEmpty()){var w=events.getFirst();w.observedQuantity=quantity;w.threshold=threshold;return;}
  WarningEpisode w=new WarningEpisode();w.product=p;w.batch=batch;w.type=type;w.observedQuantity=quantity;w.threshold=threshold;w.createdAt=clock.instant();w.expiresAt=w.createdAt.plus(Duration.ofDays(3650));
  w.previousId=warnings.findFirstByProductIdAndTypeAndBatchOrderByCreatedAtDesc(p.id,type,batch).map(x->x.id).orElse(null);warnings.save(w);workflow.created(w);
 }
}

@Service class WarningRefresh {
 private final ProductRepository products;private final InventoryService inventory;
 private final java.util.concurrent.locks.ReentrantLock sweepLock=new java.util.concurrent.locks.ReentrantLock();
 private volatile Instant lastCompleted;private volatile int failedProducts;
 WarningRefresh(ProductRepository p,InventoryService i){products=p;inventory=i;}
 @org.springframework.beans.factory.annotation.Value("${shelfwise.warning-refresh-enabled:true}") private boolean scheduledEnabled;
 @org.springframework.scheduling.annotation.Scheduled(fixedDelay=30000,initialDelay=1000)
 void scheduledRefresh(){if(scheduledEnabled)refresh();}
 public void refresh(){
  if(!sweepLock.tryLock())return;
  try{int failures=0;for(Long id:products.allIds()){try{inventory.refreshWarning(id);}catch(RuntimeException e){failures++;org.slf4j.LoggerFactory.getLogger(getClass()).warn("Warning refresh failed for product {}; retry next sweep",id,e);}}failedProducts=failures;lastCompleted=Instant.now();}finally{sweepLock.unlock();}
 }
 Map<String,Object> status(){Map<String,Object> m=new LinkedHashMap<>();m.put("intervalSeconds",30);m.put("retrySeconds",30);m.put("lastCompleted",lastCompleted);m.put("failedProducts",failedProducts);m.put("running",sweepLock.isLocked());return m;}
}
@RestController @RequestMapping("/api/warnings") class WarningRuleController {
 private final WarningRules rules;private final WarningRefresh refresh;
 WarningRuleController(WarningRules r,WarningRefresh f){rules=r;refresh=f;}
 @GetMapping("/policy") WarningPolicyView policy(){return rules.policy();}
 @PutMapping("/policy") WarningPolicyView configure(@Valid @RequestBody WarningPolicyInput in){var result=rules.configure(in);refresh.refresh();return result;}
 @PostMapping("/refresh") Map<String,Object> refresh(){refresh.refresh();return refresh.status();}
 @GetMapping("/refresh-status") Map<String,Object> status(){return refresh.status();}
}
