<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { Calendar, Home, ChevronDown, BookImage, Bookmark, Folder, FileText, Users, Palette  } from 'lucide-vue-next'
import {
  Sidebar,
  SidebarProvider,
  SidebarTrigger,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarSeparator
} from '@/components/ui/sidebar'
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

import ProfileDropdown from './ProfileDropdown.vue'

import { useRoute } from 'vue-router'
const route = useRoute()

import mainBg from '@/assets/utils/fondo_app.jpg'
import logoImg from '/logo_comfymind.svg'
import { sessionsService } from '../api/sessionsService.js'
import { userService } from '../api/userService.js'

import { useDateHelpers } from '@/lib/useDateHelpers'

const {
  ensureUTCString,
  formatLocalDate
} = useDateHelpers()

const items = [
  {
    title: 'Inicio',
    url: '/home',
    icon: Home,
  },
  {
    title: 'Calendario',
    url: '/calendar',
    icon: Calendar,
  },
]

const sessionsOpen = ref(false)
const user = ref(null)
const mySessions = ref<Array<any>>([])

const bgStyle = computed(() => ({
  backgroundImage: `url(${mainBg})`,
  backgroundSize: 'cover',
  backgroundPosition: 'top center',
}))


const headerStyle = computed(() => ({
  backgroundImage: `
    linear-gradient(
      rgba(255,255,255,0.2),
      rgba(255,255,255,0.2)
    ),
    url('/stacked-waves-haikei.svg')
  `,
  backgroundSize: 'cover',
  backgroundPosition: 'bottom center',
}))


const getDateOnly = (utcString: string): string => {
  if (!utcString) return ''
  return formatLocalDate(utcString).slice(0, 8)
}

const sortedAndNumberedSessions = computed(() => {
  const sorted = [...mySessions.value]
    .filter(s => s.ended_at != null)  // Only show completed sessions
    .sort((a, b) => {
      const dateA = new Date(ensureUTCString(a.start_date)).getTime()
      const dateB = new Date(ensureUTCString(b.start_date)).getTime()
      return dateA - dateB
    })
  
  // Group by date
  const dateMap = new Map<string, any[]>()
  sorted.forEach(s => {
    const dateKey = getDateOnly(s.start_date)
    if (!dateMap.has(dateKey)) {
      dateMap.set(dateKey, [])
    }
    dateMap.get(dateKey)!.push(s)
  })
  
  // Flatten and add start time for all sessions
  const result: any[] = []
  dateMap.forEach((sessions, dateStr) => {
    sessions.forEach((s) => {
      const startTime = formatLocalDate(s.start_date).slice(10, 16)
      result.push({
        ...s,
        startTime: startTime,
        dateStr: dateStr
      })
    })
  })
  return result
})

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
  } catch (e) {
    user.value = null
  }
  try {
    const sessions = await sessionsService.getMySessions()
    const list = Array.isArray((sessions as any)?.data)
      ? (sessions as any).data
      : (Array.isArray(sessions) ? (sessions as any) : [])
    mySessions.value = list
  } catch (e) {
    mySessions.value = []
  }
})

</script>

<template>
  <div class="min-h-screen flex flex-col text-gray-800">
    <SidebarProvider class="flex flex-1">
      <Sidebar class="bg-white">
        <SidebarContent>
          <SidebarGroup class="!mb-0 !pb-0">
            <SidebarGroupLabel>Menú principal</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem v-for="item in items" :key="item.title">
                  <SidebarMenuButton
                    as-child
                    :class="{
                      'bg-gray-500 text-white font-semibold hover:bg-gray-300': route.path === item.url,
                      'hover:bg-gray-300': route.path !== item.url
                    }"
                  >
                    <a :href="item.url">
                      <component :is="item.icon" />
                      <span>{{ item.title }}</span>
                    </a>
                  </SidebarMenuButton>

                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
          <SidebarSeparator />
          <SidebarGroup class="!mt-0 !pt-0">
            <!-- BOTÓN PADRE -->
            <SidebarMenuButton @click="sessionsOpen = !sessionsOpen">
              <Bookmark class="h-4 w-4" />
              <span>Sesiones</span>
              <ChevronDown
                class="ml-auto h-4 w-4 transition-transform"
                :class="{ 'rotate-180': sessionsOpen }"
              />
            </SidebarMenuButton>

            <!-- HIJOS -->
            <div
              v-show="sessionsOpen"
              class="relative ml-4 pl-4 border-l border-slate-200 space-y-1"
            >
              <SidebarMenuButton
                v-for="s in sortedAndNumberedSessions"
                :key="s.id"
                as-child
                :class="{
                  'bg-gray-500 text-white font-semibold hover:bg-gray-300': route.path === `/session/${s.id}`,
                  'hover:bg-gray-300': route.path !== `/session/${s.id}`
                }"
              >
                <a :href="`/session/${s.id}`">
                  <BookImage class="h-4 w-4" />
                  <span>{{ `Sesión ${s.dateStr} ${s.startTime}` }}</span>
                </a>
              </SidebarMenuButton>
            </div>
          </SidebarGroup>

          <SidebarSeparator v-if="user?.type === 'patient'" />
          <SidebarGroup class="!mb-0 !pb-0">
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem v-if="user?.type === 'patient'">
                  <SidebarMenuButton
                    as-child
                    :class="{
                      'bg-gray-500 text-white font-semibold hover:bg-gray-300': route.path === `/freeimages`,
                      'hover:bg-gray-300': route.path !== `/freeimages`
                    }"
                  >
                    <a :href="`/freeimages`">
                      <component :is="Palette" />
                      <span>{{ "Imagénes de generación libre" }}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>

      <!-- MAIN -->
      <div class="flex flex-1 flex-col">

        <!-- HEADER -->
        <header class="sticky top-0 z-50 border-b bg-white/70 backdrop-blur"
        :style="headerStyle">
          <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-2">

            <div class="flex items-center gap-4">
              <SidebarTrigger class="text-gray-700" />
              <Separator orientation="vertical" class="!h-4 hidden sm:block" />
              <div class="flex items-center gap-2">
                <img :src="logoImg" alt="ComfyMind" class="h-8 w-8" />
                <span class="text-gray-900 hidden sm:block mt-1 ml-0.5" style="font-family: 'Nunito', sans-serif; font-size: 1.7rem; font-weight: 750">ComfyMind</span>
              </div>
            </div>

            <!-- PROFILE DROPDOWN -->
            <ProfileDropdown>
              <Button variant="ghost" size="icon" class="size-10">
                <Avatar class="size-10 rounded-md">
                  <AvatarImage src="https://cdn.shadcnstudio.com/ss-assets/avatar/avatar-1.png" />
                  <AvatarFallback>JD</AvatarFallback>
                </Avatar>
              </Button>
            </ProfileDropdown>

          </div>
        </header>

        <!-- CONTENT (SE INYECTA DESDE EL PADRE VIA SLOT) -->
        <main class="flex-1 mx-auto max-w-7xl px-4 py-6">
          <slot />
        </main>

      </div>
    </SidebarProvider>
  </div>
</template>
