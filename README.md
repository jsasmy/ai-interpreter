# AI Interpreter

AI Interpreter 是一款面向会议、直播、课程和跨语言沟通场景的实时语音同传桌面应用。应用支持麦克风与桌面音频输入，通过后端 WebSocket 管道接入 DashScope LiveTranslate，实现实时识别、翻译、字幕展示、上下文纠错和字幕记录导出。

## 项目信息

- 代码仓库：[https://github.com/jsasmy/ai-interpreter](https://github.com/jsasmy/ai-interpreter)
- 项目名称：AI Interpreter
- 当前版本：2.0.0
- 应用类型：Windows 桌面实时语音同传应用
- 核心能力：麦克风同传、桌面音频同传、透明字幕窗口、上下文纠错、字幕导出

## 演示预览

### 桌面音频示例

[直接在线播放：桌面音频实时同传演示](https://cdn.jsdelivr.net/gh/jsasmy/ai-interpreter@main/docs/desktop-audio-demo.mp4)

仓库内文件：[docs/desktop-audio-demo.mp4](https://github.com/jsasmy/ai-interpreter/blob/main/docs/desktop-audio-demo.mp4)

### 麦克风示例

[直接在线播放：麦克风实时同传演示](https://cdn.jsdelivr.net/gh/jsasmy/ai-interpreter@main/docs/microphone-demo.mp4)

仓库内文件：[docs/microphone-demo.mp4](https://github.com/jsasmy/ai-interpreter/blob/main/docs/microphone-demo.mp4)

## 主要功能

- 实时同传：接入 DashScope LiveTranslate，持续接收音频并返回增量字幕与最终字幕。
- 多输入源：支持麦克风输入和桌面音频捕获，适合现场发言、线上会议、浏览器播放内容等场景。
- 独立字幕窗：Electron 版本支持透明、置顶的字幕窗口，可覆盖在会议、视频或演示画面上方。
- 多语言方向：前端支持自动识别和中、英、日、韩、法、德、西、葡、意、俄、阿、粤语、越南语、泰语、印尼语、印地语、希腊语、土耳其语等语言选项。
- 上下文纠错：后端基于最近字幕上下文修正译文，并在界面展示检查中、无需修正、已修正、纠错失败、已跳过等状态。
- 字幕管理：主界面保留最近字幕记录，支持清空与 CSV 导出。
- 桌面集成：Electron 开发模式会拉起前端页面，并通过主进程能力支持桌面音频与独立字幕窗口。
- 可选旁路能力：后端保留第二路端到端同传、ASR 旁路和文本翻译回退配置，便于在复杂实时场景下调试稳定性。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3, Vite, Element Plus |
| 桌面端 | Electron, electron-builder |
| 后端 | FastAPI, WebSocket, Pydantic Settings |
| 实时同传 | DashScope LiveTranslate |
| 文本翻译与纠错 | DashScope compatible chat API |
| 备用链路 | Xiaomi API legacy path |

## 项目结构

```text
ai-interpreter/
  backend/
    api/                    # WebSocket 与 HTTP API
    services/               # ASR、同传、文本翻译、纠错和第三方 API 封装
    config.py               # 环境变量配置
    main.py                 # FastAPI 入口
    requirements.txt
    .env.example
  frontend/
    electron/               # Electron 主进程与 preload
    src/                    # Vue 应用源码
    package.json
  docs/
    desktop-audio-demo.mp4
    microphone-demo.mp4
  launcher.py               # 简易本地启动器
  README.md
```

## 环境要求

- Windows 10/11
- Python 3.10+
- Node.js 18+
- npm
- 可用的 DashScope API Key

桌面音频捕获和透明字幕窗口依赖 Electron 能力，推荐使用 Electron 桌面模式运行。

## 配置

复制环境变量示例：

```powershell
Copy-Item backend\.env.example backend\.env
```

编辑 `backend\.env`，至少配置以下内容：

```env
TRANSLATION_PROVIDER=aliyun_livetranslate
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_LIVETRANSLATE_MODEL=qwen3.5-livetranslate-flash-realtime
DASHSCOPE_ASR_MODEL=qwen3-asr-flash-realtime
DASHSCOPE_TEXT_MODEL=qwen-flash
DASHSCOPE_REPAIR_MODEL=qwen-plus-latest
ENABLE_CONTEXTUAL_REPAIR=true
SOURCE_LANG=en
TARGET_LANG=zh
```

常用配置项：

| 变量 | 说明 |
| --- | --- |
| `TRANSLATION_PROVIDER` | 翻译服务提供方。实时同传路径使用 `aliyun_livetranslate`。 |
| `DASHSCOPE_API_KEY` | DashScope API Key。不要提交真实密钥。 |
| `DASHSCOPE_LIVETRANSLATE_MODEL` | 主实时同传模型。 |
| `ENABLE_SECOND_E2E` | 是否启用第二路端到端同传会话。 |
| `ENABLE_ASR_FALLBACK` | 是否启用实时 ASR 旁路。 |
| `ASR_FALLBACK_TRANSLATE` | ASR 旁路结果是否继续走文本翻译。 |
| `AUDIO_REPLAY_SECONDS` | 重建实时会话时回放的最近音频窗口。 |
| `ENABLE_CONTEXTUAL_REPAIR` | 是否启用基于上下文的字幕修正。 |
| `CONTEXTUAL_REPAIR_WINDOW_SIZE` | 参与上下文修正的历史字幕数量。 |
| `SOURCE_LANG` / `TARGET_LANG` | 默认源语言与目标语言。 |

## 安装依赖

后端：

```powershell
cd backend
pip install -r requirements.txt
```

前端：

```powershell
cd frontend
npm install
```

## 启动

### Electron 桌面模式

推荐使用桌面模式开发和演示：

```powershell
cd frontend
npm run desktop:dev
```

默认服务地址：

- Frontend: `http://127.0.0.1:3001`
- Backend: `http://127.0.0.1:9000`

### 手动启动前后端

后端：

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9000
```

前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 3001
```

浏览器访问：

```text
http://127.0.0.1:3001
```

### 简易启动器

仓库根目录运行：

```powershell
python launcher.py
```

启动器会依次拉起后端服务、前端开发服务，并打开浏览器页面。它适合本地快速验证；需要桌面音频捕获和独立字幕窗时，仍建议使用 Electron 桌面模式。

## 使用流程

1. 启动应用并确认右上角 API 状态为已连接。
2. 在底部选择 `Source`、`Target` 和 `Input`。
3. 选择 `麦克风` 或 `桌面音频` 输入方式。
4. 点击底部录音按钮开始捕获音频。
5. 根据需要点击 `字幕开` 打开独立字幕窗口。
6. 在主界面查看实时字幕、译文和纠错状态。
7. 点击 `导出` 保存字幕记录，或点击 `清空` 重置当前会话记录。

## 后端接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/` | `GET` | 返回应用名称、版本和运行状态。 |
| `/health` | `GET` | 健康检查。 |
| `/api/status` | `GET` | 返回当前 provider、模型和 API Key 配置状态。 |
| `/api/models` | `GET` | 返回当前启用的模型信息。 |
| `/api/tts` | `POST` | legacy TTS 接口，依赖 Xiaomi API 配置。 |
| `/ws/translate` | `WebSocket` | 实时音频、设置更新和翻译结果通道。 |

WebSocket 会接收二进制音频片段和 JSON 设置消息，并向前端推送 partial、final、correction、error 等类型的消息。

## 打包

生成未安装目录版：

```powershell
cd frontend
npm run pack:win
```

生成 Windows 安装包：

```powershell
cd frontend
npm run dist:win
```

构建产物输出到：

```text
frontend/release/
```

打包配置会把 `backend/` 作为额外资源复制到 Electron 产物中，并排除 `.env`、虚拟环境和 Python 缓存文件。发布前请确认目标机器具备运行后端所需的 Python 环境，或在后续发布流程中补充后端运行时封装。

## 开发命令

| 命令 | 目录 | 说明 |
| --- | --- | --- |
| `pip install -r requirements.txt` | `backend/` | 安装后端依赖。 |
| `python -m uvicorn main:app --host 0.0.0.0 --port 9000` | `backend/` | 启动 FastAPI 服务。 |
| `npm install` | `frontend/` | 安装前端依赖。 |
| `npm run dev` | `frontend/` | 启动 Vite 开发服务。 |
| `npm run desktop:dev` | `frontend/` | 启动 Electron 桌面开发模式。 |
| `npm run build` | `frontend/` | 构建前端静态资源。 |
| `npm run pack:win` | `frontend/` | 生成 Windows 目录版产物。 |
| `npm run dist:win` | `frontend/` | 生成 Windows 安装包。 |

## 常见问题

### API 状态显示未配置

检查 `backend\.env` 是否存在，确认 `DASHSCOPE_API_KEY` 已填写，并重启后端服务。

### 桌面音频无法捕获

请使用 Electron 桌面模式运行，并确认系统或目标应用正在输出音频。浏览器模式通常只能使用麦克风输入。

### 字幕窗口没有显示

确认使用的是 Electron 桌面模式，并检查应用是否已经收到实时字幕。独立字幕窗口需要前端主界面向 Electron 主进程同步字幕内容。

### 实时结果延迟或中断

可以检查网络连接、DashScope Key 权限、模型名称和后端日志。需要增强稳定性时，可尝试开启 `ENABLE_ASR_FALLBACK` 或 `ENABLE_SECOND_E2E` 进行旁路观察。

## 安全说明

- 不要提交真实 API Key、访问令牌或包含敏感会话信息的日志。
- `.env` 默认不应进入版本控制。
- 若用于公开演示或团队共享，建议使用权限受限的 RAM 用户或专用 API Key。
