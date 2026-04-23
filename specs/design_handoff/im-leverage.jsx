// ─── Leverage screen — HELOC + margin manual entry, no interest panel ─────────

function LeverageScreen() {
  const [tab, setTab]           = React.useState('heloc');
  const [whatIfDraw, setDraw]   = React.useState(0);

  // HELOC manual inputs
  const [helocDrawn, setHelocDrawn] = React.useState(MOCK.heloc.drawn);
  const [helocLimit, setHelocLimit] = React.useState(MOCK.heloc.limit);
  const [helocSaved, setHelocSaved] = React.useState(false);

  // Margin manual inputs
  const [marginBal,   setMarginBal]   = React.useState(MOCK.margin.balance);
  const [marginLimit, setMarginLimit] = React.useState(MOCK.margin.limit);
  const [marginSaved, setMarginSaved] = React.useState(false);

  function saveHeloc()  { setHelocSaved(true);  setTimeout(()=>setHelocSaved(false),  2000); }
  function saveMargin() { setMarginSaved(true);  setTimeout(()=>setMarginSaved(false), 2000); }

  const portVal   = portfolioTotal(MOCK.holdings);
  const drawn     = helocDrawn + whatIfDraw;
  const available = Math.max(0, helocLimit - helocDrawn);

  const base  = computeLeverage(portVal, helocDrawn,  marginBal);
  const live  = computeLeverage(portVal, drawn,        marginBal);

  const helocMoBase = (helocDrawn * MOCK.heloc.rate / 100) / 12;
  const helocMoLive = (drawn      * MOCK.heloc.rate / 100) / 12;
  const marginMo    = (marginBal  * MOCK.margin.rate / 100) / 12;

  const unregVal  = MOCK.holdings.filter(h=>h.acct==='unreg')
    .reduce((s,h)=>s+h.qty*h.priceCAD, 0);
  const marginBuf = marginBal > 0 ? (unregVal - marginBal) / unregVal : 1;

  function ratioColor(r) { return r<1.5?DS.green:r<2.0?DS.amber:DS.red; }

  return (
    <div style={{ padding:'20px', display:'grid',
      gridTemplateColumns:'1fr 320px', gap:12 }}>

      {/* ── KPI strip ─────────────────────────────────────────────────────── */}
      <div style={{ gridColumn:'1/-1', display:'grid',
        gridTemplateColumns:'repeat(5,1fr)', gap:10 }}>
        <KPICard label="HELOC drawn"    value={fmtCAD(helocDrawn)}
          sub={`of ${fmtCAD(helocLimit)} limit`} privacy="local"/>
        <KPICard label="HELOC available" value={fmtCAD(available)}
          sub={`${helocLimit>0?(helocDrawn/helocLimit*100).toFixed(0):0}% utilized`} privacy="local"/>
        <KPICard label="Margin balance"  value={fmtCAD(marginBal)}
          sub={`${MOCK.margin.broker} · ${MOCK.margin.rate}%`} privacy="local"/>
        <KPICard label="Total borrowed"  value={fmtCAD(helocDrawn+marginBal)}
          sub="HELOC + margin" privacy="local"/>
        <KPICard label="Leverage ratio"  value={`${base.ratio.toFixed(2)}×`}
          sub="Portfolio ÷ own equity" privacy="cloud"
          accent={ratioColor(base.ratio)}/>
      </div>

      {/* ── Left: tabbed manual entry ─────────────────────────────────────── */}
      <Panel>
        <div style={{ display:'flex', borderBottom:`1px solid ${DS.border}` }}>
          {[['heloc','HELOC'],['margin','Margin loan']].map(([id,lbl])=>(
            <button key={id} onClick={()=>setTab(id)} style={{
              flex:1, padding:'10px', background:'none', border:'none',
              borderBottom:`2px solid ${tab===id?DS.blue:'transparent'}`,
              fontFamily:DS.fontSans, fontSize:13,
              color:tab===id?DS.blue:DS.textSub, cursor:'pointer' }}>{lbl}</button>
          ))}
        </div>

        {/* HELOC manual entry */}
        {tab==='heloc' && (
          <>
            <div style={{ padding:'16px', borderBottom:`1px solid ${DS.border}` }}>
              <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub,
                marginBottom:14, letterSpacing:0.4, textTransform:'uppercase' }}>
                Update balances — from your lender statement
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:14 }}>
                {[
                  { label:'Amount drawn',  val:helocDrawn, set:setHelocDrawn,
                    help:'Current outstanding balance' },
                  { label:'Credit limit',  val:helocLimit, set:setHelocLimit,
                    help:'Approved ceiling from your lender' },
                ].map(({label,val,set,help})=>(
                  <div key={label}>
                    <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.text, marginBottom:2 }}>
                      {label}</div>
                    <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint,
                      fontStyle:'italic', marginBottom:6 }}>{help}</div>
                    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                      <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>$</span>
                      <input type="number" step={1000} min={0} value={val}
                        onChange={e=>{set(+e.target.value); setDraw(0);}}
                        style={{ flex:1, padding:'8px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:14,
                          outline:'none', textAlign:'right' }}/>
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>CAD</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Utilization bar */}
              <div style={{ marginBottom:12 }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontFamily:DS.fontMono, fontSize:11, color:DS.textSub, marginBottom:5 }}>
                  <span>Utilization</span>
                  <span>{helocLimit>0?(helocDrawn/helocLimit*100).toFixed(1):0}%</span>
                </div>
                <Bar pct={helocLimit>0?helocDrawn/helocLimit*100:0} color={DS.amber} height={8}/>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontFamily:DS.fontMono, fontSize:10, color:DS.textFaint, marginTop:3 }}>
                  <span>Drawn {fmtCAD(helocDrawn)}</span>
                  <span>Available {fmtCAD(available)}</span>
                </div>
              </div>

              <button onClick={saveHeloc} style={{
                padding:'7px 20px',
                background:helocSaved?DS.greenDim:DS.blue,
                border:`1px solid ${helocSaved?DS.green:DS.blue}`,
                borderRadius:3, cursor:'pointer',
                fontFamily:DS.fontSans, fontSize:13, fontWeight:600,
                color:helocSaved?DS.green:'#fff', transition:'all 0.2s' }}>
                {helocSaved?'✓ Saved':'Save'}
              </button>
            </div>
            <div style={{ padding:'12px 16px', background:DS.bgRaised,
              display:'flex', gap:20, alignItems:'center' }}>
              <div>
                <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint }}>
                  Rate (edit in Settings → HELOC)</div>
                <div style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.text }}>
                  {MOCK.heloc.rate}% p.a. · {fmtCAD(helocMoBase)}/mo</div>
              </div>
              <div style={{ marginLeft:'auto', fontFamily:DS.fontSans, fontSize:10,
                color:DS.textFaint, fontStyle:'italic' }}>
                Update after each draw or repayment
              </div>
            </div>
          </>
        )}

        {/* Margin manual entry */}
        {tab==='margin' && (
          <>
            <div style={{ padding:'16px', borderBottom:`1px solid ${DS.border}` }}>
              <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub,
                marginBottom:14, letterSpacing:0.4, textTransform:'uppercase' }}>
                Update balances — {MOCK.margin.broker} unregistered account
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:14 }}>
                {[
                  { label:'Balance outstanding', val:marginBal,   set:setMarginBal,
                    help:'Amount currently borrowed on margin' },
                  { label:'Margin limit',         val:marginLimit, set:setMarginLimit,
                    help:'Broker-approved borrowing ceiling' },
                ].map(({label,val,set,help})=>(
                  <div key={label}>
                    <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.text, marginBottom:2 }}>
                      {label}</div>
                    <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint,
                      fontStyle:'italic', marginBottom:6 }}>{help}</div>
                    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                      <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>$</span>
                      <input type="number" step={1000} min={0} value={val}
                        onChange={e=>set(+e.target.value)}
                        style={{ flex:1, padding:'8px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:14,
                          outline:'none', textAlign:'right' }}/>
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>CAD</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Utilization bar */}
              <div style={{ marginBottom:12 }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontFamily:DS.fontMono, fontSize:11, color:DS.textSub, marginBottom:5 }}>
                  <span>Utilization</span>
                  <span>{marginLimit>0?(marginBal/marginLimit*100).toFixed(1):0}%</span>
                </div>
                <Bar pct={marginLimit>0?marginBal/marginLimit*100:0} color={DS.amber} height={8}/>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontFamily:DS.fontMono, fontSize:10, color:DS.textFaint, marginTop:3 }}>
                  <span>Balance {fmtCAD(marginBal)}</span>
                  <span>Available {fmtCAD(Math.max(0,marginLimit-marginBal))}</span>
                </div>
              </div>

              {/* Margin call buffer warning */}
              {marginBuf < 0.5 && (
                <div style={{ marginBottom:12, padding:'10px 12px',
                  background:DS.amberDim, border:`1px solid #78350f`, borderRadius:3 }}>
                  <div style={{ fontFamily:DS.fontSans, fontSize:12,
                    color:DS.amber, fontWeight:600 }}>⚠ Margin buffer below 50%</div>
                  <div style={{ fontFamily:DS.fontSans, fontSize:11,
                    color:'#ca8a04', marginTop:3 }}>
                    Buffer: {(marginBuf*100).toFixed(1)}% ·
                    Call at {(MOCK.margin.callThreshold*100).toFixed(0)}%.
                  </div>
                </div>
              )}

              <button onClick={saveMargin} style={{
                padding:'7px 20px',
                background:marginSaved?DS.greenDim:DS.blue,
                border:`1px solid ${marginSaved?DS.green:DS.blue}`,
                borderRadius:3, cursor:'pointer',
                fontFamily:DS.fontSans, fontSize:13, fontWeight:600,
                color:marginSaved?DS.green:'#fff', transition:'all 0.2s' }}>
                {marginSaved?'✓ Saved':'Save'}
              </button>
            </div>
            <div style={{ padding:'12px 16px', background:DS.bgRaised,
              display:'flex', gap:20, alignItems:'center' }}>
              <div>
                <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint }}>Rate</div>
                <div style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.text }}>
                  {MOCK.margin.rate}% p.a. · {fmtCAD(marginMo)}/mo</div>
              </div>
              <div style={{ marginLeft:'auto', fontFamily:DS.fontSans, fontSize:10,
                color:DS.textFaint, fontStyle:'italic' }}>
                Call threshold configurable in Settings → Margin
              </div>
            </div>
          </>
        )}
      </Panel>

      {/* ── Right: what-if slider ─────────────────────────────────────────── */}
      <Panel>
        <SectionHead right={<PrivBadge type="cloud"/>}>HELOC what-if</SectionHead>
        <div style={{ padding:'14px 16px' }}>
          <div style={{ display:'flex', justifyContent:'space-between',
            marginBottom:8, alignItems:'baseline' }}>
            <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>
              Draw additional</span>
            <span style={{ fontFamily:DS.fontMono, fontSize:18, fontWeight:700,
              color:DS.text }}>{fmtCAD(whatIfDraw)}</span>
          </div>

          <input type="range" min={0} max={available} step={500} value={whatIfDraw}
            onChange={e=>setDraw(+e.target.value)}
            style={{ width:'100%', accentColor:DS.blue, cursor:'pointer' }}/>
          <div style={{ display:'flex', justifyContent:'space-between',
            fontFamily:DS.fontMono, fontSize:10, color:DS.textFaint, marginBottom:14 }}>
            <span>$0</span><span>{fmtCAD(available)} avail.</span>
          </div>

          {/* Live ratio — always visible */}
          <div style={{ padding:'12px', borderRadius:3,
            background: ratioColor(live.ratio)===DS.green ? DS.greenDim
                      : ratioColor(live.ratio)===DS.amber ? DS.amberDim : DS.redDim,
            border:`1px solid ${ratioColor(live.ratio)}44` }}>
            <div style={{ display:'flex', justifyContent:'space-between',
              alignItems:'baseline', marginBottom:6 }}>
              <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>
                Leverage ratio</span>
              <span style={{ fontFamily:DS.fontMono, fontSize:22, fontWeight:700,
                color:ratioColor(live.ratio) }}>{live.ratio.toFixed(2)}×</span>
            </div>
            {whatIfDraw>0 && (
              <div style={{ fontFamily:DS.fontSans, fontSize:11,
                color:ratioColor(live.ratio), marginBottom:8 }}>
                ▲ +{(live.ratio-base.ratio).toFixed(2)}× from {base.ratio.toFixed(2)}×
              </div>
            )}
            <Divider my={6}/>
            {[
              ['New HELOC balance',  fmtCAD(drawn)],
              ['Total borrowed',     fmtCAD(drawn+marginBal)],
              ['Interest delta/mo',  whatIfDraw>0?`+${fmtCAD(helocMoLive-helocMoBase)}`:'—'],
            ].map(([lbl,val])=>(
              <div key={lbl} style={{ display:'flex', justifyContent:'space-between',
                padding:'3px 0', borderBottom:`1px solid ${DS.border}` }}>
                <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>{lbl}</span>
                <span style={{ fontFamily:DS.fontMono, fontSize:11, color:DS.text }}>{val}</span>
              </div>
            ))}
            {live.ratio>=2 && (
              <div style={{ marginTop:8, fontFamily:DS.fontSans, fontSize:11,
                color:DS.red, fontWeight:600 }}>⚠ Ratio exceeds 2.0×</div>
            )}
          </div>
          <div style={{ marginTop:8, fontFamily:DS.fontSans, fontSize:10,
            color:DS.textFaint, fontStyle:'italic' }}>
            Assumes rate stays at {MOCK.heloc.rate}%. Not financial advice.
          </div>
        </div>
      </Panel>

    </div>
  );
}

Object.assign(window, { LeverageScreen });
