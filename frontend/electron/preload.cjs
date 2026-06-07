const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronSubtitles', {
  toggle: () => ipcRenderer.invoke('subtitle-window:toggle'),
  close: () => ipcRenderer.invoke('subtitle-window:close'),
  isOpen: () => ipcRenderer.invoke('subtitle-window:is-open'),
  update: (items) => ipcRenderer.invoke('subtitle-window:update', items),
  getLatest: () => ipcRenderer.invoke('subtitle-window:get-latest'),
  onClosed: (callback) => {
    const listener = () => callback()
    ipcRenderer.on('subtitle-window:closed', listener)
    return () => ipcRenderer.removeListener('subtitle-window:closed', listener)
  },
  onUpdate: (callback) => {
    const listener = (_event, items) => callback(items)
    ipcRenderer.on('subtitle-window:data', listener)
    return () => ipcRenderer.removeListener('subtitle-window:data', listener)
  },
})

contextBridge.exposeInMainWorld('electronAppConfig', {
  get: () => ipcRenderer.invoke('app-config:get'),
  save: (config) => ipcRenderer.invoke('app-config:save', config),
  clear: () => ipcRenderer.invoke('app-config:clear'),
  check: (config) => ipcRenderer.invoke('app-config:check', config),
  restartBackend: () => ipcRenderer.invoke('app-config:restart-backend'),
})
