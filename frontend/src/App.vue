<template>
  <div
    class="app"
    :class="{
      'is-recording': isRecording || isCapturing,
      'subtitle-window-mode': isSubtitleWindowMode
    }"
  >
    <div v-if="!isSubtitleWindowMode" class="background-effects">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <header v-if="!isSubtitleWindowMode" class="app-header">
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
        <button class="icon-btn" @click="showSettings = true" title="璁剧疆">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
      </div>
    </header>

    <main v-if="!isSubtitleWindowMode" class="app-main">
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
              <h3>桌面音频捕获</h3>
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
              <div class="subtitle-actions" v-if="sub.correctionStatus">
                <span class="correction-badge" :class="`status-${sub.correctionStatus}`">
                  {{ correctionStatusLabel(sub.correctionStatus) }}
                </span>
              </div>
            </div>
          </transition-group>
        </div>
      </div>

      <div class="waveform-area" :class="{ active: isRecording || isCapturing }">
        <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
      </div>
    </main>

    <footer v-if="!isSubtitleWindowMode" class="app-footer">
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
          class="action-btn speech-toggle-btn"
          :class="{ active: settings.enableSpeechReadout }"
          @click="toggleSpeechReadout"
        >
          <svg v-if="settings.enableSpeechReadout" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M23 9l-6 6M17 9l6 6"/>
          </svg>
          <span>{{ settings.enableSpeechReadout ? '朗读开' : '朗读关' }}</span>
        </button>
        <button
          class="action-btn subtitle-toggle-btn"
          :class="{ active: subtitleWindowActive }"
          @click="toggleIndependentSubtitleWindow"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 5h16a2 2 0 012 2v8a2 2 0 01-2 2H8l-4 4v-4H4a2 2 0 01-2-2V7a2 2 0 012-2z"/>
            <path d="M7 9h10M7 13h6"/>
          </svg>
          <span>{{ subtitleWindowActive ? '字幕开' : '字幕关' }}</span>
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

    <div v-if="!isSubtitleWindowMode" class="settings-drawer" :class="{ open: showSettings }">
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
          <section class="api-config-panel">
            <div class="api-config-heading">
              <h4>实时翻译配置</h4>
              <span class="api-status" :class="{ connected: apiUsable, checking: apiConfig.checking }">
                {{ apiStatusLabel }}
              </span>
            </div>
            <label class="config-field">
              <span>DashScope API Key</span>
              <input
                v-model.trim="apiConfig.dashscopeApiKey"
                class="config-input"
                type="password"
                autocomplete="off"
                :placeholder="apiConfig.hasDashscopeApiKey ? '留空保留原密钥' : '请输入 DashScope API Key'"
              />
            </label>
            <label class="config-field">
              <span>实时模型</span>
              <input
                v-model.trim="apiConfig.dashscopeLiveTranslateModel"
                class="config-input"
                type="text"
                autocomplete="off"
                placeholder="qwen3.5-livetranslate-flash-realtime"
              />
            </label>
            <button
              class="save-config-btn"
              type="button"
              :disabled="apiConfig.saving"
              @click="saveApiConfig"
            >
              {{ apiConfig.saving ? '保存中...' : '保存配置' }}
            </button>
            <div class="api-config-actions">
              <button
                class="secondary-config-btn"
                type="button"
                :disabled="apiConfig.checking || apiConfig.saving"
                @click="checkApiConfig"
              >
                {{ apiConfig.checking ? '检测中...' : '检测可用性' }}
              </button>
              <button
                class="secondary-config-btn danger"
                type="button"
                :disabled="apiConfig.saving"
                @click="clearApiConfig"
              >
                清除配置
              </button>
            </div>
            <p class="api-config-note">
              {{ apiConfig.message || '首次使用必须输入并检测 API Key，应用不会内置任何默认密钥。' }}
            </p>
          </section>
          <div class="setting-group">
            <label>智能纠错</label>
            <el-switch v-model="settings.enableCorrection" />
          </div>
          <div class="setting-group">
            <label>识别时自动打开字幕</label>
            <el-switch v-model="settings.autoOpenSubtitleWindow" />
          </div>
          <div class="setting-group">
            <label>朗读音色</label>
            <select v-model="settings.speechVoiceStyle" class="compact-setting-select">
              <option value="sweet">龙菲菲（甜美女声）</option>
              <option value="natural">龙小淳（自然女声）</option>
              <option value="system">系统默认</option>
            </select>
          </div>
          <div class="setting-group">
            <label>API 状态</label>
            <span class="api-status" :class="{ connected: apiUsable, checking: apiConfig.checking }">
              {{ apiStatusLabel }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="shouldShowFloatingSubtitle"
      class="floating-subtitle-overlay"
      :style="{ left: `${floatingSubtitlePosition.x}px`, bottom: `${floatingSubtitlePosition.bottom}px` }"
      @pointerdown="startFloatingSubtitleDrag"
    >
      <button class="floating-subtitle-close" type="button" @click="closeSubtitleWindow">×</button>
      <div v-if="activeFloatingSubtitleBlock.original || activeFloatingSubtitleBlock.translated" class="floating-subtitle-content">
        <div
          class="floating-subtitle-row"
          :class="{ partial: activeFloatingSubtitleBlock.isPartial, corrected: activeFloatingSubtitleBlock.isCorrected }"
        >
          <div v-if="activeFloatingSubtitleBlock.original" class="floating-subtitle-original">
            {{ formatFloatingText(activeFloatingSubtitleBlock.original, 260) }}
          </div>
          <div v-if="activeFloatingSubtitleBlock.translated" class="floating-subtitle-translated">
            {{ formatFloatingText(activeFloatingSubtitleBlock.translated, 300) }}
          </div>
        </div>
      </div>
      <div v-else class="floating-subtitle-empty">等待字幕...</div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { WavRecorder, float32ToPcm16Buffer } from './utils/audioUtils.js'

const isRecording = ref(false)
const isCapturing = ref(false)
const wsStatus = ref('disconnected')
const apiConnected = ref(false)
const subtitles = ref([])
const subtitleContainer = ref(null)
const waveformCanvas = ref(null)
const showSettings = ref(false)
const electronSubtitleWindowOpen = ref(false)
const independentSubtitleWindowOpen = ref(false)
const floatingSubtitleOverlayOpen = ref(false)
const isSubtitleWindowMode = new URLSearchParams(window.location.search).get('subtitleWindow') === '1'
const externalSubtitleBlock = ref(null)
const floatingSubtitlePosition = reactive({
  x: Math.round(window.innerWidth / 2),
  bottom: 92
})
const subtitleCount = ref(0)
const activeTab = ref('mic')

const settings = reactive({
  sourceLang: 'EN',
  targetLang: 'ZH',
  enableCorrection: true,
  autoOpenSubtitleWindow: true,
  enableSpeechReadout: true,
  pauseSpeechReadoutWhileListening: false,
  speechVoiceStyle: 'sweet'
})

const apiConfig = reactive({
  dashscopeApiKey: '',
  dashscopeLiveTranslateModel: 'qwen3.5-livetranslate-flash-realtime',
  hasDashscopeApiKey: false,
  saving: false,
  checking: false,
  usable: false,
  message: ''
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
let pendingSettingsAck = null
let independentSubtitleWindow = null
let removeElectronSubtitleClosedListener = null
let removeElectronSubtitleUpdateListener = null
let subtitleBroadcastChannel = null
let activeSpeechAudio = null
let activeSpeechObjectUrl = ''
let speechPlaybackQueue = Promise.resolve()
const spokenSubtitleKeys = new Set()
const pendingPartialSubtitles = new Map()
const PARTIAL_RENDER_INTERVAL_MS = 180
const MAX_STORED_SUBTITLES = 80
const FLOATING_SUBTITLE_ROWS = 3
const EXTERNAL_SUBTITLE_ROWS = 3
const API_ORIGIN = window.location.protocol === 'file:' ? 'http://127.0.0.1:9000' : ''

const latestSubtitle = computed(() => {
  for (let i = subtitles.value.length - 1; i >= 0; i--) {
    if (subtitles.value[i]?.translated) return subtitles.value[i]
  }
  return null
})

const visibleSubtitleHistory = computed(() =>
  subtitles.value.filter(subtitle => subtitle.original || subtitle.translated)
)

const floatingVisibleSubtitles = computed(() =>
  visibleSubtitleHistory.value.slice(-FLOATING_SUBTITLE_ROWS)
)

const floatingSubtitleBlock = computed(() => buildSubtitleBlock(floatingVisibleSubtitles.value))

const activeFloatingSubtitleBlock = computed(() =>
  isSubtitleWindowMode
    ? externalSubtitleBlock.value || { original: '', translated: '', isPartial: false, isCorrected: false }
    : floatingSubtitleBlock.value
)

const shouldShowFloatingSubtitle = computed(() =>
  isSubtitleWindowMode || (floatingSubtitleOverlayOpen.value && !electronSubtitleWindowOpen.value)
)

const subtitleWindowActive = computed(() =>
  electronSubtitleWindowOpen.value ||
  Boolean(independentSubtitleWindow && !independentSubtitleWindow.closed)
)

const apiUsable = computed(() => Boolean(apiConfig.usable))

const apiStatusLabel = computed(() => {
  if (apiConfig.checking) return '检测中'
  if (apiConfig.usable) return '可用'
  if (apiConnected.value || apiConfig.hasDashscopeApiKey) return '未检测'
  return '未配置'
})

const speechLangMap = {
  ZH: 'zh-CN',
  YUE: 'zh-HK',
  EN: 'en-US',
  JA: 'ja-JP',
  KO: 'ko-KR',
  FR: 'fr-FR',
  DE: 'de-DE',
  ES: 'es-ES',
  PT: 'pt-PT',
  IT: 'it-IT',
  RU: 'ru-RU',
  AR: 'ar-SA',
  VI: 'vi-VN',
  TH: 'th-TH',
  ID: 'id-ID',
  HI: 'hi-IN',
  EL: 'el-GR',
  TR: 'tr-TR'
}

const READABLE_CORRECTION_STATUSES = new Set(['checked', 'corrected'])

const sweetVoiceKeywords = [
  'xiaoxiao',
  'xiaoyi',
  'xiaomo',
  'xiaoxuan',
  'xiaohan',
  'xiaorui',
  'jenny',
  'aria',
  'zira',
  'natasha',
  'susan',
  'samantha',
  'nanami',
  'haruka',
  'sunhi',
  'natural',
  'neural',
  'online'
]

const lessSweetVoiceKeywords = [
  'yunxi',
  'yunyang',
  'david',
  'mark',
  'guy',
  'george',
  'male'
]

const dashscopeSpeechVoices = {
  sweet: 'longfeifei_v2',
  natural: 'longxiaochun_v2'
}

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

function joinSubtitleText(items = [], field = 'translated') {
  return items
    .map(item => collapseRepeatedText(item?.[field] || ''))
    .filter(Boolean)
    .join(' ')
    .replace(/\s+([，。！？；、,.!?;:])/g, '$1')
    .trim()
}

function buildSubtitleBlock(items = []) {
  return {
    original: joinSubtitleText(items, 'original'),
    translated: joinSubtitleText(items, 'translated'),
    isPartial: items.some(item => item?.isPartial),
    isCorrected: items.some(item => item?.isCorrected)
  }
}

function correctionStatusLabel(status = '') {
  const labels = {
    checking: '检查中',
    checked: '无需修正',
    corrected: '已修正',
    failed: '纠错失败',
    skipped: '已跳过'
  }
  return labels[status] || status
}

function toggleSpeechReadout() {
  settings.enableSpeechReadout = !settings.enableSpeechReadout
  if (!settings.enableSpeechReadout) {
    cancelSpeechPlayback()
  }
}

function subtitleSpeechKey(subtitle = {}) {
  const identity = subtitle.itemId || subtitle.id || subtitle.timestamp || ''
  return `${identity}:${subtitle.translated || ''}`
}

function shouldReadSubtitle(subtitle = {}) {
  return Boolean(
    settings.enableSpeechReadout &&
    !isSubtitleWindowMode &&
    subtitle.translated &&
    !subtitle.isPartial &&
    READABLE_CORRECTION_STATUSES.has(subtitle.correctionStatus)
  )
}

function getSpeechLang() {
  return speechLangMap[settings.targetLang] || 'zh-CN'
}

function scoreSpeechVoice(voice, lang) {
  const voiceLang = (voice.lang || '').toLowerCase()
  const targetLang = lang.toLowerCase()
  const baseLang = targetLang.split('-')[0]
  const name = (voice.name || '').toLowerCase()
  let score = 0

  if (voiceLang === targetLang) score += 120
  else if (voiceLang.startsWith(baseLang)) score += 80
  else return -1

  if (voice.localService) score += 8
  if (settings.speechVoiceStyle === 'system') return score

  if (name.includes('natural') || name.includes('neural') || name.includes('online')) score += 18
  if (settings.speechVoiceStyle === 'sweet') {
    sweetVoiceKeywords.forEach(keyword => {
      if (name.includes(keyword)) score += 24
    })
    lessSweetVoiceKeywords.forEach(keyword => {
      if (name.includes(keyword)) score -= 18
    })
  }

  return score
}

function chooseSpeechVoice(lang) {
  if (settings.speechVoiceStyle === 'system' || !window.speechSynthesis?.getVoices) return null
  return window.speechSynthesis
    .getVoices()
    .map(voice => ({ voice, score: scoreSpeechVoice(voice, lang) }))
    .filter(candidate => candidate.score >= 0)
    .sort((a, b) => b.score - a.score)[0]?.voice || null
}

function getSpeechToneOptions() {
  if (settings.speechVoiceStyle === 'sweet') {
    return { rate: 0.94, pitch: 1.12, volume: 1 }
  }
  if (settings.speechVoiceStyle === 'natural') {
    return { rate: 0.98, pitch: 1.02, volume: 1 }
  }
  return { rate: 1, pitch: 1, volume: 1 }
}

function cancelSpeechPlayback() {
  activeSpeechAudio?.pause?.()
  activeSpeechAudio = null
  if (activeSpeechObjectUrl) {
    URL.revokeObjectURL(activeSpeechObjectUrl)
    activeSpeechObjectUrl = ''
  }
  window.speechSynthesis?.cancel?.()
}

function readCheckedSubtitle(subtitle = {}) {
  if (!shouldReadSubtitle(subtitle)) return

  const key = subtitleSpeechKey(subtitle)
  if (spokenSubtitleKeys.has(key)) return
  spokenSubtitleKeys.add(key)

  const text = collapseRepeatedText(subtitle.translated)
  speechPlaybackQueue = speechPlaybackQueue
    .catch(() => {})
    .then(() => playCloudSpeech(text))
}

async function playCloudSpeech(text = '') {
  if (!text || !settings.enableSpeechReadout) return
  if (settings.speechVoiceStyle === 'system') {
    playSystemSpeech(text)
    return
  }

  try {
    const response = await fetch(apiUrl('/api/tts'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        voice: dashscopeSpeechVoices[settings.speechVoiceStyle] || dashscopeSpeechVoices.sweet
      })
    })
    if (!response.ok) throw new Error(await response.text())
    const audioBlob = await response.blob()
    await playAudioBlob(audioBlob)
  } catch (error) {
    console.warn('DashScope TTS failed, falling back to system voice:', error)
    playSystemSpeech(text)
  }
}

function playAudioBlob(audioBlob) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(objectUrl)
    activeSpeechAudio = audio
    activeSpeechObjectUrl = objectUrl
    audio.onended = () => {
      URL.revokeObjectURL(objectUrl)
      if (activeSpeechAudio === audio) activeSpeechAudio = null
      if (activeSpeechObjectUrl === objectUrl) activeSpeechObjectUrl = ''
      resolve()
    }
    audio.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      if (activeSpeechAudio === audio) activeSpeechAudio = null
      if (activeSpeechObjectUrl === objectUrl) activeSpeechObjectUrl = ''
      reject(new Error('语音播放失败'))
    }
    audio.play().catch(reject)
  })
}

function playSystemSpeech(text = '') {
  if (!text || !('speechSynthesis' in window)) return
  const utterance = new SpeechSynthesisUtterance(text)
  const lang = getSpeechLang()
  const tone = getSpeechToneOptions()
  utterance.lang = lang
  utterance.voice = chooseSpeechVoice(lang)
  utterance.rate = tone.rate
  utterance.pitch = tone.pitch
  utterance.volume = tone.volume
  window.speechSynthesis.speak(utterance)
}

function serializeSubtitle(subtitle = {}) {
  return {
    id: subtitle.id,
    itemId: subtitle.itemId,
    original: subtitle.original || '',
    translated: subtitle.translated || '',
    timestamp: subtitle.timestamp || '',
    source: subtitle.source || '',
    isPartial: Boolean(subtitle.isPartial),
    isCorrected: Boolean(subtitle.isCorrected),
    correctionStatus: subtitle.correctionStatus || ''
  }
}

function serializeSubtitleBlock(block = {}) {
  return {
    original: block.original || '',
    translated: block.translated || '',
    isPartial: Boolean(block.isPartial),
    isCorrected: Boolean(block.isCorrected)
  }
}

function applySubtitleWindowPayload(payload) {
  const block = payload?.block || buildSubtitleBlock(Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [])
  externalSubtitleBlock.value = block
}

function mirrorSubtitlePayload(payload) {
  try {
    localStorage.setItem('ai-interpreter-subtitle-payload', JSON.stringify(payload))
  } catch {}

  try {
    subtitleBroadcastChannel?.postMessage(payload)
  } catch {}
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

function startFloatingSubtitleDrag(event) {
  if (event.target?.closest?.('.floating-subtitle-close')) return
  event.preventDefault()

  const startX = event.clientX
  const startY = event.clientY
  const originX = floatingSubtitlePosition.x
  const originBottom = floatingSubtitlePosition.bottom

  const move = (moveEvent) => {
    floatingSubtitlePosition.x = Math.min(
      window.innerWidth - 24,
      Math.max(24, originX + moveEvent.clientX - startX)
    )
    floatingSubtitlePosition.bottom = Math.min(
      window.innerHeight - 80,
      Math.max(24, originBottom - (moveEvent.clientY - startY))
    )
  }
  const stop = () => {
    window.removeEventListener('pointermove', move)
    window.removeEventListener('pointerup', stop)
  }

  window.addEventListener('pointermove', move)
  window.addEventListener('pointerup', stop, { once: true })
}

function getElectronSubtitles() {
  if (window.electronSubtitles) return window.electronSubtitles

  try {
    const ipcRenderer = window.require?.('electron')?.ipcRenderer
    if (!ipcRenderer) return null

    return {
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
      }
    }
  } catch {
    return null
  }
}

function getElectronAppConfig() {
  if (window.electronAppConfig) return window.electronAppConfig

  try {
    const ipcRenderer = window.require?.('electron')?.ipcRenderer
    if (!ipcRenderer) return null

    return {
      get: () => ipcRenderer.invoke('app-config:get'),
      save: (config) => ipcRenderer.invoke('app-config:save', config),
      clear: () => ipcRenderer.invoke('app-config:clear'),
      check: (config) => ipcRenderer.invoke('app-config:check', config),
      restartBackend: () => ipcRenderer.invoke('app-config:restart-backend')
    }
  } catch {
    return null
  }
}

function apiUrl(path) {
  return `${API_ORIGIN}${path}`
}

async function refreshApiStatus() {
  try {
    const response = await fetch(apiUrl('/api/status'))
    const data = await response.json()
    apiConnected.value = Boolean(data.api_configured)
    if (data.api_configured) {
      apiConfig.hasDashscopeApiKey = true
    } else {
      apiConfig.usable = false
    }
    const liveModel = data.models?.livetranslate
    if (liveModel && !apiConfig.dashscopeLiveTranslateModel) {
      apiConfig.dashscopeLiveTranslateModel = liveModel
    }
    return data
  } catch {
    apiConnected.value = false
    return null
  }
}

async function loadApiConfig() {
  const electronAppConfig = getElectronAppConfig()
  let hasSavedKey = false
  try {
    const saved = await electronAppConfig?.get?.()
    if (saved) {
      hasSavedKey = Boolean(saved.hasDashscopeApiKey)
      apiConfig.hasDashscopeApiKey = hasSavedKey
      apiConfig.usable = false
      apiConfig.message = hasSavedKey
        ? '已发现本机保存的 API Key，正在检测可用性。'
        : '未配置 API Key。'
      if (saved.dashscopeLiveTranslateModel) {
        apiConfig.dashscopeLiveTranslateModel = saved.dashscopeLiveTranslateModel
      }
    }
  } catch {
    ElMessage.warning('读取应用配置失败')
  }

  const status = await refreshApiStatus()
  if (status?.models?.livetranslate && !apiConfig.dashscopeLiveTranslateModel) {
    apiConfig.dashscopeLiveTranslateModel = status.models.livetranslate
  }

  if (hasSavedKey || apiConnected.value) {
    await checkApiConfig({ silent: true, apiKey: '', model: apiConfig.dashscopeLiveTranslateModel.trim() })
  }
}

async function saveApiConfig() {
  const apiKey = apiConfig.dashscopeApiKey.trim()
  const model = apiConfig.dashscopeLiveTranslateModel.trim()

  if (!apiKey && !apiConfig.hasDashscopeApiKey && !apiConnected.value) {
    ElMessage.warning('请填写 DashScope API Key')
    return
  }

  if (!model) {
    ElMessage.warning('请填写实时模型名称')
    return
  }

  apiConfig.saving = true
  try {
    const electronAppConfig = getElectronAppConfig()
    const checkResult = await checkApiConfig({ silent: true, apiKey, model })
    if (!checkResult.usable) throw new Error(checkResult.message || 'API Key 检测未通过')

    const saved = await electronAppConfig?.save?.({
      dashscopeApiKey: apiKey,
      dashscopeLiveTranslateModel: model
    })

    const data = await applyRuntimeApiConfig({ apiKey, model, electronAppConfig })
    apiConnected.value = Boolean(data.api_configured)
    apiConfig.hasDashscopeApiKey = Boolean(saved?.hasDashscopeApiKey || data.api_configured || apiKey)
    apiConfig.usable = true
    apiConfig.message = 'DashScope API Key 已保存并检测可用。'
    apiConfig.dashscopeApiKey = ''
    ElMessage.success(electronAppConfig ? '配置已保存' : '配置已应用到当前后端')
  } catch (error) {
    if (electronAppConfig) {
      ElMessage.error(`配置未保存: ${error.message || error}`)
    } else {
      ElMessage.error(`保存配置失败: ${error.message || error}`)
    }
  } finally {
    apiConfig.saving = false
  }
}

async function checkApiConfig({ silent = false, apiKey = apiConfig.dashscopeApiKey.trim(), model = apiConfig.dashscopeLiveTranslateModel.trim() } = {}) {
  if (!apiKey && !apiConfig.hasDashscopeApiKey && !apiConnected.value) {
    const result = { usable: false, message: '请先输入 DashScope API Key' }
    apiConfig.usable = false
    apiConfig.message = result.message
    if (!silent) ElMessage.warning(result.message)
    return result
  }

  if (!model) {
    const result = { usable: false, message: '请填写实时模型名称' }
    apiConfig.usable = false
    apiConfig.message = result.message
    if (!silent) ElMessage.warning(result.message)
    return result
  }

  apiConfig.checking = true
  try {
    const electronAppConfig = getElectronAppConfig()
    let result = null

    if (electronAppConfig?.check) {
      result = await electronAppConfig.check({
        dashscopeApiKey: apiKey,
        dashscopeLiveTranslateModel: model
      })
    } else {
      const response = await fetch(apiUrl('/api/runtime-config/check'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dashscope_api_key: apiKey || undefined,
          dashscope_livetranslate_model: model
        })
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      result = await response.json()
    }

    apiConfig.usable = Boolean(result.usable)
    apiConfig.message = result.message || (result.usable ? 'API Key 可用' : 'API Key 不可用')
    if (!silent) {
      if (result.usable) ElMessage.success(apiConfig.message)
      else ElMessage.error(apiConfig.message)
    }
    return result
  } catch (error) {
    const result = { usable: false, message: `API 检测失败: ${error.message || error}` }
    apiConfig.usable = false
    apiConfig.message = result.message
    if (!silent) ElMessage.error(result.message)
    return result
  } finally {
    apiConfig.checking = false
  }
}

async function clearApiConfig() {
  const electronAppConfig = getElectronAppConfig()
  try {
    await electronAppConfig?.clear?.()
    await electronAppConfig?.restartBackend?.()
  } catch {}

  apiConfig.dashscopeApiKey = ''
  apiConfig.hasDashscopeApiKey = false
  apiConfig.usable = false
  apiConfig.message = '配置已清除，请重新输入 API Key。'
  apiConnected.value = false
  ElMessage.success('本机 API 配置已清除')
}

async function ensureApiReady() {
  if (!apiConnected.value && !apiConfig.hasDashscopeApiKey && !apiConfig.dashscopeApiKey.trim()) {
    showSettings.value = true
    ElMessage.warning('请先在设置里填写 DashScope API Key')
    return false
  }

  if (apiConfig.usable) return true

  const result = await checkApiConfig({ silent: true })
  if (result.usable) return true

  showSettings.value = true
  ElMessage.error(result.message || 'API Key 不可用，请先检测配置')
  return false
}

async function applyRuntimeApiConfig({ apiKey, model, electronAppConfig }) {
  try {
    const response = await fetch(apiUrl('/api/runtime-config'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dashscope_api_key: apiKey || undefined,
        dashscope_livetranslate_model: model
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    return await response.json()
  } catch (error) {
    if (!electronAppConfig?.restartBackend) throw error

    ElMessage.warning('正在重启后端以应用配置...')
    await electronAppConfig.restartBackend()
    const status = await waitForBackendStatus()
    if (!status?.api_configured) throw new Error('后端已重启，但 API Key 未生效')
    return status
  }
}

async function waitForBackendStatus(timeoutMs = 12000) {
  const startedAt = Date.now()
  while (Date.now() - startedAt < timeoutMs) {
    const status = await refreshApiStatus()
    if (status?.status === 'running') return status
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  throw new Error('等待后端重启超时')
}

async function toggleIndependentSubtitleWindow() {
  if (electronSubtitleWindowOpen.value || (independentSubtitleWindow && !independentSubtitleWindow.closed)) {
    closeSubtitleWindow()
    return
  }

  const electronSubtitles = getElectronSubtitles()
  if (electronSubtitles) {
    try {
      const result = await electronSubtitles.toggle()
      electronSubtitleWindowOpen.value = Boolean(result?.opened)
      independentSubtitleWindowOpen.value = false
      floatingSubtitleOverlayOpen.value = false
      renderIndependentSubtitleWindow()
      return
    } catch (err) {
      console.warn('Electron subtitle window unavailable:', err)
    }
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
      floatingSubtitleOverlayOpen.value = true
      ElMessage.warning('独立字幕窗口被拦截，已打开应用内透明字幕')
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
          background: transparent;
          color: rgba(248, 250, 252, 0.88);
          font-size: 18px;
          line-height: 24px;
          cursor: pointer;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
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
          background: transparent !important;
          background-color: transparent !important;
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
    floatingSubtitleOverlayOpen.value = true
    renderIndependentSubtitleWindow()
  } catch (err) {
    independentSubtitleWindow = null
    independentSubtitleWindowOpen.value = false
    floatingSubtitleOverlayOpen.value = true
    ElMessage.warning('独立字幕窗口不可用，已打开应用内透明字幕')
  }
}

async function ensureIndependentSubtitleWindow() {
  if (!settings.autoOpenSubtitleWindow) return
  if (electronSubtitleWindowOpen.value || (independentSubtitleWindow && !independentSubtitleWindow.closed)) return
  await toggleIndependentSubtitleWindow()
}

function closeSubtitleWindow() {
  const electronSubtitles = getElectronSubtitles()
  if (isSubtitleWindowMode) {
    electronSubtitles?.close?.().catch(() => {})
    return
  }
  if (electronSubtitles && electronSubtitleWindowOpen.value) {
    electronSubtitles.close().catch(() => {})
  }
  electronSubtitleWindowOpen.value = false

  if (independentSubtitleWindow && !independentSubtitleWindow.closed) {
    independentSubtitleWindow.close()
  }
  independentSubtitleWindow = null
  independentSubtitleWindowOpen.value = false
  floatingSubtitleOverlayOpen.value = false
}

function renderIndependentSubtitleWindow() {
  const visibleSubtitles = visibleSubtitleHistory.value
  const items = visibleSubtitles
    .slice(-EXTERNAL_SUBTITLE_ROWS)
    .map(serializeSubtitle)
  const subtitlePayload = {
    block: serializeSubtitleBlock(floatingSubtitleBlock.value),
    items
  }
  mirrorSubtitlePayload(subtitlePayload)
  const electronSubtitles = getElectronSubtitles()

  if (electronSubtitles) {
    electronSubtitles.update(subtitlePayload)
      .then((result) => {
        if (result && result.opened === false) {
          electronSubtitleWindowOpen.value = false
        } else if (result?.opened) {
          electronSubtitleWindowOpen.value = true
          floatingSubtitleOverlayOpen.value = false
        }
      })
      .catch(() => {
        electronSubtitleWindowOpen.value = false
        console.warn('Electron subtitle update failed')
      })
  }

  if (!independentSubtitleWindow || independentSubtitleWindow.closed) {
    independentSubtitleWindow = null
    independentSubtitleWindowOpen.value = false
    return
  }

  const root = independentSubtitleWindow.document.getElementById('subtitle-root')
  if (!root) return

  if (!visibleSubtitles.length) {
    root.innerHTML = '<div class="empty">等待字幕...</div>'
    return
  }

  root.innerHTML = ''
  const block = buildSubtitleBlock(visibleSubtitles.slice(-EXTERNAL_SUBTITLE_ROWS))
  const list = independentSubtitleWindow.document.createElement('div')
  list.className = 'subtitle-list'
  const row = independentSubtitleWindow.document.createElement('div')
  row.className = `subtitle-row${block.isPartial ? ' partial' : ''}`

  if (block.original) {
    const original = independentSubtitleWindow.document.createElement('div')
    original.className = 'original'
    original.textContent = block.original
    row.appendChild(original)
  }

  if (block.translated) {
    const translated = independentSubtitleWindow.document.createElement('div')
    translated.className = 'translated'
    translated.textContent = block.translated
    row.appendChild(translated)
  }
  list.appendChild(row)

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
    type: 'start',
    source_lang: settings.sourceLang.toLowerCase(),
    target_lang: settings.targetLang.toLowerCase(),
    sample_rate: 16000,
    format: 'pcm_s16le',
    data: {
      source_lang: settings.sourceLang.toLowerCase(),
      target_lang: settings.targetLang.toLowerCase(),
      enable_correction: settings.enableCorrection
    }
  }))
  return ackPromise || true
}

function sendAudioBuffer(audioBuffer) {
  if (ws?.readyState !== WebSocket.OPEN || !audioBuffer?.byteLength) return
  if (ws.bufferedAmount > 2 * 1024 * 1024) return
  ws.send(audioBuffer)
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
}

function clearAudioQueue() {
  clearAllPendingPartialSubtitles()
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
    if (!(await ensureApiReady())) return
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

    wavRecorder = new WavRecorder(16000, {
      bufferDuration: 0.04,
      continuous: true
    })
    await wavRecorder.start((pcmBuffer) => {
      sendAudioBuffer(pcmBuffer)
    }, captureStream)

    audioContext = wavRecorder.audioContext
    if (audioContext) {
      const source = audioContext.createMediaStreamSource(captureStream)
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      source.connect(analyser)
    }

    mediaRecorder = { stop: () => wavRecorder?.stop() }

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

  if (wavRecorder) {
    wavRecorder.stop()
    wavRecorder = null
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
    return Promise.resolve(sendSettings({ waitForAck: true })).then(() => true)
  }
  if (ws?.readyState === WebSocket.CONNECTING) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('WebSocket连接超时')), 5000)
      ws.addEventListener('open', () => { clearTimeout(timer); resolve() }, { once: true })
      ws.addEventListener('error', () => { clearTimeout(timer); reject(new Error('WebSocket连接失败')) }, { once: true })
    })
  }

  const wsHost = window.location.hostname || '127.0.0.1'
  const wsUrl = `ws://${wsHost}:9000/ws/translate`
  ws = new WebSocket(wsUrl)

  const openPromise = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('WebSocket连接超时')), 5000)

    ws.onopen = async () => {
      clearTimeout(timer)
      wsStatus.value = 'connected'
      await sendSettings({ waitForAck: true })
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
    if (data.type === 'subtitle_delta') {
      addSubtitle('partial', {
        ...data.content,
        item_id: data.content?.segment_id,
        source: 'livetranslate'
      })
    } else if (data.type === 'subtitle') {
      addSubtitle('final', {
        ...data.content,
        item_id: data.content?.segment_id,
        source: 'livetranslate'
      })
    } else if (data.type === 'partial' || data.type === 'final') {
      addSubtitle(data.type, data.content)
    } else if (data.type === 'asr_partial') {
      return
    } else if (data.type === 'asr_final') {
      addAsrFallback(data.content)
    } else if (data.type === 'asr_translation') {
      addAsrFallback(data.content, { updateTranslation: true })
    } else if (data.type === 'settings_updated') {
      resolveSettingsAck()
    } else if (data.type === 'correction') {
      applyCorrection(data.content)
    } else if (data.type === 'correction_status') {
      applyCorrectionStatus(data.content)
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
  let { original, translated, timestamp, item_id: itemId, source } = content
  source = source || 'livetranslate'
  if (type === 'partial') {
    original = collapseRepeatedText(original)
    translated = collapseRepeatedText(translated)
    queuePartialSubtitle({
      ...content,
      original,
      translated,
      timestamp,
      item_id: itemId,
      source
    })
    return
  }

  clearPendingPartialSubtitle(itemId, source)

  const partial = itemId
    ? subtitles.value.find(s => s.itemId === itemId) ||
      (String(itemId).startsWith('synthetic_') ? subtitles.value.find(s => s.isPartial && s.source === source) : null)
    : subtitles.value.find(s => s.isPartial && s.source === source)
  if (partial) {
    partial.isPartial = false
    partial.original = original || partial.original
    partial.translated = translated
    partial.timestamp = timestamp || partial.timestamp
    partial.source = pickSubtitleSource(partial.source, source)
    partial.correctionStatus = settings.enableCorrection && source === 'livetranslate' ? 'checking' : ''
  } else {
    subtitles.value.push({
      id: ++subtitleIdCounter,
      itemId,
      original, translated, timestamp,
      source,
      isPartial: false,
      isCorrected: false,
      correctionStatus: settings.enableCorrection && source === 'livetranslate' ? 'checking' : ''
    })
  }

  pruneSubtitles()
}

function partialSubtitleKey(itemId = '', source = 'livetranslate') {
  return itemId || `active:${source || 'livetranslate'}`
}

function queuePartialSubtitle(content) {
  const source = content.source || 'livetranslate'
  const itemId = content.item_id || content.itemId || ''
  const key = partialSubtitleKey(itemId, source)
  const existing = pendingPartialSubtitles.get(key)
  const next = {
    ...existing?.content,
    ...content,
    item_id: itemId,
    source
  }

  if (existing) {
    existing.content = next
    return
  }

  const pending = {
    content: next,
    timer: setTimeout(() => {
      pendingPartialSubtitles.delete(key)
      applyPartialSubtitle(pending.content)
    }, PARTIAL_RENDER_INTERVAL_MS)
  }
  pendingPartialSubtitles.set(key, pending)
}

function clearPendingPartialSubtitle(itemId = '', source = 'livetranslate') {
  const key = partialSubtitleKey(itemId, source)
  const pending = pendingPartialSubtitles.get(key)
  if (!pending) return
  clearTimeout(pending.timer)
  pendingPartialSubtitles.delete(key)
}

function clearAllPendingPartialSubtitles() {
  for (const pending of pendingPartialSubtitles.values()) {
    clearTimeout(pending.timer)
  }
  pendingPartialSubtitles.clear()
}

function applyPartialSubtitle(content) {
  const itemId = content.item_id || content.itemId || ''
  const source = content.source || 'livetranslate'
  const original = content.original || ''
  const translated = content.translated || ''
  const timestamp = content.timestamp
  const existing = itemId
    ? subtitles.value.find(s => s.itemId === itemId)
    : subtitles.value.find(s => s.isPartial && s.source === source)

  if (existing) {
    if (!shouldUpdatePartialText(existing.original, original) && !shouldUpdatePartialText(existing.translated, translated)) {
      return
    }
    existing.original = original || existing.original
    existing.translated = translated || existing.translated
    existing.timestamp = timestamp || existing.timestamp
    existing.source = source || existing.source
  } else {
    subtitles.value.push({
      id: ++subtitleIdCounter,
      itemId,
      original,
      translated,
      timestamp,
      source,
      isPartial: true,
      isCorrected: false,
      correctionStatus: ''
    })
  }

  pruneSubtitles()
}

function shouldUpdatePartialText(previous = '', next = '') {
  if (!next || previous === next) return false
  if (!previous) return true
  if (next.length - previous.length >= 4) return true
  return /[。！？；，,.!?;]$/.test(next)
}

function sourceRank(source = '') {
  if (source === 'livetranslate') return 3
  if (source === 'livetranslate_secondary') return 2
  if (source === 'asr_fallback') return 1
  return 0
}

function pickSubtitleSource(current = '', incoming = '') {
  return sourceRank(incoming) >= sourceRank(current) ? incoming : current
}

function shouldMergeSubtitle(existing, incomingSource, incomingType) {
  if (!existing) return false
  if (existing.source === incomingSource) return true
  if (incomingSource === 'livetranslate') return true
  if (!existing.isPartial && incomingSource === 'livetranslate_secondary') return false
  if (existing.source === 'livetranslate' && incomingType === 'partial') {
    return existing.isPartial
  }
  return sourceRank(incomingSource) >= sourceRank(existing.source) || existing.isPartial
}

function findMergeCandidate(original = '', translated = '', source = '') {
  const recent = subtitles.value.slice(-16).reverse()
  return recent.find(subtitle => {
    if (!subtitle.isPartial) return false
    if (subtitle.source === 'asr_fallback' && source !== 'livetranslate') return false
    return (
      isSimilarSubtitleText(subtitle.original, original) ||
      isSimilarSubtitleText(subtitle.translated, translated) ||
      isSimilarSubtitleText(subtitle.original, translated) ||
      isSimilarSubtitleText(subtitle.translated, original)
    )
  })
}

function normalizeSubtitleText(text = '') {
  return collapseRepeatedText(text)
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\u4e00-\u9fff]+/gu, '')
}

function isSimilarSubtitleText(a = '', b = '') {
  const left = normalizeSubtitleText(a)
  const right = normalizeSubtitleText(b)
  if (!left || !right) return false
  if (left === right || left.includes(right) || right.includes(left)) return true
  const shorter = Math.min(left.length, right.length)
  const longer = Math.max(left.length, right.length)
  return shorter >= 8 && shorter / longer > 0.82
}

function findSimilarRecentSubtitle(original = '') {
  const recent = subtitles.value.slice(-12)
  return recent.find(subtitle =>
    isSimilarSubtitleText(subtitle.original, original) ||
    isSimilarSubtitleText(subtitle.translated, original)
  )
}

function addAsrFallback(content, options = {}) {
  const original = collapseRepeatedText(content.original || '')
  if (!original) return

  const timestamp = content.timestamp || new Date().toISOString()
  const translated = collapseRepeatedText(content.translated || '')
  const existingFallback = subtitles.value
    .slice()
    .reverse()
    .find(subtitle =>
      subtitle.source === 'asr_fallback' &&
      isSimilarSubtitleText(subtitle.original, original)
    )

  if (existingFallback) {
    if (translated) {
      existingFallback.translated = translated
      existingFallback.timestamp = timestamp
      existingFallback.isPartial = false
    }
    pruneSubtitles()
    return
  }

  const similarLiveSubtitle = findSimilarRecentSubtitle(original)
  if (similarLiveSubtitle && similarLiveSubtitle.source !== 'asr_fallback') {
    return
  }

  subtitles.value.push({
    id: ++subtitleIdCounter,
    itemId: content.item_id,
    original,
    translated: translated || '等待兜底翻译...',
    timestamp,
    source: 'asr_fallback',
    isPartial: !translated,
    isCorrected: false,
    correctionStatus: ''
  })

  pruneSubtitles()
}

function pruneSubtitles() {
  subtitleCount.value = subtitles.value.length

  if (subtitles.value.length > MAX_STORED_SUBTITLES) {
    subtitles.value = subtitles.value.slice(-MAX_STORED_SUBTITLES)
  }

  nextTick(() => {
    if (subtitleContainer.value) {
      subtitleContainer.value.scrollTop = subtitleContainer.value.scrollHeight
    }
    renderIndependentSubtitleWindow()
  })
}

function applyCorrection(content) {
  if (Array.isArray(content?.replacements)) {
    for (const replacement of content.replacements) {
      const segmentId = replacement.segment_id || replacement.item_id
      const subtitle = findCorrectionTarget(segmentId, replacement)
      if (!subtitle) continue
      subtitle.original = replacement.original || subtitle.original
      subtitle.translated = replacement.translated || subtitle.translated
      subtitle.isCorrected = true
      subtitle.isPartial = false
      subtitle.correctionStatus = content.status || replacement.status || 'corrected'
      readCheckedSubtitle(subtitle)
    }
    renderIndependentSubtitleWindow()
    return
  }

  if (content?.segment_id || content?.item_id) {
    const segmentId = content.segment_id || content.item_id
    const subtitle = findCorrectionTarget(segmentId, content)
    if (subtitle) {
      subtitle.original = content.original || subtitle.original
      subtitle.translated = content.translated || subtitle.translated
      subtitle.isCorrected = true
      subtitle.isPartial = false
      subtitle.correctionStatus = content.status || 'corrected'
      readCheckedSubtitle(subtitle)
      renderIndependentSubtitleWindow()
    }
    return
  }

  const { index, original, translated } = content
  if (subtitles.value[index]) {
    subtitles.value[index].original = original
    subtitles.value[index].translated = translated
    subtitles.value[index].isCorrected = true
    subtitles.value[index].correctionStatus = 'corrected'
    subtitles.value[index].isPartial = false
    readCheckedSubtitle(subtitles.value[index])
  }
}

function applyCorrectionStatus(content = {}) {
  const segmentId = content.segment_id || content.item_id
  const subtitle = findCorrectionTarget(segmentId, content)
  if (!subtitle) return
  subtitle.correctionStatus = content.status || ''
  subtitle.correctionReason = content.reason || ''
  if (content.status === 'corrected') subtitle.isCorrected = true
  if (READABLE_CORRECTION_STATUSES.has(subtitle.correctionStatus)) {
    subtitle.isPartial = false
    readCheckedSubtitle(subtitle)
  }
  renderIndependentSubtitleWindow()
}

function findCorrectionTarget(segmentId, replacement = {}) {
  if (segmentId) {
    const byId = subtitles.value.find(s => s.itemId === segmentId)
    if (byId) return byId
  }

  const original = replacement.original || ''
  const translated = replacement.previous_translated || replacement.translated || ''
  if (!original && !translated) return null

  return subtitles.value
    .slice(-12)
    .reverse()
    .find(subtitle =>
      isSimilarSubtitleText(subtitle.original, original) ||
      isSimilarSubtitleText(subtitle.translated, translated)
    ) || null
}

async function startRecording() {
  try {
    if (!(await ensureApiReady())) return
    await connectWS()
    wavRecorder = new WavRecorder(16000, {
      bufferDuration: 0.04,
      continuous: true,
      energyThreshold: 0.065,
      maxSilenceMs: 450,
      minVoiceFrames: 5
    })
    await wavRecorder.start((pcmBuffer) => {
      sendAudioBuffer(pcmBuffer)
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
  clearAllPendingPartialSubtitles()
  spokenSubtitleKeys.clear()
  cancelSpeechPlayback()
  subtitles.value = []
  subtitleCount.value = 0
  renderIndependentSubtitleWindow()
}

watch(
  () => ({
    sourceLang: settings.sourceLang,
    targetLang: settings.targetLang,
    enableCorrection: settings.enableCorrection
  }),
  sendSettings,
  { deep: true }
)

onMounted(async () => {
  if (isSubtitleWindowMode) {
    document.body.classList.add('subtitle-window-body')
    const electronSubtitles = getElectronSubtitles()
    try {
      const cached = JSON.parse(localStorage.getItem('ai-interpreter-subtitle-payload') || 'null')
      if (cached) applySubtitleWindowPayload(cached)
    } catch {}

    try {
      const latest = await electronSubtitles?.getLatest?.()
      if (latest?.payload) applySubtitleWindowPayload(latest.payload)
    } catch {}

    removeElectronSubtitleUpdateListener = electronSubtitles?.onUpdate?.((payload) => {
      applySubtitleWindowPayload(payload)
    }) || null

    try {
      subtitleBroadcastChannel = new BroadcastChannel('ai-interpreter-subtitles')
      subtitleBroadcastChannel.onmessage = (event) => {
        applySubtitleWindowPayload(event.data)
      }
    } catch {}

    floatingSubtitleOverlayOpen.value = true
    return
  }

  drawWaveform()
  const electronSubtitles = getElectronSubtitles()
  if (electronSubtitles) {
    try {
      const result = await electronSubtitles.isOpen()
      electronSubtitleWindowOpen.value = Boolean(result?.opened)
      removeElectronSubtitleClosedListener = electronSubtitles.onClosed(() => {
        electronSubtitleWindowOpen.value = false
      })
    } catch {
      electronSubtitleWindowOpen.value = false
    }
  }

  await loadApiConfig()
})

onUnmounted(() => {
  removeElectronSubtitleUpdateListener?.()
  subtitleBroadcastChannel?.close?.()
  stopRecording()
  stopCapture()
  closeSubtitleWindow()
  clearAllPendingPartialSubtitles()
  cancelSpeechPlayback()
  removeElectronSubtitleClosedListener?.()
  if (animationId) cancelAnimationFrame(animationId)
})
</script>

<style>
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
  background: rgba(148, 163, 184, 0.12);
  color: var(--text-secondary);
  border-radius: 100px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  white-space: nowrap;
}

.correction-badge.status-checking {
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.24);
}

.correction-badge.status-checked {
  background: rgba(148, 163, 184, 0.1);
  color: var(--text-muted);
}

.correction-badge.status-corrected {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success);
  border-color: rgba(34, 197, 94, 0.2);
}

.correction-badge.status-failed,
.correction-badge.status-skipped {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.24);
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
.speech-toggle-btn.active {
  border-color: rgba(99, 102, 241, 0.48);
  background: rgba(99, 102, 241, 0.14);
  color: var(--primary-light);
}
.subtitle-toggle-btn.active {
  border-color: rgba(34, 197, 94, 0.45);
  background: rgba(34, 197, 94, 0.12);
  color: var(--success);
}

.floating-subtitle-overlay {
  position: fixed;
  left: 50%;
  bottom: 92px;
  z-index: 80;
  width: min(920px, calc(100vw - 48px));
  max-height: 48vh;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  cursor: move;
  pointer-events: auto;
  user-select: none;
  background: transparent !important;
  border: 0;
}

.floating-subtitle-content,
.floating-subtitle-empty {
  width: 100%;
  padding: 0 42px 2px;
  overflow-y: auto;
  text-align: center;
  background: transparent !important;
  color: var(--text-primary);
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.92), 0 0 2px rgba(0, 0, 0, 0.95);
}

.floating-subtitle-content {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 10px;
  max-height: 48vh;
}

.floating-subtitle-content::-webkit-scrollbar { width: 6px; }
.floating-subtitle-content::-webkit-scrollbar-track { background: transparent; }
.floating-subtitle-content::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.45);
}

.floating-subtitle-row {
  opacity: 0.94;
  transition: opacity 0.18s ease;
}

.floating-subtitle-row.partial {
  opacity: 0.72;
}

.floating-subtitle-row.corrected .floating-subtitle-translated {
  color: #4ade80;
}

.floating-subtitle-row:not(:last-child) .floating-subtitle-original {
  font-size: 14px;
  opacity: 0.72;
}

.floating-subtitle-row:not(:last-child) .floating-subtitle-translated {
  font-size: 21px;
  opacity: 0.82;
}

.floating-subtitle-original {
  margin-bottom: 8px;
  color: rgba(248, 250, 252, 0.92);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.35;
}

.floating-subtitle-translated {
  color: var(--success);
  font-size: 28px;
  font-weight: 900;
  line-height: 1.28;
}

.floating-subtitle-empty {
  color: rgba(148, 163, 184, 0.82);
  font-size: 18px;
  font-weight: 700;
}

.floating-subtitle-close {
  position: absolute;
  top: -28px;
  right: 0;
  width: 28px;
  height: 28px;
  border: 0;
  background: transparent;
  color: rgba(248, 250, 252, 0.82);
  font-size: 24px;
  line-height: 28px;
  cursor: pointer;
  pointer-events: auto;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
}

.floating-subtitle-close:hover {
  color: #fff;
}

.subtitle-window-body {
  background: transparent !important;
}

.subtitle-window-mode {
  min-height: 100vh;
  overflow: hidden;
  background: transparent !important;
}

.subtitle-window-mode .floating-subtitle-overlay {
  left: 0 !important;
  bottom: 0 !important;
  width: 100vw;
  height: 100vh;
  max-height: 100vh;
  transform: none;
  align-items: center;
  cursor: move;
  -webkit-app-region: drag;
}

.subtitle-window-mode .floating-subtitle-content,
.subtitle-window-mode .floating-subtitle-empty {
  max-height: 100vh;
  padding: 10px 42px 12px;
}

.subtitle-window-mode .floating-subtitle-close {
  top: 6px;
  right: 8px;
  -webkit-app-region: no-drag;
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

.api-config-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 0 18px;
  border-bottom: 1px solid var(--border);
}

.api-config-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.api-config-heading h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-field span {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.config-input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 13px;
  transition: border-color 0.2s, background 0.2s;
}

.config-input::placeholder {
  color: var(--text-muted);
}

.config-input:hover,
.config-input:focus {
  border-color: rgba(99, 102, 241, 0.72);
  background: rgba(255, 255, 255, 0.06);
}

.save-config-btn {
  width: 100%;
  height: 42px;
  border: 0;
  border-radius: 8px;
  background: #1f2937;
  color: #ffffff;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.save-config-btn:hover:not(:disabled) {
  background: #111827;
}

.save-config-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.api-config-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.secondary-config-btn {
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, opacity 0.2s;
}

.secondary-config-btn:hover:not(:disabled) {
  border-color: rgba(99, 102, 241, 0.7);
  background: rgba(255, 255, 255, 0.07);
}

.secondary-config-btn.danger {
  color: #fca5a5;
}

.secondary-config-btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.api-config-note {
  min-height: 18px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.5;
}

.setting-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.setting-group label { font-size: 13px; color: var(--text-primary); }

.compact-setting-select {
  width: 142px;
  height: 34px;
  padding: 0 30px 0 10px;
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  background:
    linear-gradient(45deg, transparent 50%, var(--text-secondary) 50%) calc(100% - 15px) 14px / 6px 6px no-repeat,
    linear-gradient(135deg, var(--text-secondary) 50%, transparent 50%) calc(100% - 10px) 14px / 6px 6px no-repeat,
    rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.compact-setting-select:hover,
.compact-setting-select:focus {
  border-color: rgba(99, 102, 241, 0.72);
  background-color: rgba(255, 255, 255, 0.07);
}

.compact-setting-select option {
  color: #111827;
  background: #ffffff;
}

.api-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 100px;
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.api-status.connected { background: rgba(34, 197, 94, 0.1); color: var(--success); }
.api-status.checking { background: rgba(245, 158, 11, 0.12); color: var(--warning); }

.subtitle-enter-active, .subtitle-leave-active { transition: all 0.3s; }
.subtitle-enter-from { opacity: 0; transform: translateY(16px); }
.subtitle-leave-to { opacity: 0; transform: translateX(-16px); }

.is-recording .waveform-area { height: 80px; }
</style>
