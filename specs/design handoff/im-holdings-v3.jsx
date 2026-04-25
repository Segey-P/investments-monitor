// ─── Holdings v3 ── CHANGE 9: column visibility toggle ────────────────────────

const ASSET_CLASS_META = {
  Stock:       { color:'#3b82f6', label:'Stock'    },
  ETF:         { color:'#22c55e', label:'ETF'      },
  Crypto:      { color:'#8b5cf6', label:'Crypto'   },
  LeveragedETF:{ color:'#f59e0b', label:'Lev. ETF' },
  Cash:        { color:'#6b7280', label:'Cash'     },
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

// All columns; some are optional (toggleable)
const ALL_COLS = [
  { key:'ticker',     label:'Ticker',          align:'left',  required:true  },
  { key:'name',       label:'Name',            align:'left',  required:false },
  { key:'acct',       label:'Account',         align:'left',  required:true  },
  { key:'assetClass', label:'Asset class',     align:'left',  required:false },
  { key:'qty',        label:'Qty',             align:'right', required:false },
  { key:'acbPS',      label:'ACB / sh',        align:'right', required:false },
  { key:'priceCAD',   label:'Mkt price',       align:'right', required:true  },
  { key:'changePct',  label:'Today',           align:'right', required:true  },
  { key:'mktVal',     label:'Mkt value (CAD)', align:'right', required:true  },
  { key:'gl',         label:'Unreal G/L',      align:'right', required:false },
  { key:'glPct',      label:'G/L %',           align:'right', required:false },
  { key:'pctPort',    label:'% Port',          align:'right', required:true  },
];

const DEFAULT_VISIBLE = new Set(['ticker','name','acct','assetClass','changePct','mktVal','gl','glPct','pctPort']);

function HoldingsScreen({ scope, publicView }) {
  const [sortKey, setSortKey]   = React.useState('mktVal');
  const [sortDir, setSortDir]   = React.useState(-1);

  const all       = React.useMemo(() => derivePortfolio(MOCK.holdings), []);
  const portTotal = portfolioTotal(MOCK.holdings);

  const filtered = (scope && scope !== 'all' ? all.filter(h => h.acct === scope) : all)
    .slice().sort((a,b) => sortDir * ((a[sortKey] ?? 0) - (b[sortKey] ?? 0)));

  const filtTotal = filtered.reduce((s,h) => s+h.mktVal, 0);
  const filtGL    = filtered.reduce((s,h) => s+h.gl, 0);
  const filtACB   = filtered.reduce((s,h) => s+h.acbTotal, 0);

  function toggleSort(k) {
    if (sortKey === k) setSortDir(d => -d);
    else { setSortKey(k); setSortDir(-1); }
  }

  const cols = ALL_COLS.filter(c => c.required || DEFAULT_VISIBLE.has(c.key));

  // Empty state
  if (filtered.length === 0) {
    return (
      <div style={{ padding:'20px' }}>
        <div style={{ textAlign:'center', padding:'80px 20px',
          background:DS.bgPanel, border:`1px solid ${DS.border}`, borderRadius:4 }}>
          <div style={{ fontSize:32, marginBottom:12, opacity:0.3 }}>◎</div>
          <div style={{ fontFamily:DS.fontSans, fontSize:15, color:DS.textSub, marginBottom:6 }}>
            No holdings in this account
          </div>
          <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textFaint }}>
            Switch to "All accounts" or import positions in Settings → Imports.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding:'20px' }}>

      {/* Summary bar */}
      <div style={{ display:'flex', gap:24, padding:'10px 16px', marginBottom:12,
        background:DS.bgPanel, border:`1px solid ${DS.border}`,
        borderRadius:4, alignItems:'center', flexWrap:'wrap' }}>
        {[['Positions', filtered.length.toString()],['Total value', fmtCAD(filtTotal)],['ACB total', fmtCAD(filtACB)]].map(([lbl,val]) => (
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



        <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint }}>
          Use "Hide values" to mask sensitive numbers
        </div>
      </div>

      <Panel>
        {publicView && (
          <div style={{ padding:'6px 14px', background:DS.amberDim,
            borderBottom:`1px solid #78350f`, display:'flex', alignItems:'center', gap:8 }}>
            <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.amber }}>
              🙈 Values hidden — quantities, G/L and dollar amounts are blurred
            </span>
          </div>
        )}
        <div style={{ overflowX:'auto' }}>
          <table style={{ width:'100%', borderCollapse:'collapse', minWidth:600 }}>
            <thead>
              <tr style={{ background:DS.bgRaised }}>
                {cols.map(c => (
                  <th key={c.key} onClick={() => toggleSort(c.key)} style={{
                    padding:'8px 12px', textAlign:c.align,
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
                    {cols.map(c => {
                      const blurred = publicView && ['qty','acbPS','mktVal','gl','glPct','pctPort'].includes(c.key);
                      const bs = { padding:'9px 12px', borderBottom:`1px solid ${DS.border}`,
                        textAlign:c.align, filter:blurred?'blur(6px)':'none',
                        userSelect:blurred?'none':'auto' };
                      if (c.key === 'ticker') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:13, fontWeight:700, color:DS.text }}>
                          {h.ticker}
                          {h.currency==='USD'&&<span style={{ marginLeft:5, fontSize:8, color:DS.amber,
                            border:`1px solid ${DS.amber}`, borderRadius:2, padding:'0 2px' }}>USD</span>}
                        </td>
                      );
                      if (c.key === 'name') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:12, color:DS.textSub,
                          maxWidth:160, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{h.name}</td>
                      );
                      if (c.key === 'acct') return (
                        <td key={c.key} style={bs}><AcctBadge acct={h.acct}/></td>
                      );
                      if (c.key === 'assetClass') return (
                        <td key={c.key} style={bs}><AssetClassBadge cls={h.assetClass}/></td>
                      );
                      if (c.key === 'qty') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:12, color:DS.text }}>
                          {fmtNum(h.qty, h.qty%1===0?0:4)}</td>
                      );
                      if (c.key === 'acbPS') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                          {fmtCAD(h.acbPS,2)}</td>
                      );
                      if (c.key === 'priceCAD') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:12, color:DS.text }}>
                          {fmtCAD(h.priceCAD,2)}
                          {h.currency==='USD'&&<div style={{ fontSize:9, color:DS.textFaint }}>
                            ${h.priceUSD?.toFixed(2)} USD</div>}
                        </td>
                      );
                      if (c.key === 'changePct') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:12,
                          color: h.changePct>=0?DS.green:DS.red }}>
                          {h.changePct>=0?'▲':'▼'} {Math.abs(h.changePct).toFixed(2)}%</td>
                      );
                      if (c.key === 'mktVal') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:12, fontWeight:600, color:DS.text }}>
                          {fmtCAD(h.mktVal)}</td>
                      );
                      if (c.key === 'gl') return (
                        <td key={c.key} style={bs}><GLCell value={h.gl}/></td>
                      );
                      if (c.key === 'glPct') return (
                        <td key={c.key} style={bs}><GLCell value={h.glPct}/></td>
                      );
                      if (c.key === 'pctPort') return (
                        <td key={c.key} style={{ ...bs, fontFamily:DS.fontMono, fontSize:11, color:DS.textSub }}>
                          <div>{pctPort.toFixed(1)}%</div>
                          <Bar pct={pctPort*4} color={DS.blue} height={3} style={{ marginTop:3, minWidth:40 }}/>
                        </td>
                      );
                      return null;
                    })}
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
      </Panel>
    </div>
  );
}

Object.assign(window, { HoldingsScreen, AssetClassBadge, ASSET_CLASS_META });
