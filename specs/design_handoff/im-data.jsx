// ─── Mock data & shared state (v2) ───────────────────────────────────────────
// All aggregates in CAD. BOC daily FX used for USD conversions.

const FX_USD_CAD = 1.378;
const FX_FETCHED = 'Apr 23, 2026 09:00 EDT';

const MOCK = {
  fxRate:   FX_USD_CAD,
  fxSource: 'Bank of Canada daily rate',
  fxFetched: FX_FETCHED,
  asOf: 'Apr 23, 2026  14:32 EDT',

  accounts: [
    { id:'rrsp',   label:'RRSP',          color:'#a78bfa', bg:'rgba(167,139,250,0.12)' },
    { id:'tfsa',   label:'TFSA',          color:'#14b8a6', bg:'rgba(20,184,166,0.12)'  },
    { id:'unreg',  label:'Unregistered',  color:'#f97316', bg:'rgba(249,115,22,0.12)'  },
    { id:'crypto', label:'Crypto',        color:'#8b5cf6', bg:'rgba(139,92,246,0.12)'  },
  ],

  holdings: [
    { ticker:'RY.TO',   name:'Royal Bank of Canada',     acct:'rrsp',   qty:180,  acbPS:210.44, priceCAD:234.33, currency:'CAD', assetClass:'Stock',  country:'CA', changePct: +0.82 },
    { ticker:'SHOP.TO', name:'Shopify Inc.',              acct:'tfsa',   qty:22,   acbPS:1188.20,priceCAD:1747.27,currency:'CAD', assetClass:'Stock',  country:'CA', changePct: -1.34 },
    { ticker:'BTC-CAD', name:'Bitcoin',                   acct:'crypto', qty:1.20, acbPS:29833,  priceCAD:42667,  currency:'CAD', assetClass:'Crypto', country:'—',  changePct: +3.21 },
    { ticker:'XIU.TO',  name:'iShares S&P/TSX 60 ETF',   acct:'unreg',  qty:310,  acbPS:102.60, priceCAD:100.00, currency:'CAD', assetClass:'ETF',    country:'CA', changePct: -0.44 },
    { ticker:'MSFT',    name:'Microsoft Corp',            acct:'rrsp',   qty:46,   acbPS:310.20, priceCAD:423.80*FX_USD_CAD, currency:'USD', priceUSD:423.80, assetClass:'Stock', country:'US', changePct: +1.07 },
    { ticker:'ENB.TO',  name:'Enbridge Inc.',             acct:'unreg',  qty:420,  acbPS:45.20,  priceCAD:57.10,  currency:'CAD', assetClass:'Stock',  country:'CA', changePct: +0.29 },
    { ticker:'XEQT.TO', name:'iShares Core Equity ETF',  acct:'tfsa',   qty:180,  acbPS:28.40,  priceCAD:32.10,  currency:'CAD', assetClass:'ETF',    country:'CA', changePct: +0.55 },
    { ticker:'TD.TO',   name:'TD Bank Group',             acct:'unreg',  qty:200,  acbPS:72.30,  priceCAD:65.10,  currency:'CAD', assetClass:'Stock',  country:'CA', changePct: -0.91 },
    { ticker:'VFV.TO',  name:'Vanguard S&P 500 ETF',     acct:'rrsp',   qty:88,   acbPS:116.20, priceCAD:145.20, currency:'CAD', assetClass:'ETF',    country:'US', changePct: +0.73 },
    { ticker:'ETH-CAD', name:'Ethereum',                  acct:'crypto', qty:4.0,  acbPS:2890,   priceCAD:3870,   currency:'CAD', assetClass:'Crypto', country:'—',  changePct: +2.14 },
  ],

  heloc: {
    limit:  150000,
    drawn:   94000,
    rate:      6.95,
    ledger: [
      { date:'2026-01-15', amount: 30000, purpose:'Buy MSFT (unreg.)' },
      { date:'2026-02-03', amount: 25000, purpose:'Buy ENB.TO (unreg.)' },
      { date:'2026-03-08', amount: 20000, purpose:'Home reno — kitchen' },
      { date:'2026-03-22', amount: -5000, purpose:'Partial repayment' },
      { date:'2026-04-01', amount: 24000, purpose:'Buy RY.TO (unreg.)' },
    ],
  },

  margin: {
    broker:         'Questrade',
    acct:           'unreg',
    balance:         75000,
    limit:          120000,
    rate:             7.45,
    callThreshold:    0.70,
    ledger: [
      { date:'2025-11-10', amount: 40000, purpose:'Initial draw — ENB.TO' },
      { date:'2026-01-28', amount: 35000, purpose:'Buy TD.TO + XIU.TO (unreg.)' },
    ],
  },

  property: {
    value:           880000,
    mortgageBalance: 412000,
    rate:              4.89,
    renewalDate:    'Mar 2027',
  },

  watchlist: [
    { ticker:'ATD.TO',  name:'Alimentation Couche-Tard', price:72.40,  target:68.00,  lo52:58.10,  hi52:80.20,  vol:'Low',  note:'Dip on guidance miss',        changePct: -0.62 },
    { ticker:'ENB.TO',  name:'Enbridge Inc.',             price:57.10,  target:52.00,  lo52:48.40,  hi52:60.80,  vol:'Low',  note:'Yield play; wait for rate cut',changePct: +0.29 },
    { ticker:'VFV.TO',  name:'Vanguard S&P 500 ETF',     price:145.20, target:138.00, lo52:112.30, hi52:149.40, vol:'Med',  note:'Near ATH, wait for pullback',  changePct: +0.73 },
    { ticker:'CNR.TO',  name:'CN Rail',                   price:162.40, target:148.00, lo52:134.20, hi52:174.00, vol:'Low',  note:'Patient — recession exposure', changePct: -0.18 },
    { ticker:'NVDA',    name:'NVIDIA Corp',               price:891.20, target:750.00, lo52:560.00, hi52:974.00, vol:'High', note:'USD · small starter only', currency:'USD', changePct: +2.34 },
    { ticker:'BCE.TO',  name:'BCE Inc.',                  price:33.80,  target:30.00,  lo52:28.60,  hi52:48.20,  vol:'Low',  note:'Dividend cut risk; speculative',changePct: -1.05 },
  ],

  cash: 22400,

  settings: {
    sessionTimeoutMin: 15,
    helocRate:          6.95,
    helocLimit:       150000,
    refreshEnabled:    true,
    refreshIntervalMin: 30,
    lastRefresh:       'Apr 23, 2026 14:00 EDT',
    publicSummaryPath: '/var/www/public/summary.json',
    lastPushAt:        'Apr 23, 2026 08:00 EDT',
    version:           '0.1.4-alpha',
    branch:            'main',
    lastCommit:        'a3f9c12',
    importFiles: [
      { name:'questrade_2026-04-22.csv', broker:'Questrade', importedAt:'Apr 22, 2026 20:14', rows:10 },
      { name:'questrade_2026-03-31.csv', broker:'Questrade', importedAt:'Mar 31, 2026 19:55', rows:9  },
    ],
  },
};

// ── Derived helpers ────────────────────────────────────────────────────────────

function derivePortfolio(holdings) {
  return holdings.map(h => {
    const mktVal  = h.qty * h.priceCAD;
    const acbTotal = h.qty * h.acbPS;
    const gl      = mktVal - acbTotal;
    const glPct   = acbTotal > 0 ? (gl / acbTotal) * 100 : 0;
    return { ...h, mktVal, acbTotal, gl, glPct };
  });
}

function portfolioTotal(holdings) {
  return holdings.reduce((s, h) => s + h.qty * h.priceCAD, 0);
}

function computeLeverage(portVal, helocDrawn, marginBal) {
  const totalBorrowed = helocDrawn + marginBal;
  const equity        = portVal - totalBorrowed;
  const ratio         = equity > 0 ? portVal / equity : 99;
  return { totalBorrowed, equity, ratio };
}

// ── Allocation grouping ────────────────────────────────────────────────────────
// Returns [{id, label, color, val, pct}] for a given dimension.

const DIM_COLORS = {
  account:    { rrsp:'#a78bfa', tfsa:'#14b8a6', unreg:'#f97316', crypto:'#8b5cf6' },
  assetClass: { Stock:'#3b82f6', ETF:'#22c55e', Crypto:'#8b5cf6', LeveragedETF:'#f59e0b', Cash:'#6b7280' },
  country:    { CA:'#ef4444', US:'#3b82f6', '—':'#6b7280' },
  currency:   { CAD:'#14b8a6', USD:'#f97316' },
};

const DIM_LABEL = { CA:'Canada', US:'United States', '—':'N/A' };

function groupAllocation(holdings, dim) {
  const derived = derivePortfolio(holdings);
  const total   = portfolioTotal(holdings);
  const map     = {};
  derived.forEach(h => {
    const key = dim === 'account' ? h.acct
              : dim === 'assetClass' ? h.assetClass
              : dim === 'country'    ? h.country
              :                       h.currency;
    map[key] = (map[key] || 0) + h.mktVal;
  });
  const colors = DIM_COLORS[dim] || {};
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .map(([id, val]) => ({
      id,
      label: dim === 'account'
        ? (MOCK.accounts.find(a => a.id === id)?.label || id)
        : (DIM_LABEL[id] || id),
      color: colors[id] || '#6b7280',
      val,
      pct: total > 0 ? val / total * 100 : 0,
    }));
}

// ── Formatting ─────────────────────────────────────────────────────────────────

function fmtCAD(n, decimals = 0) {
  const abs = Math.abs(n);
  const str = abs.toLocaleString('en-CA', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return (n < 0 ? '-' : '') + '$' + str;
}

function fmtPct(n, decimals = 1) {
  return (n >= 0 ? '+' : '') + n.toFixed(decimals) + '%';
}

function fmtNum(n, decimals = 2) {
  return n.toLocaleString('en-CA', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

Object.assign(window, {
  MOCK, FX_USD_CAD,
  derivePortfolio, portfolioTotal, computeLeverage, groupAllocation,
  fmtCAD, fmtPct, fmtNum,
  DIM_COLORS,
});
