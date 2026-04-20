import { isToday, isYesterday, subDays, format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { useTripStore } from '../store/tripStore'

export function DraftBox() {
  const navigate = useNavigate()
  const { drafts, deleteDraft, loadDraft } = useTripStore()

  const groups = {
    today: [],
    yesterday: [],
    week: [],
    older: []
  }

  drafts.forEach((draft) => {
    const createdAt = new Date(draft.createdAt)
    if (isToday(createdAt)) {
      groups.today.push(draft)
    } else if (isYesterday(createdAt)) {
      groups.yesterday.push(draft)
    } else if (createdAt > subDays(new Date(), 7)) {
      groups.week.push(draft)
    } else {
      groups.older.push(draft)
    }
  })

  const handleContinueEdit = (draft) => {
    loadDraft(draft.id)
    navigate('/itinerary')
  }

  const handleDeleteDraft = (e, draftId) => {
    e.stopPropagation()
    if (confirm('确定要删除这个草稿吗？')) {
      deleteDraft(draftId)
    }
  }

  const renderGroup = (title, items) => {
    if (items.length === 0) return null

    return (
      <div key={title}>
        <div
          style={{
            fontSize: 11,
            color: '#bbb',
            padding: '0 28px 8px',
            letterSpacing: '0.04em'
          }}
        >
          {title}
        </div>
        {items.map((draft) => (
          <div
            key={draft.id}
            className="fj-card fj-card-hover"
            style={{
              margin: '0 28px 10px',
              padding: '16px 18px',
              cursor: 'pointer',
              position: 'relative'
            }}
            onClick={() => handleContinueEdit(draft)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, paddingRight: 32 }}>
              <div style={{ fontSize: 11, color: '#bbb' }}>
                {format(new Date(draft.departureTime), 'M月d日')} → {format(new Date(draft.returnTime), 'M月d日')}
              </div>
              <div style={{ fontSize: 11, color: '#888' }}>继续编辑</div>
            </div>

            <div
              style={{
                fontFamily: "'Noto Serif SC', serif",
                fontSize: 22,
                fontWeight: 300,
                color: '#000',
                letterSpacing: '0.04em',
                marginBottom: 4
              }}
            >
              {draft.departure.substring(0, 3)} — {draft.destination}
            </div>

            <div style={{ fontSize: 11, color: '#bbb', marginBottom: 8 }}>{draft.days} 天</div>

            <button
              onClick={(e) => handleDeleteDraft(e, draft.id)}
              style={{
                position: 'absolute',
                top: 16,
                right: 14,
                background: 'none',
                border: 'none',
                fontSize: 14,
                color: '#ccc',
                cursor: 'pointer',
                padding: 4
              }}
              title="删除草稿"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    )
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
            草稿箱
          </div>
          <div className="fj-section-subtitle">所有正在编辑的旅途</div>
        </div>

        <div className="app-scroll" style={{ height: 'calc(100% - 80px)', paddingBottom: 40 }}>
          {drafts.length === 0 ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#ccc', fontSize: 13 }}>
              暂无草稿
            </div>
          ) : (
            <>
              {renderGroup('今天', groups.today)}
              {renderGroup('昨天', groups.yesterday)}
              {renderGroup('前 7 天', groups.week)}
              {renderGroup('更早以前', groups.older)}
            </>
          )}
        </div>
      </div>
    </div>
  )
}