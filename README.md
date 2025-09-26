# OCR-Translate-Sketch：一个实时屏幕翻译工具

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

**OCR-Translate-Sketch** 是一个为学习和探索目的打造的实时屏幕 OCR 翻译工具。

> ⚠️ **重要提示**
>
> 这是一个个人学习项目，旨在进行技术概念验证 (Proof of Concept)。它并非一个稳定、精准的生产级工具，在许多场景下可能无法正常工作。请抱着探索和交流的心态来尝试它。

## ✨ 项目初衷

你是否也曾有过这样的烦恼：玩游戏、看外语视频或文档时，总会遇到不认识的单词或句子？频繁地切换应用来查词或翻译，不仅打断了沉浸式体验，也十分影响效率。

我希望有一款工具，只需将鼠标悬停在屏幕的某个区域，就能立刻得到识别和翻译结果。**OCR-Translate-Sketch** 正是为此而生。

## 🚀 它能做什么？

*   **实时屏幕捕捉**：捕获屏幕并进行基础的图像预处理。
*   **精准文字识别**：调用 Tesseract OCR 引擎进行文字识别（默认识别英文）。
*   **即时翻译**：集成 `googletrans` 库，将识别出的英文翻译为中文，并内置缓存与重试机制，提升体验。
*   **悬浮窗展示**：以一个透明、置顶的悬浮层展示识别与翻译结果。
*   **快捷键操控**：通过全局热键，轻松控制程序的停止与模式切换。

## 🚧 已知局限

作为一款学习型项目，它还有很多不完善之处：

*   **性能瓶颈**：实时图像处理对系统资源消耗较大，在大部分设备上可能出现延迟或卡顿。
*   **识别精度**：在低光、模糊、复杂背景、艺术字体、手写体或倾斜文本等场景下，识别成功率会显著下降。
*   **交互简陋**：目前仅支持基础的识别和交互，不够智能和灵活。
*   **翻译质量**：公共翻译 API 对零散、非结构化文本的翻译效果有限。
*   **语言支持**：当前主要针对“英译中”场景打磨，其他语言支持尚不完善。

## 快速上手

### 运行环境

*   Windows 10 / 11
*   已正确安装 [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)，并确保其路径已配置在 `config.yaml` 文件中。
*   Python 3.11+

### 安装与运行 (推荐使用 uv)

[uv](https://github.com/astral-sh/uv) 是一款极速的 Python 包管理工具，能带来更流畅的开发体验。

```bash
# 1. 克隆项目代码
git clone https://github.com/KIDLi1412/OCR-Translate-Sketch.git
cd OCR-Translate-Sketch

# 2. 安装 uv (如果尚未安装)
请参考官方文档: https://github.com/astral-sh/uv

# 3. 创建虚拟环境并安装项目依赖
uv sync

# 4. 启动程序
uv run python main.py
```

### 其他方式运行

请参考project.toml

## ⚙️ 配置说明

所有配置项均位于根目录的 `config.yaml` 文件中，你可以根据自己的需求进行修改。

**关键配置项说明：**

```yaml
# Tesseract-OCR 的可执行文件路径，请务必修改为你的实际安装路径
TESSERACT_CMD: D:\\Program Files\\Tesseract-OCR\\tesseract.exe

# OCR 识别语言，需要确保你已经安装了对应的 Tesseract 语言包
OCR_LANGUAGE: eng

# 停止/启动程序的热键
STOP_HOTKEY: <alt>+c

# 切换翻译显示的热键
TRANSLATION_HOTKEY: <alt>+t

# 翻译功能总开关
TRANSLATION_ENABLED: true

# 翻译目标与源语言
TRANSLATION_TARGET_LANG: zh-cn
TRANSLATION_SOURCE_LANG: en
```

*   `TESSERACT_CMD`：**首次使用必须修改此项**，指向你电脑上 Tesseract 的安装位置。
*   `OCR_LANGUAGE`：如果需要识别其他语言，请先安装 Tesseract 对应的[语言数据包](https://github.com/tesseract-ocr/tessdata)。
*   `*_HOTKEY`：你可以自定义喜欢的快捷键。
*   其他翻译相关参数用于调优缓存和重试策略，通常无需改动。

其他配置说明参考CONFIG.md。

## 🕹️ 如何使用

1.  运行 `main.py` 启动程序。
2.  程序会创建一个覆盖全屏的透明置顶窗口。
3.  默认情况下，程序会以设定的频率对屏幕内容进行识别，并将结果实时显示在悬浮层中。
4.  你可以使用 `config.yaml` 中设置的热键来切换翻译内容的显示。
5.  通过系统托盘图标或设定的停止热键，可以安全地退出程序。

## 🗺️ 未来路线图

这个项目还有很长的路要走，以下是计划探索的方向：

*   **提升 OCR 稳定性**：实现手动选择识别区域、动态阈值调整、文本倾斜矫正等。
*    **性能优化**：探索图像批处理、并行计算、动态降采样等策略，降低资源占用。
*    **翻译功能增强**：优化段落聚合翻译、多语言自动检测，并考虑支持更多翻译服务提供方。
*    **交互体验优化**：设计更美观、更易用的悬浮层 UI，并加入图形化的设置界面。
*    **代码质量提升**：补充更完善的单元测试。

## 🤝 如何贡献

欢迎任何形式的贡献，让这个小工具变得更好！

你可以通过以下方式参与进来：

*   **提交 Issue**：反馈 Bug、提出改进建议。
*   **发起 Pull Request**：修复已知问题、开发新功能。
*   **分享你的想法**：讨论新的技术方案或应用场景。

特别期待在以下方面的帮助：

*   优化性能与稳定性。
*   改进算法，提升 OCR 识别率。
*   设计更现代化、更友好的用户界面。
*   扩展更多语言支持。

## 📜 开源许可

本项目基于 **MIT License** 开源。

## 🙏 致谢

*   **Tesseract OCR**：强大的开源 OCR 引擎。
*   **googletrans**：便捷的谷歌翻译接口库。
*   以及在开发过程中给予我灵感和帮助的所有开源社区。
