<template>
  <div class="app" :class="{ 'is-recording': isRecording || isCapturing }">
    <div class="background-effects">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
            </svg>
          </div>
          <div class="logo-text">
            <h1>AI 同声传译</h1>
            <span class="version">v2.0</span>
          </div>
        </div>
      </div>
      <div class="header-center">
        <div class="status-bar">
          <div class="status-item" :class="wsStatus">
            <span class="status-dot"></span>
            <span>{{ wsStatus === 'connected' ? '已连接' : '未连接' }}</span>
          </div>
          <div class="status-divider"></div>
          <div class="status-item">
            <span>🎙️</span>
            <span>{{ isRecording ? '录音中' : '待机' }}</span>
          </div>
          <div class="status-divider"></div>
          <div class="status-item">
            <span>📊</span>
            <span>{{ subtitleCount }} 条</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <button class="icon-btn" @click="showSettings = true" title="设置">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
      </div>
    </header>

    <main class="app-main">
      <div class="input-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          class="tab-btn" 
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <div v-if="activeTab === 'desktop'" class="browser-area">
        <div class="browser-controls">
          <div class="browser-info">
            <div class="browser-icon">
              <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="12" r="4" fill="currentColor"/>
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div>
              <h3>浏览器音频捕获</h3>
              <p>捕获浏览器标签页或系统音频进行实时翻译</p>
            </div>
          </div>
          <button 
            class="capture-btn" 
            :class="{ active: isCapturing }"
            @click="toggleRecording"
          >
            {{ isCapturing ? '停止捕获' : '开始捕获' }}
          </button>
        </div>
        <div v-if="isCapturing" class="capture-status">
          <div class="capture-wave">
            <div v-for="i in 20" :key="i" class="wave-bar" :style="{ animationDelay: `${i * 0.05}s` }"></div>
          </div>
          <span>正在捕获音频...</span>
        </div>
      </div>

      <div class="subtitle-area">
        <div class="subtitle-container" ref="subtitleContainer">
          <div v-if="subtitles.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg viewBox="0 0 80 80" fill="none">
                <circle cx="40" cy="40" r="38" stroke="currentColor" stroke-width="2" stroke-dasharray="8 4" opacity="0.3"/>
                <path d="M30 35C30 35 35 45 40 45C45 45 50 35 50 35" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
                <circle cx="32" cy="30" r="2" fill="currentColor" opacity="0.5"/>
                <circle cx="48" cy="30" r="2" fill="currentColor" opacity="0.5"/>
              </svg>
            </div>
            <p class="empty-text">选择输入方式开始翻译</p>
            <p class="empty-hint">支持麦克风录音或桌面音频捕获</p>
          </div>

          <transition-group name="subtitle" tag="div" class="subtitle-list">
            <div 
              v-for="(sub, index) in subtitles" 
              :key="sub.id || index"
              class="subtitle-item"
              :class="{ 
                'is-latest': index === subtitles.length - 1,
                'is-partial': sub.isPartial,
                'is-corrected': sub.isCorrected 
              }"
            >
              <div class="subtitle-time">{{ formatTime(sub.timestamp) }}</div>
              <div class="subtitle-content">
                <div class="original-line">
                  <span class="lang-badge source">{{ settings.sourceLang }}</span>
                  <span class="text">{{ sub.original }}</span>
                </div>
                <div class="translated-line">
                  <span class="lang-badge target">{{ settings.targetLang }}</span>
                  <span class="text">{{ sub.translated }}</span>
                </div>
              </div>
              <div class="subtitle-actions" v-if="sub.isCorrected">
                <span class="correction-badge">已修正</span>
              </div>
            </div>
          </transition-group>
        </div>
      </div>

      <div class="waveform-area" :class="{ active: isRecording || isCapturing }">
        <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
      </div>
    </main>

    <footer class="app-footer">
      <div class="footer-left">
        <div class="lang-switcher">
          <label class="select-field">
            <span>Source</span>
            <select v-model="settings.sourceLang" class="footer-select">
              <option v-for="lang in sourceLanguageOptions" :key="lang.value" :value="lang.value">
                {{ lang.label }}
              </option>
            </select>
          </label>
          <button class="swap-btn" @click="swapLangs" title="交换语言">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M7 16l-4-4m0 0l4-4m-4 4h18M17 8l4 4m0 0l-4 4m4-4H3"/>
            </svg>
          </button>
          <label class="select-field">
            <span>Target</span>
            <select v-model="settings.targetLang" class="footer-select">
              <option v-for="lang in targetLanguageOptions" :key="lang.value" :value="lang.value">
                {{ lang.label }}
              </option>
            </select>
          </label>
          <label class="select-field input-select-field">
            <span>Input</span>
            <select v-model="activeTab" class="footer-select" @change="handleInputModeChange">
              <option v-for="tab in captureTabs" :key="tab.id" :value="tab.id">
                {{ tab.label }}
              </option>
            </select>
          </label>
        </div>
      </div>

      <div class="footer-center">
        <button 
          class="record-btn" 
          :class="{ recording: isRecording || isCapturing }"
          @click="toggleRecording"
        >
          <div class="btn-inner">
            <div class="btn-icon">
              <svg v-if="!isRecording && !isCapturing" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </div>
          </div>
          <div class="btn-ripple" v-if="isRecording || isCapturing"></div>
        </button>
        <div class="record-label">{{ isRecording || isCapturing ? '停止' : activeTab === 'desktop' ? '开始桌面音频' : '开始录音' }}</div>
      </div>

      <div class="footer-right">
        <button
          class="action-btn subtitle-toggle-btn"
          :class="{ active: independentSubtitleWindowOpen }"
          @click="toggleIndependentSubtitleWindow"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 5h16a2 2 0 012 2v8a2 2 0 01-2 2H8l-4 4v-4H4a2 2 0 01-2-2V7a2 2 0 012-2z"/>
            <path d="M7 9h10M7 13h6"/>
          </svg>
          <span>{{ independentSubtitleWindowOpen ? '字幕开' : '字幕关' }}</span>
        </button>
        <button class="action-btn" @click="exportSubtitles" :disabled="subtitles.length === 0">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
          </svg>
          <span>导出</span>
        </button>
        <button class="action-btn" @click="clearSubtitles" :disabled="subtitles.length === 0">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
          <span>清空</span>
        </button>
      </div>
    </footer>

    <div class="settings-drawer" :class="{ open: showSettings }">
      <div class="drawer-overlay" @click="showSettings = false"></div>
      <div class="drawer-content">
        <div class="drawer-header">
          <h3>设置</h3>
          <button class="close-btn" @click="showSettings = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="drawer-body">
          <div class="setting-group">
            <label>智能纠错</label>
            <el-switch v-model="settings.enableCorrection" />
          </div>
          <div class="setting-group">
            <label>语音播报</label>
            <el-switch v-model="settings.enableTTS" />
          </div>
          <div class="setting-group">
            <label>字幕大小</label>
            <el-slider v-model="fontSize" :min="14" :max="32" :step="2" />
          </div>
          <div class="setting-group">
            <label>识别时自动打开字幕</label>
            <el-switch v-model="settings.autoOpenSubtitleWindow" />
          </div>
          <div class="setting-group">
            <label>API状态</label>
            <span class="api-status" :class="{ connected: apiConnected }">
              {{ apiConnected ? '已连接' : '未配置' }}
            </span>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { WavRecorder, encodeWAV } from './utils/audioUtils.js'

const isRecording = ref(false)
const isCapturing = ref(false)
const wsStatus = ref('disconnected')
const apiConnected = ref(false)
const subtitles = ref([])
const subtitleContainer = ref(null)
const waveformCanvas = ref(null)
const showSettings = ref(false)
const independentSubtitleWindowOpen = ref(false)
const fontSize = ref(20)
const subtitleCount = ref(0)
const activeTab = ref('mic')

const settings = reactive({
  sourceLang: 'EN',
  targetLang: 'ZH',
  enableCorrection: true,
  enableTTS: false,
  autoOpenSubtitleWindow: true
})

const tabs = [
  { id: 'mic', icon: '🎙️', label: '麦克风' },
  { id: 'desktop', icon: '🖥️', label: '桌面音频' }
]

const langOptions = ['AUTO', 'EN', 'ZH', 'JA', 'KO', 'FR', 'DE', 'ES', 'PT', 'IT', 'RU', 'AR', 'YUE', 'VI', 'TH', 'ID', 'HI', 'EL', 'TR']
const languageLabels = {
  AUTO: '自动',
  EN: '英语',
  ZH: '中文',
  JA: '日语',
  KO: '韩语',
  FR: '法语',
  DE: '德语',
  ES: '西班牙语',
  PT: '葡萄牙语',
  IT: '意大利语',
  RU: '俄语',
  AR: '阿拉伯语',
  YUE: '粤语',
  VI: '越南语',
  TH: '泰语',
  ID: '印尼语',
  HI: '印地语',
  EL: '希腊语',
  TR: '土耳其语'
}
const sourceLanguageOptions = langOptions.map(value => ({ value, label: languageLabels[value] }))
const targetLanguageOptions = langOptions
  .filter(value => value !== 'AUTO')
  .map(value => ({ value, label: languageLabels[value] }))
const captureTabs = tabs.filter(tab => tab.id === 'mic' || tab.id === 'desktop')

let ws = null
let audioContext = null
let analyser = null
let mediaStream = null
let mediaRecorder = null
let wavRecorder = null
let animationId = null
let subtitleIdCounter = 0
let captureStream = null
const audioSendQueue = []
const maxQueuedAudioChunks = 1200
let isFlushingAudioQueue = false
let pendingSettingsAck = null
let independentSubtitleWindow = null

const latestSubtitle = computed(() => {
  for (let i = subtitles.value.length - 1; i >= 0; i--) {
    if (subtitles.value[i]?.translated) return subtitles.value[i]
  }
  return null
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const d = new Date(timestamp)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function collapseRepeatedText(text = '') {
  let result = String(text).replace(/\s+/g, ' ').trim()
  if (!result) return ''

  for (let size = 6; size <= 80; size++) {
    let i = 0
    let changed = false
    while (i + size * 2 <= result.length) {
      const chunk = result.slice(i, i + size)
      let end = i + size
      while (result.slice(end, end + size) === chunk) {
        end += size
      }
      if (end > i + size) {
        result = result.slice(0, i + size) + result.slice(end)
        changed = true
      }
      i += 1
    }
    if (changed) size = 5
  }

  return result
}

function formatFloatingText(text = '', maxChars = 140) {
  const collapsed = collapseRepeatedText(text)
  if (collapsed.length <= maxChars) return collapsed

  const tail = collapsed.slice(-maxChars)
  const breakAt = Math.max(
    tail.indexOf('，'),
    tail.indexOf('。'),
    tail.indexOf(','),
    tail.indexOf('.'),
    tail.indexOf(' ')
  )

  if (breakAt > 8 && breakAt < tail.length - 12) {
    return tail.slice(breakAt + 1).trim()
  }
  return tail.trim()
}

function cycleLang(type) {
  const idx = langOptions.indexOf(settings[type === 'source' ? 'sourceLang' : 'targetLang'])
  settings[type === 'source' ? 'sourceLang' : 'targetLang'] = langOptions[(idx + 1) % langOptions.length]
}

function swapLangs() {
  if (settings.sourceLang === 'AUTO') return
  const temp = settings.sourceLang
  settings.sourceLang = settings.targetLang
  settings.targetLang = temp
}

function handleInputModeChange() {
  if (isRecording.value) stopRecording()
  if (isCapturing.value) stopCapture()
}

async function toggleIndependentSubtitleWindow() {
  if (independentSubtitleWindow && !independentSubtitleWindow.closed) {
    independentSubtitleWindow.close()
    independentSubtitleWindow = null
    independentSubtitleWindowOpen.value = false
    return
  }

  try {
    if ('documentPictureInPicture' in window) {
      independentSubtitleWindow = await window.documentPictureInPicture.requestWindow({
        width: 900,
        height: 180
      })
    } else {
      independentSubtitleWindow = window.open('', 'ai_subtitle_window', 'width=900,height=180,alwaysRaised=yes')
    }

    if (!independentSubtitleWindow) {
      ElMessage.warning('字幕窗口被浏览器拦截，请允许弹出窗口')
      return
    }

    independentSubtitleWindow.document.title = '独立字幕'
    independentSubtitleWindow.document.body.innerHTML = `
      <style>
        * { box-sizing: border-box; }
        html, body {
          margin: 0;
          width: 100%;
          height: 100%;
          overflow: hidden;
          background: transparent !important;
          background-color: transparent !important;
          color: #f8fafc;
          font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        body {
          padding: 18px 24px 18px 18px;
        }
        #subtitle-close {
          position: fixed;
          top: 8px;
          right: 8px;
          z-index: 10;
          width: 28px;
          height: 28px;
          border: 1px solid rgba(248, 250, 252, 0.24);
          border-radius: 999px;
          background: rgba(2, 6, 23, 0.28);
          color: rgba(248, 250, 252, 0.88);
          font-size: 18px;
          line-height: 24px;
          cursor: pointer;
          backdrop-filter: blur(8px);
        }
        #subtitle-close:hover {
          background: rgba(239, 68, 68, 0.72);
          border-color: rgba(254, 202, 202, 0.7);
          color: #fff;
        }
        #subtitle-root {
          height: 100%;
          overflow-y: auto;
          padding: 24px 12px 0 0;
          scroll-behavior: smooth;
        }
        #subtitle-root::-webkit-scrollbar {
          width: 8px;
        }
        #subtitle-root::-webkit-scrollbar-thumb {
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.45);
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
          border-radius: 10px;
          background: transparent !important;
          border: 0;
          text-align: left;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.82);
        }
        .subtitle-row.partial {
          opacity: 0.72;
        }
        .original {
          margin-bottom: 6px;
          color: rgba(241, 245, 249, 0.8);
          font-size: 14px;
          line-height: 1.4;
        }
        .translated {
          color: #22c55e;
          font-size: 22px;
          font-weight: 800;
          line-height: 1.35;
        }
        .empty {
          display: grid;
          height: 100%;
          place-items: center;
          color: rgba(148, 163, 184, 0.72);
          font-size: 18px;
          font-weight: 600;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.82);
        }
      </style>
      <button id="subtitle-close" type="button" title="关闭字幕">×</button>
      <div id="subtitle-root"><div class="empty">等待字幕...</div></div>
    `

    independentSubtitleWindow.document
      .getElementById('subtitle-close')
      ?.addEventListener('click', () => {
        independentSubtitleWindow?.close()
        independentSubtitleWindow = null
        independentSubtitleWindowOpen.value = false
      })

    independentSubtitleWindow.addEventListener('pagehide', () => {
      independentSubtitleWindow = null
      independentSubtitleWindowOpen.value = false
    })
    independentSubtitleWindow.addEventListener('beforeunload', () => {
      independentSubtitleWindow = null
      independentSubtitleWindowOpen.value = false
    })

    independentSubtitleWindowOpen.value = true
    renderIndependentSubtitleWindow()
  } catch (err) {
    independentSubtitleWindow = null
    independentSubtitleWindowOpen.value = false
    ElMessage.error('无法打开独立字幕窗口: ' + err.message)
  }
}

async function ensureIndependentSubtitleWindow() {
  if (!settings.autoOpenSubtitleWindow) return
  if (independentSubtitleWindow && !independentSubtitleWindow.closed) return
  await toggleIndependentSubtitleWindow()
}

function renderIndependentSubtitleWindow() {
  if (!independentSubtitleWindow || independentSubtitleWindow.closed) {
    independentSubtitleWindow = null
    independentSubtitleWindowOpen.value = false
    return
  }

  const root = independentSubtitleWindow.document.getElementById('subtitle-root')
  if (!root) return

  const visibleSubtitles = subtitles.value.filter(subtitle => subtitle.translated)
  if (!visibleSubtitles.length) {
    root.innerHTML = '<div class="empty">等待字幕...</div>'
    return
  }

  root.innerHTML = ''
  const list = independentSubtitleWindow.document.createElement('div')
  list.className = 'subtitle-list'

  visibleSubtitles.slice(-80).forEach((subtitle) => {
    const row = independentSubtitleWindow.document.createElement('div')
    row.className = `subtitle-row${subtitle.isPartial ? ' partial' : ''}`

    if (subtitle.original) {
      const original = independentSubtitleWindow.document.createElement('div')
      original.className = 'original'
      original.textContent = subtitle.original
      row.appendChild(original)
    }

    const translated = independentSubtitleWindow.document.createElement('div')
    translated.className = 'translated'
    translated.textContent = subtitle.translated
    row.appendChild(translated)
    list.appendChild(row)
  })

  root.appendChild(list)
  root.scrollTop = root.scrollHeight
}

function sendSettings({ waitForAck = false } = {}) {
  if (ws?.readyState !== WebSocket.OPEN) return waitForAck ? Promise.resolve(false) : false
  if (pendingSettingsAck?.timer) {
    clearTimeout(pendingSettingsAck.timer)
    pendingSettingsAck.resolve(false)
    pendingSettingsAck = null
  }
  const ackPromise = waitForAck
    ? new Promise((resolve) => {
        const timer = setTimeout(() => {
          if (pendingSettingsAck?.resolve === resolve) {
            pendingSettingsAck = null
          }
          resolve(false)
        }, 2500)
        pendingSettingsAck = { resolve, timer }
      })
    : null
  ws.send(JSON.stringify({
    type: 'settings',
    data: {
      source_lang: settings.sourceLang.toLowerCase(),
      target_lang: settings.targetLang.toLowerCase(),
      enable_correction: settings.enableCorrection,
      enable_tts: settings.enableTTS
    }
  }))
  return ackPromise || true
}

function sendAudioBlob(wavBlob) {
  audioSendQueue.push(wavBlob)
  if (audioSendQueue.length > maxQueuedAudioChunks) {
    audioSendQueue.splice(0, audioSendQueue.length - maxQueuedAudioChunks)
    ElMessage.warning('音频发送积压过多，已丢弃最旧片段')
  }
  flushAudioQueue()
}

function flushAudioQueue() {
  if (isFlushingAudioQueue || ws?.readyState !== WebSocket.OPEN) return
  isFlushingAudioQueue = true

  const pump = () => {
    if (ws?.readyState !== WebSocket.OPEN) {
      isFlushingAudioQueue = false
      return
    }

    let sent = 0
    while (audioSendQueue.length && ws.bufferedAmount < 2 * 1024 * 1024 && sent < 24) {
      ws.send(audioSendQueue.shift())
      sent += 1
    }

    if (audioSendQueue.length) {
      setTimeout(pump, ws.bufferedAmount > 2 * 1024 * 1024 ? 30 : 0)
      return
    }

    isFlushingAudioQueue = false
  }

  pump()
}

function resolveSettingsAck() {
  if (!pendingSettingsAck) return
  clearTimeout(pendingSettingsAck.timer)
  pendingSettingsAck.resolve(true)
  pendingSettingsAck = null
}

function resetAudioTransportState() {
  if (pendingSettingsAck?.timer) {
    clearTimeout(pendingSettingsAck.timer)
    pendingSettingsAck.resolve(false)
    pendingSettingsAck = null
  }
  isFlushingAudioQueue = false
}

function clearAudioQueue() {
  audioSendQueue.length = 0
  resetAudioTransportState()
}

async function toggleCapture() {
  if (isCapturing.value) {
    stopCapture()
  } else {
    await startCapture()
  }
}

async function startCapture() {
  try {
    await connectWS()
    captureStream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
        sampleRate: 16000
      }
    })

    if (captureStream.getAudioTracks().length === 0) {
      captureStream.getTracks().forEach(t => t.stop())
      captureStream = null
      ElMessage.warning('没有捕获到桌面音频，请在共享窗口里勾选共享音频')
      return
    }

    const captureAudioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 })
    const source = captureAudioContext.createMediaStreamSource(captureStream)
    analyser = captureAudioContext.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)

    const bufferSize = Math.floor(16000 * 0.08)
    let buffer = []
    let isSpeaking = false
    let silenceTimeout = null
    let voiceFrameCount = 0
    const energyThreshold = 0.065
    const maxSilenceMs = 450
    const minVoiceFrames = 5

    const processor = captureAudioContext.createScriptProcessor(4096, 1, 1)
    source.connect(processor)
    processor.connect(captureAudioContext.destination)

    processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0)
      buffer.push(...inputData)
      while (buffer.length >= bufferSize) {
        const chunk = buffer.splice(0, bufferSize)
        const wavBlob = encodeWAV(new Float32Array(chunk), 16000)
        sendAudioBlob(wavBlob)
      }
      return

      let sum = 0
      for (let i = 0; i < inputData.length; i++) sum += inputData[i] * inputData[i]
      const rms = Math.sqrt(sum / inputData.length)
      const hasVoice = rms > energyThreshold

      if (hasVoice) {
        voiceFrameCount++
        if (voiceFrameCount >= minVoiceFrames) {
          isSpeaking = true
          if (silenceTimeout) { clearTimeout(silenceTimeout); silenceTimeout = null }
        }
        if (isSpeaking) buffer.push(...inputData)
      } else {
        voiceFrameCount = 0
        if (isSpeaking) {
          buffer.push(...inputData)
          if (!silenceTimeout) {
            silenceTimeout = setTimeout(() => {
              isSpeaking = false
              silenceTimeout = null
              voiceFrameCount = 0
              if (buffer.length > 0) {
                const wavBlob = encodeWAV(new Float32Array(buffer), 16000)
                buffer = []
                sendAudioBlob(wavBlob)
              }
            }, maxSilenceMs)
          }
        }
      }

      if (buffer.length >= bufferSize && isSpeaking) {
        const chunk = buffer.splice(0, bufferSize)
        const wavBlob = encodeWAV(new Float32Array(chunk), 16000)
        sendAudioBlob(wavBlob)
      }
    }

    mediaRecorder = { stop: () => { if (silenceTimeout) clearTimeout(silenceTimeout); processor.disconnect(); captureAudioContext.close() } }

    isCapturing.value = true
    await ensureIndependentSubtitleWindow()
    drawWaveform()

    captureStream.getTracks().forEach(track => {
      track.onended = () => {
        if (isCapturing.value) stopCapture()
      }
    })

  } catch (err) {
    ElMessage.error('无法捕获音频: ' + err.message)
  }
}

function stopCapture() {
  isCapturing.value = false
  clearAudioQueue()

  if (mediaRecorder?.state !== 'inactive') {
    mediaRecorder?.stop()
  }

  if (captureStream) {
    captureStream.getTracks().forEach(t => t.stop())
  }

  if (audioContext) {
    audioContext.close()
  }

  if (ws) {
    ws.close()
    ws = null
  }

  captureStream = null
  mediaRecorder = null
  audioContext = null
  analyser = null
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else if (isCapturing.value) {
    stopCapture()
  } else if (activeTab.value === 'desktop') {
    startCapture()
  } else {
    startRecording()
  }
}

function connectWS() {
  if (ws?.readyState === WebSocket.OPEN) {
    return Promise.resolve(sendSettings({ waitForAck: true })).then(() => {
      flushAudioQueue()
    })
  }
  if (ws?.readyState === WebSocket.CONNECTING) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('WebSocket连接超时')), 5000)
      ws.addEventListener('open', () => { clearTimeout(timer); resolve() }, { once: true })
      ws.addEventListener('error', () => { clearTimeout(timer); reject(new Error('WebSocket连接失败')) }, { once: true })
    })
  }

  const wsUrl = `ws://${window.location.hostname}:9000/ws/translate`
  ws = new WebSocket(wsUrl)

  const openPromise = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('WebSocket连接超时')), 5000)

    ws.onopen = async () => {
      clearTimeout(timer)
      wsStatus.value = 'connected'
      await sendSettings({ waitForAck: true })
      flushAudioQueue()
      resolve()
    }

    ws.onerror = () => {
      clearTimeout(timer)
      wsStatus.value = 'disconnected'
      reject(new Error('WebSocket连接失败'))
    }
  })

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.type === 'partial' || data.type === 'final') {
      addSubtitle(data.type, data.content)
    } else if (data.type === 'settings_updated') {
      resolveSettingsAck()
    } else if (data.type === 'correction') {
      applyCorrection(data.content)
    } else if (data.type === 'error') {
      addSubtitle('final', {
        original: '服务返回错误',
        translated: data.content?.message || '未知错误',
        timestamp: new Date().toISOString()
      })
      ElMessage.error(data.content?.message || '识别失败')
    }
  }

  ws.onclose = () => {
    wsStatus.value = 'disconnected'
    resetAudioTransportState()
    if (isRecording.value || isCapturing.value) {
      setTimeout(connectWS, 3000)
    }
  }

  return openPromise
}

function addSubtitle(type, content) {
  let { original, translated, timestamp } = content
  if (type === 'partial') {
    original = collapseRepeatedText(original)
    translated = collapseRepeatedText(translated)
  }

  if (type === 'partial') {
    const existing = subtitles.value.find(s => s.isPartial)
    if (existing) {
      existing.original = original
      existing.translated = translated
      existing.timestamp = timestamp
    } else {
      subtitles.value.push({
        id: ++subtitleIdCounter,
        original, translated, timestamp,
        isPartial: true, isCorrected: false
      })
    }
  } else {
    const partial = subtitles.value.find(s => s.isPartial)
    if (partial) {
      partial.isPartial = false
      partial.original = original || partial.original
      partial.translated = translated
      partial.timestamp = timestamp || partial.timestamp
    } else {
      subtitles.value.push({
        id: ++subtitleIdCounter,
        original, translated, timestamp,
        isPartial: false, isCorrected: false
      })
    }
  }

  subtitleCount.value = subtitles.value.length

  if (subtitles.value.length > 100) {
    subtitles.value = subtitles.value.slice(-100)
  }

  nextTick(() => {
    if (subtitleContainer.value) {
      subtitleContainer.value.scrollTop = subtitleContainer.value.scrollHeight
    }
  })
}

function applyCorrection(content) {
  const { index, original, translated } = content
  if (subtitles.value[index]) {
    subtitles.value[index].original = original
    subtitles.value[index].translated = translated
    subtitles.value[index].isCorrected = true
  }
}

async function startRecording() {
  try {
    await connectWS()
    wavRecorder = new WavRecorder(16000, {
      bufferDuration: 0.08,
      continuous: true,
      energyThreshold: 0.065,
      maxSilenceMs: 450,
      minVoiceFrames: 5
    })
    await wavRecorder.start((wavBlob) => {
      sendAudioBlob(wavBlob)
    })

    mediaStream = wavRecorder.stream
    audioContext = wavRecorder.audioContext
    if (audioContext) {
      const source = audioContext.createMediaStreamSource(mediaStream)
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      source.connect(analyser)
    }

    isRecording.value = true
    await ensureIndependentSubtitleWindow()
    drawWaveform()
  } catch (err) {
    ElMessage.error('无法访问麦克风: ' + err.message)
  }
}

function stopRecording() {
  isRecording.value = false
  clearAudioQueue()

  if (wavRecorder) {
    wavRecorder.stop()
    wavRecorder = null
  }

  if (ws) {
    ws.close()
    ws = null
  }

  mediaRecorder = null
  mediaStream = null
  audioContext = null
  analyser = null
}

function drawWaveform() {
  const canvas = waveformCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const W = canvas.width = canvas.offsetWidth * 2
  const H = canvas.height = canvas.offsetHeight * 2

  function draw() {
    animationId = requestAnimationFrame(draw)
    ctx.clearRect(0, 0, W, H)

    if (!analyser) {
      drawIdle(ctx, W, H)
      return
    }

    const bufLen = analyser.frequencyBinCount
    const data = new Uint8Array(bufLen)
    analyser.getByteTimeDomainData(data)

    const gradient = ctx.createLinearGradient(0, 0, W, 0)
    gradient.addColorStop(0, '#6366f1')
    gradient.addColorStop(0.5, '#8b5cf6')
    gradient.addColorStop(1, '#a78bfa')

    ctx.lineWidth = 3
    ctx.strokeStyle = gradient
    ctx.beginPath()

    const sliceW = W / bufLen
    let x = 0

    for (let i = 0; i < bufLen; i++) {
      const v = data[i] / 128.0
      const y = v * H / 2
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
      x += sliceW
    }

    ctx.lineTo(W, H / 2)
    ctx.stroke()
  }

  draw()
}

function drawIdle(ctx, W, H) {
  ctx.strokeStyle = 'rgba(99, 102, 241, 0.2)'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(0, H / 2)

  const time = Date.now() / 1000
  for (let x = 0; x < W; x += 2) {
    const y = H / 2 + Math.sin(x * 0.01 + time) * 10
    ctx.lineTo(x, y)
  }
  ctx.stroke()
}

function exportSubtitles() {
  if (subtitles.value.length === 0) return

  let content = '序号\t原文\t译文\t时间\n'
  subtitles.value.forEach((s, i) => {
    content += `${i + 1}\t${s.original}\t${s.translated}\t${formatTime(s.timestamp)}\n`
  })

  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `translation_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success('导出成功')
}

function clearSubtitles() {
  subtitles.value = []
  subtitleCount.value = 0
}

watch(
  () => ({
    sourceLang: settings.sourceLang,
    targetLang: settings.targetLang,
    enableCorrection: settings.enableCorrection,
    enableTTS: settings.enableTTS
  }),
  sendSettings,
  { deep: true }
)

watch(subtitles, renderIndependentSubtitleWindow, { deep: true })

onMounted(async () => {
  drawWaveform()

  try {
    const response = await fetch('/api/status')
    const data = await response.json()
    apiConnected.value = data.api_configured
  } catch {
    apiConnected.value = false
  }
})

onUnmounted(() => {
  stopRecording()
  stopCapture()
  if (independentSubtitleWindow && !independentSubtitleWindow.closed) {
    independentSubtitleWindow.close()
  }
  if (animationId) cancelAnimationFrame(animationId)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --primary: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --accent: #a78bfa;
  --bg-primary: #0f0f23;
  --bg-secondary: #1a1a3e;
  --bg-tertiary: #252552;
  --surface: rgba(255, 255, 255, 0.03);
  --surface-hover: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.08);
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
  height: 100vh;
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.background-effects {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.orb-1 { width: 600px; height: 600px; background: var(--primary); top: -200px; left: -200px; animation: float 20s ease-in-out infinite; }
.orb-2 { width: 400px; height: 400px; background: var(--accent); bottom: -100px; right: -100px; animation: float 25s ease-in-out infinite reverse; }
.orb-3 { width: 300px; height: 300px; background: #ec4899; top: 50%; left: 50%; transform: translate(-50%, -50%); animation: float 30s ease-in-out infinite; }

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(50px, -50px); }
  50% { transform: translate(-30px, 30px); }
  75% { transform: translate(20px, 60px); }
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  z-index: 10;
}

.header-left { flex: 1; }

.logo { display: flex; align-items: center; gap: 12px; }

.logo-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 12px;
  color: white;
}

.logo-icon svg { width: 24px; height: 24px; }

.logo-text h1 { font-size: 18px; font-weight: 600; }
.version { font-size: 11px; color: var(--text-muted); }

.header-center { flex: 2; display: flex; justify-content: center; }

.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 20px;
  background: var(--surface);
  border-radius: 100px;
  border: 1px solid var(--border);
}

.status-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }

.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--danger); }
.status-item.connected .status-dot { background: var(--success); box-shadow: 0 0 8px var(--success); }

.status-divider { width: 1px; height: 16px; background: var(--border); }

.header-right { flex: 1; display: flex; justify-content: flex-end; }

.icon-btn {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover { background: var(--surface-hover); color: var(--text-primary); }
.icon-btn svg { width: 20px; height: 20px; }

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
  gap: 16px;
  z-index: 1;
  min-height: 0;
}

.input-tabs {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: var(--surface);
  border-radius: 14px;
  border: 1px solid var(--border);
  width: fit-content;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover { color: var(--text-primary); background: var(--surface-hover); }
.tab-btn.active { background: var(--primary); color: white; }

.tab-icon { font-size: 16px; }

.browser-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.browser-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: var(--surface);
  border-radius: 16px;
  border: 1px solid var(--border);
}

.browser-info { display: flex; align-items: center; gap: 16px; }

.browser-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 12px;
  color: var(--primary);
}

.browser-icon svg { width: 24px; height: 24px; }
.browser-info h3 { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
.browser-info p { font-size: 13px; color: var(--text-muted); }

.capture-btn {
  padding: 12px 24px;
  background: var(--primary);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.capture-btn:hover { background: var(--primary-dark); }
.capture-btn.active { background: var(--danger); }

.capture-status {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.capture-wave {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 24px;
}

.wave-bar {
  width: 3px;
  height: 100%;
  background: var(--danger);
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { transform: scaleY(0.3); }
  50% { transform: scaleY(1); }
}

.capture-status span { font-size: 13px; color: var(--danger); }

.subtitle-area {
  flex: 1;
  min-height: 0;
  background: var(--surface);
  border-radius: 20px;
  border: 1px solid var(--border);
  overflow: hidden;
}

.subtitle-container {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.subtitle-container::-webkit-scrollbar { width: 6px; }
.subtitle-container::-webkit-scrollbar-track { background: transparent; }
.subtitle-container::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-icon { width: 80px; height: 80px; margin-bottom: 20px; color: var(--primary); opacity: 0.5; }
.empty-text { font-size: 18px; font-weight: 500; margin-bottom: 8px; color: var(--text-secondary); }
.empty-hint { font-size: 14px; }

.subtitle-list { display: flex; flex-direction: column; gap: 12px; }

.subtitle-item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px solid transparent;
  transition: all 0.3s;
}

.subtitle-item:hover { background: rgba(255, 255, 255, 0.04); border-color: var(--border); }
.subtitle-item.is-latest { background: rgba(99, 102, 241, 0.05); border-color: rgba(99, 102, 241, 0.2); }
.subtitle-item.is-partial { opacity: 0.7; }
.subtitle-item.is-corrected { border-left: 3px solid var(--success); }

.subtitle-time { font-size: 11px; color: var(--text-muted); min-width: 60px; padding-top: 2px; }

.subtitle-content { flex: 1; min-width: 0; }

.original-line, .translated-line { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px; }
.original-line:last-child, .translated-line:last-child { margin-bottom: 0; }

.lang-badge {
  display: inline-flex;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 4px;
  letter-spacing: 0.05em;
  flex-shrink: 0;
  margin-top: 3px;
}

.lang-badge.source { background: rgba(99, 102, 241, 0.2); color: var(--primary-light); }
.lang-badge.target { background: rgba(34, 197, 94, 0.2); color: var(--success); }

.text { font-size: 14px; line-height: 1.5; }
.original-line .text { color: var(--text-primary); }
.translated-line .text { color: var(--success); }

.subtitle-actions { display: flex; align-items: center; }

.correction-badge {
  font-size: 10px;
  padding: 3px 8px;
  background: rgba(34, 197, 94, 0.1);
  color: var(--success);
  border-radius: 100px;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.waveform-area {
  height: 60px;
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow: hidden;
  transition: all 0.3s;
}

.waveform-area.active { border-color: rgba(99, 102, 241, 0.3); box-shadow: 0 0 20px rgba(99, 102, 241, 0.1); }

.waveform-canvas { width: 100%; height: 100%; display: block; }

.app-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: rgba(15, 15, 35, 0.9);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  z-index: 10;
}

.footer-left, .footer-right { flex: 1; }
.footer-right { display: flex; justify-content: flex-end; gap: 10px; }

.lang-switcher { display: flex; align-items: flex-end; gap: 10px; }

.select-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 104px;
}

.select-field span {
  padding-left: 2px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.footer-select {
  width: 100%;
  height: 38px;
  padding: 0 34px 0 12px;
  appearance: none;
  background:
    linear-gradient(45deg, transparent 50%, var(--text-secondary) 50%) calc(100% - 17px) 16px / 6px 6px no-repeat,
    linear-gradient(135deg, var(--text-secondary) 50%, transparent 50%) calc(100% - 12px) 16px / 6px 6px no-repeat,
    var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 700;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.footer-select:hover,
.footer-select:focus {
  border-color: var(--primary);
  background-color: var(--surface-hover);
}

.footer-select option {
  color: #111827;
  background: #ffffff;
}

.input-select-field { min-width: 122px; }

.lang-btn {
  padding: 8px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 50px;
  text-align: center;
}

.lang-btn:hover { background: var(--surface-hover); border-color: var(--primary); }

.swap-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s;
}

.swap-btn:hover { background: var(--primary); color: white; transform: rotate(180deg); }
.swap-btn svg { width: 16px; height: 16px; }

.footer-center { display: flex; flex-direction: column; align-items: center; gap: 6px; }

.record-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  border: none;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.record-btn:hover { transform: scale(1.05); box-shadow: 0 6px 30px rgba(99, 102, 241, 0.5); }
.record-btn:active { transform: scale(0.95); }
.record-btn.recording { background: linear-gradient(135deg, var(--danger), #dc2626); box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4); }

.btn-inner { position: relative; z-index: 1; }
.btn-icon { color: white; }
.btn-icon svg { width: 24px; height: 24px; }

.btn-ripple {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 2px solid var(--danger);
  animation: ripple 1.5s ease-out infinite;
}

@keyframes ripple { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.3); opacity: 0; } }

.record-label { font-size: 11px; color: var(--text-muted); }

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) { background: var(--surface-hover); color: var(--text-primary); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-btn svg { width: 16px; height: 16px; }
.subtitle-toggle-btn.active {
  border-color: rgba(34, 197, 94, 0.45);
  background: rgba(34, 197, 94, 0.12);
  color: var(--success);
}

.mini-action-btn {
  padding: 7px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.mini-action-btn:hover {
  background: var(--surface-hover);
  border-color: var(--primary);
}

.settings-drawer { position: fixed; inset: 0; z-index: 100; pointer-events: none; }
.settings-drawer.open { pointer-events: all; }

.drawer-overlay { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); opacity: 0; transition: opacity 0.3s; }
.settings-drawer.open .drawer-overlay { opacity: 1; }

.drawer-content {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border);
  transform: translateX(100%);
  transition: transform 0.3s;
  display: flex;
  flex-direction: column;
}

.settings-drawer.open .drawer-content { transform: translateX(0); }

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.drawer-header h3 { font-size: 15px; font-weight: 600; }

.close-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface);
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
}

.close-btn:hover { background: var(--surface-hover); }
.close-btn svg { width: 16px; height: 16px; }

.drawer-body { padding: 20px; flex: 1; overflow-y: auto; }

.setting-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.setting-group label { font-size: 13px; color: var(--text-primary); }

.api-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 100px;
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.api-status.connected { background: rgba(34, 197, 94, 0.1); color: var(--success); }

.subtitle-enter-active, .subtitle-leave-active { transition: all 0.3s; }
.subtitle-enter-from { opacity: 0; transform: translateY(16px); }
.subtitle-leave-to { opacity: 0; transform: translateX(-16px); }

.is-recording .waveform-area { height: 80px; }
</style>
