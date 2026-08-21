import { useState } from 'react'

type Side = 'buy' | 'sell'
type OrderType = 'limit' | 'market' | 'ioc' | 'fok'

interface SubmitResult {
  order_id: string
  status: string
}

const API = ''

export function OrderEntry() {
  const [side, setSide]           = useState<Side>('buy')
  const [orderType, setOrderType] = useState<OrderType>('limit')
  const [price, setPrice]         = useState('')
  const [quantity, setQuantity]   = useState('')
  const [result, setResult]       = useState<string | null>(null)
  const [loading, setLoading]     = useState(false)

  const needsPrice = orderType === 'limit' || orderType === 'ioc' || orderType === 'fok'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const body: Record<string, unknown> = {
        side,
        order_type: orderType,
        quantity: parseInt(quantity, 10),
      }
      if (needsPrice) body.price = parseFloat(price)

      const res = await fetch(`${API}/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data: SubmitResult = await res.json()
      setResult(`Submitted · ${data.order_id.slice(0, 8)}…`)
    } catch (err) {
      setResult('error')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: 6,
    color: '#e6edf3',
    padding: '6px 10px',
    fontSize: 13,
    width: '100%',
    outline: 'none',
  }

  const btnBase: React.CSSProperties = {
    padding: '6px 16px',
    borderRadius: 6,
    border: 'none',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 600,
  }

  return (
    <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #30363d', fontWeight: 700, fontSize: 13, color: '#8b949e', letterSpacing: 1 }}>
        ORDER ENTRY
      </div>
      <form onSubmit={handleSubmit} style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
        {/* Side */}
        <div style={{ display: 'flex', gap: 8 }}>
          {(['buy', 'sell'] as Side[]).map(s => (
            <button
              key={s}
              type="button"
              onClick={() => setSide(s)}
              style={{
                ...btnBase,
                flex: 1,
                background: side === s
                  ? s === 'buy' ? '#238636' : '#da3633'
                  : '#21262d',
                color: '#e6edf3',
              }}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Order type */}
        <div style={{ display: 'flex', gap: 8 }}>
          {(['limit', 'market', 'ioc', 'fok'] as OrderType[]).map(t => (
            <button
              key={t}
              type="button"
              onClick={() => setOrderType(t)}
              style={{
                ...btnBase,
                flex: 1,
                padding: '5px 4px',
                fontSize: 11,
                background: orderType === t ? '#388bfd26' : '#21262d',
                color: orderType === t ? '#58a6ff' : '#8b949e',
                border: orderType === t ? '1px solid #388bfd' : '1px solid #30363d',
              }}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Price */}
        {needsPrice && (
          <div>
            <label style={{ fontSize: 11, color: '#8b949e', marginBottom: 4, display: 'block' }}>PRICE</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={price}
              onChange={e => setPrice(e.target.value)}
              required={needsPrice}
              style={inputStyle}
              placeholder="0.00"
            />
          </div>
        )}

        {/* Quantity */}
        <div>
          <label style={{ fontSize: 11, color: '#8b949e', marginBottom: 4, display: 'block' }}>QUANTITY</label>
          <input
            type="number"
            min="1"
            step="1"
            value={quantity}
            onChange={e => setQuantity(e.target.value)}
            required
            style={inputStyle}
            placeholder="100"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            ...btnBase,
            background: side === 'buy' ? '#238636' : '#da3633',
            color: '#fff',
            marginTop: 4,
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Submitting…' : `${side === 'buy' ? 'Buy' : 'Sell'} · ${orderType.toUpperCase()}`}
        </button>

        {result && (
          <div style={{ fontSize: 11, color: result === 'error' ? '#f85149' : '#3fb950', textAlign: 'center' }}>
            {result === 'error' ? 'Error submitting order' : result}
          </div>
        )}
      </form>
    </div>
  )
}
