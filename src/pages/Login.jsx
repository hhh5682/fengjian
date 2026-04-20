import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTripStore } from '../store/tripStore'

export function Login() {
  const navigate = useNavigate()
  const { loginUser } = useTripStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password.trim()) {
      setError('请输入邮箱和密码')
      return
    }

    setLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 600))

      const user = loginUser(email, password)

      if (!user) {
        setError('邮箱或密码错误')
        return
      }

      localStorage.setItem('user', JSON.stringify(user))
      navigate('/')
    } catch (err) {
      setError('登录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fj-auth-page">
      <div className="fj-auth-inner">
        <div className="fj-auth-header">
          <div className="fj-auth-logo">风间</div>
          <div className="fj-auth-desc">AI 旅行规划助手</div>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="fj-auth-field">
            <label className="fj-auth-label">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="请输入邮箱"
              className="fj-field-input"
              style={{ fontSize: 16 }}
            />
            <div className="fj-field-line">
              <div className="fj-field-line-inner" />
            </div>
          </div>

          <div className="fj-auth-field">
            <label className="fj-auth-label">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              className="fj-field-input"
              style={{ fontSize: 16 }}
            />
            <div className="fj-field-line">
              <div className="fj-field-line-inner" />
            </div>
          </div>

          {error && <div className="fj-auth-error">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="fj-primary-btn"
            style={{ marginTop: 8 }}
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="fj-auth-footer">
          还没有账户？
          <button onClick={() => navigate('/register')} style={{ marginLeft: 4 }}>
            立即注册
          </button>
        </div>
      </div>
    </div>
  )
}