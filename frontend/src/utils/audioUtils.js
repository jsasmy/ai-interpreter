export function float32ToPcm16Buffer(samples) {
  const buffer = new ArrayBuffer(samples.length * 2)
  const view = new DataView(buffer)

  for (let i = 0, offset = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
  }

  return buffer
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
        constructor(options) {
          super()
          this.outputPcm = Boolean(options.processorOptions?.outputPcm)
          this.targetSampleRate = options.processorOptions?.targetSampleRate || 16000
          this.inputSampleRate = sampleRate
        }
        process(inputs) {
          const input = inputs[0]
          if (input && input[0]) {
            if (this.outputPcm) {
              const ratio = this.inputSampleRate / this.targetSampleRate
              const outputLength = Math.floor(input[0].length / ratio)
              const pcm = new Int16Array(outputLength)
              for (let index = 0; index < outputLength; index += 1) {
                const sampleIndex = Math.floor(index * ratio)
                const sample = Math.max(-1, Math.min(1, input[0][sampleIndex]))
                pcm[index] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
              }
              this.port.postMessage({ type: 'pcm', buffer: pcm.buffer }, [pcm.buffer])
            } else {
              this.port.postMessage(input[0])
            }
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

    this.processor = new AudioWorkletNode(this.audioContext, 'recorder-processor', {
      processorOptions: {
        outputPcm: this.continuous,
        targetSampleRate: this.sampleRate
      }
    })
    this.source.connect(this.processor)
    this.processor.connect(this.audioContext.destination)

    this.processor.port.onmessage = (e) => {
      if (this.continuous && e.data?.type === 'pcm') {
        this.onAudioData?.(e.data.buffer)
      } else {
        this._processAudioData(e.data)
      }
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
        const pcmBuffer = float32ToPcm16Buffer(new Float32Array(chunk))
        if (this.onAudioData) {
          this.onAudioData(pcmBuffer)
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
              const pcmBuffer = float32ToPcm16Buffer(float32)
              if (this.onAudioData) {
                this.onAudioData(pcmBuffer)
              }
            }
          }, this.maxSilenceMs)
        }
      }
    }

    if (this.buffer.length >= this.bufferSize && this.isSpeaking) {
      const chunk = this.buffer.splice(0, this.bufferSize)
      const float32 = new Float32Array(chunk)
      const pcmBuffer = float32ToPcm16Buffer(float32)
      if (this.onAudioData) {
        this.onAudioData(pcmBuffer)
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
