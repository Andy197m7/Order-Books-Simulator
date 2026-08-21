import type { PriceLevel } from '../types'

interface Props {
  bids: PriceLevel[]
  asks: PriceLevel[]
  spread: number | null
  mid_price: number | null
  flashSet: Set<string>
}

function LevelRow({
  level,
  side,
  maxQty,
  flash,
}: {
  level: PriceLevel
  side: 'bid' | 'ask'
  maxQty: number
  flash: boolean
}) {
  const pct = Math.min((level.quantity / maxQty) * 100, 100)
  const bg  = side === 'bid' ? 'rgba(35,134,54,0.25)' : 'rgba(218,54,51,0.25)'
  const fg  = side === 'bid' ? '#3fb950' : '#f85149'

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        padding: '2px 8px',
        fontSize: 13,
        background: flash ? (side === 'bid' ? 'rgba(35,134,54,0.45)' : 'rgba(218,54,51,0.45)') : 'transparent',
        transition: 'background 0.3s',
        position: 'relative',
      }}
    >
      <div
        style={{
          position: 'absolute',
          [side === 'bid' ? 'right' : 'left']: 0,
          top: 0,
          bottom: 0,
          width: `${pct}%`,
          background: bg,
          zIndex: 0,
        }}
      />
      <span style={{ color: fg, zIndex: 1, textAlign: side === 'bid' ? 'left' : 'right' }}>
        {level.price.toFixed(2)}
      </span>
      <span style={{ color: '#8b949e', zIndex: 1, textAlign: side === 'bid' ? 'right' : 'left' }}>
        {level.quantity}
      </span>
    </div>
  )
}

export function OrderBook({ bids, asks, spread, mid_price, flashSet }: Props) {
  const maxBidQty = Math.max(...bids.map(b => b.quantity), 1)
  const maxAskQty = Math.max(...asks.map(a => a.quantity), 1)

  return (
    <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #30363d', fontWeight: 700, fontSize: 13, color: '#8b949e', letterSpacing: 1 }}>
        ORDER BOOK
      </div>

      {/* Asks — reversed so best ask is closest to spread */}
      <div style={{ display: 'flex', flexDirection: 'column-reverse' }}>
        {asks.map(a => (
          <LevelRow
            key={a.price.toFixed(2)}
            level={a}
            side="ask"
            maxQty={maxAskQty}
            flash={flashSet.has(`ask-${a.price}`)}
          />
        ))}
      </div>

      {/* Spread */}
      <div style={{ padding: '4px 8px', textAlign: 'center', fontSize: 11, color: '#8b949e', borderTop: '1px solid #30363d', borderBottom: '1px solid #30363d' }}>
        {mid_price != null ? `Mid ${mid_price.toFixed(2)}` : '—'}
        {spread != null ? `  ·  Spread ${spread.toFixed(2)}` : ''}
      </div>

      {/* Bids */}
      <div>
        {bids.map(b => (
          <LevelRow
            key={b.price.toFixed(2)}
            level={b}
            side="bid"
            maxQty={maxBidQty}
            flash={flashSet.has(`bid-${b.price}`)}
          />
        ))}
      </div>
    </div>
  )
}
