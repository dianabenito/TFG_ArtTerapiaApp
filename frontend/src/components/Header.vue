<script setup lang="ts">
import { Calendar, Home } from 'lucide-vue-next'
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
} from '@/components/ui/sidebar'
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

import ProfileDropdown from './ProfileDropdown.vue'

import { useRoute } from 'vue-router'
const route = useRoute()

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
</script>

<template>
  <div class="flex min-h-screen w-full bg-gray-100 text-gray-800">
    <SidebarProvider>
      <Sidebar>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>ArtTeràpia App</SidebarGroupLabel>
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
        </SidebarContent>
      </Sidebar>

      <!-- MAIN -->
      <div class="flex flex-1 flex-col">

        <!-- HEADER -->
        <header class="sticky top-0 z-50 border-b bg-white/70 backdrop-blur">
          <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-2">

            <div class="flex items-center gap-4">
              <SidebarTrigger class="text-gray-700" />
              <Separator orientation="vertical" class="!h-4 hidden sm:block" />
 
              <!---
              <Breadcrumb class="hidden sm:block">
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbLink href="#">Home</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="#">Dashboard</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <BreadcrumbPage>Panel</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            -->
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
        <main class="mx-auto max-w-7xl flex-1 px-4 py-6">
          <slot />
        </main>

      </div>
    </SidebarProvider>
  </div>
</template>
