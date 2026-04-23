// ─── Login gate — dark, expanded Path C public summary ───────────────────────

function LoginScreen({ onLogin }) {
  const [pw, setPw]         = React.useState('');
  const [error, setErr]     = React.useState(false);
  const [loading, setLoad]  = React.useState(false);

  const portVal  = portfolioTotal(MOCK.holdings);
  const { ratio } = computeLeverage(portVal, MOCK.heloc.drawn, MOCK.margin.balance);
  const helocPct  = (MOCK.heloc.drawn / MOCK.heloc.limit * 100).toFixed(0);
  const allocByAcct = groupAllocation(MOCK.holdings, 'account');

  function handleSubmit(e) {
    e.preventDefault();
    setLoad(true);
    setTimeout(() => {
      if (pw.length > 0) { onLogin(); }
      else { setErr(true); setLoad(false); }
    }, 600);
  }

  return (
    <div style={{ minHeight:'100vh', background:DS.bg,
      display:'flex', alignItems:'center', justifyContent:'center',
      fontFamily:DS.fontSans, padding:'20px' }}>

      <div style={{ width:540 }}>

        {/* Wordmark */}
        <div style={{ marginBottom:24, textAlign:'center' }}>
          <div style={{ fontFamily:DS.fontMono, fontSize:28, fontWeight:700,
            color:DS.text, letterSpacing:-1 }}>IM</div>
          <div style={{ fontFamily:DS.fontSans, fontSize:13, color:DS.textSub, marginTop:4 }}>
            Investments Monitor · personal</div>
        </div>

        {/* ── Public summary card ────────────────────────────────────────── */}
        <div style={{ background:DS.bgPanel, border:`1px solid ${DS.blueDim}`,
          borderRadius:4, padding:'16px', marginBottom:16,
          borderLeft:`3px solid ${DS.blue}` }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between',
            marginBottom:14 }}>
            <span style={{ fontFamily:DS.fontSans, fontSize:12,
              color:DS.blue, fontWeight:600 }}>☁ Public summary</span>
            <PrivBadge type="cloud"/>
          </div>

          {/* Ratios */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr',
            gap:8, marginBottom:14 }}>
            {[
              ['Leverage ratio',    `${ratio.toFixed(2)}×`,
                ratio >= 2 ? DS.red : ratio >= 1.5 ? DS.amber : DS.green],
              ['HELOC utilization', `${helocPct}%`,  DS.text],
              ['Positions',         `${MOCK.holdings.length}`, DS.text],
            ].map(([lbl,val,col]) => (
              <div key={lbl} style={{ background:DS.bgRaised, borderRadius:3, padding:'10px 12px' }}>
                <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, marginBottom:4 }}>{lbl}</div>
                <div style={{ fontFamily:DS.fontMono, fontSize:18, fontWeight:700, color:col }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Allocation bar */}
          <div style={{ marginBottom:14 }}>
            <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, marginBottom:5 }}>
              Allocation by asset class (proportions)</div>
            <div style={{ height:12, display:'flex', borderRadius:2, overflow:'hidden', gap:1 }}>
              {groupAllocation(MOCK.holdings, 'assetClass').map(g => (
                <div key={g.id} title={`${g.label} ${g.pct.toFixed(1)}%`}
                  style={{ flex:g.pct, background:g.color, opacity:0.7, minWidth:g.pct>2?3:0 }}/>
              ))}
            </div>
            <div style={{ display:'flex', gap:10, marginTop:4, flexWrap:'wrap' }}>
              {groupAllocation(MOCK.holdings, 'assetClass').map(g => (
                <span key={g.id} style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint,
                  display:'flex', alignItems:'center', gap:4 }}>
                  <span style={{ width:6, height:6, background:g.color, borderRadius:1,
                    display:'inline-block', opacity:0.8 }}/>
                  {g.label} {g.pct.toFixed(0)}%
                </span>
              ))}
            </div>
          </div>

          {/* Holdings tickers + prices — as table */}
          <div style={{ marginBottom:14 }}>
            <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, marginBottom:6 }}>
              Holdings — tickers &amp; market prices</div>
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead>
                <tr>
                  {['Ticker','Price (CAD)','Today'].map(h => (
                    <th key={h} style={{ padding:'4px 8px',
                      textAlign: h==='Ticker' ? 'left' : 'right',
                      fontFamily:DS.fontSans, fontSize:9, color:DS.textFaint,
                      fontWeight:600, letterSpacing:0.4,
                      borderBottom:`1px solid ${DS.border}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MOCK.holdings.map((h, i) => (
                  <tr key={h.ticker} style={{ background:i%2?DS.bgRaised:'transparent' }}>
                    <td style={{ padding:'5px 8px', fontFamily:DS.fontMono,
                      fontSize:12, fontWeight:700, color:DS.text,
                      borderBottom:`1px solid ${DS.border}` }}>
                      {h.ticker}
                      {h.currency==='USD' && (
                        <span style={{ marginLeft:4, fontSize:8, color:DS.amber,
                          border:`1px solid ${DS.amber}`, borderRadius:2,
                          padding:'0 2px' }}>USD</span>
                      )}
                    </td>
                    <td style={{ padding:'5px 8px', textAlign:'right',
                      fontFamily:DS.fontMono, fontSize:12, color:DS.text,
                      borderBottom:`1px solid ${DS.border}` }}>
                      ${h.priceCAD.toFixed(2)}
                    </td>
                    <td style={{ padding:'5px 8px', textAlign:'right',
                      fontFamily:DS.fontMono, fontSize:12,
                      color: h.changePct>=0 ? DS.green : DS.red,
                      borderBottom:`1px solid ${DS.border}` }}>
                      {h.changePct>=0?'▲':'▼'} {Math.abs(h.changePct).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Watchlist */}
          <div>
            <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, marginBottom:6 }}>
              Watchlist — targets</div>
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead>
                <tr>
                  {['Ticker','Current','Today','Target','Gap'].map(h => (
                    <th key={h} style={{ padding:'4px 8px',
                      textAlign: h==='Ticker' ? 'left' : 'right',
                      fontFamily:DS.fontSans, fontSize:9, color:DS.textFaint,
                      fontWeight:600, letterSpacing:0.4,
                      borderBottom:`1px solid ${DS.border}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MOCK.watchlist.map((w, i) => {
                  const gap = ((w.price - w.target) / w.target * 100);
                  return (
                    <tr key={w.ticker} style={{ background:i%2?DS.bgRaised:'transparent' }}>
                      <td style={{ padding:'5px 8px', fontFamily:DS.fontMono,
                        fontSize:12, fontWeight:700, color:DS.text,
                        borderBottom:`1px solid ${DS.border}` }}>
                        {w.ticker}
                        {w.currency==='USD' && (
                          <span style={{ marginLeft:4, fontSize:8, color:DS.amber,
                            border:`1px solid ${DS.amber}`, borderRadius:2, padding:'0 2px' }}>USD</span>
                        )}
                      </td>
                      <td style={{ padding:'5px 8px', textAlign:'right',
                        fontFamily:DS.fontMono, fontSize:12, color:DS.textSub,
                        borderBottom:`1px solid ${DS.border}` }}>${w.price.toFixed(2)}</td>
                      <td style={{ padding:'5px 8px', textAlign:'right',
                        fontFamily:DS.fontMono, fontSize:12,
                        color: w.changePct>=0 ? DS.green : DS.red,
                        borderBottom:`1px solid ${DS.border}` }}>
                        {w.changePct>=0?'▲':'▼'} {Math.abs(w.changePct).toFixed(2)}%
                      </td>
                      <td style={{ padding:'5px 8px', textAlign:'right',
                        fontFamily:DS.fontMono, fontSize:12, color:DS.blue,
                        borderBottom:`1px solid ${DS.border}` }}>${w.target.toFixed(2)}</td>
                      <td style={{ padding:'5px 8px', textAlign:'right',
                        fontFamily:DS.fontMono, fontSize:12,
                        color: gap <= 0 ? DS.green : DS.amber,
                        borderBottom:`1px solid ${DS.border}` }}>
                        {gap <= 0 ? '▲ At' : `▼ ${Math.abs(gap).toFixed(1)}%`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop:10, fontFamily:DS.fontSans, fontSize:10,
            color:DS.textFaint, fontStyle:'italic' }}>
            Path C: no dollar totals, quantities or ACB in public view
          </div>
        </div>

        {/* Login form */}
        <div style={{ background:DS.bgPanel, border:`1px solid ${DS.border}`,
          borderRadius:4, padding:'20px' }}>
          <div style={{ fontFamily:DS.fontSans, fontSize:14, color:DS.text,
            fontWeight:600, marginBottom:3 }}>Unlock full view</div>
          <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub, marginBottom:16 }}>
            Holdings G/L, net worth and quantities are local-only.
          </div>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom:12 }}>
              <label style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub,
                display:'block', marginBottom:5 }}>Password</label>
              <input type="password" value={pw}
                onChange={e => { setPw(e.target.value); setErr(false); }}
                placeholder="Enter password" autoFocus
                style={{ width:'100%', padding:'9px 12px', background:DS.bgRaised,
                  border:`1px solid ${error ? DS.red : DS.border}`,
                  borderRadius:3, color:DS.text, fontFamily:DS.fontMono,
                  fontSize:14, outline:'none', boxSizing:'border-box' }}/>
              {error && <div style={{ fontFamily:DS.fontSans, fontSize:11,
                color:DS.red, marginTop:4 }}>Incorrect password</div>}
            </div>
            <button type="submit" disabled={loading} style={{
              width:'100%', padding:'10px', background: loading ? DS.bgRaised : DS.blue,
              border:'none', borderRadius:3, cursor: loading ? 'default' : 'pointer',
              fontFamily:DS.fontSans, fontSize:14, fontWeight:600,
              color: loading ? DS.textSub : '#fff' }}>
              {loading ? 'Unlocking…' : 'Unlock →'}
            </button>
          </form>
          <div style={{ marginTop:12, fontFamily:DS.fontSans, fontSize:10,
            color:DS.textFaint, textAlign:'center', fontStyle:'italic' }}>
            Demo: type any password to unlock
          </div>
        </div>

      </div>
    </div>
  );
}

Object.assign(window, { LoginScreen });
