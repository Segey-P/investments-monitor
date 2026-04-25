// ─── Design system tokens (unchanged) ─────────────────────────────────────────
const DS = {
  bg:'#0f0f0f', bgPanel:'#161616', bgRaised:'#1e1e1e', bgHover:'#252525',
  border:'#2a2a2a', borderMid:'#333',
  text:'#f0f0f0', textSub:'#888', textFaint:'#444',
  blue:'#3b82f6', blueDim:'#0f1e3d',
  green:'#22c55e', greenDim:'#0d2a18',
  red:'#ef4444',  redDim:'#2d1414',
  amber:'#f59e0b', amberDim:'#2d200a',
  cloud:'#3b82f6', local:'#ef4444',
  fontSans:"'DM Sans', sans-serif",
  fontMono:"'DM Mono', monospace",
};

const ACCT_META = {
  rrsp:  { label:'RRSP',         color:'#a78bfa', bg:'rgba(167,139,250,0.12)' },
  tfsa:  { label:'TFSA',         color:'#14b8a6', bg:'rgba(20,184,166,0.12)'  },
  unreg: { label:'Unregistered', color:'#f97316', bg:'rgba(249,115,22,0.12)'  },
  crypto:{ label:'Crypto',       color:'#8b5cf6', bg:'rgba(139,92,246,0.12)'  },
};

// ── Change-review system ──────────────────────────────────────────────────────
// Context is placed on window so cross-scope scripts can reach it
const ChangesCtx = React.createContext({ showMarkers: false });
window.ChangesCtx = ChangesCtx;

function ChangeMarker({ id, children, style: extraStyle = {} }) {
  const { showMarkers } = React.useContext(window.ChangesCtx);
  // Always render wrapper so layout styles (gridColumn etc.) always apply
  return (
    <div id={`change-${id}`} style={{
      position:'relative',
      ...(showMarkers ? {
        outline:'1.5px dashed rgba(245,158,11,0.6)',
        borderRadius:5,
        boxShadow:'0 0 12px rgba(245,158,11,0.08)',
      } : {}),
      ...extraStyle }}>
      {showMarkers && (
        <div style={{ position:'absolute', top:-9, right:-9, zIndex:1001,
          background:'#f59e0b', color:'#000', fontFamily:DS.fontMono, fontSize:9,
          fontWeight:700, width:18, height:18, borderRadius:'50%',
          display:'flex', alignItems:'center', justifyContent:'center', lineHeight:1,
          boxShadow:'0 2px 6px rgba(0,0,0,0.5)' }}>{id}</div>
      )}
      {children}
    </div>
  );
}

// Screen-level privacy legend — replaces per-row PrivBadge clutter
function PrivLegend({ items }) {
  // items: [{ type:'local'|'cloud', label }]
  return (
    <div style={{ display:'flex', gap:12, alignItems:'center', flexWrap:'wrap' }}>
      {items.map(({ type, label }) => {
        const isCloud = type === 'cloud';
        return (
          <span key={type+label} style={{ display:'inline-flex', alignItems:'center', gap:5,
            fontFamily:DS.fontSans, fontSize:11, color: isCloud ? '#60a5fa' : '#f87171' }}>
            <span style={{ display:'inline-block', width:7, height:7, borderRadius:'50%',
              background: isCloud ? '#3b82f6' : '#ef4444', opacity:0.8 }}/>
            {isCloud ? '☁' : '🔒'} {label}
          </span>
        );
      })}
    </div>
  );
}

// ── Primitives (unchanged) ────────────────────────────────────────────────────
function AcctBadge({ acct, size = 10 }) {
  const m = ACCT_META[acct] || { label: acct, color: '#888', bg: '#222' };
  return (
    <span style={{ display:'inline-block', padding:'1px 6px', border:`1px solid ${m.color}`,
      borderRadius:3, fontSize:size, fontFamily:DS.fontMono, color:m.color,
      background:m.bg, whiteSpace:'nowrap' }}>{m.label}</span>
  );
}

function PrivBadge({ type = 'cloud', size = 9 }) {
  const isCloud = type === 'cloud';
  return (
    <span style={{ display:'inline-flex', alignItems:'center', gap:3, padding:'1px 5px',
      borderRadius:2, fontSize:size, whiteSpace:'nowrap', fontFamily:DS.fontSans,
      border:`1px solid ${isCloud ? '#1d3a6e' : '#5a1a1a'}`,
      background:isCloud ? '#0a1428' : '#1a0a0a',
      color:isCloud ? '#60a5fa' : '#f87171' }}>
      {isCloud ? '☁' : '🔒'} {isCloud ? 'cloud' : 'local'}
    </span>
  );
}

function KPICard({ label, value, sub, privacy, valueColor, accent, style = {}, blurred = false }) {
  return (
    <div style={{ background:DS.bgRaised, border:`1px solid ${DS.border}`, borderRadius:4,
      padding:'12px 14px', borderTop: accent ? `2px solid ${accent}` : `2px solid transparent`, ...style }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4, gap:6 }}>
        <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub, letterSpacing:0.3, flex:1 }}>{label}</span>
        {privacy && <PrivBadge type={privacy}/>}
      </div>
      <div style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700, lineHeight:1, marginBottom:4,
        color: valueColor || DS.text, filter: blurred ? 'blur(6px)' : 'none',
        userSelect: blurred ? 'none' : 'auto', transition:'filter 0.3s' }}>{value}</div>
      {sub && <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>{sub}</div>}
    </div>
  );
}

function Divider({ my = 0 }) {
  return <div style={{ height:1, background:DS.border, margin:`${my}px 0` }}/>;
}

function SectionHead({ children, right }) {
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between',
      padding:'9px 14px', borderBottom:`1px solid ${DS.border}` }}>
      <span style={{ fontFamily:DS.fontSans, fontSize:11, fontWeight:600,
        color:DS.textSub, letterSpacing:0.8, textTransform:'uppercase' }}>{children}</span>
      {right}
    </div>
  );
}

function GLCell({ value, pct, mono = true }) {
  const pos = value >= 0;
  return (
    <span style={{ color: pos ? DS.green : DS.red,
      fontFamily: mono ? DS.fontMono : DS.fontSans, fontSize:12, whiteSpace:'nowrap' }}>
      {pos ? '▲' : '▼'} {fmtCAD(Math.abs(value))}
      {pct !== undefined && <span style={{ fontSize:10, marginLeft:4, opacity:0.75 }}>({fmtPct(pct)})</span>}
    </span>
  );
}

function Bar({ pct, color = DS.blue, height = 5, style = {} }) {
  return (
    <div style={{ height, background:DS.border, borderRadius:height, overflow:'hidden', ...style }}>
      <div style={{ width:`${Math.min(100,Math.max(0,pct))}%`, height:'100%',
        background:color, borderRadius:height }}/>
    </div>
  );
}

function Panel({ children, style = {} }) {
  return (
    <div style={{ background:DS.bgPanel, border:`1px solid ${DS.border}`,
      borderRadius:4, overflow:'hidden', ...style }}>
      {children}
    </div>
  );
}

function InlineHelp({ children }) {
  return (
    <div style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint,
      fontStyle:'italic', marginTop:3, lineHeight:1.4 }}>{children}</div>
  );
}

function FormRow({ label, help, children }) {
  return (
    <div style={{ padding:'12px 0', borderBottom:`1px solid ${DS.border}` }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:16 }}>
        <div style={{ flex:1 }}>
          <div style={{ fontFamily:DS.fontSans, fontSize:13, color:DS.text }}>{label}</div>
          {help && <InlineHelp>{help}</InlineHelp>}
        </div>
        <div style={{ display:'flex', alignItems:'center', minWidth:200 }}>{children}</div>
      </div>
    </div>
  );
}

// ── PrivBadge — kept as component but no longer rendered in screens ───────────
// Cloud/local distinction removed; privacy is handled by the Hide values toggle.

// ── CHANGE 2: TopNav with active-screen subtitle ──────────────────────────────
const SCREEN_META = {
  cockpit:   { label:'Cockpit',   sub:'Portfolio summary & key ratios'  },
  holdings:  { label:'Holdings',  sub:'All positions · G/L & ACB'       },
  leverage:  { label:'Leverage',  sub:'HELOC & margin balances'          },
  networth:  { label:'Net Worth', sub:'Assets, liabilities & equity'    },
  watchlist: { label:'Watchlist', sub:'Target prices & gap tracking'    },
  settings:  { label:'Settings',  sub:'Config, security & imports'      },
};

function TopNav({ screen, setScreen, publicView, setPublicView, reviewMode, setReviewMode, changeCount }) {
  const SCREENS = Object.keys(SCREEN_META);
  return (
    <div style={{ position:'fixed', top:0, left:0, right:0, height:44, zIndex:100,
      background:'#141414', borderBottom:`1px solid ${DS.border}`,
      display:'flex', alignItems:'center', padding:'0 20px', gap:0 }}>
      <div style={{ fontFamily:DS.fontMono, fontSize:14, fontWeight:700,
        color:DS.text, marginRight:24, letterSpacing:-0.5 }}>IM</div>

      {SCREENS.map(id => {
        const m = SCREEN_META[id];
        const active = screen === id;
        return (
          <button key={id} onClick={() => setScreen(id)} title={m.sub} style={{
            background:'none', border:'none', cursor:'pointer',
            padding:'0 14px', height:44, display:'flex', flexDirection:'column',
            alignItems:'center', justifyContent:'center', gap:1,
            borderBottom: active ? `2px solid ${DS.blue}` : '2px solid transparent',
            transition:'color 0.15s' }}>
            <span style={{ fontSize:13, fontFamily:DS.fontSans,
              color: active ? DS.blue : '#666' }}>{m.label}</span>
            {active && (
              <span style={{ fontSize:9, fontFamily:DS.fontSans,
                color:'#555', letterSpacing:0.2, whiteSpace:'nowrap' }}>{m.sub}</span>
            )}
          </button>
        );
      })}

      <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:8 }}>
        {/* CHANGE 2 badge: Review mode toggle */}
        <button onClick={() => setReviewMode(r => !r)} style={{
          background: reviewMode ? '#2d200a' : 'transparent',
          border:`1px solid ${reviewMode ? DS.amber : '#333'}`,
          borderRadius:4, padding:'3px 10px', cursor:'pointer',
          fontFamily:DS.fontSans, fontSize:11,
          color: reviewMode ? DS.amber : '#555',
          display:'flex', alignItems:'center', gap:5 }}>
          <span style={{ width:8, height:8, borderRadius:'50%',
            background: reviewMode ? DS.amber : '#444',
            display:'inline-block', flexShrink:0 }}/>
          {reviewMode ? `Reviewing ${changeCount} changes` : `Review ${changeCount} changes`}
        </button>
        <button onClick={() => setPublicView(p => !p)}
          title={publicView ? 'Values hidden — click to show' : 'Click to hide sensitive values'}
          style={{
          background: publicView ? '#1a1a1a' : 'transparent',
          border:`1px solid ${publicView ? '#555' : '#333'}`,
          borderRadius:4, padding:'3px 10px', cursor:'pointer',
          fontFamily:DS.fontSans, fontSize:11,
          color: publicView ? DS.amber : '#555',
          display:'flex', alignItems:'center', gap:5 }}>
          <span style={{ fontSize:13 }}>{publicView ? '🙈' : '👁'}</span>
          {publicView ? 'Values hidden' : 'Hide values'}
        </button>
        <span style={{ fontFamily:DS.fontMono, fontSize:10, color:DS.textFaint }}>{MOCK.asOf}</span>
      </div>
    </div>
  );
}

// ── Account scope strip ────────────────────────────────────────────────────────
function ScopeStrip({ scope, setScope }) {
  const opts = [{ id:'all', label:'All accounts' }, ...MOCK.accounts];
  return (
    <div style={{ display:'flex', gap:6, padding:'7px 20px',
      background:'#141414', borderBottom:`1px solid ${DS.border}` }}>
      {opts.map(o => {
        const m = ACCT_META[o.id];
        const active = scope === o.id;
        return (
          <button key={o.id} onClick={() => setScope(o.id)} style={{
            padding:'2px 12px',
            border:`1px solid ${active && m ? m.color : '#333'}`,
            borderRadius:12,
            background: active && m ? m.bg : active ? DS.bgRaised : 'transparent',
            fontFamily:DS.fontSans, fontSize:12,
            color: active && m ? m.color : active ? DS.text : '#555',
            cursor:'pointer', transition:'all 0.1s' }}>{o.label}</button>
        );
      })}
    </div>
  );
}

// ── Session banner ─────────────────────────────────────────────────────────────
function SessionBanner({ secondsLeft, onDismiss, onExtend }) {
  if (secondsLeft === null) return null;
  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const expired = secondsLeft <= 0;
  return (
    <div style={{ position:'fixed', top:44, left:0, right:0, zIndex:200,
      background: expired ? DS.redDim : DS.amberDim,
      border:`1px solid ${expired ? DS.red : DS.amber}`,
      padding:'8px 20px', display:'flex', alignItems:'center', justifyContent:'space-between',
      fontFamily:DS.fontSans, fontSize:13 }}>
      <span style={{ color: expired ? DS.red : DS.amber }}>
        {expired
          ? '⚠ Session expired. Sign in again.'
          : `⚠ Session expires in ${mins}:${String(secs).padStart(2,'0')} · auto-lock enabled`}
      </span>
      {!expired && (
        <div style={{ display:'flex', gap:8 }}>
          <button onClick={onExtend} style={{ background:DS.blue, border:'none', borderRadius:3,
            padding:'3px 12px', cursor:'pointer', fontFamily:DS.fontSans, fontSize:12,
            color:'#fff', fontWeight:600 }}>Stay signed in</button>
          <button onClick={onDismiss} style={{ background:'transparent', border:`1px solid #555`,
            borderRadius:3, padding:'3px 10px', cursor:'pointer',
            fontFamily:DS.fontSans, fontSize:12, color:'#888' }}>Dismiss</button>
        </div>
      )}
    </div>
  );
}

Object.assign(window, {
  DS, ACCT_META, SCREEN_META,
  ChangesCtx, ChangeMarker, PrivLegend,
  AcctBadge, PrivBadge, KPICard, Divider, SectionHead,
  GLCell, Bar, Panel, InlineHelp, FormRow,
  TopNav, ScopeStrip, SessionBanner,
});
