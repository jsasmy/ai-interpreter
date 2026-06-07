# AI Interpreter

AI Interpreter 是一个实时同声传译桌面应用。当前主链路使用阿里云百炼 DashScope 的 Qwen LiveTranslate 实时同传模型，支持麦克风、桌面音频捕获、透明字幕窗口、上下文纠错和字幕导出。

## 演示

<video src="docs/demo.mp4" controls width="100%"></video>

如果 GitHub 页面没有自动播放控件，也可以直接打开 [docs/demo.mp4](docs/demo.mp4) 查看演示。

## 主要功能

- 实时语音识别与翻译：支持英文等源语言到中文等目标语言的实时同传。
- 麦克风输入：直接使用本机麦克风进行实时翻译。
- 桌面音频输入：Electron 桌面版可捕获系统/浏览器/视频会议声音。
- 透明置顶字幕：字幕可脱离主窗口显示在视频或会议窗口上方。
- 上下文纠错：后台使用最近上下文修正字幕，并显示 `检查中`、`无需修正`、`已修正`、`纠错失败`、`已跳过` 等状态。
- 最近字幕保留：主界面保留最近字幕记录，便于回看。
- CSV 导出：可导出原文、译文和时间戳。
- Electron 自动拉起服务：桌面开发模式会自动启动后端和前端开发服务器。

## 技术栈

- Frontend: Vue 3, Vite, Element Plus
- Desktop: Electron
- Backend: FastAPI, WebSocket
- Realtime translation: DashScope LiveTranslate
- Context repair: DashScope compatible chat model

## 项目结构

```text
ai-interpreter/
  backend/
    api/
    services/
    config.py
    main.py
    requirements.txt
    .env.example
  frontend/
    electron/
      main.cjs
      preload.cjs
    src/
    package.json
  docs/
    demo.mp4
  launcher.py
  README.md
```

## 环境要求

- Windows 10/11
- Python 3.10+
- Node.js 18+
- npm
- DashScope API Key

桌面音频捕获和透明置顶字幕建议使用 Electron 桌面版；普通浏览器版主要用于前端调试。

## 配置

复制后端环境变量示例：

```powershell
Copy-Item backend\.env.example backend\.env
```

编辑 `backend\.env`，至少配置：

```env
TRANSLATION_PROVIDER=aliyun_livetranslate
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_LIVETRANSLATE_MODEL=qwen3.5-livetranslate-flash-realtime
DASHSCOPE_ASR_MODEL=qwen3-asr-flash-realtime
DASHSCOPE_REPAIR_MODEL=qwen-plus-latest
ENABLE_CONTEXTUAL_REPAIR=true
```

不要提交真实的 `.env`、API Key、Token 或账号密码。

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

## 启动方式

### 方式一：Electron 桌面版

推荐日常使用这种方式。Electron 会自动启动后端和 Vite 前端服务。

```powershell
cd frontend
npm run desktop:dev
```

如果系统默认 `python` 不是已经安装依赖的 Python，可以显式指定：

```powershell
$env:PYTHON_PATH="E:\anacodna\python.exe"
cd frontend
npm run desktop:dev
```

默认服务：

- Frontend: `http://127.0.0.1:3001`
- Backend: `http://127.0.0.1:9000`

### 方式二：手动启动后端和前端

第一个终端启动后端：

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9000
```

第二个终端启动前端：

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 3001
```

浏览器打开：

```text
http://127.0.0.1:3001
```

### 方式三：简易启动器

仓库根目录可运行：

```powershell
python launcher.py
```

## 使用说明

1. 打开应用。
2. 在底部选择 `Source`、`Target` 和 `Input`。
3. `Input` 选择 `麦克风` 时，点击底部录音按钮开始实时翻译。
4. `Input` 选择 `桌面音频` 时，Electron 版会优先捕获桌面/系统音频。
5. 点击右下角 `字幕开/字幕关` 可打开或关闭透明字幕窗口。
6. 设置中的 `识别时自动打开字幕` 控制开始识别时是否自动打开透明字幕。
7. 主界面会显示纠错状态，方便判断字幕是否已检查、已修正或失败。
8. 可点击 `导出` 保存 CSV 字幕记录。

## 打包 Windows 版本

生成未安装目录版：

```powershell
cd frontend
npm run pack:win
```

输出目录：

```text
frontend/release/win-unpacked/
```

生成安装包：

```powershell
cd frontend
npm run dist:win
```

输出目录：

```text
frontend/release/
```

注意：当前打包版本仍需要目标机器有可用 Python 环境，并安装 `backend/requirements.txt` 中的依赖。可以通过系统 `python` 或 `PYTHON_PATH` 指向对应 Python。

## 开发备注

- `backend/.env` 已被忽略，不要提交真实密钥。
- `frontend/dist/`、`frontend/release/`、日志和临时文件不会提交。
- 大文件请优先放 GitHub Releases；README 中的演示视频已压缩为适合仓库展示的小体积 mp4。
