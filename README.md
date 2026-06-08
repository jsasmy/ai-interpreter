# AI Interpreter

AI Interpreter 是一款 Windows 桌面实时同声传译应用，面向会议、直播、课程、视频播放和跨语言沟通场景。应用通过 Electron 提供桌面能力，通过 FastAPI 后端接入 DashScope LiveTranslate，将麦克风或桌面音频实时转换为原文字幕和译文字幕。

当前版本重点支持：

- 在应用内配置 DashScope API Key 和实时模型，不需要把密钥写死在 `.env` 中。
- 麦克风实时同传。
- 桌面音频实时同传，适合会议软件、浏览器、播放器等系统声音。
- 独立透明字幕窗口，可置顶覆盖在会议、视频或演示画面上。
- 字幕记录、上下文纠错、CSV 导出。
- 已检查/已修正译文自动朗读，支持 DashScope CosyVoice 甜美女声音色。
- Windows 托盘驻留：关闭主窗口后应用仍在后台运行，右键托盘退出才是真正退出。

## 项目信息

- 代码仓库：[https://github.com/jsasmy/ai-interpreter](https://github.com/jsasmy/ai-interpreter)
- 项目名称：AI Interpreter
- 当前版本：2.0.0
- 应用类型：Windows 桌面实时语音同传应用
- 桌面端：Electron
- 前端：Vue 3 + Vite + Element Plus
- 后端：FastAPI + WebSocket
- 实时同传：DashScope LiveTranslate

## 演示预览

### 综合演示


blibli视频播放:【七牛云 × XEngineer 暑期实训营-2026/6/7-批次3-赛题2-AI同声传译助手】 https://www.bilibili.com/video/BV1zJEh6vEyu/?share_source=copy_web&vd_source=42ea97b7627bd4f79ae6ebd97f62d76c


## 使用前配置

首次打开应用后，需要先在右侧“设置”里配置实时翻译服务。

### DashScope API 配置

1. 打开应用右侧“设置”面板。
2. 在“实时翻译配置”中填写 `DashScope API Key`。
3. 填写实时模型，默认推荐：

   ```text
   qwen3.5-livetranslate-flash-realtime
   ```

4. 点击“保存配置”。
5. 应用会先检测 API Key 是否可用；检测通过后才会保存并应用到当前后端。

保存后的密钥存放在本机 Electron 用户数据目录中，不会写入源码，也不会进入安装包。Windows 默认位置类似：

```text
C:\Users\<用户名>\AppData\Roaming\AI Interpreter\api-config.json
```

如果曾经用开发版保存过配置，应用也会兼容读取旧目录：

```text
C:\Users\<用户名>\AppData\Roaming\ai-interpreter-frontend\api-config.json
```

点击“清除配置”会同时删除新旧配置文件，并清空当前后端运行时 API 状态。清除后重新打开应用应显示为未配置。

### `.env.example` 的作用

`backend/.env.example` 只保留本地开发默认值和空的 API Key 占位。正常使用 Electron 应用时，请优先在应用设置里填写 API Key，不要把真实密钥提交到仓库。

## 功能说明

### 麦克风同传

麦克风模式会采集当前系统麦克风输入，适合现场发言、课堂讲解、语音聊天和线下会议。点击底部“麦克风”标签后，按“开始录音”即可开始实时识别和翻译。

### 桌面音频同传

桌面音频模式会通过 Electron 桌面捕获能力采集系统或目标窗口声音，适合翻译会议软件、浏览器视频、播放器、直播等内容。点击底部“桌面音频”标签后，按“开始桌面音频”即可开始捕获。

桌面音频依赖 Electron 桌面环境。浏览器模式通常只能使用麦克风，不能完整使用桌面音频和独立字幕窗口能力。

### 字幕显示

主界面会展示最近字幕记录，包括：

- 原文字幕
- 译文字幕
- 增量字幕和最终字幕
- 上下文纠错状态

应用会保留最近一段字幕历史，避免界面无限增长。可以点击“清空”清除当前会话记录，也可以点击“导出”保存为 CSV。

### 译文语音朗读

应用会在译文完成上下文检查后自动朗读翻译结果，只朗读 `已修正` 或 `无需修正` 状态的最终译文，避免朗读还在变化的增量字幕。底部“朗读开/朗读关”按钮可临时启用或关闭朗读。

默认朗读音色为 DashScope CosyVoice `cosyvoice-v2` 的 `longfeifei_v2`，在设置面板中显示为“龙菲菲（甜美女声）”。也可以切换为“龙小淳（自然女声）”或“系统默认”。云端 TTS 合成失败时，前端会回退到系统内置朗读能力。

朗读功能复用应用内配置的 DashScope API Key；本地开发时也可以通过 `backend/.env.example` 中的 `DASHSCOPE_TTS_MODEL` 和 `DASHSCOPE_TTS_VOICE` 调整默认 TTS 模型与音色。

### 独立字幕窗口

点击“字幕开”可以打开独立字幕窗口。该窗口是透明置顶窗口，适合覆盖到会议、视频或演示画面上。关闭字幕窗口不会退出主应用。

### 后台驻留与退出

点击窗口关闭按钮时，应用会隐藏到系统托盘并继续在后台运行。需要真正退出时，请右键托盘图标并选择“退出”。

## 开发环境要求

- Windows 10/11
- Node.js 18+
- npm
- Python 3.10+
- 可用的 DashScope API Key

建议在 Windows 下开发和打包，因为桌面音频、托盘、透明字幕窗口和 NSIS 安装包都依赖 Windows/Electron 能力。

## 安装依赖

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

## 构建并运行开发版

推荐使用 Electron 开发版，它会启动桌面应用，并由 Electron 主进程拉起后端服务。

```powershell
cd frontend
npm run desktop:dev
```

开发版默认地址：

```text
Frontend: http://127.0.0.1:3001
Backend:  http://127.0.0.1:9000
```

启动后，在应用设置里填写并保存 DashScope API Key。保存成功后，再次启动开发版会自动读取本机保存配置并静默检测，不需要重新输入。

### 手动启动前后端

如果只想调试 Web 前端和后端，也可以手动启动。

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

注意：浏览器模式不具备完整 Electron 桌面能力。需要桌面音频、独立字幕窗口、托盘驻留和本机配置持久化时，请使用 `npm run desktop:dev`。

## 打包

生成 Windows 目录版：

```powershell
cd frontend
npm run pack:win
```

生成 Windows 安装包：

```powershell
cd frontend
npm run dist:win
```

构建产物默认输出到：

```text
frontend/release/
```

## 项目结构

```text
ai-interpreter/
  backend/
    api/                    # HTTP API 和 WebSocket 接口
    services/               # DashScope、ASR、翻译、纠错等服务封装
    config.py               # 后端配置
    main.py                 # FastAPI 入口
    requirements.txt
    .env.example
  frontend/
    electron/               # Electron 主进程与 preload
    src/                    # Vue 应用
    build/                  # 应用图标等打包资源
    package.json
  README.md
```

## 后端接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/` | `GET` | 返回应用名称、版本和运行状态 |
| `/health` | `GET` | 健康检查 |
| `/api/status` | `GET` | 返回 provider、模型和 API 配置状态 |
| `/api/models` | `GET` | 返回当前模型配置 |
| `/api/runtime-config` | `POST` | 在运行时设置或清空 DashScope API Key 和实时模型 |
| `/api/runtime-config/check` | `POST` | 检测 DashScope API Key 是否可用 |
| `/api/tts` | `POST` | 译文语音朗读接口；DashScope 模式下使用 CosyVoice 生成 MP3 |
| `/ws/translate` | `WebSocket` | 实时音频、设置更新和字幕结果通道 |

WebSocket 会接收二进制音频片段和 JSON 设置消息，并向前端推送 `subtitle_delta`、`subtitle`、`correction`、`error` 等消息。

## 常用命令

| 命令 | 目录 | 说明 |
| --- | --- | --- |
| `pip install -r requirements.txt` | `backend/` | 安装后端依赖 |
| `python -m uvicorn main:app --host 0.0.0.0 --port 9000` | `backend/` | 手动启动 FastAPI 后端 |
| `npm install` | `frontend/` | 安装前端和 Electron 依赖 |
| `npm run dev` | `frontend/` | 启动 Vite Web 开发服务 |
| `npm run desktop:dev` | `frontend/` | 启动 Electron 桌面开发版 |
| `npm run build` | `frontend/` | 构建前端静态资源 |
| `npm run pack:win` | `frontend/` | 生成 Windows 目录版 |
| `npm run dist:win` | `frontend/` | 生成 Windows NSIS 安装包 |

## 常见问题

### 启动后显示未配置

打开设置，填写 DashScope API Key 和实时模型后点击“保存配置”。保存会自动检测 API Key；检测失败不会写入配置。

### 桌面音频没有声音

请使用 Electron 桌面模式或安装版，并确认目标应用正在输出声音。某些系统音频设备、会议软件或浏览器权限可能会影响桌面音频捕获。

### 独立字幕窗口没有显示

确认已经收到实时字幕，并且当前运行的是 Electron 桌面版。浏览器模式不支持 Electron 独立字幕窗口。

### 保存配置时 API 检测失败

检查以下内容：

- DashScope API Key 是否填写正确。
- 当前账号是否有模型访问权限。
- 实时模型名称是否正确。
- 网络是否能访问 DashScope。
