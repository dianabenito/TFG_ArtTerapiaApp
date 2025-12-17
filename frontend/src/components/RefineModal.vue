<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Image as ImageIcon } from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  loading: boolean
  tempImageUrl?: string | null
  promptText: string
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'update:promptText', v: string): void
  (e: 'generate'): void
  (e: 'confirm'): void
}>()
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="w-full max-w-5xl sm:max-w-5xl">
      <DialogHeader>
        <DialogTitle>Generar obra a partir de un prompt de texto</DialogTitle>
        <DialogDescription>
          Describe la obra que quieres crear y genera una imagen basada en tu descripción.
        </DialogDescription>
      </DialogHeader>

      <div class="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 mt-4">
        <div class="flex flex-col gap-4">
          <div class="grid gap-2">
            <label for="promptText" class="text-sm font-medium">Descripción de la obra</label>
            <Textarea
              id="promptText"
              :model-value="promptText"
              placeholder="Describe el contenido que quieres ver en tu obra."
              class="min-h-[200px]"
              :disabled="loading"
              @update:model-value="(v) => emit('update:promptText', v as string)"
            />
          </div>

          <div class="flex justify-end">
            <Button 
              variant="default"
              class="px-4 py-2"
              :disabled="loading || !promptText?.trim()"
              @click="emit('generate')"
            >
              Generar imagen
            </Button>
          </div>
        </div>

        <div class="hidden md:flex items-stretch">
          <div class="w-px bg-border" />
        </div>

        <div class="h-full border rounded-md">
          <div class="flex flex-col items-center justify-center h-full gap-4 py-6 text-center">
            <div v-if="loading" class="flex flex-col items-center gap-3 text-muted-foreground">
              <Loader2 class="h-6 w-6 animate-spin" />
              <span class="text-sm">Generando imagen...</span>
            </div>

            <div v-else-if="tempImageUrl" class="flex flex-col items-center gap-4 w-full">
              <img :src="tempImageUrl" alt="Previsualización" class="max-h-[360px] rounded-lg border object-contain" />
            </div>

            <div v-else class="flex flex-col items-center gap-2 text-muted-foreground">
              <ImageIcon class="h-8 w-8 opacity-50" />
              <span class="text-sm">Aún no hay ninguna imagen generada</span>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-center mt-3">
        <Button
          :disabled="loading || !tempImageUrl"
          class="bg-green-600 hover:bg-green-700 text-white px-8 py-5 rounded-lg font-bold text-lg shadow-lg"          
          @click="emit('confirm')"
        >
          Confirmar imagen
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>
