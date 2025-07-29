<template>
  <v-card 
  class="border-sm border-1 rounded-v1 ma-3 page-background d-flex flex-column" 
  elevation="0" 
  style="width:100%; height:100%;" 

  >
    <!-- Board Header -->
    <v-toolbar class="page-background-header text-grey ">
      <template v-if="!isEditing">
        <span style=" margin-left:16px" >{{ board.title }}</span>
        <v-btn icon v-if="!visitorMode" @click="startRename">
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-spacer></v-spacer>
      </template>
      <template v-else>
        <v-text-field
          v-model="localTitle"
          dense
          @keyup.enter="saveRename"
          @blur="saveRename"
          autofocus
        />
      </template>
       <!-- Inline Assignee Filter -->
       <v-select
          v-model="selectedAssigneeFilter"
          :items="assigneeOptions"
          label="Assignee"
          single-line
          variant="outlined"
          density="compact"
          class="rounded-xl border-2 filter-button"
          dense hide-details clearable
          :menu-props="{
          contentClass: 'rounded-xl text-body-2',
          }"
          style="max-width:180px"
        />

        <!-- Inline Priority Filter -->
        <v-select
          v-model="selectedPriorityFilter"
          :items="priorityOptions"
          label="Priority"
          single-line
          variant="outlined"
          density="compact"
    
          class=" rounded-xl border-2 filter-button"
          hide-details clearable
          :menu-props="{
          contentClass: 'rounded-xl text-body-2 ',
      }"
          style="max-width:180px; margin-left:8px; margin-right:8px"
        />

        <!-- Inline Due Date Filter -->
        <v-menu
          v-model="dueDateMenu"

          :close-on-content-click="false"
          dense hide-details
          style="margin-left:8px"
        >
          <template #activator="{ props: menuProps }">
            <v-text-field
              v-model="formattedDate"
              label="Due Before"
              variant="outlined"
              class="rounded-xl border-2 mr-4 filter-button"
              density="compact"
              single-line
              hide-details clearable
              v-bind="menuProps"
              style="max-width:200px; margin-right:8px"
            />
          </template>
          <v-date-picker 
          class="rounded-xl  text-body-2"
          v-model="selectedDueDateFilter" 
          @input="dueDateMenu = false"
          :min="tomorrowDate"
          /><!--           elevation="0" -->
        </v-menu>
    </v-toolbar>
<!-- <v-divider thickness="2"/> -->
    <!-- Stages Container with variable height (stages are fixed) -->
  <div
     v-if="board.stages.length === 0"
     class="text-center grey--text pa-4"
   >
        <!-- Add Stage Button now scrolls with stages -->
        <v-btn
       class="rounded-xl border-md flex-shrink-0 align-self-center"
       elevation="0"
       color="#fcfcfc"
       @click="$emit('add-stage', boardIndex)"
       :disabled="visitorMode"
     >
       <v-icon size="20" color="gray">mdi-plus</v-icon> add board
     </v-btn>
     <br/><br/>
     No stages assigned
   </div>
   <div
     v-else
     class="d-flex flex-row pa-2 flex-grow-1"
     style="overflow-x: auto;"
   >
     <draggable
       v-model="board.stages"
       :item-key="'id'"
       :animation="150"
       :group="{
         name: 'stages',
         pull: allowStageCrossBoard,
         put: allowStageCrossBoard ? ['stages'] : false
       }"
       class="d-flex flex-row flex-shrink-0"
       :disabled="visitorMode"
     >
       <template #item="{ element: stage, index: sIndex }">
          <Stage3
            :stage="isFilterApplied
                     ? { ...stage, tasks: filteredStages[sIndex].tasks }
                     : stage"
            :boardIndex="boardIndex"
            :stageIndex="sIndex"
            :visitorMode="visitorMode"
            :projectId="board.id"
            :selectedAssignee="selectedAssignee"
            @rename-stage="(sIdx, title) => $emit('rename-stage', boardIndex, sIdx, title)"
            @add-task="() => $emit('add-task', boardIndex, sIndex)"
            @open-task-dialog="tIdx => $emit('open-task-dialog', boardIndex, sIndex, tIdx)"
            @delete-stage="sIdx => $emit('delete-stage', boardIndex, sIdx)"
		  @task-dropped="taskDropped"
         />
       </template>
     </draggable>
     <!-- Add Stage Button now scrolls with stages -->
     <v-btn
       class="rounded-v1 border-2 ml-4 stage-button-add-task flex-shrink-0 align-self-center"
       icon
       tile
       style="height: 120px; width: 80px;"
       elevation="0"
       color="#fcfcfc"
       @click="$emit('add-stage', boardIndex)"
       :disabled="visitorMode"
     >
       <v-icon size="40" >mdi-plus</v-icon>
     </v-btn>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import draggable from 'vuedraggable'
import Stage3 from './Stage3-1.vue'

const props = defineProps({
  board: Object,
  boardIndex: Number,
  visitorMode: Boolean,
  allowStageCrossBoard: Boolean,
  selectedAssignee: String
})
const emit = defineEmits([
  'rename-board',
  'add-stage',
  'delete-stage',
  'add-task',
  'open-task-dialog',
  'rename-stage',
  'task-updated'
])

const isEditing = ref(false)
const localTitle = ref(props.board.title)
function startRename() {
  isEditing.value = true
}
function saveRename() {
  emit('rename-board', props.boardIndex, localTitle.value)
  isEditing.value = false
}

// Filter state
const selectedAssigneeFilter = ref<string | null>(null)
const selectedPriorityFilter = ref<string | null>(null)
const selectedDueDateFilter = ref<string | null>(null)
const dueDateMenu = ref(false)

const formattedDate = computed<string>({
  get() {
    return selectedDueDateFilter.value
      ? new Date(selectedDueDateFilter.value).toLocaleDateString(undefined, {
          day:   'numeric', month: 'short', year:  'numeric'
        })
      : ''
  },
  set(v: string) {
    selectedDueDateFilter.value = v
      ? new Date(v).toISOString().split('T')[0]
      : null
  }
})
// Compute filter options
const assigneeOptions = computed(() => {
  const set = new Set<string>()
  props.board.stages.forEach((stage: any) =>
    stage.tasks.forEach((t: any) => t.assignee && set.add(t.assignee))
  )
  return Array.from(set)
})
const priorityOptions = computed(() => {
  const set = new Set<string>()
  props.board.stages.forEach((stage: any) =>
    stage.tasks.forEach((t: any) => t.priority && set.add(t.priority))
  )
  return Array.from(set)
})

// Filtered stages
// Only compute this when you actually apply a filter
const isFilterApplied = computed(() =>
  !!(selectedAssigneeFilter.value ||
     selectedPriorityFilter.value ||
     selectedDueDateFilter.value)
)

// Pre-compute per-stage filtered task lists
const filteredStages = computed(() =>
  props.board.stages.map((stage: any) => ({
    ...stage,
    tasks: stage.tasks.filter((task: any) => {
      const byAssignee = !selectedAssigneeFilter.value || task.assignee === selectedAssigneeFilter.value
      const byPriority = !selectedPriorityFilter.value || task.priority === selectedPriorityFilter.value
      const byDate     = !selectedDueDateFilter.value || new Date(task.dueDate) <= new Date(selectedDueDateFilter.value)
      return byAssignee && byPriority && byDate
    })
  }))
)

function taskDropped(taskId, payload) {
  emit('task-updated', taskId, payload)
}

// Computed property for tomorrow's date
const tomorrowDate = computed(() => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate()); // Set to tomorrow

    // Format to YYYY-MM-DD
    const year = tomorrow.getFullYear();
    const month = String(tomorrow.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
    const day = String(tomorrow.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
});
</script>

<style scoped>
/* Any Board3-specific styles here */
/* hide the outline and the little bottom-underline */
::v-deep .v-field__outline,
::v-deep .v-field__bottom {
  display: none !important;
}

.fill-height {
    height: 100%;
    /* Make sure it fills the full screen */
}


</style>
