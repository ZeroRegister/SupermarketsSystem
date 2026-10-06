package com.shelfwise;

import jakarta.persistence.LockModeType;
import org.springframework.data.domain.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;
import java.time.Instant;
import java.util.*;

interface UserRepository extends JpaRepository<UserAccount,Long> { Optional<UserAccount> findByUsername(String username); long countByRoleAndEnabledTrue(Role role); }
interface CategoryRepository extends JpaRepository<Category,Long> { boolean existsByNameIgnoreCase(String name); }
interface SupplierRepository extends JpaRepository<Supplier,Long> {}
interface ProductRepository extends JpaRepository<Product,Long>, JpaSpecificationExecutor<Product> {
 @Lock(LockModeType.PESSIMISTIC_WRITE) @Query("select p from Product p where p.id=:id") Optional<Product> lockById(@Param("id") Long id);
 boolean existsBySkuIgnoreCaseAndIdNot(String sku,Long id); boolean existsByBarcodeIgnoreCaseAndIdNot(String barcode,Long id);
 List<Product> findAllByActiveTrue();
}
interface TransactionRepository extends JpaRepository<InventoryTransaction,Long> {
 @EntityGraph(attributePaths={"product","actor"})
 Optional<InventoryTransaction> findByActorIdAndIdempotencyKey(Long actorId,String key);
 Page<InventoryTransaction> findAllByProductIdOrderByCreatedAtDesc(Long productId,Pageable pageable);
 Page<InventoryTransaction> findAllByOrderByCreatedAtDesc(Pageable pageable);
 long countByCreatedAtAfter(Instant since);
 List<InventoryTransaction> findByCreatedAtAfter(Instant since);
}
interface WarningRepository extends JpaRepository<WarningEpisode,Long> {
 @Lock(LockModeType.PESSIMISTIC_WRITE) @Query("select w from WarningEpisode w where w.id=:id") Optional<WarningEpisode> lockById(@Param("id") Long id);
 @Lock(LockModeType.PESSIMISTIC_WRITE)
 List<WarningEpisode> findByTypeAndStateAndExpiresAtBefore(WarningType type,WarningState state,Instant now);
 Optional<WarningEpisode> findFirstByProductIdAndStateOrderByCreatedAtDesc(Long productId,WarningState state);
 Optional<WarningEpisode> findFirstByProductIdAndTypeOrderByCreatedAtDesc(Long productId,WarningType type);
 @Lock(LockModeType.PESSIMISTIC_WRITE) List<WarningEpisode> findByProductIdAndState(Long productId,WarningState state);
 Page<WarningEpisode> findAllByStateOrderByCreatedAtDesc(WarningState state,Pageable pageable);
 Page<WarningEpisode> findAllByOrderByCreatedAtDesc(Pageable pageable);
 Page<WarningEpisode> findByStateOrderByCreatedAtDesc(WarningState state,Pageable pageable);
 @Query("select w from WarningEpisode w join fetch w.product where w.state=:state and (w.type<>com.shelfwise.WarningType.RESTOCKED or w.expiresAt > CURRENT_TIMESTAMP) order by w.createdAt desc") Page<WarningEpisode> activeWarnings(@Param("state") WarningState state,Pageable page);
 @Query("select w from WarningEpisode w join fetch w.product where w.state=:state and w.type=com.shelfwise.WarningType.RESTOCKED and w.expiresAt > CURRENT_TIMESTAMP order by w.createdAt desc") Page<WarningEpisode> activeRestocked(@Param("state") WarningState state,Pageable page);
 Page<WarningEpisode> findByTypeAndStateOrderByCreatedAtDesc(WarningType type,WarningState state,Pageable pageable);
 Page<WarningEpisode> findByTypeOrderByCreatedAtDesc(WarningType type,Pageable pageable);
}
interface WarningActionRepository extends JpaRepository<WarningAction,Long> {
 List<WarningAction> findByWarningIdOrderByCreatedAtAscIdAsc(Long warningId);
}
interface SettingRepository extends JpaRepository<AppSetting,String> {}
interface CacheRevisionRepository extends JpaRepository<CacheRevision,Long> { @Modifying @Query("update CacheRevision c set c.revision=c.revision+1 where c.id=1") int increment(); }
