import * as React from "react"
import { cn } from "@/lib/utils"

const SidebarContext = React.createContext<{
  isOpen: boolean
  setIsOpen: (open: boolean) => void
}>({
  isOpen: true,
  setIsOpen: () => {},
})

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = React.useState(true)

  return (
    <SidebarContext.Provider value={{ isOpen, setIsOpen }}>
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  return React.useContext(SidebarContext)
}

export function Sidebar({ children, className }: { children: React.ReactNode; className?: string }) {
  const { isOpen } = useSidebar()

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-xray-border bg-xray-surface transition-all duration-200",
        isOpen ? "w-52" : "w-14",
        className
      )}
    >
      {children}
    </aside>
  )
}

export function SidebarHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center justify-center border-b border-xray-border h-12 px-3", className)}>
      {children}
    </div>
  )
}

export function SidebarContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex-1 overflow-y-auto py-3 px-2", className)}>
      {children}
    </div>
  )
}

export function SidebarFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("border-t border-xray-border p-2", className)}>
      {children}
    </div>
  )
}

export function SidebarMenu({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <nav className={cn("space-y-1", className)}>
      {children}
    </nav>
  )
}

export function SidebarMenuItem({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("", className)}>
      {children}
    </div>
  )
}
