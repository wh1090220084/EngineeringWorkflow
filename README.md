# Engineering Workflow

Engineering Workflow 是一个面向软件仓库任务的通用工程 Skill。它将实现、调试、评审、验证、计划和外部操作按风险分级，要求用与风险相称的证据证明结论，而不是用未经验证的推断代替结果。

该项目采用与成熟多平台 Skill 仓库相同的核心构造：一份规范化的 Skill 内容，多个只负责发现和加载的薄适配层。它支持 Codex、Claude Code、Gemini CLI 和 GitHub Copilot CLI。

## 架构

`skills/engineeringworkflow/` 是行为定义的 **single source of truth**（唯一真源）：

- `SKILL.md` 定义任务分流、风险等级和工程约束。
- `references/` 保存调试证据、严格工作流、安全信任、实验复现和压力场景等按需读取的细节。
- `agents/openai.yaml` 是单个 Skill 的 Codex UI 元数据。

根目录的适配文件不会复制或改写工作流文本：

| 平台 | 入口文件 | 加载方式 |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json` | Plugin manifest 公开 `./skills/`。 |
| Claude Code | `.claude-plugin/plugin.json` | Plugin manifest 公开 `./skills/`。 |
| Gemini CLI | `gemini-extension.json`、`GEMINI.md` | `GEMINI.md` 直接导入规范化的 `SKILL.md`。 |
| GitHub Copilot CLI | `.agents/plugins/marketplace.json` | 本地 marketplace 暴露同一插件包。 |

这种分层意味着修改工程规则时只修改 `skills/engineeringworkflow/`；修改安装或展示元数据时只修改相应平台的 adapter。不要为某个平台复制 `SKILL.md`，否则不同平台的行为会逐渐漂移。

## 目录说明

```text
.
|-- skills/engineeringworkflow/        # 规范化 Skill 内容
|   |-- SKILL.md
|   |-- references/
|   `-- agents/openai.yaml
|-- .codex-plugin/plugin.json          # Codex adapter
|-- .claude-plugin/plugin.json         # Claude Code adapter
|-- .agents/plugins/marketplace.json   # Copilot CLI marketplace adapter
|-- gemini-extension.json              # Gemini CLI adapter
|-- GEMINI.md                          # Gemini 对规范化 Skill 的导入
|-- AGENTS.md                          # 本仓库维护者入口说明
`-- scripts/validate_package.py        # 离线结构校验
```

## 使用前提

- 使用本地目录安装或加载插件时，将下文的 `<REPO_PATH>` 替换为本仓库的绝对路径。
- 每个平台都有自己的插件或扩展安装位置；在 Codex 中安装不会让 Claude Code、Gemini CLI 或 Copilot CLI 自动获得该 Skill。
- 安装完成后，先使用明确请求验证加载，例如：`Use engineering-workflow to review this repository task.`

Skill 的 `description` 允许具备原生发现能力的平台自动选择它，但自动选择由实际平台版本、模型和当前配置决定。对于需要确定工作流的任务，优先显式请求 `engineering-workflow`，不要把自动选择当作安装成功的唯一证据。

## 安装与使用

### Codex

1. 在 Codex 的 Plugins 界面或 CLI 的 `/plugins` 面板中添加本地 marketplace：`<REPO_PATH>\.agents\plugins`。
2. 从名为 `engineering-workflow` 的 marketplace 安装 **Engineering Workflow** 插件。
3. 确认插件或 Skill 列表中出现 `engineering-workflow`。
4. 在仓库任务中显式写 `$engineering-workflow`，或请求“use engineering-workflow”。

Codex 由 `.codex-plugin/plugin.json` 发现 `./skills/`。如果安装的是开发中的本地副本，更新 manifest 或 Skill 后按当前 Codex 版本的插件管理界面重新加载或重新安装该本地插件。

### Claude Code

使用本地插件目录启动 Claude Code：

```bash
claude --plugin-dir <REPO_PATH>
```

在该会话中请求 Claude Code 使用 `engineering-workflow` 处理一个仓库任务，并确认它加载的是 `skills/engineeringworkflow/SKILL.md`。如果你的 Claude Code 版本提供插件管理界面，也可以通过该界面选择同一目录安装或启用插件。

Claude Code 由 `.claude-plugin/plugin.json` 发现 `./skills/`。本地目录模式通常适合开发和验收；在新的会话中再次传入 `--plugin-dir`，或按本机插件管理器的方式持久安装。

### Gemini CLI

从本仓库的父目录安装本地扩展：

```bash
gemini extensions install ./EngineeringWorkflow
```

如果检出目录名称不同，改为绝对路径：

```bash
gemini extensions install <REPO_PATH>
```

确认 Gemini CLI 的扩展列表出现 `engineering-workflow`，然后在仓库任务中明确请求工程工作流。`gemini-extension.json` 指定 `GEMINI.md`，后者只导入 `@./skills/engineeringworkflow/SKILL.md`，因此 Gemini 使用的仍是同一份规范内容。

更新 Skill 后，根据当前 Gemini CLI 版本重新安装或更新该本地扩展，再开始一个新会话验证加载结果。

### GitHub Copilot CLI

将本仓库的 marketplace 目录注册到 Copilot CLI，然后安装它公开的插件：

```bash
copilot plugin marketplace add <REPO_PATH>/.agents/plugins
copilot plugin install engineering-workflow@engineering-workflow
```

确认已安装插件列表出现 `engineering-workflow`，再用明确的仓库任务请求该 Skill。此 marketplace 文件采用仓库根目录的相对插件源；移动整个仓库后应重新注册新的绝对路径。

若已安装的 Copilot CLI 版本使用交互式插件管理器而非上述命令，请在该管理器中添加 `<REPO_PATH>/.agents/plugins` 并选择同名插件。不要改写 `marketplace.json` 为某个用户目录的绝对路径。

## 验证

### 离线包校验

在仓库根目录运行：

```bash
python scripts/validate_package.py
```

该校验会验证：

- 所有 JSON manifest 可解析且包含所需标识字段；
- Codex 与 Claude Code 指向相同的 `./skills/` 目录；
- Copilot CLI marketplace 指向仓库根；
- Gemini 只导入规范化的 Skill；
- 规范 Skill 的名称和主标题仍存在；
- README 仍覆盖四个平台和唯一真源原则。

它不启动 Codex、Claude Code、Gemini CLI 或 GitHub Copilot CLI，因此不能证明这些平台中的真实安装、插件缓存或运行时自动选择。

### 平台级冒烟验证

在目标平台完成安装后，打开一个包含代码的仓库并发送类似请求：

```text
Use engineering-workflow to classify this repository task, state the proving evidence, and do not edit files.
```

检查代理是否读取 `skills/engineeringworkflow/SKILL.md`，并根据任务选择 Quick、Standard、Strict 或 Explore。此检查验证平台实际加载，不要求也不授权代理修改目标仓库。

## 维护

工作流行为的修改只应发生在 `skills/engineeringworkflow/SKILL.md` 或它链接的 `references/` 中。修改后：

1. 按 `SKILL.md` 的 `Validation` 部分阅读并应用匹配的只读压力场景：`skills/engineeringworkflow/references/pressure-scenarios.md`。
2. 若主 Skill 的规则改变了详细步骤，同步更新对应参考文件。
3. 运行 `python scripts/validate_package.py`，确认所有 adapter 仍指向唯一真源。
4. 对需要支持的平台重新加载本地插件或扩展，并进行一次平台级冒烟验证。

本仓库当前只提供本地包元数据。远程 marketplace 发布、公开仓库地址、版本发布、签名和许可证选择均需要仓库所有者另行授权。
