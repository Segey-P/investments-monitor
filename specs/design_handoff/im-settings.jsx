// ─── Settings screen — 6 sections ────────────────────────────────────────────

function SettingsScreen() {
  // Local state for editable fields
  const [sessionTimeout, setSessionTimeout] = React.useState(MOCK.settings.sessionTimeoutMin);
  const [helocRate,  setHelocRate]  = React.useState(MOCK.settings.helocRate);
  const [helocLimit, setHelocLimit] = React.useState(MOCK.settings.helocLimit);
  const [refreshOn,  setRefreshOn]  = React.useState(MOCK.settings.refreshEnabled);
  const [refreshMin, setRefreshMin] = React.useState(MOCK.settings.refreshIntervalMin);
  const [pushState,  setPushState]  = React.useState('idle'); // idle|working|success|error
  const [saved, setSaved]           = React.useState({});

  function markSaved(key) {
    setSaved(s => ({ ...s, [key]: true }));
    setTimeout(() => setSaved(s => ({ ...s, [key]: false })), 2000);
  }

  function handlePush() {
    setPushState('working');
    setTimeout(() => {
      // Simulate 80% success
      setPushState(Math.random() > 0.2 ? 'success' : 'error');
      setTimeout(() => setPushState('idle'), 3500);
    }, 1800);
  }

  const PUSH_STATES = {
    idle:    { label:'Regenerate + push', bg:DS.blue,     border:DS.blue,     color:'#fff',       disabled:false },
    working: { label:'Pushing…',          bg:DS.bgRaised, border:DS.border,   color:DS.textSub,   disabled:true  },
    success: { label:'✓ Pushed',          bg:DS.greenDim, border:DS.green,    color:DS.green,     disabled:true  },
    error:   { label:'✕ Push failed — retry', bg:DS.redDim,   border:DS.red, color:DS.red,       disabled:false },
  };
  const ps = PUSH_STATES[pushState];

  const SECTIONS = [
    'Security', 'Borrowing', 'Refresh', 'FX', 'Imports', 'Public summary', 'About'
  ];

  const [marginThreshold, setMarginThreshold] = React.useState(
    Math.round(MOCK.margin.callThreshold * 100)
  );
  const [activeSection, setActiveSection] = React.useState('Security');

  return (
    <div style={{ display:'flex', minHeight:'calc(100vh - 88px)' }}>

      {/* Sidebar nav */}
      <div style={{ width:200, flexShrink:0, background:DS.bgPanel,
        borderRight:`1px solid ${DS.border}`, padding:'12px 0' }}>
        {SECTIONS.map(s => (
          <button key={s} onClick={() => setActiveSection(s)} style={{
            display:'block', width:'100%', textAlign:'left',
            padding:'8px 18px', background:'none',
            border:'none', borderLeft:`2px solid ${activeSection===s ? DS.blue : 'transparent'}`,
            fontFamily:DS.fontSans, fontSize:13,
            color: activeSection===s ? DS.blue : DS.textSub,
            cursor:'pointer', transition:'color 0.1s' }}>
            {s}
          </button>
        ))}
      </div>

      {/* Content area */}
      <div style={{ flex:1, padding:'24px 32px', maxWidth:680 }}>

        {/* ── Security ─────────────────────────────────────────────────── */}
        {activeSection === 'Security' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>Security</h2>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Change password"
                  help="Min 12 characters recommended. Stored as bcrypt hash.">
                  <div style={{ display:'flex', gap:8, flex:1 }}>
                    <input type="password" placeholder="New password"
                      style={{ flex:1, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13, outline:'none' }}/>
                    <button style={{ padding:'7px 14px', background:DS.blue,
                      border:'none', borderRadius:3, cursor:'pointer',
                      fontFamily:DS.fontSans, fontSize:12, color:'#fff' }}>
                      Update
                    </button>
                  </div>
                </FormRow>

                <FormRow label="Session timeout"
                  help="After this many minutes of inactivity you will be redirected to the login screen. A warning banner appears 60 s before expiry.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input type="number" min={1} max={480} value={sessionTimeout}
                      onChange={e => setSessionTimeout(+e.target.value)}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>
                      minutes (default 15)
                    </span>
                    <button onClick={() => markSaved('timeout')}
                      style={{ padding:'7px 14px',
                        background: saved.timeout ? DS.greenDim : DS.bgRaised,
                        border:`1px solid ${saved.timeout ? DS.green : DS.border}`,
                        borderRadius:3, cursor:'pointer',
                        fontFamily:DS.fontSans, fontSize:12,
                        color: saved.timeout ? DS.green : DS.textSub }}>
                      {saved.timeout ? '✓ Saved' : 'Save'}
                    </button>
                  </div>
                </FormRow>
              </div>
            </Panel>
          </>
        )}

        {/* ── Borrowing (HELOC + Margin combined) ───────────────────────── */}
        {activeSection === 'Borrowing' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:6 }}>Borrowing</h2>
            <p style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub, marginBottom:20 }}>
              Settings for HELOC and margin loan. Dollar balances are managed on the Leverage screen.
            </p>

            {/* HELOC sub-section */}
            <div style={{ fontFamily:DS.fontSans, fontSize:11, fontWeight:600,
              color:DS.textSub, letterSpacing:0.8, textTransform:'uppercase',
              marginBottom:10 }}>HELOC</div>
            <Panel style={{ marginBottom:20 }}>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Credit limit"
                  help="Your lender's approved HELOC ceiling. Used to compute utilization % and cap the what-if slider.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>$</span>
                    <input type="number" step={1000} min={0} value={helocLimit}
                      onChange={e => setHelocLimit(+e.target.value)}
                      style={{ width:110, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>CAD</span>
                    <button onClick={() => markSaved('helocLimit')}
                      style={{ padding:'7px 14px',
                        background: saved.helocLimit ? DS.greenDim : DS.bgRaised,
                        border:`1px solid ${saved.helocLimit ? DS.green : DS.border}`,
                        borderRadius:3, cursor:'pointer',
                        fontFamily:DS.fontSans, fontSize:12,
                        color: saved.helocLimit ? DS.green : DS.textSub }}>
                      {saved.helocLimit ? '✓ Saved' : 'Save'}
                    </button>
                  </div>
                </FormRow>
                <FormRow label="Utilization warning threshold"
                  help="Show an amber warning on the Leverage screen when HELOC utilization exceeds this level.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input type="number" step={5} min={1} max={100} defaultValue={80}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% (default 80%)</span>
                    <button onClick={() => markSaved('helocThreshold')}
                      style={{ padding:'7px 14px',
                        background: saved.helocThreshold ? DS.greenDim : DS.bgRaised,
                        border:`1px solid ${saved.helocThreshold ? DS.green : DS.border}`,
                        borderRadius:3, cursor:'pointer',
                        fontFamily:DS.fontSans, fontSize:12,
                        color: saved.helocThreshold ? DS.green : DS.textSub }}>
                      {saved.helocThreshold ? '✓ Saved' : 'Save'}
                    </button>
                  </div>
                </FormRow>
              </div>
            </Panel>

            {/* Margin sub-section */}
            <div style={{ fontFamily:DS.fontSans, fontSize:11, fontWeight:600,
              color:DS.textSub, letterSpacing:0.8, textTransform:'uppercase',
              marginBottom:10 }}>Margin loan</div>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Borrowing limit"
                  help="Broker-approved margin ceiling. Used to compute utilization % on the Leverage screen.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>$</span>
                    <input type="number" step={1000} min={0} defaultValue={MOCK.margin.limit}
                      style={{ width:110, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>CAD</span>
                    <button onClick={() => markSaved('marginLimit')}
                      style={{ padding:'7px 14px',
                        background: saved.marginLimit ? DS.greenDim : DS.bgRaised,
                        border:`1px solid ${saved.marginLimit ? DS.green : DS.border}`,
                        borderRadius:3, cursor:'pointer',
                        fontFamily:DS.fontSans, fontSize:12,
                        color: saved.marginLimit ? DS.green : DS.textSub }}>
                      {saved.marginLimit ? '✓ Saved' : 'Save'}
                    </button>
                  </div>
                </FormRow>
                <FormRow label="Broker call threshold"
                  help="Equity level (% of account value) at which your broker issues a margin call. Questrade default is 70%.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input type="number" min={1} max={99} value={marginThreshold}
                      onChange={e => setMarginThreshold(+e.target.value)}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% equity (default 70%)</span>
                    <button onClick={() => markSaved('marginThreshold')}
                      style={{ padding:'7px 14px',
                        background: saved.marginThreshold ? DS.greenDim : DS.bgRaised,
                        border:`1px solid ${saved.marginThreshold ? DS.green : DS.border}`,
                        borderRadius:3, cursor:'pointer',
                        fontFamily:DS.fontSans, fontSize:12,
                        color: saved.marginThreshold ? DS.green : DS.textSub }}>
                      {saved.marginThreshold ? '✓ Saved' : 'Save'}
                    </button>
                  </div>
                </FormRow>
                <FormRow label="Warning banner threshold"
                  help="Show the amber buffer warning on the Leverage screen when margin buffer drops below this level.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input type="number" min={1} max={99} defaultValue={50}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% buffer (default 50%)</span>
                    <button onClick={() => markSaved('marginWarn')}
                      style={{ padding:'7px 14px',
                        background: saved.marginWarn ? DS.greenDim : DS.bgRaised,
                        border:`1px solid ${saved.marginWarn ? DS.green : DS.border}`,
                        borderRadius:3, cursor:'pointer',
                        fontFamily:DS.fontSans, fontSize:12,
                        color: saved.marginWarn ? DS.green : DS.textSub }}>
                      {saved.marginWarn ? '✓ Saved' : 'Save'}
                    </button>
                  </div>
                </FormRow>
              </div>
            </Panel>
          </>
        )}

        {/* ── Refresh ───────────────────────────────────────────────────── */}
        {activeSection === 'Refresh' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>Data refresh</h2>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Scheduled refresh"
                  help="When on, the app pulls fresh prices from Questrade on the configured interval. Turn off to use manual refresh only.">
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <button onClick={() => setRefreshOn(r => !r)} style={{
                      width:44, height:24, borderRadius:12,
                      background: refreshOn ? DS.blue : DS.bgRaised,
                      border:`1px solid ${refreshOn ? DS.blue : DS.border}`,
                      cursor:'pointer', position:'relative', transition:'background 0.2s',
                      padding:0 }}>
                      <div style={{ position:'absolute', top:3, width:16, height:16,
                        borderRadius:'50%', background:'#fff',
                        left: refreshOn ? 23 : 3, transition:'left 0.2s' }}/>
                    </button>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12,
                      color: refreshOn ? DS.text : DS.textSub }}>
                      {refreshOn ? 'On' : 'Off'}
                    </span>
                  </div>
                </FormRow>

                <FormRow label="Refresh interval"
                  help="How often to poll for new prices when scheduled refresh is on. Shorter intervals increase Questrade API calls; keep at 15 min+ to avoid rate limiting.">
                  <div style={{ display:'flex', alignItems:'center', gap:10,
                    opacity: refreshOn ? 1 : 0.4, pointerEvents: refreshOn ? 'auto' : 'none' }}>
                    <input type="number" min={5} max={1440} step={5} value={refreshMin}
                      onChange={e => setRefreshMin(+e.target.value)}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>
                      minutes
                    </span>
                  </div>
                </FormRow>

                <FormRow label="Last refresh">
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                      {MOCK.settings.lastRefresh}
                    </span>
                    <button style={{ padding:'7px 14px', background:DS.bgRaised,
                      border:`1px solid ${DS.border}`, borderRadius:3, cursor:'pointer',
                      fontFamily:DS.fontSans, fontSize:12, color:DS.blue }}>
                      Refresh now
                    </button>
                  </div>
                </FormRow>
              </div>
            </Panel>
          </>
        )}

        {/* ── FX ────────────────────────────────────────────────────────── */}
        {activeSection === 'FX' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>Foreign exchange</h2>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Rate source">
                  <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>
                    Bank of Canada daily rate · read-only
                  </span>
                </FormRow>
                <FormRow label="Current USD/CAD rate"
                  help="Fetched once daily at market open. Applied to all USD holdings when computing CAD totals.">
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700,
                      color:DS.text }}>{FX_USD_CAD.toFixed(4)}</span>
                    <div>
                      <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint }}>
                        Fetched {MOCK.fxFetched}
                      </div>
                      <a href="https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json"
                        target="_blank" rel="noreferrer"
                        style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>
                        BOC chart ↗
                      </a>
                    </div>
                  </div>
                </FormRow>
                <FormRow label="">
                  <div style={{ padding:'8px 12px', background:DS.bgRaised,
                    borderRadius:3, border:`1px solid ${DS.border}`,
                    fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint,
                    fontStyle:'italic' }}>
                    The rate is not editable. Change in rate applies retroactively to all
                    USD positions on next refresh.
                  </div>
                </FormRow>
              </div>
            </Panel>
          </>
        )}

        {/* ── Imports ───────────────────────────────────────────────────── */}
        {activeSection === 'Imports' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>CSV imports</h2>
            <div style={{ marginBottom:12, fontFamily:DS.fontSans, fontSize:12,
              color:DS.textSub }}>
              Place Questrade export CSVs in <code style={{ fontFamily:DS.fontMono,
                fontSize:11, color:DS.text,
                background:DS.bgRaised, padding:'1px 5px', borderRadius:2 }}>
                data/imports/
              </code>. The app detects new files on each refresh.
            </div>
            <Panel>
              <div style={{ padding:'8px 14px', borderBottom:`1px solid ${DS.border}`,
                display:'flex', gap:20,
                fontFamily:DS.fontSans, fontSize:10, fontWeight:600,
                color:DS.textSub, letterSpacing:0.4 }}>
                <span style={{ flex:2 }}>FILE</span>
                <span style={{ flex:1 }}>BROKER</span>
                <span style={{ flex:1 }}>ROWS</span>
                <span style={{ flex:1 }}>IMPORTED</span>
                <span style={{ width:90 }}></span>
              </div>
              {MOCK.settings.importFiles.map((f, i) => (
                <div key={f.name} style={{ padding:'12px 14px',
                  borderBottom: i < MOCK.settings.importFiles.length-1
                    ? `1px solid ${DS.border}` : 'none',
                  display:'flex', gap:20, alignItems:'center',
                  background: i%2 ? DS.bgRaised : 'transparent' }}>
                  <span style={{ flex:2, fontFamily:DS.fontMono, fontSize:12, color:DS.text,
                    overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                    {f.name}</span>
                  <span style={{ flex:1, fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>
                    {f.broker}</span>
                  <span style={{ flex:1, fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                    {f.rows}</span>
                  <span style={{ flex:1, fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint }}>
                    {f.importedAt}</span>
                  <button style={{ width:90, padding:'5px 10px',
                    background:DS.bgRaised, border:`1px solid ${DS.border}`,
                    borderRadius:3, cursor:'pointer',
                    fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>
                    Re-import
                  </button>
                </div>
              ))}
              <div style={{ padding:'10px 14px', background:DS.bgRaised,
                borderTop:`1px solid ${DS.border}`,
                fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint,
                fontStyle:'italic' }}>
                Supported: Questrade Activity CSV. Other brokers deferred.
              </div>
            </Panel>
          </>
        )}

        {/* ── Public summary ────────────────────────────────────────────── */}
        {activeSection === 'Public summary' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>Public summary</h2>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Output path"
                  help="File path where summary.json is written before push. Must be accessible to your web server.">
                  <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                    {MOCK.settings.publicSummaryPath}
                  </span>
                </FormRow>

                <FormRow label="Last pushed">
                  <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                    {MOCK.settings.lastPushAt}
                  </span>
                </FormRow>

                <FormRow label="Regenerate + push"
                  help="Recalculates all public-safe ratios and proportions from the current SQLite snapshot, writes summary.json, then pushes to the configured path. No dollar amounts or quantities are included.">
                  <div style={{ display:'flex', flexDirection:'column', gap:8, flex:1 }}>
                    <button onClick={handlePush} disabled={ps.disabled} style={{
                      padding:'9px 20px', background:ps.bg,
                      border:`1px solid ${ps.border}`,
                      borderRadius:3, cursor: ps.disabled ? 'default' : 'pointer',
                      fontFamily:DS.fontSans, fontSize:13, fontWeight:600,
                      color:ps.color, transition:'all 0.2s',
                      alignSelf:'flex-start' }}>
                      {pushState === 'working'
                        ? <span style={{ display:'inline-flex', alignItems:'center', gap:8 }}>
                            <span style={{ display:'inline-block', width:12, height:12,
                              border:`2px solid ${DS.textSub}`, borderTopColor:'transparent',
                              borderRadius:'50%',
                              animation:'spin 0.8s linear infinite' }}/>
                            Pushing…
                          </span>
                        : ps.label}
                    </button>
                    {pushState === 'error' && (
                      <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.red }}>
                        Push failed. Check server path permissions and network.
                      </div>
                    )}
                    {pushState === 'success' && (
                      <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.green }}>
                        summary.json written and pushed successfully.
                      </div>
                    )}
                  </div>
                </FormRow>
              </div>
            </Panel>

            {/* Payload preview */}
            <div style={{ marginTop:16 }}>
              <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub,
                marginBottom:6 }}>Payload preview (what the cloud receives)</div>
              <pre style={{ background:DS.bgPanel, border:`1px solid ${DS.border}`,
                borderRadius:3, padding:'12px 14px',
                fontFamily:DS.fontMono, fontSize:11, color:DS.textSub,
                overflow:'auto', margin:0, lineHeight:1.6 }}>
{JSON.stringify({
  generated_at: MOCK.asOf,
  leverage_ratio: 1.42,
  heloc_utilization_pct: 62.7,
  debt_to_equity: 0.61,
  mortgage_ltv_pct: 46.8,
  allocations: {
    by_account:    { RRSP:'38%', TFSA:'24%', Unregistered:'28%', Crypto:'10%' },
    by_asset_class:{ Stock:'56%', ETF:'34%', Crypto:'10%' },
    by_country:    { CA:'73%', US:'17%', other:'10%' },
    by_currency:   { CAD:'90%', USD:'10%' },
  },
  watchlist: MOCK.watchlist.map(w=>({ ticker:w.ticker, price:w.price, target:w.target,
    gap_pct: +((w.price-w.target)/w.target*100).toFixed(1) })),
}, null, 2)}
              </pre>
            </div>
          </>
        )}

        {/* ── About ─────────────────────────────────────────────────────── */}
        {activeSection === 'About' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>About</h2>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                {[
                  ['Version',     MOCK.settings.version],
                  ['Branch',      MOCK.settings.branch],
                  ['Last commit', MOCK.settings.lastCommit],
                  ['Stack',       'Streamlit v0.1 · SQLite · Python 3.12'],
                  ['Storage',     'Local SQLite — no cloud writes'],
                  ['Remote access','Tailscale required'],
                ].map(([lbl,val]) => (
                  <FormRow key={lbl} label={lbl}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                      {val}</span>
                  </FormRow>
                ))}
              </div>
            </Panel>
          </>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

Object.assign(window, { SettingsScreen });
