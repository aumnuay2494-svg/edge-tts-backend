# Edge TTS Backend - Render / Railway / Koyeb 部署版

这是给 `blue is submaker.html` 使用的 TTS 后端。它提供 `/tts` 接口，调用 Edge TTS 生成 MP3。

## 文件

```text
app.py
requirements.txt
render.yaml
Procfile
README.md
```

## Render 部署方式

1. 把本文件夹上传到 GitHub 一个仓库。
2. 打开 https://render.com
3. New + → Web Service
4. 连接你的 GitHub 仓库。
5. 设置：
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Plan: Free
6. 部署完成后，你会得到类似：

```text
https://edge-tts-backend-xxxx.onrender.com
```

7. 打开测试：

```text
https://edge-tts-backend-xxxx.onrender.com/health
```

看到：

```json
{"ok": true}
```

就成功。

## HTML 里填写

在 `blue is submaker.html` → `✨ 肯定语生成` → `TTS 后端地址` 填：

```text
https://edge-tts-backend-xxxx.onrender.com
```

不要加 `/tts`，HTML 会自动拼接。

## 接口

### POST /tts

请求：

```json
{
  "text": "我是值得被爱的人。",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "volume": "+0%"
}
```

返回：MP3 音频。

## 注意

- 免费 Render 服务会休眠，第一次请求可能慢 30–60 秒。
- 如果失败，先访问 `/health` 把服务唤醒。
- 已开启 CORS，本地 HTML 可以调用。
