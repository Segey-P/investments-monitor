// ─── Cockpit screen ───────────────────────────────────────────────────────────
// Allocation widget: Asset class / Country / Currency (Account removed — redundant)
// Gauge moved to KPI strip; holdings get full right column

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
              padding:'2px 9px',
              border:`1px solid ${dim===d.id ? DS.blue : DS.border}`,
              borderRadius:10,
              background: dim===d.id ? DS.blueDim : 'transparent',
              fontFamily:DS.fontSans, fontSize:11,
              color: dim===d.id ? DS.blue : DS.textFaint,
              cursor:'pointer', whiteSpace:'nowrap',
            }}>{d.label}</button>
          ))}
          <PrivBadge type="cloud"/>
        </div>
      </div>
      <div style={{ padding:'12px 14px' }}>
        <div style={{ height:16, display:'flex', borderRadius:3,
          overflow:'hidden', marginBottom:10, gap:1 }}>
          {groups.map(g => (
            <div key={g.id} title={`${g.label}: ${g.pct.toFixed(1)}%`}
              style={{ flex:g.pct, minWidth:g.pct>1?2:0, background:g.color, opacity:0.75 }}/>
          ))}
        </div>
        {groups.map(g => (
          <div key={g.id} style={{ display:'flex', alignItems:'center',
            justifyContent:'space-between', padding:'4px 0',
            borderBottom:`1px solid ${DS.border}` }}>
            <div style={{ display:'flex', alignItems:'center', gap:8 }}>
              <div style={{ width:7, height:7, borderRadius:2,
                background:g.color, opacity:0.85, flexShrink:0 }}/>
              <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>{g.label}</span>
            </div>
            <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.text }}>
              {g.pct.toFixed(1)}%</span>
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

function CockpitScreen({ publicView, setScreen }) {
  const holdings = React.useMemo(() => derivePortfolio(MOCK.holdings), []);
  const portTotal = portfolioTotal(MOCK.holdings);
  const { totalBorrowed, ratio } = computeLeverage(portTotal, MOCK.heloc.drawn, MOCK.margin.balance);
  const netWorth  = portTotal + MOCK.property.value + MOCK.cash
    - MOCK.property.mortgageBalance - MOCK.heloc.drawn - MOCK.margin.balance;
  const totalGL   = holdings.reduce((s,h) => s+h.gl, 0);
  const totalACB  = holdings.reduce((s,h) => s+h.acbTotal, 0);

  function ratioColor(r) { return r<1.5?DS.green:r<2.0?DS.amber:DS.red; }

  // Compact gauge for KPI strip
  function GaugeSparkline({ r, color }) {
    const clipped = Math.min(Math.max(r,1),3);
    const a       = ((clipped-1)/2)*180;
    const rad     = (a-180)*Math.PI/180;
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
        <line x1={cx} y1={cy} x2={cx+gr*Math.cos(rad)} y2={cy+gr*Math.sin(rad)}
          stroke={color} strokeWidth={2}/>
        <circle cx={cx} cy={cy} r={3} fill={color}/>
        <text x={66} y={40} fontSize="7" fontFamily="DM Sans" fill={DS.green} textAnchor="end">safe</text>
        <text x={80} y={40} fontSize="7" fontFamily="DM Sans" fill={DS.red} textAnchor="end">high</text>
      </svg>
    );
  }

  return (
    <div style={{ padding:'20px', display:'grid',
      gridTemplateColumns:'300px 1fr', gap:12 }}>

      {/* KPI strip — full width, 4 cards */}
      <div style={{ gridColumn:'1/-1', display:'grid',
        gridTemplateColumns:'repeat(4,1fr)', gap:10 }}>
        <KPICard label="Net Worth" privacy="cloud" accent={DS.blue}
          value={publicView ? '—' : fmtCAD(netWorth)}
          sub="Assets − liabilities" blurred={publicView}/>
        <KPICard label="Portfolio value" privacy="local"
          value={publicView ? '—' : fmtCAD(portTotal)}
          sub={`${holdings.length} positions`} blurred={publicView}/>
        <KPICard label="Unrealized G/L" privacy="local"
          value={publicView ? '—' : fmtCAD(totalGL)}
          sub={publicView ? 'local-only' : fmtPct(totalGL/totalACB*100)}
          valueColor={!publicView?(totalGL>=0?DS.green:DS.red):DS.textFaint}
          blurred={publicView}/>
        {/* Leverage — gauge inline in KPI card */}
        <div style={{ background:DS.bgRaised, border:`1px solid ${DS.border}`,
          borderRadius:4, padding:'12px 14px',
          borderTop:`2px solid ${ratioColor(ratio)}` }}>
          <div style={{ display:'flex', alignItems:'center',
            justifyContent:'space-between', marginBottom:4 }}>
            <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>
              Leverage ratio</span>
            <PrivBadge type="cloud"/>
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

      {/* Left col: Allocation + Watchlist */}
      <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
        <AllocationWidget holdings={MOCK.holdings}/>

        <Panel>
          <SectionHead right={
            <button onClick={() => setScreen('watchlist')} style={{
              background:'none', border:'none', cursor:'pointer',
              fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>All →</button>
          }>Watchlist</SectionHead>
          {MOCK.watchlist.slice(0,5).map(w => {
            const gap      = ((w.price-w.target)/w.target*100);
            const rangePct = (w.price-w.lo52)/(w.hi52-w.lo52)*100;
            const tgtPct   = (w.target-w.lo52)/(w.hi52-w.lo52)*100;
            return (
              <div key={w.ticker} style={{ padding:'8px 14px',
                borderBottom:`1px solid ${DS.border}` }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  alignItems:'baseline', marginBottom:3 }}>
                  <span style={{ fontFamily:DS.fontMono, fontSize:13,
                    fontWeight:700, color:DS.text }}>{w.ticker}</span>
                  <div style={{ display:'flex', gap:12, alignItems:'baseline' }}>
                    {/* Today % */}
                    <span style={{ fontFamily:DS.fontMono, fontSize:11,
                      color: w.changePct>=0?DS.green:DS.red }}>
                      {w.changePct>=0?'▲':'▼'} {Math.abs(w.changePct).toFixed(2)}%
                    </span>
                    <span style={{ fontFamily:DS.fontMono, fontSize:13,
                      color:DS.text }}>${w.price.toFixed(2)}</span>
                  </div>
                </div>
                <div style={{ position:'relative', height:4, background:DS.border,
                  borderRadius:2, marginBottom:3 }}>
                  <div style={{ position:'absolute', left:`${tgtPct}%`, top:-2,
                    width:2, height:8, background:DS.blue, transform:'translateX(-50%)' }}/>
                  <div style={{ position:'absolute', left:`${rangePct}%`, top:-2,
                    width:2, height:8, background:DS.amber, transform:'translateX(-50%)' }}/>
                </div>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint }}>
                  <span>Target <span style={{ color:DS.blue }}>${w.target.toFixed(2)}</span></span>
                  <span style={{ color:DS.amber }}>▼ {Math.abs(gap).toFixed(1)}% away</span>
                </div>
              </div>
            );
          })}
        </Panel>
      </div>

      {/* Right col: Top holdings — full height */}
      <Panel>
        <SectionHead right={
          <button onClick={() => setScreen('holdings')} style={{
            background:'none', border:'none', cursor:'pointer',
            fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>
            All holdings →
          </button>
        }>Top holdings</SectionHead>

        {/* G/L summary bar at top */}
        {!publicView && (
          <div style={{ display:'flex', gap:20, padding:'8px 14px',
            background:DS.bgRaised, borderBottom:`1px solid ${DS.border}` }}>
            {[
              ['Positions', holdings.length],
              ['Total value', fmtCAD(portTotal)],
              ['Unrealized G/L', null],
            ].map(([lbl, val]) => (
              <div key={lbl}>
                <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textSub }}>{lbl}</div>
                {lbl === 'Unrealized G/L'
                  ? <GLCell value={totalGL} pct={totalGL/totalACB*100}/>
                  : <div style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.text }}>{val}</div>}
              </div>
            ))}
          </div>
        )}

        {publicView && (
          <div style={{ padding:'6px 12px', background:DS.amberDim,
            borderBottom:`1px solid #78350f` }}>
            <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.amber }}>
              🔒 Values hidden in public view · tickers and today's change visible
            </span>
          </div>
        )}
        <div>
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
              {[...holdings].sort((a,b)=>b.mktVal-a.mktVal).map((h,i)=>(
                <tr key={h.ticker}
                  style={{ background:i%2?DS.bgRaised:'transparent', transition:'background 0.1s' }}
                  onMouseEnter={e=>e.currentTarget.style.background=DS.bgHover}
                  onMouseLeave={e=>e.currentTarget.style.background=i%2?DS.bgRaised:'transparent'}>
                  <td style={{ padding:'7px 12px', fontFamily:DS.fontMono, fontSize:12,
                    fontWeight:700, color:DS.text, borderBottom:`1px solid ${DS.border}` }}>
                    {h.ticker}
                    {h.currency==='USD'&&<span style={{ marginLeft:4, fontSize:8,
                      color:DS.amber, border:`1px solid ${DS.amber}`, borderRadius:2,
                      padding:'0 2px' }}>USD</span>}
                  </td>
                  <td style={{ padding:'7px 12px', borderBottom:`1px solid ${DS.border}` }}>
                    <AcctBadge acct={h.acct}/></td>
                  <td style={{ padding:'7px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`,
                    fontFamily:DS.fontMono, fontSize:12, color:DS.text,
                    filter:publicView?'blur(5px)':'none', userSelect:publicView?'none':'auto' }}>
                    {fmtCAD(h.mktVal)}</td>
                  <td style={{ padding:'7px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`,
                    fontFamily:DS.fontMono, fontSize:12,
                    color: h.changePct>=0?DS.green:DS.red }}>
                    {h.changePct>=0?'▲':'▼'} {Math.abs(h.changePct).toFixed(2)}%
                  </td>
                  <td style={{ padding:'7px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`,
                    filter:publicView?'blur(5px)':'none', userSelect:publicView?'none':'auto' }}>
                    <GLCell value={h.gl} pct={h.glPct}/></td>
                  <td style={{ padding:'7px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`,
                    fontFamily:DS.fontMono, fontSize:11, color:DS.textSub,
                    filter:publicView?'blur(5px)':'none', userSelect:publicView?'none':'auto' }}>
                    {(h.mktVal/portTotal*100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

    </div>
  );
}

Object.assign(window, { CockpitScreen });
