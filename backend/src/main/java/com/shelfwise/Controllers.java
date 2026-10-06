package com.shelfwise;

import jakarta.validation.Valid;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.time.Instant;
import java.util.*;

@RestControllerAdvice
class ApiErrors {
 @ExceptionHandler(DomainException.class) org.springframework.http.ResponseEntity<ErrorView> domain(DomainException e){return org.springframework.http.ResponseEntity.status(e.status).body(new ErrorView(e.code,e.getMessage(),Instant.now()));}
 @ExceptionHandler(org.springframework.web.bind.MethodArgumentNotValidException.class) org.springframework.http.ResponseEntity<ErrorView> validation(Exception e){return org.springframework.http.ResponseEntity.badRequest().body(new ErrorView("VALIDATION","Check the submitted fields and try again.",Instant.now()));}
 @ExceptionHandler(org.springframework.dao.DataIntegrityViolationException.class) org.springframework.http.ResponseEntity<ErrorView> duplicate(Exception e){return org.springframework.http.ResponseEntity.status(409).body(new ErrorView("CONFLICT","The record conflicts with existing data or is still referenced.",Instant.now()));}
 @ExceptionHandler(org.springframework.security.authentication.BadCredentialsException.class) org.springframework.http.ResponseEntity<ErrorView> credentials(Exception e){return org.springframework.http.ResponseEntity.status(401).body(new ErrorView("INVALID_CREDENTIALS","Username or password is incorrect.",Instant.now()));}
}
class DomainException extends RuntimeException {final String code;final int status;DomainException(String code,String message,int status){super(message);this.code=code;this.status=status;}}

@RestController @RequestMapping("/api")
class ApiController {
 private final InventoryService service;private final ProductRepository products;
 ApiController(InventoryService service,ProductRepository products){this.service=service;this.products=products;}
 @GetMapping("/products") PageResult<ProductView> products(@RequestParam(defaultValue="")String q,@RequestParam(required=false)Long categoryId,@RequestParam(defaultValue="")String status,@RequestParam(defaultValue="false")boolean archived,@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="20")int size,@RequestParam(defaultValue="name")String sort,@RequestParam(defaultValue="asc")String direction){return service.listProducts(q,categoryId,status,archived,page,size,sort,direction);}
 @GetMapping("/products/{id}") ProductView product(@PathVariable long id){return service.product(id);}
 @PostMapping("/products") @ResponseStatus(HttpStatus.CREATED) ProductView createProduct(@Valid @RequestBody ProductInput in){return service.saveProduct(null,in);}
 @PutMapping("/products/{id}") ProductView updateProduct(@PathVariable long id,@Valid @RequestBody ProductInput in){return service.saveProduct(id,in);}
 @DeleteMapping("/products/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) void archiveProduct(@PathVariable long id){service.archiveProduct(id);}
 @PatchMapping("/products/{id}/thresholds") ProductView thresholds(@PathVariable long id,@Valid @RequestBody ThresholdInput in){return service.thresholds(id,in);}
 @PostMapping("/transactions") @ResponseStatus(HttpStatus.CREATED) TransactionView move(@Valid @RequestBody TransactionInput in,org.springframework.security.core.Authentication auth){if((in.type()==MovementType.ADJUSTMENT||in.type()==MovementType.STOCKTAKE)&&auth.getAuthorities().stream().noneMatch(a->a.getAuthority().equals("ROLE_ADMIN")))throw new DomainException("FORBIDDEN","Submit stock adjustments and counts for approval",403);return service.move(in,auth.getName());}
 @GetMapping("/transactions") PageResult<TransactionView> transactions(@RequestParam(required=false)Long productId,@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="20")int size){return service.history(productId,page,size);}
 @GetMapping("/warnings") PageResult<WarningView> warnings(@RequestParam(defaultValue="")String type,@RequestParam(defaultValue="open")String state,@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="20")int size,@RequestParam(defaultValue="true")boolean cache){if(!type.isBlank()&&!Set.of("LOW","OUT","RESTOCKED","EXPIRING","EXPIRED","SLOW").contains(type.toUpperCase()))throw new DomainException("VALIDATION","Unknown warning type",400);if(!Set.of("open","resolved","all").contains(state.toLowerCase()))throw new DomainException("VALIDATION","Unknown warning state",400);return service.warningPage(type,state,page,size,cache);}
 @PostMapping("/warnings/{id}/ack") WarningView acknowledge(@PathVariable long id,org.springframework.security.core.Authentication auth){return service.acknowledge(id,auth.getName());}
 @org.springframework.beans.factory.annotation.Autowired private WarningWorkflow workflow;
 @GetMapping("/warnings/assignees") List<UserView> assignees(){return workflow.assignees();}
 @GetMapping("/warnings/{id}/history") List<WarningActionView> warningHistory(@PathVariable long id){return workflow.history(id);}
 @PostMapping("/warnings/{id}/actions") WarningView warningAction(@PathVariable long id,@Valid @RequestBody WarningActionInput in,org.springframework.security.core.Authentication auth){return workflow.act(id,in,auth.getName());}
 @GetMapping("/dashboard") DashboardView dashboard(){return service.dashboard();}
 @GetMapping("/stock-summary") DashboardView stockSummary(){var d=service.dashboard();return new DashboardView(d.productCount(),d.lowStock(),d.outOfStock(),d.inventoryValue(),d.transactionCount(),d.activityDates(),d.activityCounts(),d.categoryMix(),d.urgentProducts(),List.of());}
 @GetMapping("/reports/summary") Map<String,Object> report(){return service.report();}
 @GetMapping("/categories") List<Map<String,Object>> categories(){return service.categoryList().stream().map(c->Map.<String,Object>of("id",c.id,"name",c.name,"description",c.description==null?"":c.description,"active",c.active)).toList();}
 @PostMapping("/categories") @ResponseStatus(HttpStatus.CREATED) Map<String,Object> category(@Valid @RequestBody CategoryInput in){Category c=service.createCategory(in);return Map.of("id",c.id,"name",c.name);}
 @GetMapping("/suppliers") List<Map<String,Object>> suppliers(){return service.supplierList().stream().map(s->Map.<String,Object>of("id",s.id,"name",s.name,"contactName",s.contactName==null?"":s.contactName,"email",s.email==null?"":s.email,"phone",s.phone==null?"":s.phone,"active",s.active)).toList();}
 @PostMapping("/suppliers") @ResponseStatus(HttpStatus.CREATED) Map<String,Object> supplier(@Valid @RequestBody SupplierInput in){Supplier s=service.createSupplier(in);return Map.of("id",s.id,"name",s.name);}
 @PutMapping("/categories/{id}") Map<String,Object> updateCategory(@PathVariable long id,@Valid @RequestBody CategoryInput in){Category c=service.updateCategory(id,in);return Map.of("id",c.id,"name",c.name);}
 @DeleteMapping("/categories/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) void deleteCategory(@PathVariable long id){service.deleteCategory(id);}
 @PutMapping("/suppliers/{id}") Map<String,Object> updateSupplier(@PathVariable long id,@Valid @RequestBody SupplierInput in){Supplier s=service.updateSupplier(id,in);return Map.of("id",s.id,"name",s.name);}
 @DeleteMapping("/suppliers/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) void deleteSupplier(@PathVariable long id){service.deleteSupplier(id);}
 @GetMapping("/users") List<UserView> users(){return service.userList();}
 @PostMapping("/users") @ResponseStatus(HttpStatus.CREATED) UserView user(@Valid @RequestBody UserInput in){return service.createUser(in);}
 @PatchMapping("/users/{id}/enabled") UserView enabled(@PathVariable long id,@RequestBody Map<String,Boolean> in){return service.setUserEnabled(id,Boolean.TRUE.equals(in.get("enabled")));}
 @PatchMapping("/users/{id}/access") UserView access(@PathVariable long id,@Valid @RequestBody UserAccessInput in){return service.updateAccess(id,in);}
 @GetMapping("/settings") Map<String,String> settings(){return service.getSettings();}
 @PutMapping("/settings") Map<String,String> settings(@Valid @RequestBody SettingInput in){return service.putSettings(in);}
}

@org.springframework.stereotype.Component
class DemoBootstrap implements org.springframework.boot.ApplicationRunner {
 private final InventoryService service;DemoBootstrap(InventoryService service){this.service=service;}
 @Override public void run(org.springframework.boot.ApplicationArguments args){service.seed();}
 @org.springframework.scheduling.annotation.Scheduled(fixedDelay=30000,initialDelay=30000) void cleanupWarnings(){service.cleanupExpiries();}
}
