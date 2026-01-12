<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-vue-next'

interface UserLike { id?: number; full_name?: string }

type BubbleTone = 'green' | 'blue' | 'gray'

const props = defineProps<{
  messages: Array<{ sender: string; text: string }>
  role: string
  activeUser?: UserLike | null
  therapistUser?: UserLike | null
  otherUser?: UserLike | null
  title?: string
  selfLabel?: string
  otherLabel?: string
  selfTone?: BubbleTone
  otherTone?: BubbleTone
}>()

const emit = defineEmits<{
  (e: 'send', text: string): void
}>()

const newMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const resolvedOtherUser = computed(() => props.otherUser ?? props.therapistUser ?? null)

const bubbleStyles = {
  self: {
    green: 'ml-auto bg-green-100 text-green-900 rounded-tr-sm',
    blue: 'ml-auto bg-blue-100 text-blue-900 rounded-tr-sm',
    gray: 'ml-auto bg-gray-200 text-gray-900 rounded-tr-sm'
  },
  other: {
    gray: 'mr-auto bg-gray-100 text-gray-900 rounded-tl-sm',
    blue: 'mr-auto bg-blue-50 text-blue-900 rounded-tl-sm',
    green: 'mr-auto bg-green-50 text-green-900 rounded-tl-sm'
  }
} satisfies Record<'self' | 'other', Record<BubbleTone, string>>

const baseBubble = 'max-w-[75%] px-3 py-2 rounded-xl text-sm shadow-sm break-words'

const getBubbleClass = (msg: { sender: string }) => {
  const isSelf = msg.sender === props.role
  const tone = (isSelf ? props.selfTone : props.otherTone) ?? (isSelf ? 'green' : 'gray')
  const variant = bubbleStyles[isSelf ? 'self' : 'other'][tone] ?? bubbleStyles[isSelf ? 'self' : 'other'].gray
  return `${baseBubble} ${variant}`
}

const getSenderLabel = (msg: { sender: string }) => {
  if (msg.sender === props.role) return props.selfLabel ?? 'Tú'
  return (
    resolvedOtherUser.value?.full_name ||
    props.otherLabel ||
    (props.role === 'patient' ? 'Terapeuta' : 'Paciente')
  )
}

const handleSend = () => {
  const t = newMessage.value?.trim()
  if (!t) return
  emit('send', t)
  newMessage.value = ''
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

onMounted(async () => {
  // Si ya hay mensajes al montar, scrollear al final
  if (props.messages.length > 0) {
    await scrollToBottom()
  }
})

watch(() => props.messages, scrollToBottom, { deep: true })
</script>

<template>
  <div class="flex flex-col h-full max-h-[600px] rounded-xl border shadow-lg bg-white rounded-t-xl">
    <div class="flex items-center justify-between px-4 py-3 border-b rounded-t-xl" style="background-color: rgba(96, 165, 250, 0.6);">
          <div class="flex items-center gap-2 ">
            <h2 class="text-sm font-semibold text-black">{{ title || 'Chat con el terapeuta' }}</h2>
      </div>
    </div>

    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-3 space-y-2 bg-blue-50/50 min-h-0">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="getBubbleClass(msg)"
      >
        <div class="text-xs font-semibold opacity-80 mb-0.5">
          {{ getSenderLabel(msg) }}
        </div>
        <div>
          {{ msg.text }}
        </div>
      </div>
    </div>

    <div class="p-3 border-t rounded-b-xl" style="background-color: rgba(96, 165, 250, 0.25);">
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
