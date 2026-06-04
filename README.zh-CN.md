<div align="center">

# 🎬 Xiaoer VideoLab · 小耳抓视频

### 一键。任意视频。全在本地。

工具栏点一下，当前页面的视频就落进你的 `~/Downloads`。
底层是一个超小的本地 [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) 守护进程 —— 开箱即通 **1800+ 网站**
（YouTube · B站 · X/Twitter · TikTok · Vimeo · Twitch · 微博 …）。

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
![Platform](https://img.shields.io/badge/平台-macOS-lightgrey)
![Manifest V3](https://img.shields.io/badge/Chrome-MV3-4285F4?logo=googlechrome&logoColor=white)
![Python stdlib only](https://img.shields.io/badge/Python-仅标准库-3776AB?logo=python&logoColor=white)
![localhost only](https://img.shields.io/badge/网络-仅本机-27ae60)

[English](README.md) · **简体中文**

</div>

---

## 为什么做它

浏览器里的视频下载插件大多是个泥潭：动不动要「读取你在所有网站上的全部数据」权限，还偷偷回传。
Xiaoer VideoLab 反着来：

- **扩展几乎什么都不做。** 你点它的时候，它只读*当前标签页的 URL* 这一个字符串，POST 给 `127.0.0.1`。
  不抓页面、无 content script、不连任何远程服务器。
- **下载在本地完成。** 一个小小的 Python 守护进程把 URL 交给久经考验的开源工具 `yt-dlp`，
  所有「聪明活」都在一个你能亲自审计的工具里。
- **除了 `yt-dlp` 去取你要的那个视频，没有任何东西离开你的电脑。**

## 工作原理

```
 ┌─────────────────────┐   点击     ┌──────────────────────────┐         ┌──────────┐
 │  浏览器工具栏按钮     │ ─────────► │  daemon @ 127.0.0.1:7788 │ ──────► │  yt-dlp  │ ──► ~/Downloads
 │  (Chrome MV3 扩展)   │  POST url  │  (Python 标准库, launchd)│  调用   └──────────┘        │
 └─────────────────────┘            └──────────────────────────┘                              ▼
        ▲   角标: … ✓ ✕ !                       │                                     macOS 系统通知
        └───────────────────────────────────────┘                                      "✅ <文件名>"
```

- **daemon** —— Python 标准库 `http.server`，监听 `127.0.0.1:7788`，由 `launchd` 开机自启。
- **extension** —— Chrome MV3，一个工具栏按钮，取 `tab.url` POST 给 daemon。
- **产物** —— `~/Downloads/<标题> [<id>].mp4`（默认 ≤1080p mp4，可配置）。
- **日志** —— `~/Library/Logs/xiaoer-videolab.log`

## 环境要求

- **macOS**（后台服务用 `launchd`；daemon 本身跨平台，手动跑即可）
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) 和 `ffmpeg`：
  ```bash
  brew install yt-dlp ffmpeg
  ```
- 任意 Chromium 内核浏览器（Chrome / Arc / Edge / Brave / Dia …）

## 安装

```bash
git clone https://github.com/Jane-xiaoer/xiaoer-videolab.git
cd xiaoer-videolab
./scripts/install.sh
```

安装脚本会按你自己的路径**动态生成** LaunchAgent 并启动 daemon。然后加载扩展：

1. 打开 `chrome://extensions/`
2. 右上角打开 **开发者模式**
3. 点 **加载已解压的扩展程序** → 选 `extension/` 文件夹
4. 把图标固定到工具栏

## 使用

打开任意视频页 → 点工具栏按钮 → 弹「开始下载」通知，完成后弹「✅ &lt;文件名&gt;」。

| 角标 | 含义 |
|:---:|---|
| `…` | 请求已发，正在下 |
| `✓` | daemon 接单了（下载在后台继续） |
| `✕` | 连不上 daemon |
| `!` | daemon 报错（看通知 / 日志） |

## 配置

全部可选 —— 设好后重新跑 `./scripts/install.sh` 即可写进服务：

| 变量 | 默认 | 作用 |
|---|---|---|
| `VIDEOLAB_PORT` | `7788` | daemon 端口 |
| `VIDEOLAB_DOWNLOADS` | `~/Downloads` | 下载目录 |
| `VIDEOLAB_YT_DLP` | 自动探测 | `yt-dlp` 二进制路径 |
| `VIDEOLAB_PREFIX` | _（无）_ | 文件名前缀，比如 `小耳-` |
| `VIDEOLAB_MAX_HEIGHT` | `1080` | 最大画质高度（要 4K 填 `2160`） |
| `VIDEOLAB_COOKIES_BROWSER` | _（关）_ | 从某浏览器取 cookie（`chrome`/`brave`/`firefox`/`edge`/`safari`），用于**登录态 / 私域**视频 |
| `VIDEOLAB_APP_NAME` | `Xiaoer VideoLab` | 通知里显示的名字 |

```bash
# 例：4K + 从 Chrome 取登录 cookie + 文件名带「小耳-」前缀
VIDEOLAB_MAX_HEIGHT=2160 VIDEOLAB_COOKIES_BROWSER=chrome VIDEOLAB_PREFIX="小耳-" ./scripts/install.sh
```

## 常用命令

```bash
# daemon 还活着吗
curl http://127.0.0.1:7788/health

# 看日志
tail -f ~/Library/Logs/xiaoer-videolab.log

# 重启 daemon
launchctl unload ~/Library/LaunchAgents/com.xiaoer.videolab.plist
launchctl load   ~/Library/LaunchAgents/com.xiaoer.videolab.plist

# 不用扩展，直接命令行下载
curl -X POST http://127.0.0.1:7788/download \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# 卸载服务
./scripts/uninstall.sh
```

## 安全

- daemon 只绑定 `127.0.0.1`，外网打不到。
- CORS 设为 `*`，因为这是无密钥的本机端口。如果担心*同机其他进程*乱发，
  在 `daemon/server.py` 里加一个共享 `X-Token` 校验即可。
- 扩展唯一的主机权限是 `http://127.0.0.1:7788/*`。

## 常见问题

**提示「连不上 daemon」（`✕`）。** 跑 `curl http://127.0.0.1:7788/health`，失败就看
`tail ~/Library/Logs/xiaoer-videolab.err.log`，并确认 `yt-dlp` 已安装。

**下下来画质很低 / 只有声音。** 有些站把视频和音频拆开了，装上 `ffmpeg` 让 `yt-dlp` 能合流。

**私有 / 会员视频下不了。** 把 `VIDEOLAB_COOKIES_BROWSER` 设成你登录的那个浏览器，再重装一次。

**不是 macOS？** 扩展跨平台，只有*安装脚本*是 macOS 专属。Linux/Windows 自己跑
`python3 daemon/server.py` 即可（任何进程管理器都行）。

## 参与贡献

欢迎 Issue 和 PR。整个项目约 400 行标准库 Python + 原生 JS，好读好 fork。
如果你加了在意的能力（新的格式档位、Firefox manifest、Linux 服务文件），发过来。

## 作者

**Jane** · 小耳 / Xiaoer —— *一组会听、会读、会找、会帮你整理信息的小工具。*

- GitHub：[@Jane-xiaoer](https://github.com/Jane-xiaoer)
- 邮箱：xiaoerzhan@gmail.com

它是 **小耳** 工具箱的一员，同门还有
[小耳 Ask](https://github.com/Jane-xiaoer/xiaoer-ask) 和
[小耳一键改名 Smart Rename](https://github.com/Jane-xiaoer/smart-rename)。

## 致谢

完全站在 [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) 的肩膀上 —— 本项目只是给它套了个友好的一键按钮。
请支持并尊重 yt-dlp 项目。

## 许可证

[MIT](LICENSE) © 2026 Jane（小耳 / Xiaoer）

> 只下载你有权下载的内容。请自行遵守你使用本工具的网站的服务条款与适用的版权法律。
