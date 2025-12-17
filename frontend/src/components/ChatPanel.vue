<script setup lang="ts">
import { ref } from 'vue'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-vue-next'

interface UserLike { id?: number; full_name?: string }

const props = defineProps<{
  messages: Array<{ sender: string; text: string }>
  role: string
  activeUser?: UserLike | null
  therapistUser?: UserLike | null
  title?: string
}>()

const emit = defineEmits<{
  (e: 'send', text: string): void
}>()

const newMessage = ref('')

const handleSend = () => {
  const t = newMessage.value?.trim()
  if (!t) return
  emit('send', t)
  newMessage.value = ''
}
</script>

<template>
  <div class="flex flex-col h-full rounded-xl border shadow-lg bg-white">
    <div class="flex items-center justify-between px-4 py-3 border-b bg-blue-500 text-white rounded-t-xl">
      <div class="flex items-center gap-2">
        <h2 class="text-sm font-semibold">{{ title || 'Chat con el terapeuta' }}</h2>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-4 py-3 space-y-2 bg-blue-50/50">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="[
          'max-w-[75%] px-3 py-2 rounded-xl text-sm shadow-sm break-words',
          msg.sender === props.role
            ? 'ml-auto bg-green-100 text-green-900 rounded-tr-sm'
            : 'mr-auto bg-gray-100 text-gray-900 rounded-tl-sm'
        ]"
      >
        <div class="text-xs font-semibold opacity-80 mb-0.5">
          {{ msg.sender === 'patient' ? (props.activeUser?.full_name ?? 'Tú') : (props.therapistUser?.full_name ?? 'Terapeuta') }}
        </div>
        <div>
          {{ msg.text }}
        </div>
      </div>
    </div>

    <div class="p-3 border-t bg-blue-50 rounded-b-xl">
      <div class="flex gap-2">
        <Input
          v-model="newMessage"
          placeholder="Escribe un mensaje…"
          @keyup.enter="handleSend"
          class="flex-1 bg-white text-gray-900"
        />
        <Button
          size="icon"
          class="bg-blue-600 text-white hover:bg-blue-500"
          @click="handleSend"
          aria-label="Enviar mensaje"
        >
          <Send class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
