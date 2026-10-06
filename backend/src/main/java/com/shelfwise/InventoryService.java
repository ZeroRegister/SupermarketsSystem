package com.shelfwise;

import jakarta.persistence.EntityManager;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import java.math.BigDecimal;
import java.time.*;
import java.util.*;
import java.util.concurrent.TimeUnit;

@Service
class InventoryService {
 private final ProductRepository products; private final CategoryRepository categories; private final SupplierRepository suppliers;
 private final UserRepository users; private final TransactionRepository transactions; private final WarningRepository warnings;
 private final SettingRepository settings; private final CacheRevisionRepository revisions; private final StringRedisTemplate redis;
 private final PasswordEncoder encoder; private final ShelfwiseProperties props; private final EntityManager em;
 @org.springframework.beans.factory.annotation.Autowired private WarningWorkflow workflow;
 @org.springframework.beans.factory.annotation.Autowired private BatchInventory batchInventory;
 @org.springframework.beans.factory.annotation.Autowired private WarningRules warningRules;
 InventoryService(ProductRepository p,CategoryRepository c,SupplierRepository s,UserRepository u,TransactionRepository t,WarningRepository w,SettingRepository set,CacheRevisionRepository rev,StringRedisTemplate redis,PasswordEncoder encoder,ShelfwiseProperties props,EntityManager em){this.products=p;this.categories=c;this.suppliers=s;this.users=u;this.transactions=t;this.warnings=w;this.settings=set;this.revisions=rev;this.redis=redis;this.encoder=encoder;this.props=props;this.em=em;}

 @Transactional(readOnly=true) PageResult<ProductView> listProducts(String q,Long categoryId,String status,boolean archived,int page,int size,String sort,String direction){
  String field=Set.of("name","sku","quantity","price","updatedAt").contains(sort)?sort:"name";
  Sort order=Sort.by("desc".equalsIgnoreCase(direction)?Sort.Direction.DESC:Sort.Direction.ASC,field).and(Sort.by("id"));
  Pageable pageable=PageRequest.of(Math.max(page,0),Math.min(Math.max(size,1),100),order);
  Specification<Product> spec=(root,query,cb)->{
   var predicates=new ArrayList<jakarta.persistence.criteria.Predicate>();
   predicates.add(cb.equal(root.get("active"),!archived));
   if(q!=null&&!q.isBlank()){String like="%"+q.trim().toLowerCase(Locale.ROOT)+"%";predicates.add(cb.or(cb.like(cb.lower(root.get("name")),like),cb.like(cb.lower(root.get("sku")),like),cb.like(cb.lower(root.get("barcode")),like)));}
   if(categoryId!=null)predicates.add(cb.equal(root.get("category").get("id"),categoryId));
   if("out".equals(status))predicates.add(cb.equal(root.get("sellableQuantity"),0L));
   if("low".equals(status))predicates.add(cb.and(cb.greaterThan(root.get("sellableQuantity"),0L),cb.lessThanOrEqualTo(root.get("sellableQuantity"),root.get("reorderThreshold"))));
   if("healthy".equals(status))predicates.add(cb.greaterThan(root.get("sellableQuantity"),root.get("reorderThreshold")));
   return cb.and(predicates.toArray(jakarta.persistence.criteria.Predicate[]::new));
  };
  return PageResult.of(products.findAll(spec,pageable).map(ProductView::of));
 }
 @Transactional(readOnly=true) ProductView product(long id){return ProductView.of(products.findById(id).orElseThrow(()->notFound("Product not found")));}
 @Transactional ProductView saveProduct(Long id,ProductInput in){
  if(in.safetyStock()>in.reorderThreshold())throw bad("Safety stock must not exceed reorder threshold");
  Product p=id==null?new Product():products.lockById(id).orElseThrow(()->notFound("Product not found"));
  if(id!=null&&p.quantity>0){/* quantity is never writable through catalog input */}
  if(products.existsBySkuIgnoreCaseAndIdNot(in.sku().trim(),p.id==null?0L:p.id))throw conflict("SKU already exists");
  if(in.barcode()!=null&&!in.barcode().isBlank()&&products.existsByBarcodeIgnoreCaseAndIdNot(in.barcode().trim(),p.id==null?0L:p.id))throw conflict("Barcode already exists");
  p.sku=in.sku().trim();p.barcode=blankToNull(in.barcode());p.name=in.name().trim();p.unit=in.unit().trim();p.price=in.price();p.safetyStock=in.safetyStock();p.reorderThreshold=in.reorderThreshold();
  p.category=in.categoryId()==null?null:categories.findById(in.categoryId()).orElseThrow(()->bad("Category not found"));
  p.supplier=in.supplierId()==null?null:suppliers.findById(in.supplierId()).orElseThrow(()->bad("Supplier not found"));p.updatedAt=Instant.now();
  Product saved=products.saveAndFlush(p); updateWarning(saved);invalidate();return ProductView.of(saved);
 }
 @Transactional void archiveProduct(long id){Product p=products.lockById(id).orElseThrow(()->notFound("Product not found"));p.active=false;p.updatedAt=Instant.now();updateWarning(p);invalidate();}
 @Transactional ProductView thresholds(long id,ThresholdInput in){if(in.safetyStock()>in.reorderThreshold())throw bad("Safety stock must not exceed reorder threshold");Product p=products.lockById(id).orElseThrow(()->notFound("Product not found"));p.safetyStock=in.safetyStock();p.reorderThreshold=in.reorderThreshold();p.updatedAt=Instant.now();updateWarning(p);invalidate();return ProductView.of(p);}
 @Transactional(isolation=org.springframework.transaction.annotation.Isolation.READ_COMMITTED) TransactionView move(TransactionInput in,String username){
  UserAccount actor=users.findByUsername(username).orElseThrow(()->notFound("User not found"));
  Product p=products.lockById(in.productId()).orElseThrow(()->notFound("Product not found"));if(!p.active)throw bad("Archived products cannot receive stock movements");
  var prior=transactions.findByActorIdAndIdempotencyKey(actor.id,in.idempotencyKey());
  if(prior.isPresent()){InventoryTransaction t=prior.get();boolean sameQuantity=in.type()==MovementType.STOCKTAKE?t.quantityAfter==in.quantity():t.delta==signedDelta(in);if(!t.product.id.equals(in.productId())||t.type!=in.type()||!sameQuantity||!t.reason.equals(in.reason().trim())||!t.requestMetadata.equals(in.metadata()))throw conflict("Idempotency key was already used with a different request");return TransactionView.of(t);}
  long delta=in.type()==MovementType.STOCKTAKE?in.quantity()-p.quantity:signedDelta(in);if(in.type()==MovementType.STOCKTAKE&&(in.quantity()<0||in.quantity()>1_000_000_000L))throw bad("Stocktake quantity must be between zero and 1,000,000,000");if(delta==0&&in.type()!=MovementType.STOCKTAKE)throw bad("Movement quantity must be non-zero");long after;
  try{after=Math.addExact(p.quantity,delta);}catch(ArithmeticException e){throw bad("Quantity is outside the supported range");}
  if(after<0)throw bad("Insufficient stock: available quantity is "+p.quantity);if(after>1_000_000_000L)throw bad("Maximum stock quantity exceeded");
  InventoryTransaction t=new InventoryTransaction();t.product=p;t.actor=actor;t.type=in.type();t.delta=delta;t.quantityBefore=p.quantity;t.quantityAfter=after;t.reason=in.reason().trim();t.idempotencyKey=in.idempotencyKey();t.requestMetadata=in.metadata();
  p.updatedAt=Instant.now();transactions.saveAndFlush(t);batchInventory.apply(p,t,in);p.quantity=after;updateWarning(p);invalidate();return TransactionView.of(t);
 }
 private long signedDelta(TransactionInput in){return switch(in.type()){case STOCK_IN->{if(in.quantity()<=0)throw bad("Stock-in quantity must be positive");yield in.quantity();}case STOCK_OUT->{if(in.quantity()<=0)throw bad("Stock-out quantity must be positive");yield -in.quantity();}case ADJUSTMENT->{if(in.quantity()==0)throw bad("Adjustment cannot be zero");yield in.quantity();}case STOCKTAKE->{yield in.quantity();}};}
 @Transactional(readOnly=true) PageResult<TransactionView> history(Long productId,int page,int size){Pageable p=PageRequest.of(Math.max(page,0),Math.min(Math.max(size,1),100));var result=productId==null?transactions.findAllByOrderByCreatedAtDesc(p):transactions.findAllByProductIdOrderByCreatedAtDesc(productId,p);return PageResult.of(result.map(TransactionView::of));}

 @Transactional(readOnly=true) PageResult<WarningView> warningPage(String type,String state,int page,int size,boolean cacheEnabled){
  String revision=Long.toString(revisions.findById(1L).map(r->r.revision).orElse(0L));String key="warning:"+revision+":"+type+":"+state+":"+page+":"+size;
  if(cacheEnabled)try{String value=redis.opsForValue().get(key);if(value!=null)return decodePage(value);}catch(Exception ignored){}
  Pageable pageable=PageRequest.of(Math.max(page,0),Math.min(Math.max(size,1),100));Page<WarningEpisode> result;
  WarningType selectedType=type==null||type.isBlank()?null:WarningType.valueOf(type.toUpperCase(Locale.ROOT));
  if("open".equalsIgnoreCase(state))result=selectedType==null?warnings.activeWarnings(WarningState.OPEN,pageable):selectedType==WarningType.RESTOCKED?warnings.activeRestocked(WarningState.OPEN,pageable):warnings.findByTypeAndStateOrderByCreatedAtDesc(selectedType,WarningState.OPEN,pageable);
  else if("resolved".equalsIgnoreCase(state))result=selectedType==null?warnings.findByStateOrderByCreatedAtDesc(WarningState.RESOLVED,pageable):warnings.findByTypeAndStateOrderByCreatedAtDesc(selectedType,WarningState.RESOLVED,pageable);
  else result=selectedType==null?warnings.findAllByOrderByCreatedAtDesc(pageable):warnings.findByTypeOrderByCreatedAtDesc(selectedType,pageable);
  var filtered=result.map(WarningView::of);
  // Filter in SQL before pagination so totals describe the selected warning type.
  PageResult<WarningView> response=new PageResult<>(filtered.getContent(),filtered.getNumber(),filtered.getSize(),filtered.getTotalElements(),filtered.getTotalPages());
  if(cacheEnabled)try{redis.opsForValue().set(key,new com.fasterxml.jackson.databind.ObjectMapper().findAndRegisterModules().disable(com.fasterxml.jackson.databind.SerializationFeature.WRITE_DATES_AS_TIMESTAMPS).writeValueAsString(response),props.cacheTtlSeconds(),TimeUnit.SECONDS);}catch(Exception ignored){}
  return response;
 }
 private PageResult<WarningView> decodePage(String json){try{return new com.fasterxml.jackson.databind.ObjectMapper().findAndRegisterModules().readValue(json,new com.fasterxml.jackson.core.type.TypeReference<PageResult<WarningView>>(){});}catch(Exception e){throw new IllegalStateException(e);}}
 @Transactional WarningView acknowledge(long id,String username){return workflow.acknowledge(id,username);}
 @Transactional(readOnly=true) DashboardView dashboard(){
  List<Product> all=products.findAllByActiveTrue();long low=all.stream().filter(p->p.sellableQuantity>0&&p.sellableQuantity<=p.reorderThreshold).count();long out=all.stream().filter(p->p.sellableQuantity==0).count();
  BigDecimal value=all.stream().map(p->p.price.multiply(BigDecimal.valueOf(p.quantity))).reduce(BigDecimal.ZERO,BigDecimal::add);
  List<ProductView> urgent=all.stream().filter(p->p.sellableQuantity<=p.reorderThreshold).sorted(Comparator.comparingLong(p->p.sellableQuantity)).limit(6).map(ProductView::of).toList();
  var series=activitySeries();List<String> dates=series.get(0);List<Long> counts=series.get(1);
  Map<String,List<Product>> groups=new TreeMap<>();for(Product p:all)groups.computeIfAbsent(p.category==null?"Uncategorised":p.category.name,k->new ArrayList<>()).add(p);
  List<CategoryMetric> mix=groups.entrySet().stream().map(e->new CategoryMetric(e.getKey(),e.getValue().stream().mapToLong(p->p.quantity).sum(),e.getValue().size())).toList();
  var page=warningPage("","open",0,5,true);
  return new DashboardView(all.size(),low,out,value,transactions.count(),dates,counts,mix,urgent,page.items());
 }
 @Transactional(readOnly=true) Map<String,Object> report(){List<Product> all=products.findAll();var series=activitySeries();LocalDate today=LocalDate.now(ZoneOffset.UTC);return Map.of("activeProducts",all.stream().filter(p->p.active).count(),"lowStock",all.stream().filter(p->p.active&&p.sellableQuantity>0&&p.sellableQuantity<=p.reorderThreshold).count(),"outOfStock",all.stream().filter(p->p.active&&p.sellableQuantity==0).count(),"inventoryValue",all.stream().filter(p->p.active).map(p->p.price.multiply(BigDecimal.valueOf(p.quantity))).reduce(BigDecimal.ZERO,BigDecimal::add),"movementsToday",transactions.countByCreatedAtAfter(today.atStartOfDay(ZoneOffset.UTC).toInstant()),"totalMovements",transactions.count(),"activityDates",series.get(0),"activityCounts",series.get(1));}
 private List<List> activitySeries(){LocalDate today=LocalDate.now(ZoneOffset.UTC);LocalDate start=today.minusDays(6);Map<LocalDate,Long> grouped=new HashMap<>();for(InventoryTransaction t:transactions.findByCreatedAtAfter(start.atStartOfDay(ZoneOffset.UTC).toInstant())){LocalDate date=t.createdAt.atZone(ZoneOffset.UTC).toLocalDate();grouped.merge(date,1L,Long::sum);}List<String> dates=new ArrayList<>();List<Long> counts=new ArrayList<>();for(int i=6;i>=0;i--){LocalDate d=today.minusDays(i);dates.add(d.toString());counts.add(grouped.getOrDefault(d,0L));}return List.of(dates,counts);}
 @Transactional(readOnly=true) List<Category> categoryList(){return categories.findAll(Sort.by("name"));}
 @Transactional Category createCategory(CategoryInput in){if(categories.existsByNameIgnoreCase(in.name()))throw conflict("Category name already exists");return categories.save(new Category(in.name().trim(),blankToNull(in.description())));}
 @Transactional Category updateCategory(long id,CategoryInput in){Category c=categories.findById(id).orElseThrow(()->notFound("Category not found"));c.name=in.name().trim();c.description=blankToNull(in.description());invalidate();return c;}
 @Transactional void deleteCategory(long id){if(!categories.existsById(id))throw notFound("Category not found");categories.deleteById(id);categories.flush();invalidate();}
 @Transactional(readOnly=true) List<Supplier> supplierList(){return suppliers.findAll(Sort.by("name"));}
 @Transactional Supplier createSupplier(SupplierInput in){Supplier s=new Supplier();s.name=in.name().trim();s.contactName=blankToNull(in.contactName());s.email=blankToNull(in.email());s.phone=blankToNull(in.phone());return suppliers.save(s);}
 @Transactional Supplier updateSupplier(long id,SupplierInput in){Supplier s=suppliers.findById(id).orElseThrow(()->notFound("Supplier not found"));s.name=in.name().trim();s.contactName=blankToNull(in.contactName());s.email=blankToNull(in.email());s.phone=blankToNull(in.phone());invalidate();return s;}
 @Transactional void deleteSupplier(long id){if(!suppliers.existsById(id))throw notFound("Supplier not found");suppliers.deleteById(id);suppliers.flush();invalidate();}
 @Transactional(readOnly=true) List<UserView> userList(){return users.findAll(Sort.by("username")).stream().map(UserView::of).toList();}
 @Transactional UserView createUser(UserInput in){if(in.password().getBytes(java.nio.charset.StandardCharsets.UTF_8).length>72)throw bad("Password must fit within 72 UTF-8 bytes");if(users.findByUsername(in.username().trim()).isPresent())throw conflict("Username already exists");return UserView.of(users.save(new UserAccount(in.username().trim(),in.displayName().trim(),encoder.encode(in.password()),in.role())));}
 @Transactional UserView setUserEnabled(long id,boolean enabled){em.find(CacheRevision.class,1L,jakarta.persistence.LockModeType.PESSIMISTIC_WRITE);UserAccount u=users.findById(id).orElseThrow(()->notFound("User not found"));if(u.role==Role.ADMIN&&u.enabled&&!enabled&&users.countByRoleAndEnabledTrue(Role.ADMIN)<=1)throw conflict("At least one enabled administrator is required");u.enabled=enabled;return UserView.of(u);}
 @Transactional UserView updateAccess(long id,UserAccessInput in){em.find(CacheRevision.class,1L,jakarta.persistence.LockModeType.PESSIMISTIC_WRITE);UserAccount u=users.findById(id).orElseThrow(()->notFound("User not found"));if(u.role==Role.ADMIN&&u.enabled&&(in.role()!=Role.ADMIN||!in.enabled())&&users.countByRoleAndEnabledTrue(Role.ADMIN)<=1)throw conflict("At least one enabled administrator is required");u.role=in.role();u.enabled=in.enabled();return UserView.of(u);}
 @Transactional(readOnly=true) Map<String,String> getSettings(){Map<String,String> m=new TreeMap<>();settings.findAll().forEach(s->m.put(s.settingKey,s.settingValue));return m;}
 @Transactional Map<String,String> putSettings(SettingInput in){set("business_name",in.businessName().trim());set("currency",in.currency());invalidate();return getSettings();}
 private void set(String k,String v){AppSetting s=settings.findById(k).orElseGet(AppSetting::new);s.settingKey=k;s.settingValue=v;settings.save(s);}

 @Transactional void seed(){if(!props.demoEnabled()||props.demoPassword()==null||props.demoPassword().length()<12||users.count()>0)return;
  for(Role role:Role.values()){String username=role.name().toLowerCase();users.save(new UserAccount(username,role==Role.ADMIN?"Alex Morgan":role==Role.MANAGER?"Jordan Lee":"Sam Taylor",encoder.encode(props.demoPassword()),role));}
  Category produce=categories.save(new Category("Produce","Fresh fruit and vegetables"));Category dairy=categories.save(new Category("Dairy & chilled","Milk, dairy and refrigerated goods"));Category pantry=categories.save(new Category("Pantry","Shelf-stable groceries"));
  addProduct("PRD-1042","4890000001042","Organic whole milk 1L","bottle",3.49,2,8,dairy);addProduct("PRD-1088","4890000001088","Free-range eggs (12 pack)","pack",5.29,4,10,dairy);addProduct("PRD-1125","4890000001125","Sourdough loaf","loaf",4.25,3,8,pantry);addProduct("PRD-1210","4890000001210","Bananas, loose","kg",2.80,6,18,produce);addProduct("PRD-1304","4890000001304","Greek yoghurt 500g","tub",6.50,5,12,dairy);addProduct("PRD-1440","4890000001440","Ground coffee 250g","bag",12.90,3,8,pantry);addProduct("PRD-1512","4890000001512","Baby spinach 120g","bag",4.10,0,6,produce);addProduct("PRD-1668","4890000001668","Oat drink 1L","carton",5.20,0,5,dairy);addProduct("PRD-1701","4890000001701","Tomatoes, vine","kg",7.90,11,15,produce);addProduct("PRD-1819","4890000001819","Penne pasta 500g","pack",3.20,0,12,pantry);
  for(Product p:products.findAll())updateWarning(p);
 }
 private void addProduct(String sku,String code,String name,String unit,double price,long qty,long threshold,Category c){Product p=new Product();p.sku=sku;p.barcode=code;p.name=name;p.unit=unit;p.price=BigDecimal.valueOf(price);p.quantity=qty;p.safetyStock=Math.min(qty/2,threshold);p.reorderThreshold=threshold;p.category=c;p=products.save(p);batchInventory.seedBalance(p);if(qty>0){InventoryTransaction t=new InventoryTransaction();t.product=p;t.actor=users.findByUsername("admin").orElseThrow();t.type=MovementType.STOCK_IN;t.delta=qty;t.quantityBefore=0;t.quantityAfter=qty;t.reason="Opening demonstration stock";t.idempotencyKey="seed-"+sku;transactions.save(t);}}
 @Transactional void cleanupExpiries(){var expired=warnings.findByTypeAndStateAndExpiresAtBefore(WarningType.RESTOCKED,WarningState.OPEN,Instant.now());for(WarningEpisode w:expired)workflow.recover(w);if(!expired.isEmpty())invalidate();}
 @Transactional void updateWarning(Product p){batchInventory.recompute(p);warningRules.refresh(p);List<WarningEpisode> open=warnings.findByProductIdAndState(p.id,WarningState.OPEN).stream().filter(w->w.type==WarningType.LOW||w.type==WarningType.OUT||w.type==WarningType.RESTOCKED).toList();WarningType next=p.sellableQuantity==0?WarningType.OUT:p.sellableQuantity<=p.reorderThreshold?WarningType.LOW:null;
  if(!p.active){for(WarningEpisode w:open)workflow.recover(w);return;}
  if(next==null){boolean hadShortage=open.stream().anyMatch(w->w.type!=WarningType.RESTOCKED);for(WarningEpisode w:open)if(w.type!=WarningType.RESTOCKED)workflow.recover(w);if(hadShortage&&open.stream().noneMatch(w->w.type==WarningType.RESTOCKED)){WarningEpisode w=new WarningEpisode();w.product=p;w.type=WarningType.RESTOCKED;w.observedQuantity=p.sellableQuantity;w.threshold=p.reorderThreshold;w.createdAt=Instant.now();w.expiresAt=w.createdAt.plus(Duration.ofHours(24));warnings.save(w);workflow.created(w);}return;}
  for(WarningEpisode w:open)if(w.type!=next||w.type==WarningType.RESTOCKED)workflow.recover(w);
  if(open.stream().noneMatch(w->w.type==next&&w.state==WarningState.OPEN)){WarningEpisode w=new WarningEpisode();w.product=p;w.type=next;w.observedQuantity=p.sellableQuantity;w.threshold=p.reorderThreshold;w.createdAt=Instant.now();w.expiresAt=w.createdAt.plus(Duration.ofDays(3650));w.previousId=warnings.findFirstByProductIdAndTypeOrderByCreatedAtDesc(p.id,next).map(x->x.id).orElse(null);warnings.save(w);workflow.created(w);}
  else open.stream().filter(w->w.type==next&&w.state==WarningState.OPEN).findFirst().ifPresent(w->{w.observedQuantity=p.sellableQuantity;w.threshold=p.reorderThreshold;});
 }
 private void invalidate(){revisions.increment();}
 @Transactional void refreshWarning(long id){Product p=products.lockById(id).orElseThrow(()->notFound("Product not found"));String before=warningFingerprint(p);updateWarning(p);if(!before.equals(warningFingerprint(p)))invalidate();}
 private String warningFingerprint(Product p){return p.sellableQuantity+":"+warnings.findByProductIdAndState(p.id,WarningState.OPEN).stream().map(w->w.id+":"+w.type+":"+w.observedQuantity+":"+w.threshold).sorted().toList();}
 private String blankToNull(String s){return s==null||s.isBlank()?null:s.trim();}
 private RuntimeException bad(String m){return new DomainException("VALIDATION",m,400);}private RuntimeException notFound(String m){return new DomainException("NOT_FOUND",m,404);}private RuntimeException conflict(String m){return new DomainException("CONFLICT",m,409);}
}
