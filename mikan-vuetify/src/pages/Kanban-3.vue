<template  >
      <Sidebar @select-project="selectedBoard = $event" />

      <v-app-bar  v-if="showDevBar" app fixed color="white" elevation="2">
      <v-toolbar-title>Developer Mode!!!</v-toolbar-title>

      <!-- Board filter -->
      <v-select
        v-model="selectedBoard"
        :items="boardOptions"
        label="Board"
        clearable
        dense
        hide-details
        style="max-width:200px"
      />

      <!-- Assignee filter -->
      <v-select
        v-model="selectedAssignee"
        :items="assigneeOptions"
        label="Assignee"
        clearable
        dense
        hide-details
        style="max-width:200px"
      />

      <v-spacer />

      <v-btn text @click="logData">Log Data</v-btn>
      <v-btn text @click="visitorMode = !visitorMode">
        {{ visitorMode ? 'Exit Visitor Mode' : 'Visitor Mode' }}
      </v-btn>
      <v-btn text @click="allowBoardReordering = !allowBoardReordering">
        {{ allowBoardReordering ? 'Lock Boards' : 'Reorder Boards' }}
      </v-btn>
      <v-btn text @click="allowStageCrossBoard = !allowStageCrossBoard">
        {{ allowStageCrossBoard ? 'Lock Stages' : 'Cross-Board Stages' }}
      </v-btn>
      <v-btn color="primary" @click="addBoard" :disabled="visitorMode">
        <v-icon left>mdi-plus</v-icon> Add Board
      </v-btn>
    </v-app-bar>


 <!-- SUGGESTION: Replace the fixed container+row with Vuetify App Bar -->
 <v-main class="pa-0 unified-background" style="display:flex; flex-direction:column; height:100vh; min-height:0; overflow:hidden;">
    <v-container fluid class="pa-0 pr-6 fill-height" style="width:100%;">
      <!-- No boards at all -->
      <div v-if="boards.length === 0" class="text-center grey--text pa-4">
        No boards defined
      </div>

      <!-- Boards exist but filters removed everything -->
      <!-- <div v-else-if="filteredBoards.length === 0" class="text-center grey--text pa-4">
        No stages/tasks match your filters
      </div> -->

      <!-- 3) Show filtered boards -->
      <!-- SUGGESTION: Bind draggable to real `boards` and filter inside Board2.vue -->
      <draggable
        v-model="boards"
        item-key="id"
        :animation="150"
        
        class="d-flex flex-column fill-height"
        style="width:100%; flex:1 1 auto;"
        :disabled="visitorMode || !allowBoardReordering"
      >
        <template #item="{ element: board, index: bIndex }">

          <Board 
            v-if="!selectedBoard || board.title === selectedBoard"
           :board="selectedAssignee
             ? {
                 ...board,
                 stages: board.stages
                   .map(sg => ({
                     ...sg,
                     tasks: sg.tasks.filter(t => t.assignee === selectedAssignee)
                   }))
                   .filter(sg => sg.tasks.length > 0)
               }
             : board"
            :boardIndex="bIndex"
            :visitorMode="visitorMode"
            :selectedAssignee="selectedAssignee"
            :allowStageCrossBoard="allowStageCrossBoard"
            @delete-board="deleteBoard"
            @rename-board="renameBoard"
            @add-stage="addStage"
            @add-task="addTask"
            @delete-task="deleteTask"
            @rename-stage="renameStage"
            @delete-stage="deleteStage"
            @open-task-dialog="openTaskDialog"
			@task-updated="taskDropped"
          />

        </template>
      </draggable>
      
    </v-container>

    <!-- TASK MODAL REPLACEMENT -->
    <TaskDetail
      v-model="isTaskDialogOpen"
      :task="selectedTask"
      :visitorMode="visitorMode"
      @save-task="handleTaskSave"
      @delete-task="confirmDeleteTask"
    />

  <!-- DELETE CONFIRMATION WHY IS THIS HARDCODED FOR KANBAN 2 AND 3 WHYYYY--> 
  <v-dialog v-model="isDeleteConfirmOpen" max-width="500px">
    <v-card class="rounded-xl pa-4">
      <v-card-title>Confirm Delete</v-card-title>
      <v-card-text>Are you sure you want to delete this task?</v-card-text>
      <v-card-actions>
        <v-btn text class="stage-button-cancel rounded-xl"  @click="isDeleteConfirmOpen = false">Cancel</v-btn>
        <v-btn class="ml-3 stage-button-delete-dialog rounded-xl" @click="deleteTaskConfirmed">Yes, Delete</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <Chatbot />
  </v-main> 

</template>
<script setup lang="ts">
import { ref,computed, watch } from 'vue'
import axios from 'axios'
import { boards, fetchBoards } from '@/stores/boards'
import { useRoute } from "vue-router";
import draggable from 'vuedraggable'
import Board from '@/components/MyTasksComponent/Board3-1.vue'
import TaskDetail from '@/components/MyTasksComponent/TaskDetail.vue'
import { useChatbotStore } from '@/stores/chatbotStore'; // 1. Import the chatbot store 
const chatbotStore = useChatbotStore(); // 2. Create an instance of the chatbot store
// import Sidebar3 from '@/components/MyTasksComponent/Sidebar3.vue'

const showDevBar = false

let nextId = 2000
function genId() { return nextId++ }

// ─── 1. Your mock data as Board→Stage→Task ───────────────────────────

// ─── 2. Filter state ────────────────────────────────────────────────
const route = useRoute();
const selectedBoard = computed<string|null>(() => {
  const b = route.query.board;
  return typeof b === "string" ? b : null;
});
// const selectedBoard    = ref<string | null>(null)
const selectedAssignee = ref<string | null>(null)

// ─── 3. Dropdown options ──────────────────────────────────────────
// Board titles for the first dropdown
const boardOptions = computed(() => boards.value.map(b => b.title))

// Unique assignees across all tasks
const assigneeOptions = computed(() => {
  const map = new Map<number, string>()
  boards.value.forEach(b =>
    b.stages.forEach(sg =>
      sg.tasks.forEach(t => {
        if (t.assignee_id && t.assignee) {
          map.set(t.assignee_id, t.assignee)
        }
      })
    )
  )
  return Array.from(map.entries()).map(([id, name]) => ({ id, name }))
})

// ——— 4) COMPUTE FILTERED BOARDS ———
/**
* We flatten all boards from all (or the selected) projects,
* then within each board we only keep tasks matching bothe
* selectedAssignee (if any).
*/
const filteredBoards = computed(() => {
return boards.value
  // 4a) Keep only matching boards (or all if none selected)
  .filter(b => !selectedBoard.value || b.title === selectedBoard.value)
  // 4b) For each kept board, filter its stages & tasks
  .map(b => ({
    ...b,
    stages: b.stages
      // map each stage, filtering tasks by assignee
      .map(sg => ({
        ...sg,
        tasks: selectedAssignee.value
          ? sg.tasks.filter(t => t.assignee === selectedAssignee.value)
          : sg.tasks
      }))
      // then drop any stage with zero tasks
      .filter(sg => sg.tasks.length > 0)
  }))
  // 4c) drop any board where all stages got filtered out
  .filter(b => b.stages.length > 0)
})
// MOCK DATA ENDS HERE

const visitorMode = ref(false)
const allowBoardReordering = ref(false)
const allowStageCrossBoard = ref(false)

// Task dialog state
const isTaskDialogOpen = ref(false)
const isDeleteConfirmOpen = ref(false)
const editingInfo = ref({ boardIndex: null as number | null, stageIndex: null as number | null, taskIndex: null as number | null })
const editedTaskTitle = ref('')

const selectedTask = computed(() => {
const { boardIndex, stageIndex, taskIndex } = editingInfo.value
if (boardIndex!==null && stageIndex!==null && taskIndex!==null) {
  return boards.value[boardIndex].stages[stageIndex].tasks[taskIndex]
}
return null
})

async function handleTaskSave(taskId, updatedTask) {
  const { boardIndex, stageIndex, taskIndex } = editingInfo.value;

  if (boardIndex !== null && stageIndex !== null && taskIndex !== null) {
    const existingTask = boards.value[boardIndex].stages[stageIndex].tasks[taskIndex];

    boards.value[boardIndex].stages[stageIndex].tasks[taskIndex] = {
        ...existingTask,
        ...updatedTask,
        id: taskId,
        dueDate: updatedTask.due_date,
        assignee: assigneeOptions.value.find(a => a.id === updatedTask.assignee_id)?.name || existingTask.assignee
    };

    const project_id = boards.value[boardIndex].id;
    const payload = {
      ...updatedTask,
      project_id: project_id,
    };

    try {
      await axios.put(`http://localhost:8000/tasks/update_task/${taskId}`, payload);
      console.log(`✅ Task updated from dialog with Task ID : ${taskId}`, payload);
      await fetchBoards();
      isTaskDialogOpen.value = false;
    } catch (err) {
      console.error("❌ Failed to update task from dialog:", err);
    }
  }
}

async function taskDropped(taskId, payload) {
  try {
    await axios.put(`http://localhost:8000/tasks/update_task/${taskId}`, payload)
    console.log("Task updated successfully")
  } catch (err) {
    console.error("❌ Failed to update task:", err.response?.data || err.message)
  }
}


watch(selectedAssignee, assignee => {
// whenever you pick someone, lock down the UI
visitorMode.value = assignee !== null
})

function addBoard() {
boards.value.push({ id: genId(), title: `New Board ${boards.value.length+1}`, stages: [] })
}
function deleteBoard(boardIndex: number) {
boards.value.splice(boardIndex, 1)
}
function renameBoard(boardIndex: number, newTitle: string) {
boards.value[boardIndex].title = newTitle
}
// NEW: renameStage handler
function renameStage(boardIndex: number, stageIndex: number, newTitle: string) {
boards.value[boardIndex].stages[stageIndex].title = newTitle
}

function addStage(boardIndex: number) {
boards.value[boardIndex].stages.push({ id: genId(), title: `Stage ${boards.value[boardIndex].stages.length+1}`, tasks: [] })
}
function deleteStage(boardIndex: number, stageIndex: number) {
boards.value[boardIndex].stages.splice(stageIndex, 1)
}
function addTask(boardIndex: number, stageIndex: number) {
boards.value[boardIndex].stages[stageIndex].tasks.push({ id: genId(), title: `Task ${boards.value[boardIndex].stages[stageIndex].tasks.length+1}` })
}
function deleteTask(boardIndex: number, stageIndex: number, taskIndex: number) {
boards.value[boardIndex].stages[stageIndex].tasks.splice(taskIndex, 1)
}
function openTaskDialog(boardIndex: number, stageIndex: number, taskId: number) {
  const tasks    = boards.value[boardIndex].stages[stageIndex].tasks
  const realIdx  = tasks.findIndex(t => t.id === taskId)
  if (realIdx !== -1) {
    editingInfo.value = { boardIndex, stageIndex, taskIndex: realIdx }
    isTaskDialogOpen.value = true
  }
}
function closeTaskDialog() {
isTaskDialogOpen.value = false
editedTaskTitle.value = ''
}
function saveTaskEdit() {
const { boardIndex, stageIndex, taskIndex } = editingInfo.value
if (boardIndex!==null && stageIndex!==null && taskIndex!==null) {
  boards.value[boardIndex].stages[stageIndex].tasks[taskIndex].title = editedTaskTitle.value
}
closeTaskDialog()
}
function confirmDeleteTask() {
isTaskDialogOpen.value = false
isDeleteConfirmOpen.value = true
}
function deleteTaskConfirmed() {
const { boardIndex, stageIndex, taskIndex } = editingInfo.value
if (boardIndex!==null && stageIndex!==null && taskIndex!==null) {
  deleteTask(boardIndex, stageIndex, taskIndex)
}
isDeleteConfirmOpen.value = false
}
function logData() {
  console.log(
    JSON.stringify(
      boards.value,
      (key, value) => {
        // If it's a native File, serialize its key props:
        if (value instanceof File) {
          return { name: value.name, size: value.size, type: value.type };
        }
        // If it's our metadata object wrapping a File in `raw`:
        if (value && typeof value === 'object' && 'raw' in value && value.raw instanceof File) {
          const { raw, ...meta } = value;
          return meta;
        }
        return value;
      },
      2
    )
  )
}


// ------------------------------------------- CHATBOT -------------------------------------------
// 2. Define a reusable function to set the context based on the Kanban view
const updateChatContext = () => {
    // The most relevant context is what the user is currently seeing.
    // We use the `filteredBoards` computed property for this.
    const currentViewData = filteredBoards.value;

    // Check if there is data to provide as context
    if (currentViewData && currentViewData.length > 0) {
        chatbotStore.setPageContext(currentViewData, 'Kanban Board Page');
        console.log("Chatbot context SET for Kanban Board page.");
    } else {
        // If filters result in no boards being displayed, clear the context
        // to prevent the chatbot from answering based on old or hidden data.
        chatbotStore.clearPageContext();
        console.log("No filtered boards available; chatbot context cleared.");
    }
};

// 3. Watch for changes in the filtered data
// This will automatically fire whenever the user changes a filter,
// ensuring the chatbot's context is always up-to-date.
watch(filteredBoards, () => {
    updateChatContext();
}, {
  deep: true // Necessary for watching changes within the array of boards and tasks
});

// 4. Use onMounted to set the initial context when the component loads
onMounted(() => {
    updateChatContext();
});

// 5. Use onUnmounted to clean up and clear the context when leaving the page
onUnmounted(() => {
  chatbotStore.clearPageContext();
  console.log("Chatbot context CLEARED from Kanban page.");
});

</script>

<style scoped>
/* ============ NEUMORPHIC STYLES ============ */
.neu {
background: #e0e0e0;
border-radius: 16px;
box-shadow:
  8px 8px 16px #bebebe,
 -8px -8px 16px #ffffff;
transition: all 0.3s ease;
}

.neu-inset {
box-shadow:
  inset 8px 8px 16px #bebebe,
  inset -8px -8px 16px #ffffff;
}

.neu-btn {
background: #e0e0e0;
border-radius: 12px;
box-shadow:
  5px 5px 10px #bebebe,
 -5px -5px 10px #ffffff;
transition: 0.2s ease;
}

.neu-btn:active {
box-shadow:
  inset 5px 5px 10px #bebebe,
  inset -5px -5px 10px #ffffff;
}

.fill-height {
  height: 100%;
  /* Make sure it fills the full screen */
}

.card-1 {
  border: thin solid lightgray;
  box-shadow: none;
}

.border-1 {
  border: 2px solid #abcdef;
  box-shadow: none;
}

.custom-background {
  background-color: #e0e0e0; /* or any grey hex/RGB */
}

/* src/assets/styles/custom.css */
.rounded-v1 {
  border-radius: 16px !important;
}
.rounded-v2 {
  border-radius: 12px !important;
}

/* reusable utilities
.border-1   { --v-border-color: 255, 0, 0;   --v-border-opacity: 1; }
.border-2  { --v-border-color: 0, 0, 255;   --v-border-opacity: 1; } */
</style>
