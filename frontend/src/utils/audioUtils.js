export function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)

  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(view, 36, 'data')
  view.setUint32(40, samples.length * 2, true)

  for (let i = 0, offset = 44; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i))
  }
}

function calculateRMS(samples) {
  let sum = 0
  for (let i = 0; i < samples.length; i++) {
    sum += samples[i] * samples[i]
  }
  return Math.sqrt(sum / samples.length)
}

export class WavRecorder {
  constructor(sampleRate = 16000, options = {}) {
    this.sampleRate = sampleRate
    this.audioContext = null
    this.stream = null
    this.source = null
    this.processor = null
    this.onAudioData = null
    this.buffer = []
    this.silenceBuffer = []
    this.bufferDuration = options.bufferDuration || 1.0
    this.bufferSize = Math.floor(sampleRate * this.bufferDuration)
    this.continuous = options.continuous || false
    this.energyThreshold = options.energyThreshold || 0.05
    this.silenceTimeout = null
    this.maxSilenceMs = options.maxSilenceMs || 1000
    this.isSpeaking = false
    this.voiceFrameCount = 0
    this.minVoiceFrames = options.minVoiceFrames || 6
  }

  async start(onAudioData, inputStream = null) {
    this.onAudioData = onAudioData
    this.buffer = []

    this.stream = inputStream || await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, sampleRate: this.sampleRate }
    })

    if (this.stream.getAudioTracks().length === 0) {
      this.stream.getTracks().forEach(t => t.stop())
      throw new Error('没有捕获到音频轨道')
    }

    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: this.sampleRate })
    this.source = this.audioContext.createMediaStreamSource(this.stream)

    if (this.audioContext.audioWorklet) {
      await this._startWithWorklet()
    } else {
      this._startWithScriptProcessor()
    }
  }

  async _startWithWorklet() {
    const workletCode = `
      class RecorderProcessor extends AudioWorkletProcessor {
        constructor() {
          super()
        }
        process(inputs) {
          const input = inputs[0]
          if (input && input[0]) {
            this.port.postMessage(input[0])
          }
          return true
        }
      }
      registerProcessor('recorder-processor', RecorderProcessor)
    `
    const blob = new Blob([workletCode], { type: 'application/javascript' })
    const url = URL.createObjectURL(blob)
    await this.audioContext.audioWorklet.addModule(url)
    URL.revokeObjectURL(url)

    this.processor = new AudioWorkletNode(this.audioContext, 'recorder-processor')
    this.source.connect(this.processor)
    this.processor.connect(this.audioContext.destination)

    this.processor.port.onmessage = (e) => {
      this._processAudioData(e.data)
    }
  }

  _startWithScriptProcessor() {
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1)
    this.source.connect(this.processor)
    this.processor.connect(this.audioContext.destination)

    this.processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0)
      this._processAudioData(new Float32Array(inputData))
    }
  }

  _processAudioData(data) {
    if (this.continuous) {
      this.buffer.push(...data)
      while (this.buffer.length >= this.bufferSize) {
        const chunk = this.buffer.splice(0, this.bufferSize)
        const wavBlob = encodeWAV(new Float32Array(chunk), this.sampleRate)
        if (this.onAudioData) {
          this.onAudioData(wavBlob)
        }
      }
      return
    }

    const rms = calculateRMS(data)
    const hasVoice = rms > this.energyThreshold

    if (hasVoice) {
      this.voiceFrameCount++
      if (this.voiceFrameCount >= this.minVoiceFrames) {
        this.isSpeaking = true
        if (this.silenceTimeout) {
          clearTimeout(this.silenceTimeout)
          this.silenceTimeout = null
        }
      }
      if (this.isSpeaking) {
        this.buffer.push(...data)
      }
    } else {
      this.voiceFrameCount = 0
      if (this.isSpeaking) {
        this.buffer.push(...data)
        if (!this.silenceTimeout) {
          this.silenceTimeout = setTimeout(() => {
            this.isSpeaking = false
            this.silenceTimeout = null
            this.voiceFrameCount = 0
            if (this.buffer.length > 0) {
              const float32 = new Float32Array(this.buffer)
              this.buffer = []
              const wavBlob = encodeWAV(float32, this.sampleRate)
              if (this.onAudioData) {
                this.onAudioData(wavBlob)
              }
            }
          }, this.maxSilenceMs)
        }
      }
    }

    if (this.buffer.length >= this.bufferSize && this.isSpeaking) {
      const chunk = this.buffer.splice(0, this.bufferSize)
      const float32 = new Float32Array(chunk)
      const wavBlob = encodeWAV(float32, this.sampleRate)
      if (this.onAudioData) {
        this.onAudioData(wavBlob)
      }
    }
  }

  stop() {
    if (this.silenceTimeout) {
      clearTimeout(this.silenceTimeout)
      this.silenceTimeout = null
    }
    if (this.processor) {
      if (this.processor instanceof AudioWorkletNode) {
        this.processor.disconnect()
      } else {
        this.processor.disconnect()
        this.processor.onaudioprocess = null
      }
    }
    if (this.source) this.source.disconnect()
    if (this.stream) this.stream.getTracks().forEach(t => t.stop())
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
    }
    this.processor = null
    this.source = null
    this.stream = null
    this.audioContext = null
    this.buffer = []
    this.isSpeaking = false
  }

  getAnalyser() {
    return this.audioContext
  }
}
