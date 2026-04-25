// ─── Login gate — clean local lock screen ────────────────────────────────────

function LoginScreen({ onLogin }) {
  const [pw, setPw]        = React.useState('');
  const [error, setErr]    = React.useState(false);
  const [loading, setLoad] = React.useState(false);

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

      <div style={{ width:360 }}>

        {/* Wordmark */}
        <div style={{ marginBottom:32, textAlign:'center' }}>
          <div style={{ fontFamily:DS.fontMono, fontSize:36, fontWeight:700,
            color:DS.text, letterSpacing:-2, marginBottom:6 }}>IM</div>
          <div style={{ fontFamily:DS.fontSans, fontSize:13, color:DS.textSub }}>
            Investments Monitor · personal</div>
        </div>

        {/* Login card */}
        <div style={{ background:DS.bgPanel, border:`1px solid ${DS.border}`,
          borderRadius:6, padding:'28px 24px' }}>

          <div style={{ textAlign:'center', marginBottom:24 }}>
            <div style={{ fontSize:32, marginBottom:8, opacity:0.3 }}>🔒</div>
            <div style={{ fontFamily:DS.fontSans, fontSize:15, fontWeight:600,
              color:DS.text, marginBottom:6 }}>This data is private</div>
            <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub, lineHeight:1.5 }}>
              All holdings, balances and net worth live locally on this machine.
              Enter your password to unlock.
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom:14 }}>
              <label style={{ fontFamily:DS.fontSans, fontSize:11, color:DS.textSub,
                display:'block', marginBottom:5, letterSpacing:0.3 }}>PASSWORD</label>
              <input type="password" value={pw}
                onChange={e => { setPw(e.target.value); setErr(false); }}
                placeholder="Enter password" autoFocus
                style={{ width:'100%', padding:'10px 12px', background:DS.bgRaised,
                  border:`1px solid ${error ? DS.red : DS.border}`,
                  borderRadius:4, color:DS.text, fontFamily:DS.fontMono,
                  fontSize:14, outline:'none' }}/>
              {error && (
                <div style={{ fontFamily:DS.fontSans, fontSize:11,
                  color:DS.red, marginTop:5 }}>Incorrect password</div>
              )}
            </div>
            <button type="submit" disabled={loading} style={{
              width:'100%', padding:'11px', background: loading ? DS.bgRaised : DS.blue,
              border:'none', borderRadius:4, cursor: loading ? 'default' : 'pointer',
              fontFamily:DS.fontSans, fontSize:14, fontWeight:600,
              color: loading ? DS.textSub : '#fff', transition:'background 0.2s' }}>
              {loading ? 'Unlocking…' : 'Unlock →'}
            </button>
          </form>

          <div style={{ marginTop:14, fontFamily:DS.fontSans, fontSize:10,
            color:DS.textFaint, textAlign:'center', fontStyle:'italic' }}>
            Demo: type any password to unlock
          </div>
        </div>

        <div style={{ marginTop:16, textAlign:'center', fontFamily:DS.fontSans,
          fontSize:11, color:DS.textFaint }}>
          Session auto-locks after {MOCK.settings.sessionTimeoutMin} min of inactivity
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { LoginScreen });
