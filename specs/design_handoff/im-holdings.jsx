// ─── Holdings screen — dark, asset class column, summary at top, no filter bar ─

const ASSET_CLASS_META = {
  Stock:       { color:'#3b82f6', label:'Stock'     },
  ETF:         { color:'#22c55e', label:'ETF'       },
  Crypto:      { color:'#8b5cf6', label:'Crypto'    },
  LeveragedETF:{ color:'#f59e0b', label:'Lev. ETF'  },
  Cash:        { color:'#6b7280', label:'Cash'      },
};

function AssetClassBadge({ cls }) {
  const m = ASSET_CLASS_META[cls] || { color:'#666', label:cls };
  return (
    <span style={{ display:'inline-block', padding:'1px 6px',
      border:`1px solid ${m.color}`, borderRadius:3, fontSize:10,
      fontFamily:DS.fontMono, color:m.color, background:`${m.color}18`,
      whiteSpace:'nowrap' }}>{m.label}</span>
  );
}

function HoldingsScreen({ scope, publicView }) {
  const [sortKey, setSortKey] = React.useState('mktVal');
  const [sortDir, setSortDir] = React.useState(-1);

  const all       = React.useMemo(() => derivePortfolio(MOCK.holdings), []);
  const portTotal = portfolioTotal(MOCK.holdings);

  // Filter by scope strip (no in-screen filter bar)
  const filtered = (scope && scope !== 'all' ? all.filter(h => h.acct === scope) : all)
    .slice().sort((a,b) => sortDir * ((a[sortKey] ?? 0) - (b[sortKey] ?? 0)));

  const filtTotal = filtered.reduce((s,h) => s+h.mktVal, 0);
  const filtGL    = filtered.reduce((s,h) => s+h.gl, 0);
  const filtACB   = filtered.reduce((s,h) => s+h.acbTotal, 0);

  function toggleSort(k) {
    if (sortKey === k) setSortDir(d => -d);
    else { setSortKey(k); setSortDir(-1); }
  }

  const COL = [
    { key:'ticker',    label:'Ticker',          align:'left'  },
    { key:'name',      label:'Name',            align:'left'  },
    { key:'acct',      label:'Account',         align:'left'  },
    { key:'assetClass',label:'Asset class',     align:'left'  },
    { key:'qty',       label:'Qty',             align:'right' },
    { key:'acbPS',     label:'ACB / sh',        align:'right' },
    { key:'priceCAD',  label:'Mkt price',       align:'right' },
    { key:'changePct', label:'Today',           align:'right' },
    { key:'mktVal',    label:'Mkt value (CAD)', align:'right' },
    { key:'gl',        label:'Unreal G/L',      align:'right' },
    { key:'glPct',     label:'G/L %',           align:'right' },
    { key:'pctPort',   label:'% Port',          align:'right' },
  ];

  return (
    <div style={{ padding:'20px' }}>

      {/* Summary bar — top, before table */}
      <div style={{ display:'flex', gap:24, padding:'10px 16px', marginBottom:12,
        background:DS.bgPanel, border:`1px solid ${DS.border}`,
        borderRadius:4, alignItems:'center', flexWrap:'wrap' }}>
        {[
          ['Positions', filtered.length.toString()],
          ['Total value', fmtCAD(filtTotal)],
          ['ACB total', fmtCAD(filtACB)],
        ].map(([lbl,val]) => (
          <div key={lbl}>
            <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textSub }}>{lbl}</div>
            <div style={{ fontFamily:DS.fontMono, fontSize:14, color:DS.text,
              filter:publicView?'blur(5px)':'none' }}>{val}</div>
          </div>
        ))}
        <div>
          <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textSub }}>Unrealized G/L</div>
          <div style={{ filter:publicView?'blur(5px)':'none' }}>
            <GLCell value={filtGL} pct={filtGL/filtACB*100}/>
          </div>
        </div>
        <div style={{ marginLeft:'auto', display:'flex', gap:8, alignItems:'center' }}>
          <PrivBadge type="local"/>
          <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint }}>
            All dollar values are local-only
          </span>
        </div>
      </div>

      <Panel>
        <div style={{ position:'relative' }}>
          {publicView && (
            <div style={{ padding:'6px 14px', background:DS.amberDim,
              borderBottom:`1px solid #78350f`, display:'flex', alignItems:'center', gap:8 }}>
              <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.amber }}>
                🔒 Public view — tickers and prices visible · quantities, values and G/L are hidden
              </span>
            </div>
          )}

          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'collapse', minWidth:1100 }}>
              <thead>
                <tr style={{ background:DS.bgRaised }}>
                  {COL.map(c => (
                    <th key={c.key} onClick={() => toggleSort(c.key)}
                      style={{ padding:'8px 12px', textAlign:c.align,
                        fontFamily:DS.fontSans, fontSize:10, fontWeight:600,
                        color: sortKey===c.key ? DS.blue : DS.textSub,
                        borderBottom:`1px solid ${DS.border}`,
                        cursor:'pointer', letterSpacing:0.4,
                        whiteSpace:'nowrap', userSelect:'none' }}>
                      {c.label} {sortKey===c.key?(sortDir===-1?'▼':'▲'):''}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((h,i) => {
                  const pctPort = h.mktVal/portTotal*100;
                  return (
                    <tr key={h.ticker}
                      style={{ background:i%2?DS.bgRaised:'transparent', transition:'background 0.1s' }}
                      onMouseEnter={e=>e.currentTarget.style.background=DS.bgHover}
                      onMouseLeave={e=>e.currentTarget.style.background=i%2?DS.bgRaised:'transparent'}>
                      <td style={{ padding:'9px 12px', borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:13, fontWeight:700, color:DS.text }}>
                        {h.ticker}
                        {h.currency==='USD'&&<span style={{ marginLeft:5, fontSize:8,
                          color:DS.amber, border:`1px solid ${DS.amber}`,
                          borderRadius:2, padding:'0 2px' }}>USD</span>}
                      </td>
                      <td style={{ padding:'9px 12px', borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:12, color:DS.textSub,
                        maxWidth:160, whiteSpace:'nowrap', overflow:'hidden',
                        textOverflow:'ellipsis' }}>{h.name}</td>
                      <td style={{ padding:'9px 12px', borderBottom:`1px solid ${DS.border}` }}>
                        <AcctBadge acct={h.acct}/></td>
                      <td style={{ padding:'9px 12px', borderBottom:`1px solid ${DS.border}` }}>
                        <AssetClassBadge cls={h.assetClass}/></td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:12, color:DS.text,
                        filter:publicView?'blur(6px)':'none', userSelect:publicView?'none':'auto' }}>
                        {fmtNum(h.qty, h.qty%1===0?0:4)}</td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:12, color:DS.textSub,
                        filter:publicView?'blur(6px)':'none', userSelect:publicView?'none':'auto' }}>
                        {fmtCAD(h.acbPS,2)}</td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:12, color:DS.text }}>
                        {fmtCAD(h.priceCAD,2)}
                        {h.currency==='USD'&&<div style={{ fontSize:9, color:DS.textFaint }}>
                          ${h.priceUSD?.toFixed(2)} USD</div>}
                      </td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:12,
                        color: h.changePct>=0?DS.green:DS.red }}>
                        {h.changePct>=0?'▲':'▼'} {Math.abs(h.changePct).toFixed(2)}%
                      </td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:12, fontWeight:600, color:DS.text,
                        filter:publicView?'blur(6px)':'none', userSelect:publicView?'none':'auto' }}>
                        {fmtCAD(h.mktVal)}</td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        filter:publicView?'blur(6px)':'none', userSelect:publicView?'none':'auto' }}>
                        <GLCell value={h.gl}/></td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        filter:publicView?'blur(6px)':'none', userSelect:publicView?'none':'auto' }}>
                        <GLCell value={h.glPct}/></td>
                      <td style={{ padding:'9px 12px', textAlign:'right',
                        borderBottom:`1px solid ${DS.border}`,
                        fontFamily:DS.fontMono, fontSize:11, color:DS.textSub,
                        filter:publicView?'blur(6px)':'none', userSelect:publicView?'none':'auto' }}>
                        <div>{pctPort.toFixed(1)}%</div>
                        <Bar pct={pctPort*4} color={DS.blue} height={3}
                          style={{ marginTop:3, minWidth:40 }}/>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div style={{ padding:'8px 14px', background:DS.bgRaised,
            borderTop:`1px solid ${DS.border}`,
            fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, fontStyle:'italic' }}>
            USD converted at {FX_USD_CAD} (BOC) · click headers to sort
          </div>
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, { HoldingsScreen, AssetClassBadge, ASSET_CLASS_META });
