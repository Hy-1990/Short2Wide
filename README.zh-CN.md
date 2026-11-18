# Short2Wide · 画幅工作台

[English](README.md) · **简体中文**

用 **DreamAPI Seedance 2.5** 改编短视频画幅。在本机导入小于五分钟的视频，逐段生成、左右对照，一次确认后导出，并保留原片声音。

https://github.com/user-attachments/assets/d491bf93-465d-4457-af80-4c962772e220

[下载 20 秒短片 · 30 fps](docs/assets/short2wide-zh-CN.mp4) · [流程与边界](docs/showcase.md)

> 需要自备 DreamAPI 密钥。应用在本机运行，生成时会把参考片段传至付费云服务。模型可能拒绝素材，也可能产生文字、动作或时序偏差。

## 主流程

1. **导入**：粘贴公开的 YouTube/TikTok 地址，或上传小于五分钟、512MB 以内的本地视频，选择 16:9 或 9:16。
2. **生成**：按画面变化与音频停顿分段，逐段生成。上传、模型生成、对齐均有明确的动效与用时反馈。
3. **查看**：左右均可单独播放、暂停、拖动进度；“同步播放”每次都让两边从当前片段起点重播。
4. **导出**：所有片段生成完成后，点击一次“确认全部并导出”，无需逐段勾选。

![中文工作台](docs/assets/workspace.zh-CN.jpg)

“高级选项”默认折叠，包含两节点线性对齐与模型音频开关。关闭模型音频后，预览和导出仍使用原片音轨。

## 首页就是本机项目库

历史项目直接显示缩略图、生成进度、导出状态和下载入口；返回首页即可继续上次的项目。已移除与真实工作台不一致的静态 demo/example 入口。

![本机项目](docs/assets/home.zh-CN.jpg)

## 安装运行

需要 Python **3.10+**、FFmpeg/ffprobe。Node **22+ 仅用于 JavaScript 回归测试**。

```sh
git clone https://github.com/Hy-1990/Short2Wide.git
cd Short2Wide
bash start.sh
```

macOS/Linux 下，脚本自动创建 `.venv`、安装 Python 依赖并在前台启动；后续运行复用环境。启动成功后会打印访问地址。保持终端开启，按 `Ctrl+C` 停止。更换端口：`bash start.sh --port 4179`。

FFmpeg 需单独安装，并确保 `ffmpeg`、`ffprobe` 在 PATH 中。Windows 可通过 WSL 使用脚本；或依次运行 `python -m venv .venv`、`.venv\Scripts\activate`、`python -m pip install -r requirements.txt`、`python -B server.py --port 4178`。

打开 [http://127.0.0.1:4178/](http://127.0.0.1:4178/)，通过右上角 DreamAPI 配置密钥。明暗/跟随系统主题与中英文选项跨页面保留。

项目已内置 `scripts/dreamapi.py`，不需要安装任何 agent skill。启动必须使用 `server.py`。

## 数据与恢复

- 服务仅监听 127.0.0.1，保留 Host/Origin 检查与静态文件白名单。
- 密钥保存在仓库之外的 `~/.config/reframe-studio/dreamapi.json`，权限为0600；不存浏览器、不回传已保存密钥。
- 项目位于 `~/.local/share/reframe-studio/projects/`，保留旧版本本机项目兼容性。
- 首页上传只进入本机。点击生成时才上传参考片段并调用计费模型。
- 查询超时继续查询原任务；无任务ID的未知提交停止，避免重复扣费。新的明确重试保留旧任务记录。
- 对齐失败保留此前可播放的文件，原始素材、模型输出、原音预览和成片分开保存。

## 使用边界

工具不人为限制人数、语言、是否口播或有无音轨，但服务商仍可能限制参考素材。自动分段不是语义识别，生成文字、动作、口型需要自行检查。

默认按总时长归一；两节点只校正线性偏移与速度，不能保证中间全部事件同步。最终使用原文件音轨，编码为AAC以兼容MP4；无音轨输入保持静音。

下载受平台登录、地区与视频可见性影响。生成音频的审核失败不等于原视频有问题；明确需要重试时，可先在高级选项关闭模型音频。

## 验证

```sh
node --test test_playback.mjs
python -B -m unittest -q test_pipeline.py test_server.py test_provider.py
```

自动测试使用临时素材与替代接口响应，不提交计费任务。[完整验证记录](docs/verification.md)

代码采用 [MIT](LICENSE)，字体、服务和演示媒体分别遵循[第三方说明](THIRD-PARTY.md)。
