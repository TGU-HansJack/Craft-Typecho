# Craft-Typecho

Vue3Admin「创意工坊」远程项目索引仓库。

- 索引文件：`repo.json`
- 索引更新时间：`2026-02-06`（见 `repo.json.updatedAt`）

## 使用方式

1. 在 Vue3Admin 后台 → 额外功能 → 创意工坊，选择使用“远程 repo.json”。
2. 填入 `repo.json` 的 Raw 地址并保存（本仓库示例：`https://raw.githubusercontent.com/TGU-HansJack/Craft-Typecho/main/repo.json`）。
3. 刷新页面，即可在表格中查看项目并一键安装/打开使用文档。

## repo.json 字段

`repo.json` 的字段含义（与创意工坊表格列对应）：

- `updatedAt`：索引更新时间（`YYYY-MM-DD`）
- `projects[]`：项目列表
  - `id`：唯一标识（建议小写 + `-`）
  - `name`：项目名称（表格“项目”）
  - `type`：`plugin` / `theme`（表格“类型”）
  - `version`：版本号（表格“版本”）
  - `author`：作者（表格“作者”）
  - `typecho`：Typecho 版本要求（表格“Typecho”）
  - `description`：简介（表格“介绍”）
  - `link`：项目仓库/主页（通常为 GitHub；表格项目名会指向此链接）
  - `readme`：使用文档链接（表格“使用文档”按钮）
  - `isGithub`：是否 GitHub 仓库
  - `direct`：是否支持直连安装
  - `branch`：Git 分支（可选；用于安装时拉取指定分支，如 `v2.x`）
  - `subdir`：仓库子目录（可选；用于“仓库里包含多个项目/配套插件”等场景，如 `配套插件/BsCore`）
  - `dir`：解压后的目录名（用于安装）

## 当前项目

| 项目 | 类型 | 版本 | 作者 | Typecho | 介绍 | 操作 |
| --- | --- | --- | --- | --- | --- | --- |
| [MediaLibrary-Pro](https://github.com/TGU-HansJack/MediaLibrary-Typecho-Plugin-Pro) | 插件 | 0.1.7 | 寒士杰克 | >=1.2.0 | 一个功能强大的 Typecho 媒体库管理插件，提供完整的媒体文件管理、预览、编辑和优化功能。 | [使用文档](https://craft.hansjack.com/plugins/medialibrary.html) |
| [OneBlog](https://github.com/cncodehub/OneBlog) | 主题 | 3.6.5 | 彼岸临窗 | >=1.2.1 | 一款简约清新文艺的写作记录类 Typecho 主题，适合生活记录、文学作品、个人日志等文字类博客。 | [使用文档](https://docs.oneblog.net) |
| [Joe](https://github.com/HaoOuBa/Joe) | 主题 | 7.7.1 | Joe | — | 一款基于 Typecho 的双栏极致优化主题。 | [使用文档](https://78.al) |
| [Pinghsu](https://github.com/chakhsu/pinghsu) | 主题 | 1.6.2 | Chakhsu Lau | 开发版 | 一款以性能优化为出发点、兼顾设计美学的 Typecho 主题。 | [使用文档](https://www.linpx.com/p/more-detailed-pinghsu-theme-set-tutorial.html) |
| [BearSimple](https://github.com/whitebearcode/typecho-bearsimple) | 主题 | 2.9.9 | BearNotion | >=1.3.0 | 一款简洁大方的 Typecho 主题（V2），需配套插件 BsCore。 | [使用文档](https://www.bearnotion.ru/typecho-bearsimple.html) |
| [BsCore](https://github.com/whitebearcode/typecho-bearsimple) | 插件 | 2.9.9 | BearNotion | >=1.3.0 | BearSimple 主题核心插件（配套插件），安装后无需进行其他设置。 | [使用文档](https://www.bearnotion.ru/typecho-bearsimple.html) |

## 声明

本仓库只维护创意工坊索引文件；各项目的版权与许可证请以对应项目仓库为准。

如果这个仓库对你有帮助，欢迎请作者喝杯咖啡。
