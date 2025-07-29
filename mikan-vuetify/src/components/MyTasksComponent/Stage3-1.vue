<!-- // ========================
// Stage.vue
// ======================== -->
<template>
  
  <v-sheet 
  elevation="0" 
  class="border-2 rounded-v2 ma-2 hover:black d-flex flex-column stage-background" 
  style="
  min-width: 340px; 
  max-width: 340px; 
  display:flex; 
  flex-direction:column;">
    <v-toolbar density="compact" class="rounded-v2 stage-background-header" >
      <template v-if="!isEditing">
        <v-toolbar-title  class="text-subtitle-1 my-0 py-0 text-grey">{{ stage.title }}</v-toolbar-title>
        <v-spacer />
        <v-btn density="compact" class="stage-button-edit" icon  v-if="!visitorMode" @click="startRename">
          <v-icon size="20px">mdi-pencil</v-icon>
        </v-btn>
        
       <!-- DeleteDialog trigger -->
       <DeleteDialog
         v-model="showDelete"
         title="Delete Stage?"
         message="This will remove this stage and all its tasks."
         @confirm="onConfirmDelete"
       />
<!-- <v-btn density="compact" icon class="mr-3" v-if="!visitorMode" @click="$emit('delete-stage', props.stageIndex)"> -->
        <v-btn density="compact" class="mr-3 stage-button-delete" icon  v-if="!visitorMode" @click="showDelete = true">
          <v-icon size="20px">mdi-delete</v-icon>
        </v-btn>
      </template>
      <template v-else>
        <v-text-field v-model="localTitle" dense @keyup.enter="saveRename" @blur="saveRename" autofocus />
      </template>
    </v-toolbar>

    <!-- <draggable
      v-model="stage.tasks"
      :item-key="'id'"
      :animation="150"
      :group="{ name: `tasks-board-${boardIndex}`, pull: true, put: [`tasks-board-${boardIndex}`] }"
      class="pa-2"
      
      style="min-height:75vh; max-height: 75vh; overflow-y:auto" 
      :disabled="visitorMode"

    > -->
    <draggable
      v-model="stage.tasks"
      :item-key="'id'"
      :animation="150"
      :group="{ name: `tasks-board-${boardIndex}`, pull: true, put: [`tasks-board-${boardIndex}`] }"
      class="pa-2 flex-grow-1 overflow-y-auto"
       
      :disabled="visitorMode"
	  @change="onTaskDrop"

    >
      <template #item="{ element: task, index: tIndex }">

        <TaskCard 
        :task="task" 
        :visitorMode="visitorMode" 
        @click="$emit('open-task-dialog', task.id)" 
        />

      </template>

      <template #footer>
        <div v-if="(
            !selectedAssignee
              ? stage.tasks.length === 0
              : stage.tasks.filter(t => t.assignee === selectedAssignee).length === 0
          )" class="pa-4 text-center grey--text" style="font-size:.9rem;">
          No tasks
        </div>
      </template>

    </draggable>
    <!-- <v-divider></v-divider> -->
    <v-card-actions class="pa-0 pt-0 justify-center">
      <v-btn density="compact" class="stage-button-add-task rounded-xl border-2 border-md ma-auto bg-grey-lighten-4" @click="$emit('add-task')" :disabled="visitorMode">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
    </v-card-actions>
  </v-sheet>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import draggable from 'vuedraggable'
import TaskCard from './TaskCard2-3.vue'
import DeleteDialog from './DeleteDialog.vue'

// Accept assignee filter
const props = defineProps({
  stage: Object,
  boardIndex: Number,
  stageIndex: Number,
  visitorMode: Boolean,
  selectedAssignee: String,
  projectId: Number
})
const emit = defineEmits(['add-task','delete-stage','open-task-dialog','rename-stage', 'task-dropped'])

const isEditing = ref(false)
const localTitle = ref(props.stage.title)
const showDelete = ref(false)
function startRename() { isEditing.value = true }
function saveRename() {
  emit('rename-stage', props.stageIndex, localTitle.value)
  isEditing.value = false
}
function onConfirmDelete() { emit('delete-stage', props.stageIndex) }

function onTaskDrop(evt) {
  const { added } = evt;
  if (added && added.element) {
    const task = added.element;

    const reverseStageMap = {
      "To Do": "to-do",
      "In Progress": "in-progress",
      "Done": "done"
    };
    const newStatus = reverseStageMap[props.stage.title] || "to-do";

    // Only send update if status actually changed
      if (task.status !== newStatus) {
        const payload = {
          assignee_id: task.assignee_id,
          project_id: props.projectId,
          title: task.title || "",
          description: task.description || "",
          due_date: task.dueDate || "",
        priority: task.priority || "",
        status: newStatus
      };

      console.log(`Updating task ${task.id}:`, payload);
      task.status = newStatus;
      emit("task-dropped", task.id, payload);
    }
  }
}

</script>

<style>

.card-soft {
  background-color: #fff;
  border-radius: 16px;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.04),
    0 4px 12px rgba(0, 0, 0, 0.06);  /* Stronger shadow for depth */
  transition: box-shadow 0.2s ease, transform 0.1s ease;
 
}
.fill-height {
    height: 100%;
    /* Make sure it fills the full screen */
}


</style>