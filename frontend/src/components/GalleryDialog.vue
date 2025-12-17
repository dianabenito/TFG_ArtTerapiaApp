<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'

const props = defineProps<{
  open: boolean
  templates: Array<any>
  generated: Array<any>
  uploaded: Array<any>
  multiSelectMode: boolean
  selectedImages: Array<any>
  minMultiSelect: number
  isLoading?: boolean
  getImageUrl: (fileName: string) => string
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'toggle', img: any): void
  (e: 'confirm'): void
  (e: 'selectSingle', img: any): void
}>()

const isSelected = (img: any) => props.selectedImages.some(i => i.fileName === img.fileName)
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="max-w-5xl max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ multiSelectMode ? 'Selecciona imágenes para combinar' : 'Selecciona una imagen' }}</DialogTitle>
        <DialogDescription>{{ multiSelectMode ? 'Selecciona de 2 a 4 imagenes que se mezclaran para crear una nueva obra.' : 'Selecciona una imagen como punto de partida para tu obra.' }}</DialogDescription>
      </DialogHeader>

      <div class="flex items-center gap-3 mb-2">
        <Button
          v-if="multiSelectMode"
          size="sm"
          :disabled="selectedImages.length < minMultiSelect"
          @click="emit('confirm')"
        >
          Confirmar selección ({{ selectedImages.length }})
        </Button>
      </div>

      <div class="space-y-4">
        <div v-if="templates?.length">
          <h3>Templates</h3>
          <div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-[10px] mt-5">
            <div
              v-for="img in templates"
              :key="img.id || img.fileName"
              class="img-item cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-lg border"
              @click.stop="multiSelectMode ? emit('toggle', img) : emit('selectSingle', img)"
              :class="isSelected(img) ? 'ring-2 ring-blue-500 ring-offset-2 bg-blue-50' : ''"
            >
              <img :src="getImageUrl(img.fileName)" class="w-full aspect-square object-cover rounded-lg border" />
            </div>
          </div>
        </div>

        <div v-if="generated?.length">
          <h3>Generadas</h3>
          <div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-[10px] mt-5">
            <div
              v-for="img in generated"
              :key="img.id || img.fileName"
              class="img-item cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-lg border"
              @click.stop="multiSelectMode ? emit('toggle', img) : emit('selectSingle', img)"
              :class="isSelected(img) ? 'ring-2 ring-blue-500 ring-offset-2 bg-blue-50' : ''"
            >
              <img :src="getImageUrl(img.fileName)" class="w-full aspect-square object-cover rounded-lg border" />
            </div>
          </div>
        </div>

        <div v-if="uploaded?.length">
          <h3>Subidas</h3>
          <div class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-[10px] mt-5">
            <div
              v-for="img in uploaded"
              :key="img.id || img.fileName"
              class="img-item cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-lg border"
              @click.stop="multiSelectMode ? emit('toggle', img) : emit('selectSingle', img)"
              :class="isSelected(img) ? 'ring-2 ring-blue-500 ring-offset-2 bg-blue-50' : ''"
            >
              <img :src="getImageUrl(img.fileName)" class="w-full aspect-square object-cover rounded-lg border" />
            </div>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
