<template>
  <div class="calendar-container">
    <div class="toolbar">
      <button @click="() => router.push('/home')">Volver al inicio</button>
      <button v-if="user && user.type === 'therapist'" class="btn-primary" @click="showCreateModal = true">Crear nueva sesión</button>
    </div>

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

            <button
              class="btn-primary"
              v-if="(user && user.type === 'therapist') && canCancel(selectedSession)"
              @click="eliminarSesion(selectedSession.id)">
              Cancelar sesión
            </button>
          <button @click="closeModal">Cerrar</button>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreate">
      <div class="modal">
        <h3>Nueva sesión</h3>
        <form class="create-form" @submit.prevent="createSession">
          <label>
            Paciente
            <select v-model="newSession.patientId" required>
              <option value="" disabled>Selecciona paciente</option>
              <option v-for="p in patients" :key="p.id" :value="p.id">{{ p.full_name }} ({{ p.email }})</option>
            </select>
          </label>
          <label>
            Inicio
            <input v-model="newSession.start" type="datetime-local" required />
          </label>
          <label>
            Fin
            <input v-model="newSession.end" type="datetime-local" required />
          </label>
          <div class="actions">
            <button type="button" @click="closeCreate">Cancelar</button>
            <button type="submit" class="btn-primary">Confirmar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/daygrid";
import { userService } from '../api/userService';
import { sessionsService } from '../api/sessionsService';
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
const patients = ref([])
const showCreateModal = ref(false)
const newSession = ref({ patientId: '', start: '', end: '' })

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
  } catch (e) {
    user.value = null
  }

  try {
    const allUsers = await userService.getUsers()
    patients.value = Array.isArray(allUsers) ? allUsers.filter(u => u.type === 'patient') : []
  } catch (e) {
    patients.value = []
  }

  await loadSessions()
  try {
    activeSession.value = await sessionsService.getActiveSession()
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

const eliminarSesion = async (sessionId) => {
  const ok = confirm('¿Estás seguro de que deseas cancelar esta sesión?')
  if (!ok) return

  try {
    await sessionsService.deleteSession(sessionId)
    alert('Sesión cancelada correctamente')
    await loadSessions()
    closeModal()
  } catch (e) {
    console.error('Error cancelando sesión:', e)
    alert('No se pudo cancelar la sesión')
  }
}

const canCancel = (session) => {
  if (!session) return false
  if (isSessionActive(session)) return false
  if (!session.start_date) return false
  return new Date(session.start_date) > new Date()
}

const createSession = async () => {
  try {
    if (!newSession.value.patientId || !newSession.value.start || !newSession.value.end) {
      alert('Completa paciente, inicio y fin')
      return
    }
    const session_data = {
      start_date: new Date(newSession.value.start).toISOString(),
      end_date: new Date(newSession.value.end).toISOString()
    }
    const created = await sessionsService.createSession(newSession.value.patientId, session_data)
    console.log('Sesión creada:', created)
    await loadSessions()
    closeCreate()
  } catch (e) {
    console.error('Error creando sesión:', e)
    alert('No se pudo crear la sesión')
  }
}

const loadSessions = async () => {
  const sessions = await sessionsService.getMySessions();
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
}

const closeCreate = () => {
  showCreateModal.value = false
  newSession.value = { patientId: '', start: '', end: '' }
}

</script>

<style>

.toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.create-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.create-form label {
  display: flex;
  flex-direction: column;
  font-size: 0.9rem;
  color: #111;
  gap: 0.25rem;
}

.create-form input,
.create-form select {
  padding: 0.45rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
}

.link {
  background: transparent;
  border: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0.25rem 0.35rem;
}

.muted {
  color: #6b7280;
  margin: 0;
  grid-column: 1 / -1;
}

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
