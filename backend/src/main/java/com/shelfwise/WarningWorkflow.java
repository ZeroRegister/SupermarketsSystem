package com.shelfwise;

import java.time.Instant;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class WarningWorkflow {
 private final WarningRepository warnings;
 private final WarningActionRepository actions;
 private final UserRepository users;
 private final CacheRevisionRepository revisions;
 WarningWorkflow(WarningRepository w,WarningActionRepository a,UserRepository u,CacheRevisionRepository r){warnings=w;actions=a;users=u;revisions=r;}
 @Transactional WarningView acknowledge(long id,String username){
  WarningEpisode w=locked(id);
  if(w.acknowledgedBy!=null)return WarningView.of(w);
  ensureOpen(w);
  w.acknowledgedBy=actor(username);w.acknowledgedAt=Instant.now();
  if(w.reviewStage==ReviewStage.PENDING)w.reviewStage=ReviewStage.CONFIRMED;
  log(w,w.acknowledgedBy,"CONFIRM","Warning confirmed");revisions.increment();return WarningView.of(w);
 }
 @Transactional WarningView act(long id,WarningActionInput in,String username){
  WarningEpisode w=locked(id);UserAccount actor=actor(username);
  if(!"NOTE".equals(in.action()))ensureOpen(w);
  switch(in.action()){
   case "ASSIGN" -> {
    w.assignedTo=in.assigneeId()==null?null:users.findById(in.assigneeId()).filter(u->u.enabled).orElseThrow(()->error("Assignee must be an enabled team member",400));
   }
   case "PROCESS" -> {w.reviewStage=ReviewStage.PROCESSING;}
   case "NOTE" -> {}
   default -> throw error("Unknown warning action",400);
  }
  log(w,actor,in.action(),in.note().trim());revisions.increment();return WarningView.of(w);
 }
 @Transactional(readOnly=true) List<WarningActionView> history(long id){
  if(!warnings.existsById(id))throw error("Warning not found",404);
  return actions.findByWarningIdOrderByCreatedAtAscIdAsc(id).stream().map(WarningActionView::of).toList();
 }
 @Transactional(readOnly=true) List<UserView> assignees(){return users.findAll().stream().filter(u->u.enabled).map(UserView::of).toList();}
 void recover(WarningEpisode w){if(w.state==WarningState.RESOLVED)return;w.state=WarningState.RESOLVED;w.reviewStage=ReviewStage.RECOVERED;w.recoveredAt=Instant.now();log(w,null,"RECOVER","Rule condition cleared or superseded");}
 void created(WarningEpisode w){log(w,null,"DETECT","Rule condition detected");}
 private void log(WarningEpisode w,UserAccount actor,String action,String note){WarningAction a=new WarningAction();a.warning=w;a.actor=actor;a.action=action;a.note=note;actions.save(a);}
 private WarningEpisode locked(long id){return warnings.lockById(id).orElseThrow(()->error("Warning not found",404));}
 private UserAccount actor(String username){return users.findByUsername(username).filter(u->u.enabled).orElseThrow(()->error("User not found",404));}
 private void ensureOpen(WarningEpisode w){if(w.state!=WarningState.OPEN)throw error("Recovered warnings cannot change processing state",409);}
 private DomainException error(String message,int status){return new DomainException(status==404?"NOT_FOUND":status==409?"CONFLICT":"VALIDATION",message,status);}
}
