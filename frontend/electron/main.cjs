const { app, BrowserWindow, Menu, Tray, desktopCapturer, ipcMain, nativeImage, screen, session } = require('electron')
const { spawn, spawnSync } = require('child_process')
const fs = require('fs')
const http = require('http')
const path = require('path')

const FRONTEND_PORT = Number(process.env.FRONTEND_PORT || 3001)
const BACKEND_PORT = Number(process.env.BACKEND_PORT || 9000)
const FRONTEND_URL = process.env.FRONTEND_URL || `http://127.0.0.1:${FRONTEND_PORT}`
const appName = 'AI Interpreter'

app.setName(appName)

const frontendRoot = path.resolve(__dirname, '..')
const projectRoot = app.isPackaged ? process.resourcesPath : path.resolve(frontendRoot, '..')
const backendRoot = path.join(projectRoot, 'backend')
const logsRoot = app.isPackaged ? path.join(app.getPath('userData'), 'logs') : path.join(projectRoot, 'logs')
const appConfigPath = path.join(app.getPath('userData'), 'api-config.json')
const legacyDevConfigPath = path.join(app.getPath('appData'), 'ai-interpreter-frontend', 'api-config.json')
const iconPath = path.join(frontendRoot, 'build', 'icon.ico')

let mainWindow = null
let subtitleWindow = null
let backendProcess = null
let tray = null
let isQuitting = false
const childProcesses = []
let startupError = ''
let latestSubtitlePayload = []
const preloadPath = path.join(__dirname, 'preload.cjs')

function ensureLogsRoot() {
  fs.mkdirSync(logsRoot, { recursive: true })
}

function normalizeApiConfig(config = {}) {
  return {
    dashscopeApiKey: typeof config.dashscopeApiKey === 'string' ? config.dashscopeApiKey.trim() : '',
    dashscopeLiveTranslateModel: typeof config.dashscopeLiveTranslateModel === 'string'
      ? config.dashscopeLiveTranslateModel.trim()
      : '',
  }
}

function readApiConfig() {
  try {
    const configPath = fs.existsSync(appConfigPath) ? appConfigPath : legacyDevConfigPath
    if (!fs.existsSync(configPath)) return normalizeApiConfig()
    return normalizeApiConfig(JSON.parse(fs.readFileSync(configPath, 'utf8')))
  } catch (error) {
    appendStartupError(`read api config failed: ${error.message}`)
    return normalizeApiConfig()
  }
}

function getApiConfigForRenderer() {
  const config = readApiConfig()
  return {
    hasDashscopeApiKey: Boolean(config.dashscopeApiKey),
    dashscopeLiveTranslateModel: config.dashscopeLiveTranslateModel,
  }
}

function saveApiConfig(input = {}) {
  const existing = readApiConfig()
  const incoming = normalizeApiConfig(input)
  const next = {
    dashscopeApiKey: incoming.dashscopeApiKey || existing.dashscopeApiKey,
    dashscopeLiveTranslateModel: incoming.dashscopeLiveTranslateModel || existing.dashscopeLiveTranslateModel,
  }

  fs.mkdirSync(path.dirname(appConfigPath), { recursive: true })
  fs.writeFileSync(appConfigPath, `${JSON.stringify(next, null, 2)}\n`, 'utf8')
  return getApiConfigForRenderer()
}

function clearApiConfig() {
  for (const configPath of [appConfigPath, legacyDevConfigPath]) {
    if (fs.existsSync(configPath)) fs.rmSync(configPath, { force: true })
  }
  return getApiConfigForRenderer()
}

function getBackendConfigEnv() {
  const config = readApiConfig()
  const env = { TRANSLATION_PROVIDER: 'aliyun_livetranslate' }
  if (config.dashscopeApiKey) env.DASHSCOPE_API_KEY = config.dashscopeApiKey
  if (config.dashscopeLiveTranslateModel) {
    env.DASHSCOPE_LIVETRANSLATE_MODEL = config.dashscopeLiveTranslateModel
  }
  return env
}

function cloneSubtitlePayload(payload) {
  try {
    return JSON.parse(JSON.stringify(payload || []))
  } catch {
    return []
  }
}

function commandExists(command) {
  if (path.isAbsolute(command) && fs.existsSync(command)) return command

  const pathValue = process.env.PATH || process.env.Path || ''
  const extensions = process.platform === 'win32'
    ? (process.env.PATHEXT || '.COM;.EXE;.BAT;.CMD').split(';')
    : ['']
  const names = process.platform === 'win32' && !path.extname(command)
    ? extensions.flatMap((ext) => [`${command}${ext}`, `${command}${ext.toLowerCase()}`])
    : [command]

  for (const dir of pathValue.split(path.delimiter)) {
    for (const name of names) {
      const fullPath = path.join(dir, name)
      if (fs.existsSync(fullPath)) return fullPath
    }
  }
  return ''
}

function appendStartupError(message) {
  startupError += `${message}\n`
}

function buildChildEnv(extraEnv = {}) {
  const env = {}
  const seen = new Map()

  const assign = (key, value) => {
    if (value === undefined) return
    const normalized = process.platform === 'win32' ? key.toLowerCase() : key
    const finalKey = process.platform === 'win32' && normalized === 'path' ? 'Path' : key
    const previousKey = seen.get(normalized)
    if (previousKey && previousKey !== finalKey) delete env[previousKey]
    seen.set(normalized, finalKey)
    env[finalKey] = value
  }

  for (const [key, value] of Object.entries(process.env)) assign(key, value)
  for (const [key, value] of Object.entries(extraEnv)) assign(key, value)
  return env
}

function getPythonCommand() {
  const candidates = [
    process.env.PYTHON_PATH,
    'E:\\anacodna\\python.exe',
    path.join(projectRoot, '.venv', process.platform === 'win32' ? 'Scripts\\python.exe' : 'bin/python'),
    path.join(backendRoot, '.venv', process.platform === 'win32' ? 'Scripts\\python.exe' : 'bin/python'),
    'python',
    'python3',
  ].filter(Boolean)

  for (const candidate of candidates) {
    const resolved = commandExists(candidate)
    if (!resolved) continue

    const check = spawnSync(resolved, ['-c', 'import fastapi, uvicorn'], {
      cwd: backendRoot,
      env: buildChildEnv(),
      encoding: 'utf8',
      windowsHide: true,
    })
    if (check.status === 0) return resolved
    appendStartupError(`skip python: ${resolved}\n${(check.stderr || check.stdout || '').trim()}`)
  }
  return 'python'
}

function getNodeCommand() {
  const candidates = [
    process.env.NODE_PATH,
    process.platform === 'win32' ? 'C:\\Program Files\\Nodejs\\node.exe' : '',
    'node',
    'node.exe',
  ].filter(Boolean)

  for (const candidate of candidates) {
    const resolved = commandExists(candidate)
    if (resolved && !resolved.toLowerCase().includes('electron')) return resolved
  }
  return 'node'
}

function spawnManaged(command, args, options) {
  ensureLogsRoot()
  const label = options.label
  const logPath = path.join(logsRoot, `${label}.electron.log`)
  const log = fs.createWriteStream(logPath, { flags: 'a' })
  log.write(`\n[${new Date().toISOString()}] starting ${command} ${args.join(' ')} cwd=${options.cwd}\n`)

  const child = spawn(command, args, {
    cwd: options.cwd,
    env: buildChildEnv(options.env),
    shell: false,
    windowsHide: true,
  })

  child.stdout?.pipe(log)
  child.stderr?.pipe(log)
  child.on('error', (error) => {
    const message = `${label} spawn failed: ${error.message}`
    log.write(`\n[${new Date().toISOString()}] ${message}\n`)
    appendStartupError(`${message}\nlog: ${logPath}`)
  })
  child.on('exit', (code, signal) => {
    log.write(`\n[${new Date().toISOString()}] ${label} exited code=${code} signal=${signal}\n`)
    log.end()
    const index = childProcesses.indexOf(child)
    if (index !== -1) childProcesses.splice(index, 1)
    if (backendProcess === child) backendProcess = null
    if (code && !child.expectedExit) appendStartupError(`${label} exited early, log: ${logPath}`)
  })
  childProcesses.push(child)
  return child
}

function stopManagedChild(child, timeoutMs = 5000) {
  return new Promise((resolve) => {
    if (!child || child.killed || child.exitCode !== null) {
      resolve()
      return
    }

    let settled = false
    const done = () => {
      if (settled) return
      settled = true
      resolve()
    }

    child.expectedExit = true
    child.once('exit', done)
    child.kill()
    setTimeout(done, timeoutMs)
  })
}

function isHttpReady(url) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      res.resume()
      resolve(res.statusCode >= 200 && res.statusCode < 500)
    })
    req.on('error', () => resolve(false))
    req.setTimeout(1000, () => {
      req.destroy()
      resolve(false)
    })
  })
}

function fetchJson(url, timeoutMs = 1000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let body = ''
      res.setEncoding('utf8')
      res.on('data', (chunk) => {
        body += chunk
      })
      res.on('end', () => {
        try {
          resolve(JSON.parse(body))
        } catch (error) {
          reject(error)
        }
      })
    })
    req.on('error', reject)
    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error('request timed out'))
    })
  })
}

function postJson(url, payload, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload || {})
    const parsed = new URL(url)
    const req = http.request({
      hostname: parsed.hostname,
      port: parsed.port,
      path: `${parsed.pathname}${parsed.search}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
      timeout: timeoutMs,
    }, (res) => {
      let responseBody = ''
      res.setEncoding('utf8')
      res.on('data', (chunk) => {
        responseBody += chunk
      })
      res.on('end', () => {
        let data = {}
        try {
          data = responseBody ? JSON.parse(responseBody) : {}
        } catch (error) {
          reject(error)
          return
        }
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const error = new Error(`HTTP ${res.statusCode}`)
          error.statusCode = res.statusCode
          error.body = data
          reject(error)
          return
        }
        resolve(data)
      })
    })
    req.on('error', reject)
    req.on('timeout', () => {
      req.destroy(new Error('request timed out'))
    })
    req.write(body)
    req.end()
  })
}

async function isProjectBackendRunning() {
  try {
    const status = await fetchJson(`http://127.0.0.1:${BACKEND_PORT}/api/status`)
    return status?.status === 'running' && status?.version === '2.0.0'
  } catch {
    return false
  }
}

function getWindowsPortListenerPid(port) {
  if (process.platform !== 'win32') return 0
  const result = spawnSync('netstat', ['-ano', '-p', 'tcp'], {
    encoding: 'utf8',
    windowsHide: true,
  })
  if (result.status !== 0) return 0

  const pattern = new RegExp(`(?:^|\\s)(?:127\\.0\\.0\\.1|0\\.0\\.0\\.0|\\[::\\]|\\[::1\\]|\\S+):${port}\\s+\\S+\\s+LISTENING\\s+(\\d+)`, 'i')
  for (const line of (result.stdout || '').split(/\r?\n/)) {
    const match = line.match(pattern)
    if (match) return Number(match[1])
  }
  return 0
}

async function stopExternalProjectBackend() {
  if (!(await isProjectBackendRunning())) {
    throw new Error('port is occupied by an unknown service')
  }

  const pid = getWindowsPortListenerPid(BACKEND_PORT)
  if (!pid) throw new Error(`could not find process listening on port ${BACKEND_PORT}`)
  if (pid === process.pid) throw new Error('refusing to stop current Electron process')

  try {
    process.kill(pid)
  } catch (error) {
    throw new Error(`failed to stop backend process ${pid}: ${error.message}`)
  }

  const stopped = await waitForPortClosed(`http://127.0.0.1:${BACKEND_PORT}/api/status`)
  if (!stopped) throw new Error(`backend process ${pid} did not stop`)
}

async function waitForPortClosed(url, timeoutMs = 5000) {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    if (!(await isHttpReady(url))) return true
    await new Promise((resolve) => setTimeout(resolve, 300))
  }
  return false
}

async function waitForHttp(url, timeoutMs = 25000) {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    if (await isHttpReady(url)) return true
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  return false
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch]))
}

function createTrayIcon() {
  if (fs.existsSync(iconPath)) return nativeImage.createFromPath(iconPath)

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
      <rect width="32" height="32" rx="8" fill="#111827"/>
      <circle cx="16" cy="16" r="11" fill="#22c55e"/>
      <path d="M11 17.5c2.2 2.6 7.8 2.6 10 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
      <path d="M12 11.5h8" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
      <path d="M16 8.5v6" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
    </svg>
  `
  return nativeImage.createFromDataURL(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`)
}

function showMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow()
    return
  }
  if (mainWindow.isMinimized()) mainWindow.restore()
  mainWindow.show()
  mainWindow.focus()
}

function quitFromTray() {
  isQuitting = true
  closeSubtitleWindow()
  stopChildProcesses()
  app.quit()
}

function setupTray() {
  if (tray) return
  tray = new Tray(createTrayIcon())
  tray.setToolTip('AI 同声传译助手')
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: '打开主窗口', click: showMainWindow },
    { type: 'separator' },
    { label: '退出', click: quitFromTray },
  ]))
  tray.on('click', showMainWindow)
}

async function showStartupError(title, detail) {
  await mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
    <body style="margin:0;background:#0f0f23;color:#f8fafc;font-family:Microsoft YaHei,sans-serif;display:grid;place-items:center;min-height:100vh">
      <main style="max-width:760px;padding:32px;line-height:1.7">
        <h1 style="font-size:24px;margin:0 0 16px">${escapeHtml(title)}</h1>
        <pre style="white-space:pre-wrap;background:#18182f;border:1px solid #34345f;border-radius:8px;padding:16px;color:#cbd5e1">${escapeHtml(detail)}</pre>
      </main>
    </body>
  `)}`)
}

function getSubtitleWindowHtml() {
  return `
    <body>
      <style>
        * { box-sizing: border-box; }
        html, body {
          margin: 0;
          width: 100%;
          height: 100%;
          overflow: hidden;
          background: transparent !important;
          color: #f8fafc;
          font-family: Inter, "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        body {
          padding: 12px 14px 14px;
          -webkit-app-region: drag;
          user-select: none;
        }
        .drag-strip {
          position: fixed;
          inset: 0 42px auto 0;
          height: 34px;
          -webkit-app-region: drag;
          z-index: 2;
          cursor: move;
        }
        #subtitle-close {
          position: fixed;
          top: 8px;
          right: 8px;
          z-index: 5;
          width: 28px;
          height: 28px;
          border: 1px solid rgba(248, 250, 252, 0.28);
          border-radius: 999px;
          background: rgba(15, 23, 42, 0.12);
          color: rgba(248, 250, 252, 0.92);
          font-size: 18px;
          line-height: 24px;
          cursor: pointer;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.92);
          -webkit-app-region: no-drag;
        }
        #subtitle-close:hover {
          background: rgba(239, 68, 68, 0.75);
          border-color: rgba(254, 202, 202, 0.78);
          color: #fff;
        }
        #subtitle-root {
          height: 100%;
          overflow-y: auto;
          padding: 30px 14px 0 0;
          scroll-behavior: smooth;
          background: transparent !important;
          -webkit-app-region: drag;
        }
        #subtitle-root::-webkit-scrollbar { width: 8px; }
        #subtitle-root::-webkit-scrollbar-track { background: transparent; }
        #subtitle-root::-webkit-scrollbar-thumb {
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.5);
        }
        .subtitle-list {
          display: flex;
          min-height: 100%;
          flex-direction: column;
          justify-content: flex-end;
          gap: 10px;
        }
        .subtitle-row {
          width: 100%;
          padding: 4px 6px;
          border: 0;
          background: transparent !important;
          pointer-events: none;
          text-shadow: 0 2px 9px rgba(0, 0, 0, 0.92), 0 0 2px rgba(0, 0, 0, 0.9);
        }
        .subtitle-row.partial { opacity: 0.76; }
        .original {
          margin-bottom: 6px;
          color: rgba(241, 245, 249, 0.88);
          font-size: 15px;
          line-height: 1.35;
          font-weight: 650;
        }
        .translated {
          color: #22c55e;
          font-size: 25px;
          font-weight: 850;
          line-height: 1.32;
        }
        .empty {
          display: grid;
          height: 100%;
          place-items: center;
          color: rgba(203, 213, 225, 0.78);
          font-size: 18px;
          font-weight: 700;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
        }
      </style>
      <div class="drag-strip"></div>
      <button id="subtitle-close" type="button" title="Close">&times;</button>
      <div id="subtitle-root"><div class="empty">Waiting...</div></div>
      <script>
        const electronApi = window.electronSubtitles || (() => {
          try {
            const { ipcRenderer } = require('electron');
            return {
              close: () => ipcRenderer.invoke('subtitle-window:close'),
              onUpdate: (callback) => ipcRenderer.on('subtitle-window:data', (_event, items) => callback(items))
            };
          } catch {
            return null;
          }
        })();
        const root = document.getElementById('subtitle-root');
        const closeButton = document.getElementById('subtitle-close');
        let stickToBottom = true;

        closeButton.addEventListener('click', () => {
          electronApi?.close();
        });

        root.addEventListener('scroll', () => {
          stickToBottom = root.scrollHeight - root.scrollTop - root.clientHeight < 32;
        });

        function render(payload) {
          const subtitles = Array.isArray(payload)
            ? payload.filter(item => item?.original || item?.translated)
            : Array.isArray(payload?.items)
              ? payload.items.filter(item => item?.original || item?.translated)
              : [];
          const block = payload && !Array.isArray(payload) && payload.block ? payload.block : null;
          const originalText = block?.original || '';
          const translatedText = block?.translated || '';
          const isPartial = Boolean(block?.isPartial) || subtitles.some((subtitle) => subtitle.isPartial);

          if (!originalText && !translatedText && !subtitles.length) {
            root.innerHTML = '<div class="empty">Waiting...</div>';
            return;
          }

          const shouldStick = stickToBottom || root.scrollHeight - root.scrollTop - root.clientHeight < 64;
          root.innerHTML = '';
          const list = document.createElement('div');
          list.className = 'subtitle-list';

          const current = subtitles.slice(-3);
          const fallbackOriginalText = current.map((subtitle) => subtitle.original || '').filter(Boolean).join(' ').trim();
          const fallbackTranslatedText = current.map((subtitle) => subtitle.translated || '').filter(Boolean).join(' ').trim();
          const row = document.createElement('div');
          row.className = 'subtitle-row' + (isPartial ? ' partial' : '');

          if (originalText || fallbackOriginalText) {
            const original = document.createElement('div');
            original.className = 'original';
            original.textContent = originalText || fallbackOriginalText;
            row.appendChild(original);
          }

          if (translatedText || fallbackTranslatedText) {
            const translated = document.createElement('div');
            translated.className = 'translated';
            translated.textContent = translatedText || fallbackTranslatedText;
            row.appendChild(translated);
          }
          list.appendChild(row);

          root.appendChild(list);
          if (shouldStick) root.scrollTop = root.scrollHeight;
        }

        electronApi?.onUpdate(render);
      </script>
    </body>
  `
}

function notifySubtitleClosed() {
  mainWindow?.webContents.send('subtitle-window:closed')
}

function closeSubtitleWindow() {
  if (subtitleWindow && !subtitleWindow.isDestroyed()) {
    subtitleWindow.close()
  }
  subtitleWindow = null
  notifySubtitleClosed()
}

function getSubtitleAppUrl() {
  if (app.isPackaged) return null
  const url = new URL(FRONTEND_URL)
  url.searchParams.set('subtitleWindow', '1')
  return url.toString()
}

function createSubtitleWindow() {
  if (subtitleWindow && !subtitleWindow.isDestroyed()) {
    subtitleWindow.focus()
    return subtitleWindow
  }

  const { workArea } = screen.getPrimaryDisplay()
  const windowWidth = Math.min(980, workArea.width - 80)
  const windowHeight = 170

  subtitleWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    minWidth: 520,
    minHeight: 120,
    x: Math.round(workArea.x + (workArea.width - windowWidth) / 2),
    y: Math.round(workArea.y + workArea.height - windowHeight - 72),
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    hasShadow: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    movable: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  subtitleWindow.setAlwaysOnTop(true, 'screen-saver')
  subtitleWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })
  if (app.isPackaged) {
    subtitleWindow.loadFile(path.join(frontendRoot, 'dist', 'index.html'), {
      query: { subtitleWindow: '1' },
    })
  } else {
    subtitleWindow.loadURL(getSubtitleAppUrl())
  }
  subtitleWindow.webContents.once('did-finish-load', () => {
    subtitleWindow?.webContents.send('subtitle-window:data', latestSubtitlePayload)
    subtitleWindow?.showInactive()
  })
  subtitleWindow.on('closed', () => {
    subtitleWindow = null
    notifySubtitleClosed()
  })

  return subtitleWindow
}

function setupSubtitleWindowIpc() {
  ipcMain.handle('subtitle-window:toggle', () => {
    if (subtitleWindow && !subtitleWindow.isDestroyed()) {
      closeSubtitleWindow()
      return { available: true, opened: false }
    }
    createSubtitleWindow()
    return { available: true, opened: true }
  })

  ipcMain.handle('subtitle-window:close', () => {
    closeSubtitleWindow()
    return { available: true, opened: false }
  })

  ipcMain.handle('subtitle-window:is-open', () => ({
    available: true,
    opened: Boolean(subtitleWindow && !subtitleWindow.isDestroyed()),
  }))

  ipcMain.handle('subtitle-window:get-latest', () => ({
    available: true,
    opened: Boolean(subtitleWindow && !subtitleWindow.isDestroyed()),
    payload: latestSubtitlePayload,
  }))

  ipcMain.handle('subtitle-window:update', (_event, subtitles) => {
    latestSubtitlePayload = cloneSubtitlePayload(subtitles)
    if (subtitleWindow && !subtitleWindow.isDestroyed()) {
      subtitleWindow.webContents.send('subtitle-window:data', latestSubtitlePayload)
      return { available: true, opened: true }
    }
    return { available: true, opened: false }
  })
}

async function checkAndApplyRuntimeConfig(config) {
  const input = normalizeApiConfig(config)
  const saved = readApiConfig()
  const apiKey = input.dashscopeApiKey || saved.dashscopeApiKey
  const model = input.dashscopeLiveTranslateModel || saved.dashscopeLiveTranslateModel
  const payload = {
    dashscope_api_key: apiKey || undefined,
    dashscope_livetranslate_model: model || undefined,
  }

  await startBackend()
  const result = await postJson(`http://127.0.0.1:${BACKEND_PORT}/api/runtime-config/check`, payload)
  if (result.usable) {
    await postJson(`http://127.0.0.1:${BACKEND_PORT}/api/runtime-config`, payload)
  }
  return result
}

async function applySavedRuntimeConfig() {
  const saved = readApiConfig()
  if (!saved.dashscopeApiKey) return { applied: false }

  const payload = {
    dashscope_api_key: saved.dashscopeApiKey,
    dashscope_livetranslate_model: saved.dashscopeLiveTranslateModel || undefined,
  }

  try {
    await postJson(`http://127.0.0.1:${BACKEND_PORT}/api/runtime-config`, payload, 3000)
  } catch (error) {
    if (error.statusCode === 404) {
      await restartBackend()
      await postJson(`http://127.0.0.1:${BACKEND_PORT}/api/runtime-config`, payload, 3000)
    } else {
      throw error
    }
  }

  return { applied: true }
}

async function clearRuntimeConfig() {
  const payload = { dashscope_api_key: '' }

  try {
    await startBackend()
    await postJson(`http://127.0.0.1:${BACKEND_PORT}/api/runtime-config`, payload, 3000)
  } catch (error) {
    if (error.statusCode === 404) {
      await restartBackend()
      await postJson(`http://127.0.0.1:${BACKEND_PORT}/api/runtime-config`, payload, 3000)
      return
    }
    throw error
  }
}

function setupAppConfigIpc() {
  ipcMain.handle('app-config:get', () => getApiConfigForRenderer())
  ipcMain.handle('app-config:save', (_event, config) => saveApiConfig(config))
  ipcMain.handle('app-config:clear', async () => {
    const result = clearApiConfig()
    await clearRuntimeConfig()
    return result
  })
  ipcMain.handle('app-config:check', async (_event, config) => {
    try {
      return await checkAndApplyRuntimeConfig(config)
    } catch (error) {
      if (error.statusCode === 404) {
        await restartBackend()
        return checkAndApplyRuntimeConfig(config)
      }
      throw error
    }
  })
  ipcMain.handle('app-config:restart-backend', async () => {
    await restartBackend()
    return { restarted: true, apiConfigured: readApiConfig().dashscopeApiKey.length > 0 }
  })
}

async function startBackend({ force = false } = {}) {
  const ready = await isHttpReady(`http://127.0.0.1:${BACKEND_PORT}/api/status`)
  if (ready && !force) return
  if (force && ready && !backendProcess) {
    await stopExternalProjectBackend()
  }
  if (force && backendProcess) {
    await stopManagedChild(backendProcess)
  }

  const python = getPythonCommand()
  backendProcess = spawnManaged(python, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)], {
    cwd: backendRoot,
    label: 'backend',
    env: getBackendConfigEnv(),
  })
  const started = await waitForHttp(`http://127.0.0.1:${BACKEND_PORT}/api/status`)
  if (!started) {
    throw new Error(`backend failed to start. Python: ${python}\n${startupError || `log: ${path.join(logsRoot, 'backend.electron.log')}`}`)
  }
}

async function restartBackend() {
  await startBackend({ force: true })
}

async function startFrontendDevServer() {
  if (app.isPackaged) return
  const ready = await isHttpReady(FRONTEND_URL)
  if (ready) return

  const node = getNodeCommand()
  const viteBin = path.join(frontendRoot, 'node_modules', 'vite', 'bin', 'vite.js')
  spawnManaged(node, [viteBin, '--host', '127.0.0.1', '--port', String(FRONTEND_PORT)], {
    cwd: frontendRoot,
    label: 'frontend',
    env: { BROWSER: 'none' },
  })
  const started = await waitForHttp(FRONTEND_URL)
  if (!started) {
    throw new Error(`frontend failed to start. Node: ${node}\n${startupError || `log: ${path.join(logsRoot, 'frontend.electron.log')}`}`)
  }
}

function setupDesktopAudioCapture() {
  session.defaultSession.setDisplayMediaRequestHandler(async (_request, callback) => {
    const sources = await desktopCapturer.getSources({
      types: ['screen', 'window'],
      thumbnailSize: { width: 320, height: 180 },
    })
    const preferredSource = sources.find((source) => source.id.startsWith('screen:')) || sources[0]

    if (!preferredSource) {
      callback({})
      return
    }

    callback({
      video: preferredSource,
      audio: process.platform === 'win32' ? 'loopback' : undefined,
    })
  }, { useSystemPicker: false })
}

async function createWindow() {
  setupTray()
  setupDesktopAudioCapture()

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: '#0f0f23',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    autoHideMenuBar: true,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  mainWindow.on('close', (event) => {
    if (isQuitting) return
    event.preventDefault()
    mainWindow.hide()
  })

  try {
    await startBackend()
    await applySavedRuntimeConfig()

    if (app.isPackaged) {
      await mainWindow.loadFile(path.join(frontendRoot, 'dist', 'index.html'))
    } else {
      await startFrontendDevServer()
      await mainWindow.loadURL(FRONTEND_URL)
      if (process.env.ELECTRON_OPEN_DEVTOOLS === '1') {
        mainWindow.webContents.openDevTools({ mode: 'detach' })
      }
    }
  } catch (error) {
    await showStartupError('Desktop startup failed', error.message || String(error))
  }
}

function stopChildProcesses() {
  for (const child of childProcesses.splice(0)) {
    child.expectedExit = true
    if (!child.killed) child.kill()
  }
}

app.whenReady().then(() => {
  setupSubtitleWindowIpc()
  setupAppConfigIpc()
  return createWindow()
})

app.on('window-all-closed', () => {
  if (isQuitting) {
    stopChildProcesses()
    if (process.platform !== 'darwin') app.quit()
  }
})

app.on('before-quit', () => {
  isQuitting = true
  stopChildProcesses()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
