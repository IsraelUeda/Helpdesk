import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const links = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/tickets', label: 'Chamados' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="px-5 py-4">
        <p className="text-lg font-semibold text-slate-900">Helpdesk</p>
      </div>
      <nav className="flex flex-col gap-1 px-3">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `rounded-md px-3 py-2 text-sm font-medium ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:bg-slate-50'
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto border-t border-slate-200 px-5 py-4">
        <p className="truncate text-sm text-slate-600">{user?.email}</p>
        <button
          type="button"
          onClick={logout}
          className="mt-2 text-sm font-medium text-slate-500 hover:text-red-600"
        >
          Sair
        </button>
      </div>
    </aside>
  )
}
