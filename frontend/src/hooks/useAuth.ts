/**
 * useAuth — provides current user, login, logout.
 * All role checks in the app go through this hook.
 */

import { useContext } from 'react'
import { AuthContext } from '@/context/AuthContext'

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
