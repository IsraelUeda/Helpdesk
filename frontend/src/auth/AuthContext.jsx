import { createContext, useContext, useState } from 'react'

const STORAGE_KEY = 'helpdesk:user'

const AuthContext = createContext(null)

function readStoredUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser)

  // Mock: aceita qualquer e-mail válido com senha de 6+ caracteres.
  // Substituir pela chamada à API quando o backend existir.
  async function login(email, password) {
    await new Promise((resolve) => setTimeout(resolve, 500))
    if (!email.includes('@') || password.length < 6) {
      throw new Error('E-mail ou senha inválidos.')
    }
    const loggedUser = { email, name: email.split('@')[0] }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedUser))
    setUser(loggedUser)
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
