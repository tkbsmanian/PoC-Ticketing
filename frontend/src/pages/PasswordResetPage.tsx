import { FormEvent, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '@/api/auth'

export function PasswordResetPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleRequest = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await authApi.requestPasswordReset(email)
      setMessage('If that email exists, a reset link has been sent.')
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async (e: FormEvent) => {
    e.preventDefault()
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await authApi.confirmPasswordReset(token!, password)
      setMessage('Password updated. You can now sign in.')
      setTimeout(() => navigate('/login'), 2000)
    } catch {
      setError('Reset link is invalid or has expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>{token ? 'Set New Password' : 'Reset Password'}</h1>

        {message && <p className="success-banner" role="status">{message}</p>}
        {error && <p className="field-error" role="alert">{error}</p>}

        {!token ? (
          <form onSubmit={handleRequest} noValidate>
            <div className="field">
              <label htmlFor="email">Email address</label>
              <input
                id="email" type="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Sending…' : 'Send Reset Link'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleConfirm} noValidate>
            <div className="field">
              <label htmlFor="password">New password</label>
              <input
                id="password" type="password" required minLength={8}
                value={password} onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="confirm">Confirm password</label>
              <input
                id="confirm" type="password" required
                value={confirm} onChange={(e) => setConfirm(e.target.value)}
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        )}

        <a href="/login">Back to sign in</a>
      </div>
    </div>
  )
}
