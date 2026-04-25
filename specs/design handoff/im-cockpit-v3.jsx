// ─── Cockpit v3 ── CHANGE 1: KPI strip reworked ──────────────────────────────
// Removed duplicate "Net Worth" card (already has its own screen).
// Added "Today's Δ" (portfolio daily P&L) and "Biggest mover" instead.

function AllocationWidget({ holdings }) {
  const DIMS = [
    { id:'assetClass', label:'Asset class' },
    { id:'country',    label:'Country'     },
    { id:'currency',   label:'Currency'    },
  ];
  const [dim, setDim] = React.useState('assetClass');
  const groups = groupAllocation(holdings, dim);
  return (
    <Panel>
      <div style={{ padding:'10px 14px', borderBottom:`1px solid ${DS.border}`,
        display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <span style={{ fontFamily:DS.fontSans, fontSize:11, fontWeight:600,
          color:DS.textSub, letterSpacing:0.8, textTransform:'uppercase' }}>Allocation</span>
        <div style={{ display:'flex', alignItems:'center', gap:4 }}>
          {DIMS.map(d => (
            <button key={d.id} onClick={() => setDim(d.id)} style={{
              padding:'2px 9px', border:`1px solid ${dim===d.id ? DS.blue : DS.border}`,
              borderRadius:10, background: dim===d.id ? DS.blueDim : 'transparent',
              fontFamily:DS.fontSans, fontSize:11,
              color: dim===d.id ? DS.blue : DS.textFaint,
              cursor:'pointer', whiteSpace:'nowrap' }}>{d.label}</button>
          ))}
        </div>
      </div>
      <div style={{ padding:'12px 14px' }}>
        <div style={{ height:16, display:'flex', borderRadius:3, overflow:'hidden', marginBottom:10, gap:1 }}>
          {groups.map(g => (
            <div key={g.id} title={`${g.label}: ${g.pct.toFixed(1)}%`}
              style={{ flex:g.pct, minWidth:g.pct>1?2:0, background:g.color, opacity:0.75 }}/>
          ))}
        </div>
        {groups.map(g => (
          <div key={g.id} style={{ display:'flex', alignItems:'center',
            justifyContent:'space-between', padding:'4px 0', borderBottom:`1px solid ${DS.border}` }}>
            <div style={{ display:'flex', alignItems:'center', gap:8 }}>
              <div style={{ width:7, height:7, borderRadius:2, background:g.color, opacity:0.85, flexShrink:0 }}/>
              <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>{g.label}</span>
            </div>
            <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.text }}>{g.pct.toFixed(1)}%</span>
          </div>
        ))}
        <div style={{ marginTop:8, fontFamily:DS.fontSans, fontSize:10,
          color:DS.textFaint, fontStyle:'italic' }}>
          Proportions only · no dollar amounts in cloud view
        </div>
      </div>
    </Panel>
  );
}

// ── Mini what-if panel (Cockpit) ──────────────────────────────────────────────
function MiniWhatIf({ portVal, ratio: baseRatio }) {
  const [draw,     setDraw]     = React.useState(0);
  const [drawdown, setDrawdown] = React.useState(0);
  const available = Math.max(0, MOCK.heloc.limit - MOCK.heloc.drawn);
  const stressed  = computeLeverage(portVal * (1 - drawdown/100), MOCK.heloc.drawn + draw, MOCK.margin.balance);
  function ratioColor(r) { return r<1.5?DS.green:r<2.0?DS.amber:DS.red; }
  const hasWhatIf = draw > 0 || drawdown > 0;

  return (
    <div style={{ padding:'12px 14px' }}>
      <div style={{ marginBottom:12 }}>
        <div style={{ display:'flex', justifyContent:'space-between', marginBottom:4 }}>
          <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>Draw HELOC</span>
          <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.text }}>{draw>0?`+${fmtCAD(draw)}`:'—'}</span>
        </div>
        <input type="range" min={0} max={available} step={500} value={draw}
          onChange={e=>setDraw(+e.target.value)}
          style={{ width:'100%', accentColor:DS.blue }}/>
      </div>

      <div style={{ marginBottom:14 }}>
        <div style={{ display:'flex', justifyContent:'space-between', marginBottom:4 }}>
          <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>If markets fall</span>
          <span style={{ fontFamily:DS.fontMono, fontSize:12,
            color: drawdown===0?DS.text:drawdown<15?DS.amber:DS.red }}>
            {drawdown===0?'—':`−${drawdown}%`}
          </span>
        </div>
        <input type="range" min={0} max={50} step={1} value={drawdown}
          onChange={e=>setDrawdown(+e.target.value)}
          style={{ width:'100%', accentColor:DS.red }}/>
      </div>

      <div style={{ padding:'10px 12px', borderRadius:3,
        background: ratioColor(stressed.ratio)===DS.green?DS.greenDim
          :ratioColor(stressed.ratio)===DS.amber?DS.amberDim:DS.redDim,
        border:`1px solid ${ratioColor(stressed.ratio)}44` }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline' }}>
          <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>
            {hasWhatIf?'Stressed ratio':'Current ratio'}</span>
          <span style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700,
            color:ratioColor(stressed.ratio) }}>{stressed.ratio.toFixed(2)}×</span>
        </div>
        {hasWhatIf && (
          <div style={{ fontFamily:DS.fontSans, fontSize:10, color:ratioColor(stressed.ratio), marginTop:4 }}>
            {stressed.ratio > baseRatio ? '▲' : '▼'} {Math.abs(stressed.ratio-baseRatio).toFixed(2)}× vs current {baseRatio.toFixed(2)}×
          </div>
        )}
      </div>
      {hasWhatIf && (
        <button onClick={()=>{setDraw(0);setDrawdown(0);}} style={{ marginTop:8,
          padding:'4px 12px', background:'transparent', border:`1px solid ${DS.border}`,
          borderRadius:3, cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>
          Reset
        </button>
      )}
    </div>
  );
}

function CockpitScreen({ publicView, setScreen }) {
  const holdings  = React.useMemo(() => derivePortfolio(MOCK.holdings), []);
  const portTotal = portfolioTotal(MOCK.holdings);
  const { totalBorrowed, ratio } = computeLeverage(portTotal, MOCK.heloc.drawn, MOCK.margin.balance);
  const totalGL  = holdings.reduce((s,h) => s+h.gl, 0);
  const totalACB = holdings.reduce((s,h) => s+h.acbTotal, 0);

  // Today's dollar change across all positions
  const todayDelta = holdings.reduce((s,h) => s + (h.mktVal * h.changePct / 100), 0);

  // Biggest mover by abs % today
  const biggestMover = [...holdings].sort((a,b) =>
    Math.abs(b.changePct) - Math.abs(a.changePct))[0];

  function ratioColor(r) { return r<1.5?DS.green:r<2.0?DS.amber:DS.red; }

  function GaugeSparkline({ r, color }) {
    const clipped = Math.min(Math.max(r,1),3);
    const a   = ((clipped-1)/2)*180;
    const rad = (a-180)*Math.PI/180;
    const [cx,cy,gr] = [40,36,28];
    return (
      <svg width={80} height={42} viewBox="0 0 80 42">
        <defs>
          <linearGradient id="g2" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%"   stopColor={DS.green}/>
            <stop offset="50%"  stopColor={DS.amber}/>
            <stop offset="100%" stopColor={DS.red}/>
          </linearGradient>
        </defs>
        <path d="M10,36 A30,30 0 0,1 70,36" fill="none" stroke="#2a2a2a" strokeWidth={8} strokeLinecap="round"/>
        <path d="M10,36 A30,30 0 0,1 70,36" fill="none" stroke="url(#g2)" strokeWidth={8} strokeLinecap="round" opacity={0.4}/>
        <line x1={cx} y1={cy} x2={cx+gr*Math.cos(rad)} y2={cy+gr*Math.sin(rad)} stroke={color} strokeWidth={2}/>
        <circle cx={cx} cy={cy} r={3} fill={color}/>
        <text x={14} y={40} fontSize="7" fontFamily="DM Sans" fill={DS.green}>safe</text>
        <text x={66} y={40} fontSize="7" fontFamily="DM Sans" fill={DS.red} textAnchor="end">high</text>
      </svg>
    );
  }

  return (
    <div style={{ padding:'20px', display:'grid', gridTemplateColumns:'1fr', gap:12 }}>

      {/* CHANGE 1: KPI strip */}
      <ChangeMarker id={1} style={{ gridColumn:'1/-1' }}>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10 }}>
          {/* Portfolio value */}
          <KPICard label="Portfolio value"
            value={fmtCAD(portTotal)}
            sub={`${holdings.length} positions`} blurred={publicView}/>

          {/* Today's Δ — new */}
          <div style={{ background:DS.bgRaised, border:`1px solid ${DS.border}`, borderRadius:4,
            padding:'12px 14px',
            borderTop:`2px solid ${todayDelta>=0 ? DS.green : DS.red}` }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4 }}>
              <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>Today's Δ</span>
            </div>
            <div style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700, lineHeight:1, marginBottom:4,
              color: todayDelta>=0 ? DS.green : DS.red,
              filter: publicView ? 'blur(6px)' : 'none', userSelect: publicView ? 'none' : 'auto' }}>
              {todayDelta>=0?'+':''}{fmtCAD(todayDelta)}
            </div>
            <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>
              {publicView ? 'local-only' : fmtPct(todayDelta/portTotal*100) + ' on portfolio'}
            </div>
          </div>

          {/* Biggest mover — new */}
          <div style={{ background:DS.bgRaised, border:`1px solid ${DS.border}`, borderRadius:4,
            padding:'12px 14px',
            borderTop:`2px solid ${biggestMover?.changePct>=0 ? DS.green : DS.red}` }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4 }}>
              <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>Biggest mover</span>
            </div>
            <div style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700, lineHeight:1, marginBottom:4,
              color: biggestMover?.changePct>=0 ? DS.green : DS.red }}>
              {biggestMover?.ticker}
            </div>
            <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>
              {biggestMover?.changePct>=0?'▲':'▼'} {Math.abs(biggestMover?.changePct).toFixed(2)}% today
            </div>
          </div>

          {/* Leverage */}
          <div style={{ background:DS.bgRaised, border:`1px solid ${DS.border}`,
            borderRadius:4, padding:'12px 14px',
            borderTop:`2px solid ${ratioColor(ratio)}` }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4 }}>
              <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>Leverage ratio</span>
            </div>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <div>
                <div style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700,
                  color:ratioColor(ratio), lineHeight:1 }}>{ratio.toFixed(2)}×</div>
                <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub, marginTop:4 }}>
                  {fmtCAD(totalBorrowed)} borrowed</div>
              </div>
              <GaugeSparkline r={ratio} color={ratioColor(ratio)}/>
            </div>
          </div>
        </div>
      </ChangeMarker>

      {/* 3-column middle row: Allocation · Watchlist · Mini what-if */}
      <div style={{ gridColumn:'1/-1', display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12 }}>

        {/* Allocation */}
        <AllocationWidget holdings={MOCK.holdings}/>

        {/* Watchlist preview */}
        <Panel>
          <SectionHead right={
            <button onClick={() => setScreen('watchlist')} style={{ background:'none', border:'none',
              cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>All →</button>
          }>Watchlist</SectionHead>
          {MOCK.watchlist.slice(0,6).map(w => {
            const gap = ((w.price-w.target)/w.target*100);
            const gapColor = gap<=0 ? DS.green : Math.abs(gap)<10 ? DS.amber : DS.red;
            return (
              <div key={w.ticker} style={{ padding:'8px 14px', borderBottom:`1px solid ${DS.border}`,
                display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div>
                  <a href={`https://finance.yahoo.com/quote/${w.ticker}`}
                    target="_blank" rel="noreferrer"
                    style={{ fontFamily:DS.fontMono, fontSize:13, fontWeight:700,
                      color:DS.blue, textDecoration:'none' }}>{w.ticker}</a>
                  <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, marginTop:1 }}>
                    target ${w.target.toFixed(2)}
                  </div>
                </div>
                <div style={{ textAlign:'right' }}>
                  <div style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.text }}>${w.price.toFixed(2)}</div>
                  <div style={{ fontFamily:DS.fontMono, fontSize:10, color:gapColor }}>
                    {gap<=0 ? '● At target' : `▼ ${Math.abs(gap).toFixed(1)}%`}
                  </div>
                </div>
              </div>
            );
          })}
        </Panel>

        {/* Mini what-if */}
        <Panel>
          <SectionHead right={
            <button onClick={() => setScreen('leverage')} style={{ background:'none', border:'none',
              cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>Full →</button>
          }>Leverage what-if</SectionHead>
          <MiniWhatIf portVal={portTotal} ratio={ratio}/>
        </Panel>
      </div>

      {/* Top 15 holdings — full width, bottom */}
      <Panel style={{ gridColumn:'1/-1' }}>
        <SectionHead right={
          <button onClick={() => setScreen('holdings')} style={{ background:'none', border:'none',
            cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>All holdings →</button>
        }>Top 15 holdings</SectionHead>
        {!publicView && (
          <div style={{ display:'flex', gap:20, padding:'8px 14px',
            background:DS.bgRaised, borderBottom:`1px solid ${DS.border}` }}>
            {[['Positions', holdings.length],['Total value', fmtCAD(portTotal)],['Unrealized G/L', null]].map(([lbl,val]) => (
              <div key={lbl}>
                <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textSub }}>{lbl}</div>
                {lbl==='Unrealized G/L'
                  ? <GLCell value={totalGL} pct={totalGL/totalACB*100}/>
                  : <div style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.text }}>{val}</div>}
              </div>
            ))}
          </div>
        )}
        {publicView && (
          <div style={{ padding:'6px 12px', background:DS.amberDim, borderBottom:`1px solid #78350f` }}>
            <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.amber }}>
              🙈 Values hidden · tickers and today's % change still visible
            </span>
          </div>
        )}
        <table style={{ width:'100%', borderCollapse:'collapse' }}>
          <thead>
            <tr style={{ background:DS.bgRaised }}>
              {['Ticker','Acct','Mkt Value','Today','G/L','% Port'].map(h => (
                <th key={h} style={{ padding:'6px 12px',
                  textAlign:h==='Ticker'||h==='Acct'?'left':'right',
                  fontFamily:DS.fontSans, fontSize:10, fontWeight:600, color:DS.textSub,
                  borderBottom:`1px solid ${DS.border}`, letterSpacing:0.4 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...holdings].sort((a,b)=>b.mktVal-a.mktVal).slice(0,15).map((h,i) => (
              <tr key={h.ticker} style={{ background:i%2?DS.bgRaised:'transparent', transition:'background 0.1s' }}
                onMouseEnter={e=>e.currentTarget.style.background=DS.bgHover}
                onMouseLeave={e=>e.currentTarget.style.background=i%2?DS.bgRaised:'transparent'}>
                <td style={{ padding:'7px 12px', fontFamily:DS.fontMono, fontSize:12, fontWeight:700,
                  color:DS.text, borderBottom:`1px solid ${DS.border}` }}>
                  {h.ticker}
                  {h.currency==='USD'&&<span style={{ marginLeft:4, fontSize:8, color:DS.amber,
                    border:`1px solid ${DS.amber}`, borderRadius:2, padding:'0 2px' }}>USD</span>}
                </td>
                <td style={{ padding:'7px 12px', borderBottom:`1px solid ${DS.border}` }}><AcctBadge acct={h.acct}/></td>
                <td style={{ padding:'7px 12px', textAlign:'right', borderBottom:`1px solid ${DS.border}`,
                  fontFamily:DS.fontMono, fontSize:12, color:DS.text,
                  filter:publicView?'blur(5px)':'none', userSelect:publicView?'none':'auto' }}>{fmtCAD(h.mktVal)}</td>
                <td style={{ padding:'7px 12px', textAlign:'right', borderBottom:`1px solid ${DS.border}`,
                  fontFamily:DS.fontMono, fontSize:12, color: h.changePct>=0?DS.green:DS.red }}>
                  {h.changePct>=0?'▲':'▼'} {Math.abs(h.changePct).toFixed(2)}%</td>
                <td style={{ padding:'7px 12px', textAlign:'right', borderBottom:`1px solid ${DS.border}`,
                  filter:publicView?'blur(5px)':'none', userSelect:publicView?'none':'auto' }}>
                  <GLCell value={h.gl} pct={h.glPct}/></td>
                <td style={{ padding:'7px 12px', textAlign:'right', borderBottom:`1px solid ${DS.border}`,
                  fontFamily:DS.fontMono, fontSize:11, color:DS.textSub,
                  filter:publicView?'blur(5px)':'none', userSelect:publicView?'none':'auto' }}>
                  {(h.mktVal/portTotal*100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}

Object.assign(window, { CockpitScreen });
