<script setup>
import { ref, onMounted } from "vue"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuGroup,
} from "@/components/ui/dropdown-menu"

import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

import {
  UserIcon,
  SettingsIcon,
  CreditCardIcon,
  UsersIcon,
  SquarePenIcon,
  CirclePlusIcon,
  LogOutIcon,
} from "lucide-vue-next"

const user = ref(null)
const errorMsg = ref('')

import { useRouter } from 'vue-router'
import { userService } from '../api/userService'

const router = useRouter()

onMounted(async () => {
  try {
    user.value = await userService.getCurrentUser()
    console.log('Usuario actual:', user.value)
  } catch (error) {
    errorMsg.value = error.response?.data?.detail || 'No autenticado'
  }
})

const logout = () => {
  userService.logout()
  router.push('/')
}
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <slot />
    </DropdownMenuTrigger>

    <DropdownMenuContent class="w-80" align="end">
      <DropdownMenuLabel class="flex items-center gap-4 px-4 py-2.5 font-normal">
        <div class="relative">
          <Avatar class="size-10">
            <AvatarImage src="https://cdn.shadcnstudio.com/ss-assets/avatar/avatar-1.png" />
            <AvatarFallback>JD</AvatarFallback>
          </Avatar>
          <span class="absolute right-0 bottom-0 block size-2 rounded-full bg-green-600 ring-2 ring-white"></span>
        </div>
        <div class="flex flex-col items-start">
          <span class="text-lg font-semibold">{{ user.full_name }}</span>
          <span class="text-gray-500 text-base">{{ user.email }}</span>
        </div>
      </DropdownMenuLabel>

      <DropdownMenuSeparator />

      <DropdownMenuGroup>
        <DropdownMenuItem class="px-4 py-2.5 text-base">
          <UserIcon class="size-5" />
          <span>My account</span>
        </DropdownMenuItem>
        <DropdownMenuItem class="px-4 py-2.5 text-base">
          <SettingsIcon class="size-5" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuItem class="px-4 py-2.5 text-base">
          <CreditCardIcon class="size-5" />
          <span>Billing</span>
        </DropdownMenuItem>
      </DropdownMenuGroup>

      <DropdownMenuSeparator />

      <DropdownMenuGroup>
        <DropdownMenuItem class="px-4 py-2.5 text-base">
          <UsersIcon class="size-5" />
          <span>Manage team</span>
        </DropdownMenuItem>
        <DropdownMenuItem class="px-4 py-2.5 text-base">
          <SquarePenIcon class="size-5" />
          <span>Customization</span>
        </DropdownMenuItem>
        <DropdownMenuItem class="px-4 py-2.5 text-base">
          <CirclePlusIcon class="size-5" />
          <span>Add team account</span>
        </DropdownMenuItem>
      </DropdownMenuGroup>

      <DropdownMenuSeparator />

      <DropdownMenuItem class="px-4 py-2.5 text-base text-red-600" @click="logout()">
        <LogOutIcon class="size-5"/>
        <span>Logout</span>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
