<template>
  <div class="calendar-container">
    <FullCalendar :options="calendarOptions" 
        @eventClick="handleEventClick"
    />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3>Detalles de la sesión</h3>
        <dl v-if="selectedSession">
          <dt>ID</dt>
          <dd>{{ selectedSession.id ?? 'N/D' }}</dd>
          <dt>Paciente</dt>
          <dd>{{ selectedSession.patient_id ?? 'N/D' }}</dd>
          <dt>Terapeuta</dt>
          <dd>{{ selectedSession.therapist_id ?? 'N/D' }}</dd>
          <dt>Inicio</dt>
          <dd>{{ selectedSession.start_date ?? 'N/D' }}</dd>
          <dt>Fin</dt>
          <dd>{{ selectedSession.end_date ?? 'N/D' }}</dd>
          <dt>Finalizada</dt>
          <dd>{{ selectedSession.ended_at ?? 'N/D' }}</dd>
        </dl>
        <div class="actions">
            <button class="btn-primary" v-if="isSessionActive(selectedSession)" @click="isSessionActive(selectedSession) ? router.push(`/session/${selectedSession.id}/${user.type}`) : null">
                Ir a sesión activa
            </button>
          <button @click="closeModal">Cerrar</button>
        </div>
      </div>
    </div>

    <div>
        <button @click="() => router.push('/home')">Volver al inicio</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/daygrid";
import { userService } from '../api/userService';
import { useRouter } from "vue-router";

const calendarOptions = ref({
  plugins: [dayGridPlugin],
  initialView: 'dayGridMonth',
  events: [],
  eventColor: '#3b82f6',
  height: 'auto',
});

const showModal = ref(false)
const selectedSession = ref(null)
const router = useRouter()
const loading = ref(true)
const activeSession = ref(null)
const user = ref(null)

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
  } catch (e) {
    user.value = null
  }

  const sessions = await userService.getMySessions();
  // API returns { data: [...], count: n }; normalize to array of sessions
  const list = Array.isArray(sessions?.data) ? sessions.data : (Array.isArray(sessions) ? sessions : []);

  calendarOptions.value = {
    ...calendarOptions.value,
    events: list.map(s => ({
      title: "Sesión",
      start: s.start_date,
      end: s.end_date,
      extendedProps: { session: s },
    })),
    eventClick: handleEventClick,
  };
  try {
    activeSession.value = await userService.getActiveSession()
    console.log('Active session:', activeSession.value)
  } catch (e) {
    activeSession.value = null
  } finally {
    loading.value = false
  }
});

function handleEventClick(info) {
  selectedSession.value = info.event.extendedProps?.session || null
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedSession.value = null
}

const isSessionActive = (session) => {
  if (!session || !activeSession.value) return false
  return session.id === activeSession.value.id
}

</script>

<style>
.calendar-container {
  max-width: 900px;
  margin: auto;
  padding: 1rem;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  max-width: 420px;
  width: 100%;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
  color: #111;
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.modal dl {
  margin: 0;
}

.modal dt {
  font-weight: 600;
}

.modal dd {
  margin: 0 0 0.4rem 0;
  color: #333;
}

.modal .actions {
  text-align: right;
  margin-top: 0.75rem;
}

.modal button {
  padding: 0.35rem 0.75rem;
  border: 1px solid #ccc;
  background: #f4f4f4;
  border-radius: 4px;
  cursor: pointer;
}

.modal button:hover {
  background: #e9e9e9;
}

.btn-primary {
  background: #3b82f6 !important;
  color: white !important;
  border-color: #3b82f6 !important;
}

.btn-primary:hover {
  background: #2563eb !important;
}
</style>
