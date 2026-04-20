import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export function Profile() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  useEffect(() => {
    const rawUser = localStorage.getItem('user')
    if (rawUser) {
      try {
        setUser(JSON.parse(rawUser))
      } catch {
        setUser(null)
      }
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <div className="app-scroll">
      <div className="fj-page" style={{ position: 'relative', height: '100%' }}>
        <div className="fj-section-head">
          <button className="fj-back" onClick={() => navigate('/')}>
            ‹ 返回
          </button>
          <div
            style={{
              fontFamily: "'Noto Serif SC', serif",
              fontSize: 22,
              fontWeight: 300,
              color: '#000',
              letterSpacing: '0.08em',
              marginBottom: 4,
              marginTop: 12
            }}
          >
            我的主页
          </div>
          <div className="fj-section-subtitle">查看账户信息与草稿入口</div>
        </div>

        <div style={{ padding: '0 28px 120px' }}>
          <div
            className="fj-card"
            style={{
              padding: '18px 18px 16px',
              marginBottom: 12
            }}
          >
            <div
              style={{
                fontSize: 10,
                color: '#bbb',
                letterSpacing: '0.12em',
                marginBottom: 8
              }}
            >
              ACCOUNT
            </div>
            <div
              style={{
                fontFamily: "'Noto Serif SC', serif",
                fontSize: 20,
                fontWeight: 300,
                color: '#111',
                letterSpacing: '0.04em',
                marginBottom: 6
              }}
            >
              {user?.nickname || '风间用户'}
            </div>
            <div style={{ fontSize: 12, color: '#999' }}>{user?.email || '未登录邮箱'}</div>
          </div>

          <button
            className="fj-secondary-btn"
            onClick={() => navigate('/drafts')}
            style={{ marginBottom: 10 }}
          >
            进入我的草稿箱
          </button>

          <button className="fj-primary-btn" onClick={handleLogout}>
            退出登录
          </button>
        </div>
      </div>
    </div>
  )
}