// ─── Design system tokens ─────────────────────────────────────────────────────
const DS = {
  bg:        '#0f0f0f',
  bgPanel:   '#161616',
  bgRaised:  '#1e1e1e',
  bgHover:   '#252525',
  border:    '#2a2a2a',
  borderMid: '#333',
  text:      '#f0f0f0',
  textSub:   '#888',
  textFaint: '#444',
  blue:      '#3b82f6',
  blueDim:   '#0f1e3d',
  green:     '#22c55e',
  greenDim:  '#0d2a18',
  red:       '#ef4444',
  redDim:    '#2d1414',
  amber:     '#f59e0b',
  amberDim:  '#2d200a',
  cloud:     '#3b82f6',
  local:     '#ef4444',
  fontSans:  "'DM Sans', sans-serif",
  fontMono:  "'DM Mono', monospace",
};

const ACCT_META = {
  rrsp:   { label:'RRSP',          color:'#a78bfa', bg:'rgba(167,139,250,0.12)' },
  tfsa:   { label:'TFSA',          color:'#14b8a6', bg:'rgba(20,184,166,0.12)'  },
  unreg:  { label:'Unregistered',  color:'#f97316', bg:'rgba(249,115,22,0.12)'  },
  crypto: { label:'Crypto',        color:'#8b5cf6', bg:'rgba(139,92,246,0.12)'  },
};

// ── Primitives ────────────────────────────────────────────────────────────────

function AcctBadge({ acct, size = 10 }) {
  const m = ACCT_META[acct] || { label: acct, color: '#888', bg: '#222' };
  return (
    <span style={{ display:'inline-block', padding:'1px 6px',
      border:`1px solid ${m.color}`, borderRadius:3, fontSize:size,
      fontFamily:DS.fontMono, color:m.color, background:m.bg, whiteSpace:'nowrap' }}>
      {m.label}
    </span>
  );
}

function PrivBadge({ type = 'cloud', size = 9 }) {
  const isCloud = type === 'cloud';
  return (
    <span style={{ display:'inline-flex', alignItems:'center', gap:3,
      padding:'1px 5px', borderRadius:2, fontSize:size, whiteSpace:'nowrap',
      fontFamily:DS.fontSans,
      border:`1px solid ${isCloud ? '#1d3a6e' : '#5a1a1a'}`,
      background:isCloud ? '#0a1428' : '#1a0a0a',
      color:isCloud ? '#60a5fa' : '#f87171' }}>
      {isCloud ? '☁' : '🔒'} {isCloud ? 'cloud' : 'local'}
    </span>
  );
}

function KPICard({ label, value, sub, privacy, valueColor, accent, style = {}, blurred = false }) {
  return (
    <div style={{ background:DS.bgRaised, border:`1px solid ${DS.border}`,
      borderRadius:4, padding:'12px 14px',
      borderTop: accent ? `2px solid ${accent}` : `2px solid transparent`,
      ...style }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:4, gap:6 }}>
        <span style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub, letterSpacing:0.3, flex:1 }}>{label}</span>
        {privacy && <PrivBadge type={privacy}/>}
      </div>
      <div style={{ fontFamily:DS.fontMono, fontSize:20, fontWeight:700, lineHeight:1, marginBottom:4,
        color: valueColor || DS.text,
        filter: blurred ? 'blur(6px)' : 'none', userSelect: blurred ? 'none' : 'auto',
        transition:'filter 0.3s' }}>
        {value}
      </div>
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
      <div style={{ width:`${Math.min(100, Math.max(0, pct))}%`, height:'100%',
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
      fontStyle:'italic', marginTop:3, lineHeight:1.4 }}>
      {children}
    </div>
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

// ── Top navigation ─────────────────────────────────────────────────────────────
function TopNav({ screen, setScreen, publicView, setPublicView }) {
  const SCREENS = [
    { id:'cockpit',   label:'Cockpit'   },
    { id:'holdings',  label:'Holdings'  },
    { id:'leverage',  label:'Leverage'  },
    { id:'networth',  label:'Net Worth' },
    { id:'watchlist', label:'Watchlist' },
    { id:'settings',  label:'Settings'  },
  ];
  return (
    <div style={{ position:'fixed', top:0, left:0, right:0, height:44, zIndex:100,
      background:'#141414', borderBottom:`1px solid ${DS.border}`,
      display:'flex', alignItems:'center', padding:'0 20px', gap:0 }}>
      <div style={{ fontFamily:DS.fontMono, fontSize:14, fontWeight:700,
        color:DS.text, marginRight:24, letterSpacing:-0.5 }}>IM</div>
      {SCREENS.map(s => (
        <button key={s.id} onClick={() => setScreen(s.id)} style={{
          background:'none', border:'none', cursor:'pointer',
          padding:'0 14px', height:44, fontSize:13, fontFamily:DS.fontSans,
          color: screen === s.id ? DS.blue : '#666',
          borderBottom: screen === s.id ? `2px solid ${DS.blue}` : '2px solid transparent',
          transition:'color 0.15s' }}>
          {s.label}
        </button>
      ))}
      <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:10 }}>
        <button onClick={() => setPublicView(p => !p)} style={{
          background: publicView ? DS.blueDim : 'transparent',
          border:`1px solid ${publicView ? DS.blue : '#444'}`,
          borderRadius:4, padding:'3px 10px', cursor:'pointer',
          fontFamily:DS.fontSans, fontSize:11,
          color: publicView ? DS.blue : '#666' }}>
          ☁ {publicView ? 'Public view' : 'Full view'}
        </button>
        <span style={{ fontFamily:DS.fontMono, fontSize:10, color:DS.textFaint }}>{MOCK.asOf}</span>
      </div>
    </div>
  );
}

// ── Account scope strip ────────────────────────────────────────────────────────
function ScopeStrip({ scope, setScope }) {
  const opts = [
    { id:'all', label:'All accounts' },
    ...MOCK.accounts,
  ];
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
            cursor:'pointer', transition:'all 0.1s' }}>
            {o.label}
          </button>
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
      padding:'8px 20px',
      display:'flex', alignItems:'center', justifyContent:'space-between',
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
  DS, ACCT_META,
  AcctBadge, PrivBadge, KPICard, Divider, SectionHead,
  GLCell, Bar, Panel, InlineHelp, FormRow,
  TopNav, ScopeStrip, SessionBanner,
});
