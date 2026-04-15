'use client'

import { useRouter } from 'next/navigation'
import { LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { authApi } from '@/lib/api/auth'

export function Topbar() {
  const router = useRouter()

  const handleLogout = async () => {
    await authApi.logout()
    router.push('/login')
    router.refresh()
  }

  return (
    <header className="flex h-14 items-center justify-end border-b bg-background px-4">
      <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2 text-muted-foreground">
        <LogOut size={15} />
        Sign out
      </Button>
    </header>
  )
}
