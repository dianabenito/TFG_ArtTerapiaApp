<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Image as ImageIcon, FolderOpen, Brush } from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  loading: boolean
  tempImageUrl?: string | null
  promptText: string
  activeTab: string
  isLoadingGallery: boolean
  uploadFileName?: string | null
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'update:promptText', v: string): void
  (e: 'update:activeTab', v: string): void
  (e: 'fileChange', file: File): void
  (e: 'uploadAndTransform'): void
  (e: 'drawSketch'): void
  (e: 'confirm'): void
}>()

const onFile = (ev: Event) => {
  const input = ev.target as HTMLInputElement
  const f = input.files && input.files[0]
  if (f) emit('fileChange', f)
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="w-full max-w-5xl sm:max-w-5xl">
      <DialogHeader>
        <DialogTitle>Generar obra a partir de un esbozo</DialogTitle>
        <DialogDescription>
          Sube un esbozo desde tu biblioteca o dibujalo en el editor, y añade una descripción para transformar el esbozo en una nueva obra.
        </DialogDescription>
      </DialogHeader>

      <div class="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 mt-4">
        <div class="flex flex-col gap-4">
          <Tabs :model-value="activeTab" @update:model-value="(v) => emit('update:activeTab', v as string)">
            <TabsList class="mx-auto mb-3">
              <TabsTrigger value="upload">Subir boceto</TabsTrigger>
              <TabsTrigger value="draw">Dibujar boceto</TabsTrigger>
            </TabsList>

            <TabsContent value="upload">
              <div class="grid gap-2 mb-3">
                <Label for="fileInput">Paso 1: Sube un boceto desde la biblioteca de archivos de tu ordenador:</Label>
                <div class="flex items-center gap-3">
                  <div class="relative shrink-0">
                    <input id="fileInput" type="file" accept="image/*" @change="onFile" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                    <Button variant="outline">
                      <FolderOpen class="h-4 w-4" />
                      <span>Seleccionar archivo</span>
                    </Button>
                  </div>
                  <span class="text-sm text-muted-foreground truncate max-w-xs">{{ uploadFileName || 'Ningún archivo seleccionado' }}</span>
                </div>
              </div>

              <div class="h-px bg-border my-4" />

              <div class="grid gap-2">
                <Label for="promptText">Paso 2: Describe la obra que quieres crear a partir del boceto subido:</Label>
                <Textarea id="promptText" :model-value="promptText" placeholder="Describe tu boceto en detalle para reconvertirlo en una obra final." class="min-h-[200px]" :disabled="loading" @update:model-value="(v) => emit('update:promptText', v as string)" />
              </div>

              <Button class="mt-3" @click="emit('uploadAndTransform')" :disabled="isLoadingGallery || !uploadFileName || !promptText?.trim()" variant="default">Transformar boceto</Button>
            </TabsContent>

            <TabsContent value="draw">
              <div class="grid gap-2">
                <Label for="promptText">Diseña un nuevo boceto en el editor:</Label>
              </div>
              <div class="flex justify-start mt-3">
                <Button variant="default" class="px-4 py-2" @click="emit('drawSketch')">
                  <Brush class="h-4 w-4" />
                  Ir a dibujar boceto
                </Button>
              </div>
            </TabsContent>
          </Tabs>
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
        <Button :disabled="loading || !tempImageUrl" class="bg-green-600 hover:bg-green-700 text-white px-8 py-5 rounded-lg font-bold text-lg shadow-lg" @click="emit('confirm')">Confirmar imagen</Button>
      </div>
    </DialogContent>
  </Dialog>
</template>
