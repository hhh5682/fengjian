import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTripStore } from '../store/tripStore'

export function Register() {
  const navigate = useNavigate()
  const { registerUser, loginUser } = useTripStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password.trim() || !confirmPassword.trim()) {
      setError('请填写所有字段')
      return
    }

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    if (password.length < 6) {
      setError('密码长度至少 6 位')
      return
    }

    setLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 600))

      registerUser(email, password)
      const user = loginUser(email, password)

      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
        navigate('/')
      } else {
        setError('注册失败，请重试')
      }
    } catch (err) {
      setError('注册失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fj-auth-page">
      <div className="fj-auth-inner">
        <div className="fj-auth-header">
          <div className="fj-auth-logo">风间</div>
          <div className="fj-auth-desc">创建账户开始规划</div>
        </div>

        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
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
              placeholder="请输入密码（至少 6 位）"
              className="fj-field-input"
              style={{ fontSize: 16 }}
            />
            <div className="fj-field-line">
              <div className="fj-field-line-inner" />
            </div>
          </div>

          <div className="fj-auth-field">
            <label className="fj-auth-label">确认密码</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="请再次输入密码"
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
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <div className="fj-auth-footer">
          已有账户？
          <button onClick={() => navigate('/login')} style={{ marginLeft: 4 }}>
            立即登录
          </button>
        </div>
      </div>
    </div>
  )
}