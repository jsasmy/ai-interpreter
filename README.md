# AI 同声传译助手

基于小米AI API的实时同声传译系统，支持多语言实时翻译、文件导入、URL链接翻译、浏览器音频捕获等功能。

## 功能特性

- **实时语音翻译**: 麦克风录音实时翻译
- **文件导入翻译**: 支持音频/视频文件导入翻译
- **URL链接翻译**: 输入音频/视频链接直接翻译
- **浏览器音频捕获**: 捕获浏览器标签页音频进行翻译
- **多语言支持**: EN/ZH/JA/KO/FR/DE
- **智能纠错**: 上下文感知的翻译修正
- **双语字幕**: 实时双语字幕显示
- **字幕导出**: CSV格式导出翻译记录

## 项目结构

```
ai-interpreter/
├── frontend/              # Vue3前端
│   └── src/
│       ├── App.vue        # 主界面
│       └── main.js        # 入口
├── backend/               # FastAPI后端
│   ├── api/
│   │   └── websocket.py   # API路由
│   ├── services/
│   │   ├── xiaomi_api.py       # 小米API客户端
│   │   ├── asr_service.py      # 语音识别
│   │   ├── translate_service.py # 翻译服务
│   │   └── correction_service.py # 纠错服务
│   ├── main.py            # 主程序
│   └── config.py          # 配置
├── 启动.bat               # 启动脚本
└── 打包.bat               # 打包脚本
```

## 快速开始

### 1. 配置API

编辑 `backend/.env` 文件：

```env
XIAOMI_API_KEY=your_api_key_here
XIAOMI_API_BASE=https://token-plan-cn.xiaomimimo.com/v1
XIAOMI_API_ENDPOINT=tp-cssf9gh45m7axddhvpj2j5rnfyo3uaf63g0jmqfpzja3crsm
```

### 2. 启动服务

双击 `启动.bat` 或手动启动：

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend
npm install
npm run dev
```

### 3. 访问

- 前端: http://localhost:3001
- 后端: http://localhost:9000
- API文档: http://localhost:9000/docs

## 使用说明

### 麦克风录音
1. 点击"麦克风"标签
2. 点击录音按钮开始
3. 说话后自动识别翻译

### 文件导入
1. 点击"文件"标签
2. 拖放或点击选择音频/视频文件
3. 等待处理完成

### URL链接
1. 点击"链接"标签
2. 输入音频/视频URL
3. 点击"翻译"按钮

### 浏览器捕获
1. 点击"浏览器"标签
2. 点击"开始捕获"
3. 选择要捕获的标签页
4. 播放音频自动翻译

## 小米API模型

| 模型 | 用途 |
|------|------|
| mimo-v2.5-asr | 语音识别 |
| mimo-v2.5 | 语言模型/翻译 |
| mimo-v2.5-tts | 语音合成 |

## 技术栈

- 前端: Vue 3 + Element Plus + WebSocket
- 后端: FastAPI + WebSocket + httpx
- AI: 小米AI API
