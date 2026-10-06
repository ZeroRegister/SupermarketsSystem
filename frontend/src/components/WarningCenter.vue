<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api, warnings } from '../api'
import type { Page, Warning, WarningAction, User } from '../types'
const page=ref<Page<Warning>>(), state=ref('open'), type=ref(''), index=ref(0), loading=ref(false), saving=ref(false)
const selected=ref<Warning>(), history=ref<WarningAction[]>([]), assignees=ref<User[]>([]), open=ref(false), assignee=ref<number>(), note=ref('')
const labels:Record<string,string>={OUT:'Out of stock',LOW:'Low stock',RESTOCKED:'Restocked',PENDING:'Pending',CONFIRMED:'Confirmed',PROCESSING:'Processing',RECOVERED:'Recovered'}
async function load(){loading.value=true;try{page.value=await warnings({state:state.value,type:type.value,page:index.value,size:20})}catch(e:any){ElMessage.error(e.response?.data?.message||'Could not load warnings')}finally{loading.value=false}}
watch([state,type],()=>{index.value=0;load()});watch(index,load);onMounted(load)
async function inspect(w:Warning){selected.value=w;assignee.value=w.assignedToId;note.value='';open.value=true;try{history.value=(await api.get(`/warnings/${w.id}/history`)).data;assignees.value=(await api.get('/warnings/assignees')).data}catch{ElMessage.error('Could not load warning history')}}
async function act(action:string){if(!selected.value||saving.value)return;if(action!=='CONFIRM'&&!note.value.trim())return ElMessage.warning('Add a handling note');saving.value=true;try{const id=selected.value.id;selected.value=(await api.post(`/warnings/${id}/${action==='CONFIRM'?'ack':'actions'}`,action==='CONFIRM'?{}:{action,assigneeId:assignee.value??null,note:note.value})).data;history.value=(await api.get(`/warnings/${id}/history`)).data;note.value='';await load();ElMessage.success('Warning updated')}catch(e:any){ElMessage.error(e.response?.data?.message||'Could not update warning')}finally{saving.value=false}}
</script>
<template>
 <section class="view table-view" v-loading="loading">
  <div class="page-heading"><h1>Warning center</h1><el-button @click="load">Refresh</el-button></div>
  <div class="surface-card table-surface">
   <div class="table-toolbar feature-toolbar"><el-select v-model="state" aria-label="Warning state"><el-option label="Active warnings" value="open"/><el-option label="Recovered history" value="resolved"/><el-option label="All events" value="all"/></el-select><el-select v-model="type" aria-label="Warning type"><el-option label="All types" value=""/><el-option v-for="t in ['OUT','LOW','RESTOCKED']" :key="t" :label="labels[t]" :value="t"/></el-select><span>{{ page?.totalElements||0 }} events</span></div>
   <el-table :data="page?.items||[]" stripe><el-table-column label="PRODUCT" min-width="220"><template #default="{row}"><b>{{ row.productName }}</b><div>{{ row.sku }}</div></template></el-table-column><el-table-column label="WARNING" width="160"><template #default="{row}"><el-tag :type="row.type==='OUT'?'danger':row.type==='RESTOCKED'?'success':'warning'">{{ labels[row.type] }}</el-tag></template></el-table-column><el-table-column prop="severity" label="SEVERITY" width="110"/><el-table-column label="STATUS" width="140"><template #default="{row}">{{ labels[row.reviewStage] }}</template></el-table-column><el-table-column label="ASSIGNED TO" min-width="140"><template #default="{row}">{{ row.assignedTo||'Unassigned' }}</template></el-table-column><el-table-column prop="quantity" label="QUANTITY" width="110"/><el-table-column width="120"><template #default="{row}"><el-button @click="inspect(row)">Handle</el-button></template></el-table-column><template #empty>No warnings</template></el-table>
   <div class="table-pagination"><span>{{ page?.totalElements||0 }} events</span><el-pagination :current-page="index+1" @current-change="index=$event-1" :page-size="20" :total="page?.totalElements||0" layout="prev, pager, next"/></div>
  </div>
  <el-dialog v-model="open" :title="selected?.productName||'Warning'" width="680px">
   <template v-if="selected"><div class="feature-facts"><span>{{ labels[selected.type] }} · {{ selected.severity }}</span><span>{{ labels[selected.reviewStage] }}</span><span>Quantity {{ selected.quantity }} / threshold {{ selected.threshold }}</span><span v-if="selected.previousId">Previous event #{{ selected.previousId }}</span></div>
    <el-form label-position="top"><el-form-item label="Assigned team member"><el-select v-model="assignee" clearable :disabled="selected.state==='RESOLVED'"><el-option v-for="u in assignees" :key="u.id" :label="u.displayName" :value="u.id"/></el-select></el-form-item><el-form-item label="Handling note"><el-input v-model="note" type="textarea" :rows="3" maxlength="1000"/></el-form-item></el-form>
    <div class="feature-actions"><el-button v-if="selected.state==='OPEN'&&!selected.acknowledgedBy" :loading="saving" @click="act('CONFIRM')">Confirm</el-button><el-button v-if="selected.state==='OPEN'" :disabled="saving" @click="act('ASSIGN')">Save assignment</el-button><el-button v-if="selected.state==='OPEN'&&selected.reviewStage!=='PROCESSING'" type="primary" :disabled="saving" @click="act('PROCESS')">Start handling</el-button><el-button :disabled="saving" @click="act('NOTE')">Add note</el-button></div>
    <h3>History</h3><el-timeline><el-timeline-item v-for="a in history" :key="a.id" :timestamp="new Date(a.createdAt).toLocaleString()"><b>{{ a.actor }} · {{ a.action }}</b><div>{{ a.note }}</div></el-timeline-item></el-timeline>
   </template>
  </el-dialog>
 </section>
</template>
