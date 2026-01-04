import { Outlet, Link, useLocation } from 'react-router-dom'

export default function App() {
  const location = useLocation()
  
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-xray-border bg-xray-surface">
        <div className="max-w-screen-2xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-lg font-semibold tracking-tight">
              X-Ray
            </Link>
            <nav className="flex items-center gap-1">
              <NavLink to="/" current={location.pathname === '/'}>
                Runs
              </NavLink>
              <NavLink to="/compare" current={location.pathname === '/compare'}>
                Compare
              </NavLink>
              <NavLink to="/docs" current={location.pathname === '/docs'}>
                Docs
              </NavLink>
            </nav>
          </div>
          <div className="text-xs text-xray-dim">
            Pipeline Observability
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-screen-2xl mx-auto px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

function NavLink({ to, current, children }: { to: string; current: boolean; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className={`px-3 py-1.5 rounded text-sm transition-colors ${
        current
          ? 'bg-xray-elevated text-xray-text'
          : 'text-xray-muted hover:text-xray-text'
      }`}
    >
      {children}
    </Link>
  )
}
