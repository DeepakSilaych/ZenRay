import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useSidebar, Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarMenu, SidebarMenuItem } from '@/components/ui/sidebar'
import { LayoutDashboard, GitCompare, Key, LogOut, Menu, X, Zap } from 'lucide-react'

export function AppSidebar() {
  const location = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { isOpen, setIsOpen } = useSidebar()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menuItems = [
    { path: '/', label: 'Runs', icon: LayoutDashboard },
    { path: '/compare', label: 'Compare', icon: GitCompare },
    { path: '/api-keys', label: 'API Keys', icon: Key },
  ]

  return (
    <Sidebar className="h-screen">
      {/* Header */}
      <SidebarHeader>
        <div className="flex items-center justify-between w-full">
          {isOpen ? (
            <>
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-500" />
                <span className="font-semibold">ZenRay</span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-xray-elevated rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsOpen(true)}
              className="w-full flex justify-center p-1.5 hover:bg-xray-elevated rounded transition-colors"
            >
              <Menu className="w-[18px] h-[18px]" />
            </button>
          )}
        </div>
      </SidebarHeader>

      {/* Navigation */}
      <SidebarContent>
        <SidebarMenu>
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <SidebarMenuItem key={item.path}>
                <Link
                  to={item.path}
                  className={`
                    flex items-center rounded-md transition-colors
                    ${isOpen ? 'gap-2.5 px-2.5 py-2' : 'justify-center p-2'}
                    ${isActive 
                      ? 'bg-blue-600 text-white' 
                      : 'text-xray-muted hover:bg-xray-elevated hover:text-xray-text'
                    }
                  `}
                >
                  <Icon className="w-[18px] h-[18px] flex-shrink-0" />
                  {isOpen && <span className="text-sm font-medium">{item.label}</span>}
                </Link>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarContent>

      {/* Footer - User */}
      <SidebarFooter>
        {user && (
          <div className="space-y-2">
            {/* User Info */}
            <div className={`flex items-center ${isOpen ? 'gap-2.5' : 'justify-center'}`}>
              {user.picture ? (
                <img 
                  src={user.picture} 
                  alt={user.name || user.email} 
                  className="w-7 h-7 rounded-full flex-shrink-0"
                />
              ) : (
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-semibold flex-shrink-0">
                  {(user.name || user.email).charAt(0).toUpperCase()}
                </div>
              )}
              {isOpen && (
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{user.name || 'User'}</div>
                  <div className="text-xs text-xray-muted truncate">{user.email}</div>
                </div>
              )}
            </div>

            {/* Sign Out Button */}
            <button
              onClick={handleLogout}
              className={`
                flex items-center rounded-md transition-colors text-xray-muted hover:bg-xray-elevated hover:text-xray-text
                ${isOpen ? 'w-full gap-2.5 px-2.5 py-1.5' : 'w-full justify-center p-2'}
              `}
            >
              <LogOut className="w-4 h-4 flex-shrink-0" />
              {isOpen && <span className="text-sm">Sign Out</span>}
            </button>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  )
}
