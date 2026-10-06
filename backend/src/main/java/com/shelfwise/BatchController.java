package com.shelfwise;
import java.time.Clock;
import java.util.List;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import org.springframework.transaction.annotation.Transactional;

@org.springframework.context.annotation.Configuration class TimeConfiguration {
 @org.springframework.context.annotation.Bean Clock businessClock(){return Clock.systemUTC();}
}
@RestController @RequestMapping("/api") class BatchController {
 private final BatchInventory batches;private final InventoryService inventory;
 BatchController(BatchInventory b,InventoryService i){batches=b;inventory=i;}
 @GetMapping("/batches") PageResult<BatchView> list(@RequestParam(required=false)Long productId,@RequestParam(defaultValue="0")int page,@RequestParam(defaultValue="20")int size){return batches.list(productId,page,size);}
 @PostMapping("/batches/{id}/control") @Transactional BatchView control(@PathVariable long id,@Valid @RequestBody BatchControlInput in,org.springframework.security.core.Authentication auth){var b=batches.control(id,in,auth.getName());inventory.refreshWarning(b.productId());return b;}
 @GetMapping("/batches/{id}/history") List<AllocationView> history(@PathVariable long id){return batches.history(id);}
 @GetMapping("/batches/{id}/controls") List<BatchActionView> controls(@PathVariable long id){return batches.controls(id);}
 @GetMapping("/transactions/{id}/allocations") List<AllocationView> allocations(@PathVariable long id){return batches.transactionAllocations(id);}
}
