<script setup>
import { Sidebar, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

import ProfileDropdown from './ProfileDropdown.vue'
</script>

<template>
  <div class="flex min-h-screen w-full bg-gray-100 text-gray-800">
    <SidebarProvider>

      <!-- SIDEBAR -->
      <Sidebar>
        <div
          class="m-6 h-full rounded-md border border-gray-300 bg-[repeating-linear-gradient(45deg,#e5e7eb,#e5e7eb_1px,#f9fafb_2px,#f9fafb_15px)]"
        />
      </Sidebar>

      <!-- MAIN -->
      <div class="flex flex-1 flex-col">

        <!-- HEADER -->
        <header class="sticky top-0 z-50 border-b bg-white/70 backdrop-blur">
          <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-2">

            <div class="flex items-center gap-4">
              <SidebarTrigger class="text-gray-700" />
              <Separator orientation="vertical" class="!h-4 hidden sm:block" />

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
