// ─── Watchlist v3 ── CHANGE 8: taller sparkbar, better marker visibility ──────
// CHANGE 10: Gap % column color-coded with distance context

function WatchlistScreen() {
  const [items, setItems]       = React.useState(MOCK.watchlist.map((w, i) => ({ ...w, id: i })));
  const [editId, setEditId]     = React.useState(null);
  const [editTarget, setEditTarget] = React.useState('');
  const [editNote,   setEditNote]   = React.useState('');
  const [deleteId,   setDeleteId]   = React.useState(null);
  const [showAdd,    setShowAdd]    = React.useState(false);
  const [newTicker,  setNewTicker]  = React.useState('');
  const [newTarget,  setNewTarget]  = React.useState('');
  const [newNote,    setNewNote]    = React.useState('');

  const VOL_META = {
    Low:  { color: DS.green, shape: '●' },
    Med:  { color: DS.amber, shape: '◆' },
    High: { color: DS.red,   shape: '▲' },
  };

  function startEdit(w)  { setEditId(w.id); setEditTarget(w.target.toFixed(2)); setEditNote(w.note); }
  function saveEdit(id)  {
    setItems(items => items.map(w => w.id===id ? { ...w, target:parseFloat(editTarget)||w.target, note:editNote } : w));
    setEditId(null);
  }
  function doDelete(id)  { setItems(items => items.filter(w => w.id!==id)); setDeleteId(null); }
  function addItem() {
    if (!newTicker || !newTarget) return;
    setItems(items => [...items, {
      id:Date.now(), ticker:newTicker.toUpperCase(), name:'—',
      price:0, target:parseFloat(newTarget), lo52:0, hi52:0, vol:'Low', note:newNote,
    }]);
    setNewTicker(''); setNewTarget(''); setNewNote(''); setShowAdd(false);
  }

  // Empty state
  if (items.length === 0) {
    return (
      <div style={{ padding:'20px' }}>
        <div style={{ display:'flex', justifyContent:'flex-end', marginBottom:12 }}>
          <button onClick={() => setShowAdd(true)} style={{ padding:'5px 14px',
            border:`1px solid ${DS.blue}`, borderRadius:3, background:DS.blueDim,
            fontFamily:DS.fontSans, fontSize:12, color:DS.blue, cursor:'pointer' }}>
            + Add ticker
          </button>
        </div>
        <div style={{ textAlign:'center', padding:'80px 20px',
          background:DS.bgPanel, border:`1px solid ${DS.border}`, borderRadius:4 }}>
          <div style={{ fontSize:32, marginBottom:12, opacity:0.3 }}>◎</div>
          <div style={{ fontFamily:DS.fontSans, fontSize:15, color:DS.textSub, marginBottom:6 }}>
            No tickers on your watchlist yet
          </div>
          <div style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textFaint }}>
            Add a ticker and a target price to start tracking distance-to-buy.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding:'20px' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textFaint }}>
            Tickers and prices are not blurred in privacy mode.
          </span>
        </div>
        <button onClick={() => setShowAdd(s => !s)} style={{ padding:'5px 14px',
          border:`1px solid ${DS.blue}`, borderRadius:3,
          background: showAdd ? DS.blueDim : 'transparent',
          fontFamily:DS.fontSans, fontSize:12, color:DS.blue, cursor:'pointer' }}>
          {showAdd ? '✕ Cancel' : '+ Add ticker'}
        </button>
      </div>

      {showAdd && (
        <div style={{ marginBottom:12, padding:'14px 16px', background:DS.bgPanel,
          border:`1px solid ${DS.border}`, borderRadius:4,
          display:'flex', gap:10, alignItems:'flex-end', flexWrap:'wrap' }}>
          {[
            { label:'Ticker', val:newTicker, set:setNewTicker, w:100, ph:'e.g. ATD.TO' },
            { label:'Target price', val:newTarget, set:setNewTarget, w:120, ph:'0.00', type:'number' },
            { label:'Notes (optional)', val:newNote, set:setNewNote, w:240, ph:'Brief rationale' },
          ].map(({ label, val, set, w, ph, type }) => (
            <div key={label}>
              <div style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textSub, marginBottom:4 }}>{label}</div>
              <input value={val} onChange={e => set(e.target.value)} placeholder={ph} type={type||'text'}
                style={{ width:w, padding:'7px 10px', background:DS.bgRaised,
                  border:`1px solid ${DS.border}`, borderRadius:3,
                  color:DS.text, fontFamily:DS.fontMono, fontSize:13, outline:'none' }}/>
            </div>
          ))}
          <button onClick={addItem} style={{ padding:'7px 18px', background:DS.blue,
            border:'none', borderRadius:3, cursor:'pointer',
            fontFamily:DS.fontSans, fontSize:13, fontWeight:600, color:'#fff', marginBottom:1 }}>Add</button>
        </div>
      )}

      <Panel>
        <table style={{ width:'100%', borderCollapse:'collapse' }}>
          <thead>
            <tr style={{ background:DS.bgRaised }}>
              {[['Ticker','left',110],['Name','left',180],['Current','right',100],
                ['Today','right',90],['Target','right',120],['Gap %','right',100],
                ['Notes','left',0],['','right',110]
              ].map(([h,align,w]) => (
                <th key={h} style={{ padding:'8px 12px', textAlign:align, width:w||undefined,
                  fontFamily:DS.fontSans, fontSize:10, fontWeight:600,
                  color:DS.textSub, borderBottom:`1px solid ${DS.border}`,
                  letterSpacing:0.4, whiteSpace:'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((w, i) => {
              const gap = w.price > 0 ? ((w.price - w.target) / w.target * 100) : 0;
              const vm  = VOL_META[w.vol] || VOL_META.Med;
              const isEditing  = editId === w.id;
              const isDeleting = deleteId === w.id;
              // Gap color: green=at/below target, amber=within 10%, red=>10% away
              const gapColor = gap<=0 ? DS.green : Math.abs(gap)<10 ? DS.amber : DS.red;

              return (
                <tr key={w.id} style={{ background: isEditing ? DS.bgHover : i%2 ? DS.bgRaised : 'transparent',
                  transition:'background 0.1s' }}>

                  <td style={{ padding:'10px 12px', borderBottom:`1px solid ${DS.border}` }}>
                    <a href={`https://finance.yahoo.com/quote/${w.ticker}`}
                      target="_blank" rel="noreferrer"
                      style={{ fontFamily:DS.fontMono, fontSize:13, fontWeight:700,
                        color:DS.blue, textDecoration:'none', borderBottom:`1px solid ${DS.blue}44` }}>
                      {w.ticker}
                    </a>
                    {w.currency==='USD' && (
                      <span style={{ marginLeft:5, fontSize:8, color:DS.amber,
                        border:`1px solid ${DS.amber}`, borderRadius:2, padding:'0 2px' }}>USD</span>
                    )}
                  </td>

                  <td style={{ padding:'10px 12px', borderBottom:`1px solid ${DS.border}`,
                    fontFamily:DS.fontSans, fontSize:12, color:DS.textSub }}>{w.name}</td>

                  <td style={{ padding:'10px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`,
                    fontFamily:DS.fontMono, fontSize:13, color:DS.text, fontWeight:600 }}>
                    {w.price > 0 ? `$${w.price.toFixed(2)}` : '—'}
                  </td>

                  <td style={{ padding:'10px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`,
                    fontFamily:DS.fontMono, fontSize:12,
                    color: w.changePct>=0 ? DS.green : DS.red }}>
                    {w.changePct>=0?'▲':'▼'} {Math.abs(w.changePct).toFixed(2)}%
                  </td>

                  <td style={{ padding:'6px 12px', textAlign:'right', borderBottom:`1px solid ${DS.border}` }}>
                    {isEditing ? (
                      <input type="number" step="0.01" value={editTarget}
                        onChange={e => setEditTarget(e.target.value)} autoFocus
                        style={{ width:90, padding:'4px 8px', textAlign:'right',
                          background:DS.bg, border:`1px solid ${DS.blue}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontMono, fontSize:13, outline:'none' }}/>
                    ) : (
                      <span style={{ fontFamily:DS.fontMono, fontSize:13, color:DS.blue }}>
                        ${w.target.toFixed(2)}</span>
                    )}
                  </td>

                  {/* CHANGE 10: Gap % with distance-based color + label */}
                  <td style={{ padding:'10px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}` }}>
                    {w.price > 0 ? (
                      <span style={{ fontFamily:DS.fontMono, fontSize:12, color:gapColor,
                        display:'flex', alignItems:'center', justifyContent:'flex-end', gap:4 }}>
                        <span style={{ width:6, height:6, borderRadius:'50%',
                          background:gapColor, display:'inline-block', opacity:0.8 }}/>
                        {gap<=0 ? 'At target' : `▼ ${Math.abs(gap).toFixed(1)}%`}
                      </span>
                    ) : '—'}
                  </td>

                  <td style={{ padding:'6px 12px', borderBottom:`1px solid ${DS.border}` }}>
                    {isEditing ? (
                      <input value={editNote} onChange={e => setEditNote(e.target.value)}
                        style={{ width:'100%', padding:'4px 8px', background:DS.bg,
                          border:`1px solid ${DS.border}`, borderRadius:3,
                          color:DS.text, fontFamily:DS.fontSans, fontSize:12, outline:'none' }}/>
                    ) : (
                      <span style={{ fontFamily:DS.fontSans, fontSize:12, color:DS.textSub,
                        fontStyle: w.note ? 'italic' : 'normal' }}>
                        {w.note || <span style={{ color:DS.textFaint }}>—</span>}
                      </span>
                    )}
                  </td>

                  <td style={{ padding:'6px 12px', textAlign:'right',
                    borderBottom:`1px solid ${DS.border}`, whiteSpace:'nowrap' }}>
                    {isDeleting ? (
                      <span style={{ display:'inline-flex', gap:6 }}>
                        <button onClick={() => doDelete(w.id)} style={{ padding:'3px 10px',
                          background:DS.redDim, border:`1px solid ${DS.red}`, borderRadius:3,
                          cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.red }}>Delete</button>
                        <button onClick={() => setDeleteId(null)} style={{ padding:'3px 8px',
                          background:'transparent', border:`1px solid ${DS.border}`, borderRadius:3,
                          cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>Cancel</button>
                      </span>
                    ) : isEditing ? (
                      <span style={{ display:'inline-flex', gap:6 }}>
                        <button onClick={() => saveEdit(w.id)} style={{ padding:'3px 10px',
                          background:DS.greenDim, border:`1px solid ${DS.green}`, borderRadius:3,
                          cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.green }}>Save</button>
                        <button onClick={() => setEditId(null)} style={{ padding:'3px 8px',
                          background:'transparent', border:`1px solid ${DS.border}`, borderRadius:3,
                          cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.textSub }}>Cancel</button>
                      </span>
                    ) : (
                      <span style={{ display:'inline-flex', gap:6 }}>
                        <button onClick={() => startEdit(w)} style={{ padding:'3px 10px',
                          background:'transparent', border:`1px solid ${DS.border}`, borderRadius:3,
                          cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.blue }}>Edit</button>
                        <button onClick={() => setDeleteId(w.id)} style={{ padding:'3px 8px',
                          background:'transparent', border:`1px solid ${DS.border}`, borderRadius:3,
                          cursor:'pointer', fontFamily:DS.fontSans, fontSize:11, color:DS.textFaint }}>✕</button>
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div style={{ padding:'8px 12px', background:DS.bgRaised, borderTop:`1px solid ${DS.border}` }}>
          <span style={{ fontFamily:DS.fontSans, fontSize:10, color:DS.textFaint, fontStyle:'italic' }}>Click Edit to update target price or notes</span>
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, { WatchlistScreen });
