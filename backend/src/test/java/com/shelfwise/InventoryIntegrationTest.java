package com.shelfwise;

import static org.assertj.core.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import com.fasterxml.jackson.databind.ObjectMapper;

@SpringBootTest @AutoConfigureMockMvc @Testcontainers
class InventoryIntegrationTest {
 @Container static MySQLContainer<?> mysql=new MySQLContainer<>("mysql:8.4.8");
 @Container static GenericContainer<?> redis=new GenericContainer<>("redis:7.4.9-alpine").withExposedPorts(6379);
 @DynamicPropertySource static void properties(DynamicPropertyRegistry r){r.add("spring.datasource.url",mysql::getJdbcUrl);r.add("spring.datasource.username",mysql::getUsername);r.add("spring.datasource.password",mysql::getPassword);r.add("spring.data.redis.host",redis::getHost);r.add("spring.data.redis.port",()->redis.getMappedPort(6379));r.add("shelfwise.demo-enabled",()->true);r.add("shelfwise.demo-password",()->"test-only-demo-password");}
 @Autowired InventoryService service; @Autowired ProductRepository products; @Autowired TransactionRepository transactions; @Autowired WarningRepository warnings;
 @Autowired MockMvc mvc; @Autowired ObjectMapper mapper;
 @Autowired WarningWorkflow workflow;
 @Autowired BatchInventory batches;
 @Test void batchDispatchUsesFefoAndExcludesExpiredOrQuarantined(){
  Product p=fresh();var today=batches.today();
  service.move(new TransactionInput(p.id,MovementType.STOCK_IN,4L,"Early",UUID.randomUUID().toString(),"early",null,today.plusDays(1),null),"admin");
  service.move(new TransactionInput(p.id,MovementType.STOCK_IN,6L,"Late",UUID.randomUUID().toString(),"late",null,today.plusDays(5),null),"admin");
  service.move(new TransactionInput(p.id,MovementType.STOCK_IN,3L,"Expired",UUID.randomUUID().toString(),"expired",null,today.minusDays(1),null),"admin");
  assertThat(service.product(p.id).quantity()).isEqualTo(13);assertThat(service.product(p.id).sellableQuantity()).isEqualTo(10);
  var out=service.move(movement(p,MovementType.STOCK_OUT,5,UUID.randomUUID().toString()),"clerk");
  assertThat(batches.transactionAllocations(out.id())).extracting(AllocationView::batchNumber).containsExactly("early","late");
  assertThat(batches.transactionAllocations(out.id())).extracting(AllocationView::delta).containsExactly(-4L,-1L);
  var late=batches.list(p.id,0,100).items().stream().filter(b->b.batchNumber().equals("late")).findFirst().orElseThrow();
  batches.control(late.id(),new BatchControlInput(true,"Damaged packaging"),"manager");service.refreshWarning(p.id);
  assertThat(service.product(p.id).sellableQuantity()).isZero();
  assertThatThrownBy(()->service.move(movement(p,MovementType.STOCK_OUT,1,UUID.randomUUID().toString()),"admin")).isInstanceOf(DomainException.class);
  assertThat(service.product(p.id).quantity()).isEqualTo(8);
 }
 @Test void receiptReplayChecksBatchMetadataAndRollsBackInvalidDates(){
  Product p=fresh();String key=UUID.randomUUID().toString();
  var in=new TransactionInput(p.id,MovementType.STOCK_IN,3L,"Receipt",key,"a",null,batches.today(),null);
  assertThat(service.move(in,"admin").id()).isEqualTo(service.move(in,"admin").id());
  assertThatThrownBy(()->service.move(new TransactionInput(p.id,MovementType.STOCK_IN,3L,"Receipt",key,"b",null,batches.today(),null),"admin")).isInstanceOf(DomainException.class);
  assertThat(batches.list(p.id,0,100).totalElements()).isEqualTo(1);
  assertThatThrownBy(()->service.move(new TransactionInput(p.id,MovementType.STOCK_IN,3L,"Invalid",UUID.randomUUID().toString(),"bad",batches.today(),batches.today().minusDays(1),null),"admin")).isInstanceOf(DomainException.class);
  assertThat(service.product(p.id).quantity()).isEqualTo(3);
 }
 @Test void warningHandlingKeepsConditionAndAudit(){
  Product p=fresh();var w=service.warningPage("OUT","open",0,100,false).items().stream().filter(x->x.productId().equals(p.id)).findFirst().orElseThrow();
  var manager=service.userList().stream().filter(u->u.username().equals("manager")).findFirst().orElseThrow();
  workflow.acknowledge(w.id(),"manager");
  var assigned=workflow.act(w.id(),new WarningActionInput("ASSIGN",manager.id(),"Follow up delivery"),"admin");
  assertThat(assigned.assignedTo()).isEqualTo("Jordan Lee");
  assertThat(workflow.act(w.id(),new WarningActionInput("PROCESS",null,"Contacted supplier"),"manager").reviewStage()).isEqualTo(ReviewStage.PROCESSING);
  assertThat(service.product(p.id).quantity()).isZero();
  service.move(movement(p,MovementType.STOCK_IN,8,UUID.randomUUID().toString()),"admin");
  assertThat(workflow.history(w.id())).extracting(WarningActionView::action).contains("CONFIRM","ASSIGN","PROCESS","RECOVER");
  assertThatThrownBy(()->workflow.act(w.id(),new WarningActionInput("PROCESS",null,"Again"),"manager")).isInstanceOf(DomainException.class);
  service.move(movement(p,MovementType.STOCK_OUT,8,UUID.randomUUID().toString()),"admin");
  var newer=service.warningPage("OUT","open",0,100,false).items().stream().filter(x->x.productId().equals(p.id)).findFirst().orElseThrow();
  assertThat(newer.previousId()).isEqualTo(w.id());assertThat(newer.reviewStage()).isEqualTo(ReviewStage.PENDING);
 }
 Product fresh(){String n=UUID.randomUUID().toString().substring(0,8);var p=service.saveProduct(null,new ProductInput("TEST-"+n,null,"Test product "+n,"pcs",new BigDecimal("2.49"),2L,5L,null,null));return products.findById(p.id()).orElseThrow();}
 TransactionInput movement(Product p,MovementType type,long qty,String key){return new TransactionInput(p.id,type,qty,"Integration test",key);}
 @Test void emptySearchAndStablePagination()throws Exception{mvc.perform(get("/api/products?q=not-a-real-sku-zz").with(user("admin").roles("ADMIN"))).andExpect(status().isOk()).andExpect(jsonPath("$.totalElements").value(0));mvc.perform(get("/api/products?size=1000").with(user("admin").roles("ADMIN"))).andExpect(jsonPath("$.size").value(100));}
 @Test void unauthorizedUserCannotReadInventory()throws Exception{mvc.perform(get("/api/products")).andExpect(status().isUnauthorized());}
 @Test void csrfRequiredForUnsafeMethods()throws Exception{mvc.perform(post("/api/transactions").with(user("admin").roles("ADMIN")).contentType("application/json").content("{}")).andExpect(status().isForbidden());}
 @Test void clerkCannotAcknowledgeOrManageUsers()throws Exception{mvc.perform(post("/api/warnings/1/ack").with(user("clerk").roles("CLERK")).with(csrf())).andExpect(status().isForbidden());mvc.perform(get("/api/users").with(user("clerk").roles("CLERK"))).andExpect(status().isForbidden());}
 @Test void managerCannotPostStock()throws Exception{mvc.perform(post("/api/transactions").with(user("manager").roles("MANAGER")).with(csrf()).contentType("application/json").content("{}")).andExpect(status().isForbidden());}
 @Test void badCatalogInputRejected()throws Exception{mvc.perform(post("/api/products").with(user("admin").roles("ADMIN")).with(csrf()).contentType("application/json").content("{\"sku\":\"\",\"name\":\"\",\"price\":-1}")).andExpect(status().isBadRequest());}
 @Test void receiptAndDispatchHaveAuditHistory(){Product p=fresh();var in=service.move(movement(p,MovementType.STOCK_IN,8,UUID.randomUUID().toString()),"clerk");assertThat(in.quantityBefore()).isZero();assertThat(in.quantityAfter()).isEqualTo(8);var out=service.move(movement(p,MovementType.STOCK_OUT,3,UUID.randomUUID().toString()),"clerk");assertThat(out.quantityAfter()).isEqualTo(5);assertThat(service.product(p.id).quantity()).isEqualTo(5);assertThat(service.history(p.id,0,20).totalElements()).isEqualTo(2);}
 @Test void negativeStockRejectedWithoutHistory(){Product p=fresh();long count=transactions.count();assertThatThrownBy(()->service.move(movement(p,MovementType.STOCK_OUT,1,UUID.randomUUID().toString()),"admin")).isInstanceOf(DomainException.class);assertThat(transactions.count()).isEqualTo(count);assertThat(service.product(p.id).quantity()).isZero();}
 @Test void exactReplayReturnsSameId(){Product p=fresh();var body=movement(p,MovementType.STOCK_IN,4,UUID.randomUUID().toString());var a=service.move(body,"admin");var b=service.move(body,"admin");assertThat(a.id()).isEqualTo(b.id());assertThat(service.product(p.id).quantity()).isEqualTo(4);}
 @Test void changedPayloadReplayConflicts(){Product p=fresh();String key=UUID.randomUUID().toString();service.move(movement(p,MovementType.STOCK_IN,4,key),"admin");assertThatThrownBy(()->service.move(movement(p,MovementType.STOCK_IN,5,key),"admin")).isInstanceOf(DomainException.class).hasMessageContaining("different request");}
 @Test void thresholdEqualityIsLowAndZeroIsOut(){Product p=fresh();assertThat(service.warningPage("OUT","open",0,100,false).items()).anyMatch(w->w.productId().equals(p.id));service.move(movement(p,MovementType.STOCK_IN,5,UUID.randomUUID().toString()),"admin");assertThat(service.warningPage("LOW","open",0,100,false).items()).anyMatch(w->w.productId().equals(p.id));}
 @Test void healthyReplenishmentResolvesShortage(){Product p=fresh();service.move(movement(p,MovementType.STOCK_IN,6,UUID.randomUUID().toString()),"admin");assertThat(service.warningPage("OUT","open",0,100,false).items()).noneMatch(w->w.productId().equals(p.id));assertThat(service.warningPage("RESTOCKED","open",0,100,false).items()).anyMatch(w->w.productId().equals(p.id));}
 @Test void acknowledgementIsVisibleThroughCache(){Product p=fresh();var w=service.warningPage("OUT","open",0,100,true).items().stream().filter(x->x.productId().equals(p.id)).findFirst().orElseThrow();service.acknowledge(w.id(),"manager");assertThat(service.warningPage("OUT","open",0,100,true).items()).anyMatch(x->x.id().equals(w.id())&&"Jordan Lee".equals(x.acknowledgedBy()));assertThat(service.product(p.id).quantity()).isZero();}
 @Test void signedAdjustmentAndAbsoluteCount(){Product p=fresh();service.move(movement(p,MovementType.STOCK_IN,10,UUID.randomUUID().toString()),"admin");var a=service.move(movement(p,MovementType.ADJUSTMENT,-2,UUID.randomUUID().toString()),"admin");assertThat(a.quantityAfter()).isEqualTo(8);var c=service.move(movement(p,MovementType.STOCKTAKE,3,UUID.randomUUID().toString()),"admin");assertThat(c.delta()).isEqualTo(-5);assertThat(c.quantityAfter()).isEqualTo(3);}
 @Test void countToZeroIsAuditable(){Product p=fresh();service.move(movement(p,MovementType.STOCK_IN,3,UUID.randomUUID().toString()),"admin");var c=service.move(movement(p,MovementType.STOCKTAKE,0,UUID.randomUUID().toString()),"admin");assertThat(c.delta()).isEqualTo(-3);assertThat(c.quantityAfter()).isZero();}
 @Test void archivedProductCannotMove(){Product p=fresh();service.archiveProduct(p.id);assertThatThrownBy(()->service.move(movement(p,MovementType.STOCK_IN,1,UUID.randomUUID().toString()),"admin")).isInstanceOf(DomainException.class).hasMessageContaining("Archived");}
 @Test void uniqueSkuAndThresholdHierarchy(){Product p=fresh();assertThatThrownBy(()->service.saveProduct(null,new ProductInput(p.sku,null,"Other","pcs",BigDecimal.ONE,0L,0L,null,null))).isInstanceOf(DomainException.class);assertThatThrownBy(()->service.saveProduct(null,new ProductInput("NEW-"+UUID.randomUUID(),null,"Other","pcs",BigDecimal.ONE,5L,4L,null,null))).isInstanceOf(DomainException.class);}
 @Test void concurrentDispatchCannotOversell()throws Exception{Product p=fresh();service.move(movement(p,MovementType.STOCK_IN,7,UUID.randomUUID().toString()),"admin");var executor=Executors.newFixedThreadPool(6);try{List<Future<Boolean>> results=new ArrayList<>();for(int i=0;i<12;i++)results.add(executor.submit(()->{try{service.move(movement(p,MovementType.STOCK_OUT,1,UUID.randomUUID().toString()),"clerk");return true;}catch(DomainException e){return false;}}));int successes=0;for(var f:results)if(f.get())successes++;assertThat(successes).isEqualTo(7);assertThat(service.product(p.id).quantity()).isZero();}finally{executor.shutdownNow();}}
 @Test void concurrentIdenticalSubmissionDoesNotDuplicate()throws Exception{Product p=fresh();var body=movement(p,MovementType.STOCK_IN,4,UUID.randomUUID().toString());var executor=Executors.newFixedThreadPool(4);try{List<Future<Long>> futures=new ArrayList<>();for(int i=0;i<4;i++)futures.add(executor.submit(()->service.move(body,"admin").id()));Set<Long> ids=new HashSet<>();for(var f:futures)ids.add(f.get());assertThat(ids).hasSize(1);assertThat(service.product(p.id).quantity()).isEqualTo(4);}finally{executor.shutdownNow();}}

 @Test void sameCountStillRecordsAudit(){Product p=fresh();var c=service.move(movement(p,MovementType.STOCKTAKE,0,UUID.randomUUID().toString()),"admin");assertThat(c.delta()).isZero();assertThat(service.history(p.id,0,20).totalElements()).isEqualTo(1);}
 @Test void managerThresholdEndpointAndClerkDenial()throws Exception{Product p=fresh();String body="{\"safetyStock\":1,\"reorderThreshold\":4}";mvc.perform(patch("/api/products/"+p.id+"/thresholds").with(user("manager").roles("MANAGER")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isOk()).andExpect(jsonPath("$.reorderThreshold").value(4));mvc.perform(patch("/api/products/"+p.id+"/thresholds").with(user("clerk").roles("CLERK")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isForbidden());}
 @Test void lastAdminCannotBeDisabledOrDemoted(){var admin=service.userList().stream().filter(u->u.username().equals("admin")).findFirst().orElseThrow();assertThatThrownBy(()->service.setUserEnabled(admin.id(),false)).isInstanceOf(DomainException.class);assertThatThrownBy(()->service.updateAccess(admin.id(),new UserAccessInput(Role.CLERK,true))).isInstanceOf(DomainException.class);}
 @Test void archivedWarningsAreResolved(){Product p=fresh();service.archiveProduct(p.id);assertThat(service.warningPage("OUT","open",0,100,false).items()).noneMatch(w->w.productId().equals(p.id));}
 @Test void restockedExpiresAndNewShortageStartsNewEpisode(){Product p=fresh();service.move(movement(p,MovementType.STOCK_IN,8,UUID.randomUUID().toString()),"admin");service.move(movement(p,MovementType.STOCK_OUT,8,UUID.randomUUID().toString()),"admin");assertThat(service.warningPage("RESTOCKED","open",0,100,false).items()).noneMatch(w->w.productId().equals(p.id));assertThat(service.warningPage("OUT","open",0,100,false).items()).anyMatch(w->w.productId().equals(p.id));}
 @Test void warningFiltersHaveAccurateTotals(){Product p=fresh();var page=service.warningPage("OUT","open",0,100,false);assertThat(page.items()).allMatch(w->w.type()==WarningType.OUT);assertThat(page.totalElements()).isEqualTo(page.items().size());}

 @Test void concurrentAcknowledgementsPreserveFirstReviewer()throws Exception{Product p=fresh();var w=service.warningPage("OUT","open",0,100,false).items().stream().filter(x->x.productId().equals(p.id)).findFirst().orElseThrow();var ex=Executors.newFixedThreadPool(2);try{var a=ex.submit(()->service.acknowledge(w.id(),"admin"));var b=ex.submit(()->service.acknowledge(w.id(),"manager"));assertThat(a.get().acknowledgedBy()).isEqualTo(b.get().acknowledgedBy());}finally{ex.shutdownNow();}}
 @Test void invalidCredentialsAndNullLoginFieldsReturnClientErrors()throws Exception{mvc.perform(post("/api/auth/login").with(csrf()).contentType("application/json").content("{\"username\":\"admin\",\"password\":\"incorrect-password\"}")).andExpect(status().isUnauthorized());mvc.perform(post("/api/auth/login").with(csrf()).contentType("application/json").content("{\"username\":null,\"password\":null}")).andExpect(status().isBadRequest());}
}
