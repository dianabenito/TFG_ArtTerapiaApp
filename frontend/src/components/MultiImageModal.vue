<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, Image as ImageIcon, Check, UploadCloud } from 'lucide-vue-next'
// no Label needed for the button-only upload

interface ImageItem {
  id?: string | number
  fileName: string
  seed?: number | null
}

const props = defineProps<{
  open: boolean
  loading: boolean
  tempImageUrl?: string | null
  templates: ImageItem[]
  generated: ImageItem[]
  uploaded: ImageItem[]
  selectedImages: ImageItem[]
  minMultiSelect: number
  maxMultiSelect: number
    isLoadingGallery: boolean
    uploadFileName?: string | null
  getImageUrl: (fileName: string) => string
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'toggle', img: ImageItem): void
    (e: 'fileChange', file: File): void
    (e: 'uploadImage'): void
  (e: 'generate'): void
  (e: 'confirm'): void
}>()

const isSelected = (img: ImageItem) => {
  return props.selectedImages.some(i => i.fileName === img.fileName)
}

const canGenerate = computed(() => {
  return props.selectedImages.length >= props.minMultiSelect && 
         props.selectedImages.length <= props.maxMultiSelect
})

const onFile = (ev: Event) => {
  const input = ev.target as HTMLInputElement
  const f = input.files && input.files[0]
  if (f) emit('fileChange', f)
}

const fileInput = ref<HTMLInputElement | null>(null)
const onFileAndUpload = (ev: Event) => {
  onFile(ev)
  emit('uploadImage')
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="w-full max-w-5xl sm:max-w-5xl max-h-[90vh] overflow-y-auto">
      <DialogHeader class="pb-2">
        <DialogTitle>Mezclar imágenes para crear una nueva obra</DialogTitle>
        <DialogDescription>
          Selecciona entre {{ minMultiSelect }} y {{ maxMultiSelect }} imágenes de tu galería para combinarlas en una nueva obra.
        </DialogDescription>
      </DialogHeader>

      <div class="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 mt-2">
        <!-- GALERÍA CON SELECCIÓN MÚLTIPLE Y TABS -->
        <div class="flex flex-col gap-3">
          
          <Tabs default-value="templates" class="w-full">
            <div class="flex items-center justify-between gap-2">
              <TabsList class="w-auto">
                <TabsTrigger value="templates" class="px-3">Plantillas</TabsTrigger>
                <TabsTrigger value="generated" class="px-3">Generadas</TabsTrigger>
                <TabsTrigger value="uploaded" class="px-3">Subidas</TabsTrigger>
              </TabsList>
              <div class="flex items-center gap-2">
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  class="sr-only"
                  @change="onFileAndUpload"
                />
                <Button
                  size="sm"
                  variant="outline"
                  :disabled="loading || isLoadingGallery"
                  @click="fileInput?.click()"
                >
                  <UploadCloud class="h-4 w-4" />
                  <span class="ml-2">Subir imagen</span>
                </Button>
                <span class="text-xs text-muted-foreground truncate max-w-[180px]">{{ uploadFileName || '' }}</span>
              </div>
            </div>

            
            <TabsContent value="templates" class="mt-3">
              <div v-if="templates?.length" class="grid grid-cols-4 gap-2 max-h-[300px] overflow-y-auto">
                <div
                  v-for="img in templates"
                  :key="img.fileName"
                  class="relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all hover:shadow-md aspect-square"
                  :class="isSelected(img) ? 'border-blue-500 ring-2 ring-blue-300' : 'border-transparent'"
                  @click="emit('toggle', img)"
                >
                  <img
                    :src="getImageUrl(img.fileName)"
                    :alt="img.fileName"
                    class="w-full h-full object-cover"
                  />
                  <div
                    v-if="isSelected(img)"
                    class="absolute top-1 right-1 bg-blue-500 text-white rounded-full p-1"
                  >
                    <Check class="h-3 w-3" />
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-muted-foreground text-center py-4">
                No hay imágenes de plantilla
              </div>
            </TabsContent>

            <TabsContent value="generated" class="mt-3">
              <div v-if="generated?.length" class="grid grid-cols-4 gap-2 max-h-[300px] overflow-y-auto">
                <div
                  v-for="img in generated"
                  :key="img.fileName"
                  class="relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all hover:shadow-md aspect-square"
                  :class="isSelected(img) ? 'border-blue-500 ring-2 ring-blue-300' : 'border-transparent'"
                  @click="emit('toggle', img)"
                >
                  <img
                    :src="getImageUrl(img.fileName)"
                    :alt="img.fileName"
                    class="w-full h-full object-cover"
                  />
                  <div
                    v-if="isSelected(img)"
                    class="absolute top-1 right-1 bg-blue-500 text-white rounded-full p-1"
                  >
                    <Check class="h-3 w-3" />
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-muted-foreground text-center py-4">
                No hay imágenes generadas
              </div>
            </TabsContent>
            
            <TabsContent value="uploaded" class="mt-3">
              <div v-if="uploaded?.length" class="grid grid-cols-4 gap-2 max-h-[300px] overflow-y-auto">
                <div
                  v-for="img in uploaded"
                  :key="img.fileName"
                  class="relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all hover:shadow-md aspect-square"
                  :class="isSelected(img) ? 'border-blue-500 ring-2 ring-blue-300' : 'border-transparent'"
                  @click="emit('toggle', img)"
                >
                  <img
                    :src="getImageUrl(img.fileName)"
                    :alt="img.fileName"
                    class="w-full h-full object-cover"
                  />
                  <div
                    v-if="isSelected(img)"
                    class="absolute top-1 right-1 bg-blue-500 text-white rounded-full p-1"
                  >
                    <Check class="h-3 w-3" />
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-muted-foreground text-center py-4">
                No hay imágenes subidas
              </div>
            </TabsContent>
          </Tabs>

          <Button
            variant="default"
            class="px-3 py-2 w-full text-sm"
            @click="emit('generate')"
            :disabled="!canGenerate || loading"
          >
            {{ loading ? 'Generando...' : 'Generar imagen combinada' }}
          </Button>
        </div>

        <!-- SEPARADOR -->
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
