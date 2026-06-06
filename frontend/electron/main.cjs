const { app, BrowserWindow, desktopCapturer, session } = require('electron')
const { spawn } = require('child_process')
const fs = require('fs')
const http = require('http')
const path = require('path')

const FRONTEND_PORT = Number(process.env.FRONTEND_PORT || 3001)
const BACKEND_PORT = Number(process.env.BACKEND_PORT || 9000)
const FRONTEND_URL = process.env.FRONTEND_URL || `http://127.0.0.1:${FRONTEND_PORT}`

const frontendRoot = path.resolve(__dirname, '..')
const projectRoot = path.resolve(frontendRoot, '..')
const backendRoot = path.join(projectRoot, 'backend')
const logsRoot = path.join(projectRoot, 'logs')

let mainWindow = null
const childProcesses = []

function ensureLogsRoot() {
  fs.mkdirSync(logsRoot, { recursive: true })
}

function spawnManaged(command, args, options) {
  ensureLogsRoot()
  const label = options.label
  const logPath = path.join(logsRoot, `${label}.electron.log`)
  const log = fs.createWriteStream(logPath, { flags: 'a' })
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: { ...process.env, ...options.env },
    shell: process.platform === 'win32',
    windowsHide: true,
  })

  child.stdout?.pipe(log)
  child.stderr?.pipe(log)
  child.on('exit', (code, signal) => {
    log.write(`\n[${new Date().toISOString()}] ${label} exited code=${code} signal=${signal}\n`)
    log.end()
  })
  childProcesses.push(child)
  return child
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

async function waitForHttp(url, timeoutMs = 25000) {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    if (await isHttpReady(url)) return true
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  return false
}

async function startBackend() {
  const ready = await isHttpReady(`http://127.0.0.1:${BACKEND_PORT}/api/status`)
  if (ready) return

  const python = process.env.PYTHON_PATH || 'python'
  spawnManaged(python, ['main.py'], {
    cwd: backendRoot,
    label: 'backend',
  })
  await waitForHttp(`http://127.0.0.1:${BACKEND_PORT}/api/status`)
}

async function startFrontendDevServer() {
  if (app.isPackaged) return
  const ready = await isHttpReady(FRONTEND_URL)
  if (ready) return

  spawnManaged('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(FRONTEND_PORT)], {
    cwd: frontendRoot,
    label: 'frontend',
    env: {
      BROWSER: 'none',
    },
  })
  await waitForHttp(FRONTEND_URL)
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
  setupDesktopAudioCapture()

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: '#0f0f23',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  await startBackend()

  if (app.isPackaged) {
    await mainWindow.loadFile(path.join(frontendRoot, 'dist', 'index.html'))
  } else {
    await startFrontendDevServer()
    await mainWindow.loadURL(FRONTEND_URL)
    if (process.env.ELECTRON_OPEN_DEVTOOLS === '1') {
      mainWindow.webContents.openDevTools({ mode: 'detach' })
    }
  }
}

function stopChildProcesses() {
  for (const child of childProcesses.splice(0)) {
    if (!child.killed) {
      child.kill()
    }
  }
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  stopChildProcesses()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', stopChildProcesses)

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
