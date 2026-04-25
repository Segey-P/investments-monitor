// ─── Settings v3 ── CHANGE 6: one Save per section, not per field ─────────────

// ── File upload zone ──────────────────────────────────────────────────────────
function UploadZone() {
  const [dragging, setDragging] = React.useState(false);
  const [uploaded, setUploaded] = React.useState([]);
  const inputRef = React.useRef(null);

  function handleFiles(files) {
    const csvs = [...files].filter(f => f.name.endsWith('.csv'));
    if (!csvs.length) return;
    setUploaded(prev => [...prev, ...csvs.map(f => ({
      name: f.name, size: f.size, ts: new Date().toLocaleTimeString()
    }))]);
  }

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
        style={{ border:`2px dashed ${dragging ? DS.blue : DS.border}`,
          borderRadius:6, padding:'28px 20px', textAlign:'center',
          background: dragging ? DS.blueDim : DS.bgPanel,
          cursor:'pointer', transition:'all 0.15s' }}>
        <input ref={inputRef} type="file" accept=".csv" multiple
          onChange={e => handleFiles(e.target.files)} style={{ display:'none' }}/>
        <div style={{ fontSize:28, marginBottom:8, opacity: dragging ? 1 : 0.4 }}>⬆</div>
        <div style={{ fontFamily:DS.fontSans, fontSize:13,
          color: dragging ? DS.blue : DS.textSub, marginBottom:4 }}>
          {dragging ? 'Drop to import' : 'Drop a Questrade CSV here, or click to browse'}
        </div>
        <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint }}>
          Supported: Questrade Activity CSV · .csv files only
        </div>
      </div>
      {uploaded.length > 0 && (
        <div style={{ marginTop:10 }}>
          {uploaded.map((f, i) => (
            <div key={i} style={{ display:'flex', alignItems:'center', gap:12,
              padding:'8px 12px', background:DS.greenDim, borderRadius:3,
              border:`1px solid ${DS.green}44`, marginBottom:6 }}>
              <span style={{ fontFamily:DS.fontMono, fontSize:11, color:DS.green }}>✓</span>
              <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.text, flex:1 }}>{f.name}</span>
              <span style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint }}>
                {(f.size/1024).toFixed(1)} KB · {f.ts}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SettingsScreen() {
  const [sessionTimeout, setSessionTimeout] = React.useState(MOCK.settings.sessionTimeoutMin);
  const [helocRate,      setHelocRate]      = React.useState(MOCK.settings.helocRate);
  const [helocLimit,     setHelocLimit]     = React.useState(MOCK.settings.helocLimit);
  const [helocWarnPct,   setHelocWarnPct]   = React.useState(80);
  const [refreshOn,      setRefreshOn]      = React.useState(MOCK.settings.refreshEnabled);
  const [refreshMin,     setRefreshMin]     = React.useState(MOCK.settings.refreshIntervalMin);
  const [marginLimit,    setMarginLimit]    = React.useState(MOCK.margin.limit);
  const [marginThreshold,setMarginThreshold]= React.useState(Math.round(MOCK.margin.callThreshold*100));
  const [marginWarnPct,  setMarginWarnPct]  = React.useState(50);

  // One saved state per section (CHANGE 6)
  const [sectionSaved, setSectionSaved] = React.useState({});

  const [activeSection, setActiveSection]   = React.useState('Security');

  function saveSection(key) {
    setSectionSaved(s => ({ ...s, [key]: true }));
    setTimeout(() => setSectionSaved(s => ({ ...s, [key]: false })), 2200);
  }


  // Reusable section Save button
  function SaveBtn({ sectionKey }) {
    const saved = sectionSaved[sectionKey];
    return (
      <div style={{ padding:'16px', borderTop:`1px solid ${DS.border}`,
        display:'flex', alignItems:'center', gap:12 }}>
        <button onClick={() => saveSection(sectionKey)} style={{
          padding:'8px 22px',
          background: saved ? DS.greenDim : DS.blue,
          border:`1px solid ${saved ? DS.green : DS.blue}`,
          borderRadius:3, cursor:'pointer', fontFamily:DS.fontSans,
          fontSize:13, fontWeight:600,
          color: saved ? DS.green : '#fff', transition:'all 0.2s' }}>
          {saved ? '✓ Saved' : 'Save changes'}
        </button>
        {saved && (
          <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>
            Settings updated
          </span>
        )}
      </div>
    );
  }

  const SECTIONS = ['Security','Borrowing','Refresh','FX','Imports','About'];

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
            cursor:'pointer', transition:'color 0.1s' }}>{s}</button>
        ))}
      </div>

      {/* Content area */}
      <div style={{ flex:1, padding:'24px 32px', maxWidth:700 }}>

        {/* ── Security ──────────────────────────────────────────────────── */}
        {activeSection === 'Security' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:20 }}>Security</h2>
            <ChangeMarker id={6}>
              <Panel>
                <div style={{ padding:'0 16px' }}>
                  <FormRow label="Change password"
                    help="Min 12 characters recommended. Stored as bcrypt hash.">
                    <div style={{ display:'flex', gap:8, flex:1 }}>
                      <input type="password" placeholder="New password"
                        style={{ flex:1, padding:'7px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:13, outline:'none' }}/>
                    </div>
                  </FormRow>
                  <FormRow label="Session timeout"
                    help="After this many minutes of inactivity you will be redirected to login. A warning banner appears 60 s before expiry.">
                    <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                      <input type="number" min={1} max={480} value={sessionTimeout}
                        onChange={e => setSessionTimeout(+e.target.value)}
                        style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                          outline:'none', textAlign:'right' }}/>
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>minutes (default 15)</span>
                    </div>
                  </FormRow>
                </div>
                <SaveBtn sectionKey="security"/>
              </Panel>
            </ChangeMarker>
          </>
        )}

        {/* ── Borrowing ─────────────────────────────────────────────────── */}
        {activeSection === 'Borrowing' && (
          <>
            <h2 style={{ fontFamily:DS.fontSans, fontSize:16, fontWeight:600,
              color:DS.text, marginBottom:6 }}>Borrowing</h2>
            <p style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub, marginBottom:20 }}>
              Settings for HELOC and margin loan. Dollar balances are managed on the Leverage screen.
            </p>

            <div style={{ fontFamily:DS.fontSans, fontSize:11, fontWeight:600, color:DS.textSub,
              letterSpacing:0.8, textTransform:'uppercase', marginBottom:10 }}>HELOC</div>
            <ChangeMarker id={6} style={{ marginBottom:20 }}>
              <Panel>
                <div style={{ padding:'0 16px' }}>
                  <FormRow label="Credit limit"
                    help="Your lender's approved HELOC ceiling. Caps the what-if slider on the Leverage screen.">
                    <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                      <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>$</span>
                      <input type="number" step={1000} min={0} value={helocLimit}
                        onChange={e => setHelocLimit(+e.target.value)}
                        style={{ width:110, padding:'7px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                          outline:'none', textAlign:'right' }}/>
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>CAD</span>
                    </div>
                  </FormRow>
                  <FormRow label="Interest rate"
                    help="Annual rate used to compute monthly interest estimates on Leverage screen.">
                    <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                      <input type="number" step={0.05} min={0} max={30} value={helocRate}
                        onChange={e => setHelocRate(+e.target.value)}
                        style={{ width:80, padding:'7px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                          outline:'none', textAlign:'right' }}/>
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% p.a.</span>
                    </div>
                  </FormRow>
                  <FormRow label="Utilization warning threshold"
                    help="Show an amber warning when HELOC utilization exceeds this level.">
                    <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                      <input type="number" step={5} min={1} max={100} value={helocWarnPct}
                        onChange={e => setHelocWarnPct(+e.target.value)}
                        style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                          outline:'none', textAlign:'right' }}/>
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% (default 80%)</span>
                    </div>
                  </FormRow>
                </div>
                <SaveBtn sectionKey="heloc"/>
              </Panel>
            </ChangeMarker>

            <div style={{ fontFamily:DS.fontSans, fontSize:11, fontWeight:600, color:DS.textSub,
              letterSpacing:0.8, textTransform:'uppercase', marginBottom:10 }}>Margin loan</div>
            <Panel>
              <div style={{ padding:'0 16px' }}>
                <FormRow label="Borrowing limit"
                  help="Broker-approved margin ceiling. Used to compute utilization %.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.textSub }}>$</span>
                    <input type="number" step={1000} min={0} value={marginLimit}
                      onChange={e => setMarginLimit(+e.target.value)}
                      style={{ width:110, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>CAD</span>
                  </div>
                </FormRow>
                <FormRow label="Broker call threshold"
                  help="Equity % at which your broker issues a margin call. Questrade default is 70%.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input type="number" min={1} max={99} value={marginThreshold}
                      onChange={e => setMarginThreshold(+e.target.value)}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% equity (default 70%)</span>
                  </div>
                </FormRow>
                <FormRow label="Warning banner threshold"
                  help="Show margin buffer warning when buffer drops below this level.">
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input type="number" min={1} max={99} value={marginWarnPct}
                      onChange={e => setMarginWarnPct(+e.target.value)}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>% buffer (default 50%)</span>
                  </div>
                </FormRow>
              </div>
              <SaveBtn sectionKey="margin"/>
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
                  help="When on, the app pulls fresh prices from Questrade on the configured interval.">
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <button onClick={() => setRefreshOn(r => !r)} style={{
                      width:44, height:24, borderRadius:12,
                      background: refreshOn ? DS.blue : DS.bgRaised,
                      border:`1px solid ${refreshOn ? DS.blue : DS.border}`,
                      cursor:'pointer', position:'relative', transition:'background 0.2s', padding:0 }}>
                      <div style={{ position:'absolute', top:3, width:16, height:16, borderRadius:'50%',
                        background:'#fff', left: refreshOn ? 23 : 3, transition:'left 0.2s' }}/>
                    </button>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12,
                      color: refreshOn ? DS.text : DS.textSub }}>{refreshOn ? 'On' : 'Off'}</span>
                  </div>
                </FormRow>
                <FormRow label="Refresh interval"
                  help="How often to poll for new prices. Keep at 15 min+ to avoid Questrade rate limiting.">
                  <div style={{ display:'flex', alignItems:'center', gap:10,
                    opacity: refreshOn ? 1 : 0.4, pointerEvents: refreshOn ? 'auto' : 'none' }}>
                    <input type="number" min={5} max={1440} step={5} value={refreshMin}
                      onChange={e => setRefreshMin(+e.target.value)}
                      style={{ width:70, padding:'7px 10px', background:DS.bgRaised,
                        border:`1px solid ${DS.border}`, borderRadius:3,
                        color:DS.text, fontFamily:DS.fontMono, fontSize:13,
                        outline:'none', textAlign:'right' }}/>
                    <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>minutes</span>
                  </div>
                </FormRow>
                <FormRow label="Last refresh">
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>
                      {MOCK.settings.lastRefresh}</span>
                    <button style={{ padding:'7px 14px', background:DS.bgRaised,
                      border:`1px solid ${DS.border}`, borderRadius:3, cursor:'pointer',
                      fontFamily:DS.fontSans, fontSize:12, color:DS.blue }}>Refresh now</button>
                  </div>
                </FormRow>
              </div>
              <SaveBtn sectionKey="refresh"/>
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
                    Bank of Canada daily rate · read-only</span>
                </FormRow>
                <FormRow label="Current USD/CAD"
                  help="Fetched once daily at market open. Applied to all USD holdings.">
                  <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                    <span style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700, color:DS.text }}>
                      {FX_USD_CAD.toFixed(4)}</span>
                    <div>
                      <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint }}>
                        Fetched {MOCK.fxFetched}</div>
                      <a href="https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json"
                        target="_blank" rel="noreferrer"
                        style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>BOC chart ↗</a>
                    </div>
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

            {/* Upload zone */}
            <UploadZone/>

            <div style={{ marginTop:20, marginBottom:12, fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>
              Previously imported files
            </div>

            {MOCK.settings.importFiles.length === 0 ? (
              <div style={{ textAlign:'center', padding:'60px 20px',
                background:DS.bgPanel, border:`1px solid ${DS.border}`, borderRadius:4 }}>
                <div style={{ fontSize:28, marginBottom:10, opacity:0.3 }}>⬆</div>
                <div style={{ fontFamily:DS.fontSans, fontSize:14, color:DS.textSub, marginBottom:4 }}>
                  No import files found</div>
                <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textFaint }}>
                  Drop a Questrade Activity CSV into data/imports/ and refresh.
                </div>
              </div>
            ) : (
              <Panel>
                <div style={{ padding:'8px 14px', borderBottom:`1px solid ${DS.border}`,
                  display:'flex', gap:20, fontFamily:DS.fontSans, fontSize:10,
                  fontWeight:600, color:DS.textSub, letterSpacing:0.4 }}>
                  <span style={{ flex:2 }}>FILE</span>
                  <span style={{ flex:1 }}>BROKER</span>
                  <span style={{ flex:1 }}>ROWS</span>
                  <span style={{ flex:1 }}>IMPORTED</span>
                  <span style={{ width:90 }}></span>
                </div>
                {MOCK.settings.importFiles.map((f, i) => (
                  <div key={f.name} style={{ padding:'12px 14px',
                    borderBottom: i < MOCK.settings.importFiles.length-1 ? `1px solid ${DS.border}` : 'none',
                    display:'flex', gap:20, alignItems:'center',
                    background: i%2 ? DS.bgRaised : 'transparent' }}>
                    <span style={{ flex:2, fontFamily:DS.fontMono, fontSize:12, color:DS.text,
                      overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{f.name}</span>
                    <span style={{ flex:1, fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>{f.broker}</span>
                    <span style={{ flex:1, fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>{f.rows}</span>
                    <span style={{ flex:1, fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint }}>{f.importedAt}</span>
                    <button style={{ width:90, padding:'5px 10px', background:DS.bgRaised,
                      border:`1px solid ${DS.border}`, borderRadius:3, cursor:'pointer',
                      fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>Re-import</button>
                  </div>
                ))}
                <div style={{ padding:'10px 14px', background:DS.bgRaised,
                  borderTop:`1px solid ${DS.border}`,
                  fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint, fontStyle:'italic' }}>
                  Supported: Questrade Activity CSV. Other brokers deferred.
                </div>
              </Panel>
            )}
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
                    <span style={{ fontFamily:DS.fontMono, fontSize:12, color:DS.textSub }}>{val}</span>
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
