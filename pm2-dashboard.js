#!/usr/bin/env node
/**
 * PM2 本地 Web 仪表盘
 * 使用: node pm2-dashboard.js
 * 访问: http://localhost:9615
 */
const http = require('http')
const pm2 = require('/opt/homebrew/lib/node_modules/pm2')

const PORT = 9615
const LOG_LINES = 80 // 每个服务保留最近多少行日志

// 内存中存储各服务日志
const logs = {}

// 判断一行是否已有时间戳（后端 Python logging 自带，无需重复添加）
const RE_HAS_TIMESTAMP = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}/

function nowStr() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function stampLines(lines) {
  return lines.map(l => RE_HAS_TIMESTAMP.test(l) ? l : `[${nowStr()}] ${l}`)
}

function tailFile(filePath, name, type) {
  if (!filePath) return
  const fs = require('fs')
  const key = `${name}-${type}`
  if (!logs[key]) logs[key] = []

  // 先读已有内容（历史行加时间戳占位，避免误导）
  try {
    const content = fs.readFileSync(filePath, 'utf8')
    const lines = content.split('\n').filter(Boolean)
    logs[key] = stampLines(lines).slice(-LOG_LINES)
  } catch {}

  // 监听新增内容，实时打上时间戳
  let pos = 0
  try { pos = fs.statSync(filePath).size } catch {}
  fs.watch(filePath, () => {
    try {
      const stat = fs.statSync(filePath)
      if (stat.size < pos) { pos = 0; logs[key] = [] } // 文件被截断
      const buf = Buffer.alloc(stat.size - pos)
      const fd = fs.openSync(filePath, 'r')
      fs.readSync(fd, buf, 0, buf.length, pos)
      fs.closeSync(fd)
      pos = stat.size
      const newLines = stampLines(buf.toString('utf8').split('\n').filter(Boolean))
      logs[key].push(...newLines)
      if (logs[key].length > LOG_LINES) logs[key] = logs[key].slice(-LOG_LINES)
    } catch {}
  })
}

function getProcessList() {
  return new Promise((resolve, reject) => {
    pm2.list((err, list) => {
      if (err) return reject(err)
      resolve(list.map(p => ({
        id: p.pm_id,
        name: p.name,
        status: p.pm2_env.status,
        pid: p.pid,
        uptime: p.pm2_env.pm_uptime,
        restarts: p.pm2_env.restart_time,
        cpu: p.monit?.cpu ?? 0,
        mem: Math.round((p.monit?.memory ?? 0) / 1024 / 1024),
        outLog: p.pm2_env.pm_out_log_path,
        errLog: p.pm2_env.pm_err_log_path,
      })))
    })
  })
}

const HTML = `<!DOCTYPE html>
<html lang="zh" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PM2 Dashboard</title>
<style>
  /* ── CSS 变量：Light 主题（默认） ── */
  :root, [data-theme="light"] {
    --bg:        #f5f7fa;
    --bg-card:   #ffffff;
    --bg-metric: #f0f2f5;
    --bg-btn:    #ffffff;
    --bg-bar:    #ffffff;
    --border:    #e4e7ed;
    --text:      #1a1a2e;
    --text-sub:  #606980;
    --text-mute: #9aa3b2;
    --tab-active:#2563eb;
    --tab-text:  #606980;
    --log-out:   #374151;
    --log-hover: #f0f2f5;
    --scroll:    #d1d5db;
    --shadow:    0 1px 4px rgba(0,0,0,.06);
  }
  /* ── CSS 变量：Dark 主题 ── */
  [data-theme="dark"] {
    --bg:        #0f1117;
    --bg-card:   #1a1f2e;
    --bg-metric: #0f1117;
    --bg-btn:    #1e2433;
    --bg-bar:    #0f1117;
    --border:    #1e2433;
    --text:      #e2e8f0;
    --text-sub:  #94a3b8;
    --text-mute: #475569;
    --tab-active:#3b82f6;
    --tab-text:  #64748b;
    --log-out:   #94a3b8;
    --log-hover: #1e2433;
    --scroll:    #2d3748;
    --shadow:    none;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { transition: background .2s, color .2s; }
  body { font-family: 'SF Pro Display', -apple-system, sans-serif; background: var(--bg); color: var(--text); }

  .header { padding: 14px 24px; border-bottom: 1px solid var(--border); background: var(--bg-card);
             display: flex; align-items: center; gap: 12px; box-shadow: var(--shadow); }
  .header h1 { font-size: 16px; font-weight: 700; }
  .badge { font-size: 11px; padding: 2px 8px; border-radius: 9999px;
           background: var(--bg-metric); color: var(--text-mute); border: 1px solid var(--border); }
  .last-update { margin-left: auto; font-size: 12px; color: var(--text-mute); }

  /* 主题切换按钮 */
  .theme-btn { padding: 5px 10px; border-radius: 20px; border: 1px solid var(--border);
               background: var(--bg-metric); color: var(--text-sub); cursor: pointer;
               font-size: 13px; transition: all .2s; display: flex; align-items: center; gap: 5px; }
  .theme-btn:hover { border-color: var(--tab-active); color: var(--tab-active); }

  .main { padding: 20px 24px; display: flex; flex-direction: column; gap: 20px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
  .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
          padding: 16px; box-shadow: var(--shadow); transition: box-shadow .2s; }
  .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }

  .card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .dot.online  { background: #22c55e; box-shadow: 0 0 6px #22c55e66; }
  .dot.errored, .dot.stopped  { background: #ef4444; }
  .dot.stopping, .dot.launching { background: #f59e0b; }
  .app-name { font-weight: 600; font-size: 14px; }
  .app-id { margin-left: auto; font-size: 11px; color: var(--text-mute); }

  .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .metric { background: var(--bg-metric); border-radius: 8px; padding: 10px; }
  .metric-label { font-size: 10px; color: var(--text-mute); margin-bottom: 4px; text-transform: uppercase; letter-spacing: .5px; }
  .metric-value { font-size: 17px; font-weight: 700; }
  .metric-value.green  { color: #16a34a; }
  .metric-value.blue   { color: #2563eb; }
  .metric-value.yellow { color: #d97706; }
  .metric-value.red    { color: #dc2626; }
  [data-theme="dark"] .metric-value.green  { color: #22c55e; }
  [data-theme="dark"] .metric-value.blue   { color: #60a5fa; }
  [data-theme="dark"] .metric-value.yellow { color: #fbbf24; }
  [data-theme="dark"] .metric-value.red    { color: #f87171; }

  .actions { margin-top: 12px; display: flex; gap: 8px; }
  .btn { padding: 5px 12px; border-radius: 6px; border: 1px solid var(--border);
         background: var(--bg-btn); color: var(--text-sub); cursor: pointer;
         font-size: 12px; transition: all .15s; }
  .btn:hover { border-color: var(--tab-active); color: var(--tab-active); }
  .btn.danger:hover { border-color: #ef4444; color: #ef4444; background: #fef2f2; }
  [data-theme="dark"] .btn.danger:hover { background: #7f1d1d; }
  a.btn-link { text-decoration: none; display: inline-flex; align-items: center;
               background: #2563eb; border-color: #2563eb; color: #fff !important; }
  a.btn-link:hover { background: #1d4ed8; border-color: #1d4ed8; color: #fff !important; }
  [data-theme="dark"] a.btn-link { background: #3b82f6; border-color: #3b82f6; }
  [data-theme="dark"] a.btn-link:hover { background: #2563eb; border-color: #2563eb; }

  .logs-section { background: var(--bg-card); border: 1px solid var(--border);
                  border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); }
  .logs-tabs { display: flex; border-bottom: 1px solid var(--border); background: var(--bg-metric); }
  .tab { padding: 10px 20px; font-size: 13px; cursor: pointer; color: var(--tab-text);
         border-bottom: 2px solid transparent; transition: color .15s; }
  .tab.active { color: var(--tab-active); border-bottom-color: var(--tab-active); background: var(--bg-card); }
  .tab:hover:not(.active) { color: var(--text); }

  .log-content { height: 380px; overflow-y: auto; padding: 12px 16px;
                 font-family: 'Menlo', 'Consolas', monospace; font-size: 12px; line-height: 1.7; }
  .log-line { white-space: pre-wrap; word-break: break-all; padding: 1px 4px; border-radius: 3px; }
  .log-line.err { color: #dc2626; }
  .log-line.out { color: var(--log-out); }
  .log-line:hover { background: var(--log-hover); }
  [data-theme="dark"] .log-line.err { color: #f87171; }

  .status-bar { padding: 6px 24px; background: var(--bg-bar); border-top: 1px solid var(--border);
                font-size: 11px; color: var(--text-mute); display: flex; gap: 16px; }
  .status-online { color: #16a34a; }
  .status-error  { color: #dc2626; }
  [data-theme="dark"] .status-online { color: #22c55e; }
  [data-theme="dark"] .status-error  { color: #f87171; }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--scroll); border-radius: 3px; }
</style>
</head>
<body>
<div class="header">
  <h1>⚙ PM2 Dashboard</h1>
  <span class="badge" id="total-badge">-</span>
  <span class="last-update" id="last-update">-</span>
  <button class="theme-btn" onclick="toggleTheme()" id="theme-btn">🌙 深色</button>
</div>
<div class="main">
  <div class="cards" id="cards"></div>
  <div class="logs-section">
    <div class="logs-tabs" id="tabs"></div>
    <div class="log-content" id="log-content"></div>
  </div>
</div>
<div class="status-bar">
  <span>自动刷新: 3s</span>
  <span id="status-online">-</span>
  <span id="status-errored">-</span>
</div>
<script>
let activeTab = null
let autoScroll = true

// 各服务对应的 Web 地址（按需修改端口）
const SERVICE_URLS = {
  backend:   null,         // backend 无需直接访问
  frontend:  'http://localhost:5173',
  'g2-ssr':  null,        // g2-ssr 无需直接访问
  dashboard: 'http://localhost:9615',
}

function statusColor(s) {
  if (s === 'online') return 'green'
  if (s === 'errored' || s === 'stopped') return 'red'
  return 'yellow'
}

function formatUptime(ts) {
  if (!ts) return '-'
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return s + 's'
  if (s < 3600) return Math.floor(s/60) + 'm'
  if (s < 86400) return Math.floor(s/3600) + 'h ' + Math.floor((s%3600)/60) + 'm'
  return Math.floor(s/86400) + 'd'
}

async function api(path, method='GET') {
  const r = await fetch(path, {method})
  return r.json()
}

async function refresh() {
  const data = await api('/api/list')
  const online = data.filter(p => p.status === 'online').length
  const errored = data.filter(p => p.status === 'errored').length
  document.getElementById('total-badge').textContent = data.length + ' 个进程'
  document.getElementById('last-update').textContent = '更新于 ' + new Date().toLocaleTimeString()
  document.getElementById('status-online').className = 'status-online'
  document.getElementById('status-online').textContent = '✓ 运行中 ' + online
  const errEl = document.getElementById('status-errored')
  errEl.textContent = errored ? '✗ 异常 ' + errored : ''
  errEl.className = errored ? 'status-error' : ''

  // 更新卡片
  const cards = document.getElementById('cards')
  cards.innerHTML = data.map(p => \`
    <div class="card">
      <div class="card-header">
        <div class="dot \${p.status}"></div>
        <span class="app-name">\${p.name}</span>
        <span class="app-id">id:\${p.id} · pid:\${p.pid || '-'}</span>
      </div>
      <div class="metrics">
        <div class="metric"><div class="metric-label">状态</div>
          <div class="metric-value \${statusColor(p.status)}">\${p.status}</div></div>
        <div class="metric"><div class="metric-label">运行时长</div>
          <div class="metric-value blue">\${p.status==='online' ? formatUptime(p.uptime) : '-'}</div></div>
        <div class="metric"><div class="metric-label">CPU</div>
          <div class="metric-value \${p.cpu>80?'red':p.cpu>40?'yellow':'green'}">\${p.cpu}%</div></div>
        <div class="metric"><div class="metric-label">内存</div>
          <div class="metric-value blue">\${p.mem} MB</div></div>
      </div>
      <div class="actions">
        <button class="btn" onclick="action('\${p.name}','restart')">重启</button>
        <button class="btn" onclick="action('\${p.name}','stop')">停止</button>
        <button class="btn" onclick="showLog('\${p.name}')">查看日志</button>
        \${p.name === 'frontend' ? \`<a class="btn btn-link" href="http://localhost:5173" target="_blank">打开系统 ↗</a>\` : ''}
      </div>
    </div>
  \`).join('')

  // 初始化 tab
  if (!activeTab && data.length > 0) activeTab = data[0].name
  const tabs = document.getElementById('tabs')
  tabs.innerHTML = data.map(p => \`
    <div class="tab \${activeTab===p.name?'active':''}" onclick="showLog('\${p.name}')">\${p.name}</div>
  \`).join('')

  if (activeTab) refreshLog(activeTab)
}

async function refreshLog(name) {
  const data = await api('/api/logs/' + name)
  const el = document.getElementById('log-content')
  const wasAtBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 20
  el.innerHTML = [
    ...data.out.map(l => \`<div class="log-line out">\${escHtml(l)}</div>\`),
    ...data.err.map(l => \`<div class="log-line err">[ERR] \${escHtml(l)}</div>\`)
  ].join('')
  if (wasAtBottom || autoScroll) el.scrollTop = el.scrollHeight
}

function showLog(name) {
  activeTab = name
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.textContent === name)
  })
  refreshLog(name)
}

async function action(name, act) {
  await api('/api/' + act + '/' + name, 'POST')
  setTimeout(refresh, 1000)
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

refresh()
setInterval(refresh, 3000)

// ── 主题切换 ──
function toggleTheme() {
  const html = document.documentElement
  const isDark = html.getAttribute('data-theme') === 'dark'
  const next = isDark ? 'light' : 'dark'
  html.setAttribute('data-theme', next)
  localStorage.setItem('pm2-theme', next)
  document.getElementById('theme-btn').textContent = next === 'dark' ? '☀️ 浅色' : '🌙 深色'
}

// 初始化主题（读取上次选择）
;(function initTheme() {
  const saved = localStorage.getItem('pm2-theme') || 'light'
  document.documentElement.setAttribute('data-theme', saved)
  document.getElementById('theme-btn').textContent = saved === 'dark' ? '☀️ 浅色' : '🌙 深色'
})()
</script>
</body>
</html>`

const server = http.createServer(async (req, res) => {
  const url = req.url

  if (url === '/' || url === '/index.html') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
    return res.end(HTML)
  }

  if (url === '/api/list') {
    try {
      const list = await getProcessList()
      // 首次获取到进程列表时启动日志监听
      list.forEach(p => {
        if (!logs[`${p.name}-out`]) tailFile(p.outLog, p.name, 'out')
        if (!logs[`${p.name}-err`]) tailFile(p.errLog, p.name, 'err')
      })
      res.writeHead(200, { 'Content-Type': 'application/json' })
      return res.end(JSON.stringify(list))
    } catch (e) {
      res.writeHead(500)
      return res.end(JSON.stringify({ error: e.message }))
    }
  }

  const logMatch = url.match(/^\/api\/logs\/(.+)$/)
  if (logMatch) {
    const name = logMatch[1]
    res.writeHead(200, { 'Content-Type': 'application/json' })
    return res.end(JSON.stringify({
      out: logs[`${name}-out`] || [],
      err: logs[`${name}-err`] || [],
    }))
  }

  const actionMatch = url.match(/^\/api\/(restart|stop|start)\/(.+)$/)
  if (actionMatch && req.method === 'POST') {
    const [, action, name] = actionMatch
    pm2[action](name, (err) => {
      res.writeHead(err ? 500 : 200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: !err, error: err?.message }))
    })
    return
  }

  res.writeHead(404)
  res.end('Not found')
})

pm2.connect(false, (err) => {
  if (err) { console.error('无法连接 PM2:', err); process.exit(1) }
  server.listen(PORT, () => {
    console.log(`✅ PM2 Dashboard 已启动: http://localhost:${PORT}`)
    console.log('Ctrl+C 退出（不影响 PM2 进程）')
  })
})

process.on('SIGINT', () => { pm2.disconnect(); process.exit(0) })
