# AI Interpreter

实时语音翻译测试版。当前主路径使用阿里云百炼 DashScope 的 Qwen3.5 LiveTranslate 实时同传模型，支持麦克风和桌面音频输入，并提供独立字幕窗口。

## 当前能力

- 麦克风实时语音翻译
- 桌面音频捕获，用于识别浏览器视频、会议或系统播放声音
- 源语言、目标语言、输入源下拉切换
- 独立字幕窗口，支持在应用页面外显示字幕
- CSV 字幕导出

## 技术栈

- Frontend: Vue 3, Vite, Element Plus, WebSocket
- Desktop shell: Electron
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
    electron/
      main.cjs
    src/
      App.vue
      main.js
      utils/audioUtils.js
    package.json
```

## 环境配置

先准备 Python、Node.js 和 npm，然后复制示例文件并填写自己的 DashScope 密钥：

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

推荐使用两个 PowerShell 终端分别启动后端和前端。

### 1. 安装依赖

后端依赖：

```powershell
cd backend
pip install -r requirements.txt
```

前端依赖：

```powershell
cd frontend
npm install
```

### 2. 启动后端

在项目根目录执行：

```powershell
cd backend
python main.py
```

看到后端监听 `9000` 端口后保持该终端不要关闭。

### 3. 启动前端

另开一个 PowerShell，在项目根目录执行：

```powershell
cd frontend
npm run dev
```

然后打开前端地址。

默认地址：

- Frontend: http://127.0.0.1:3001
- Backend: http://127.0.0.1:9000
- API docs: http://127.0.0.1:9000/docs

### 可选：使用启动器

仓库根目录有一个简易启动器：

```powershell
python launcher.py
```

它会尝试启动后端和前端，并打开浏览器。这个启动器仍然是浏览器版本，不是桌面客户端。

## Electron 桌面版启动

桌面版入口位于 `frontend/electron/main.cjs`。它会自动启动：

- FastAPI 后端：http://127.0.0.1:9000
- Vite 前端：http://127.0.0.1:3001
- Electron 应用窗口

启动方式：

```powershell
cd frontend
npm run desktop:dev
```

如果系统里的 `python` 不是项目要用的 Python，可以显式指定：

```powershell
$env:PYTHON_PATH="E:\anacodna\python.exe"
cd frontend
npm run desktop:dev
```

桌面版会拦截页面里的桌面音频捕获请求，在 Windows 上优先使用 Electron 的 system audio loopback。也就是说，Input 选择 `桌面音频` 后，采集路径会比普通浏览器版更接近桌面客户端。

## 使用说明

1. 打开前端页面。
2. 在底部选择 Source、Target 和 Input。
3. Input 选择 `麦克风` 时，点击底部录音按钮开始麦克风识别。
4. Input 选择 `桌面音频` 时，点击开始后在浏览器共享窗口中选择标签页或屏幕，并勾选共享音频。
5. 主页面右下角的 `字幕开/字幕关` 用于手动打开或关闭独立字幕窗口。
6. 设置里的 `识别时自动打开字幕` 控制开始识别时是否自动弹出独立字幕窗口。

当前版本暂时只保留麦克风和桌面音频实时识别，不包含文件上传或 URL 链接翻译入口。

## 当前测试版说明

- 这是实时同传测试版本，重点验证 Qwen3.5 LiveTranslate 的端到端识别和翻译体验。
- 音频分片已调到较低延迟，后端 VAD 也做了更快的句尾判定。
- 过短停顿可能被切成两句；如果后续需要更稳定长句，可适当增加 VAD 静音等待时间。
