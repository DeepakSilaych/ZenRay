import { Outlet } from 'react-router-dom'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/AppSidebar'

export default function App() {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <AppSidebar />
        <main className="flex-1 overflow-y-auto bg-xray-bg">
          <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
    </SidebarProvider>
  )
}
