# AI Interpreter

实时语音翻译测试版。当前主路径使用阿里云百炼 DashScope 的 Qwen3.5 LiveTranslate 实时同传模型，支持麦克风和桌面音频输入，并提供独立字幕窗口。

## 当前能力

- 麦克风实时语音翻译
- 桌面音频捕获，用于识别浏览器视频、会议或系统播放声音
- 源语言、目标语言、输入源下拉切换
- 独立字幕窗口，支持在应用页面外显示字幕
- 文件和 URL 翻译入口保留
- CSV 字幕导出

## 技术栈

- Frontend: Vue 3, Vite, Element Plus, WebSocket
- Backend: FastAPI, WebSocket, websockets
- Realtime model: `qwen3.5-livetranslate-flash-realtime-2026-05-19`
- ASR model: `qwen3-asr-flash-realtime`

## 项目结构

```text
ai-interpreter/
  backend/
    api/
      websocket.py
    services/
      aliyun_livetranslate_service.py
      asr_service.py
      translate_service.py
      correction_service.py
    config.py
    main.py
    requirements.txt
    .env.example
  frontend/
    src/
      App.vue
      main.js
      utils/audioUtils.js
    package.json
```

## 环境配置

复制示例文件并填写自己的密钥：

```powershell
Copy-Item backend\.env.example backend\.env
```

最小配置：

```env
TRANSLATION_PROVIDER=aliyun_livetranslate
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_LIVETRANSLATE_MODEL=qwen3.5-livetranslate-flash-realtime-2026-05-19
DASHSCOPE_ASR_MODEL=qwen3-asr-flash-realtime
```

不要提交真实 `.env` 或 API Key。

## 本地启动

后端：

```powershell
cd backend
pip install -r requirements.txt
python main.py
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

默认地址：

- Frontend: http://127.0.0.1:3001
- Backend: http://127.0.0.1:9000
- API docs: http://127.0.0.1:9000/docs

## 使用说明

1. 打开前端页面。
2. 在底部选择 Source、Target 和 Input。
3. Input 选择 `麦克风` 时，点击底部录音按钮开始麦克风识别。
4. Input 选择 `桌面音频` 时，点击开始后在浏览器共享窗口中选择标签页或屏幕，并勾选共享音频。
5. 在设置中点击 `独立字幕` 打开独立字幕窗口。

## 当前测试版说明

- 这是实时同传测试版本，重点验证 Qwen3.5 LiveTranslate 的端到端识别和翻译体验。
- 音频分片已调到较低延迟，后端 VAD 也做了更快的句尾判定。
- 过短停顿可能被切成两句；如果后续需要更稳定长句，可适当增加 VAD 静音等待时间。
