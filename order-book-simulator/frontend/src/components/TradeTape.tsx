import { useEffect, useRef } from 'react'
import type { TradeEvent } from '../types'

interface Props {
  trades: TradeEvent[]
}

export function TradeTape({ trades }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [trades.length])

  return (
    <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden', display: 'flex', flexDirection: 'column', height: 340 }}>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #30363d', fontWeight: 700, fontSize: 13, color: '#8b949e', letterSpacing: 1, flexShrink: 0 }}>
        TIME &amp; SALES
      </div>
      <div style={{ overflowY: 'auto', flex: 1, padding: '4px 0' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '80px 70px 60px', padding: '2px 12px', fontSize: 11, color: '#484f58', borderBottom: '1px solid #21262d', marginBottom: 4 }}>
          <span>PRICE</span><span>QTY</span><span>SIDE</span>
        </div>
        {trades.slice(-200).map(t => (
          <div
            key={t.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '80px 70px 60px',
              padding: '2px 12px',
              fontSize: 12,
            }}
          >
            <span style={{ color: t.aggressor_side === 'buy' ? '#3fb950' : '#f85149', fontWeight: 600 }}>
              {t.price.toFixed(2)}
            </span>
            <span style={{ color: '#c9d1d9' }}>{t.quantity}</span>
            <span style={{ color: t.aggressor_side === 'buy' ? '#3fb950' : '#f85149', fontSize: 11 }}>
              {t.aggressor_side === 'buy' ? 'BUY' : 'SELL'}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
