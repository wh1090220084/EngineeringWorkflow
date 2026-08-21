# Engineering Workflow（中文）

[English documentation](README.md)

Engineering Workflow 是一个面向软件仓库任务的通用工程 Skill。它将计划、实现、调试、评审、验证和外部操作按风险分级，并要求用与风险相称的新鲜证据支持结论。

![Engineering Workflow 架构](docs/images/architecture.svg)

## 架构

`skills/engineeringworkflow/` 是行为定义的 **single source of truth**（唯一真源）。`SKILL.md` 保存共享路由规则，`references/` 保存按需读取的详细流程。平台文件只是发现和加载适配层，不复制工作流正文。

![交付工作流](docs/images/workflow.svg)

本包支持 Codex、Claude Code、Gemini CLI 和 GitHub Copilot CLI：

| 平台 | 入口 | 加载方式 |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json` | 向 Codex 暴露 `./skills/`。 |
| Claude Code | `.claude-plugin/plugin.json` | 向 Claude Code 暴露 `./skills/`。 |
| Gemini CLI | `gemini-extension.json`、`GEMINI.md` | 导入规范化的 `SKILL.md`。 |
| GitHub Copilot CLI | `.agents/plugins/marketplace.json` | 暴露本地 marketplace 条目。 |

## 按风险分级

Skill 会选择能够可信保护结果的最轻工作流。共享接口、安全、数据、依赖、不可逆操作、生产变更和外部副作用会触发升级。

![风险等级](docs/images/risk-levels.svg)

- **Quick**：调用方明确、局部且可逆的小改动。
- **Standard**：普通行为变更、Bug、重构或多文件工作。
- **Strict**：公共接口、安全、数据/模型、依赖、生产或外部操作。
- **Explore**：有明确学习目标的隔离性探索和未知遗留行为。

## 证据优先于结论

完成声明必须由最终编辑之后的新鲜证据支持。如果最强验证不可用，Skill 会使用最强的可重复替代证据，并说明剩余未知项。

![证据阶梯](docs/images/evidence-ladder.svg)

最终交接会记录变更文件、验证命令及结果、文档更新、安全检查、例外、已知限制和后续责任。

## 安装和使用

将下文的 `<REPO_PATH>` 替换为本仓库的绝对路径。每个平台都有自己的安装机制；在一个平台安装不会自动让其他平台获得该 Skill。

### Codex

在 Codex 的 Plugins 界面或 `/plugins` 命令中添加本地 marketplace 或插件目录，然后安装 `engineering-workflow`。确认插件或 Skill 列表中出现 **Engineering Workflow**。需要确定路由时，显式调用 `$engineering-workflow`。

包清单是 `.codex-plugin/plugin.json`，它暴露 `./skills/`。Codex 的本地插件界面和 CLI 细节可能随版本变化，请以已安装版本显示的命令为准。

### Claude Code

用本地插件目录启动会话：

```bash
claude --plugin-dir <REPO_PATH>
```

请求 Claude Code 使用 `engineering-workflow`，并确认它读取的是 `skills/engineeringworkflow/SKILL.md`。`.claude-plugin/plugin.json` 负责暴露共享的 `./skills/` 目录。

### Gemini CLI

从本仓库的父目录安装本地扩展：

```bash
gemini extensions install ./EngineeringWorkflow
```

如果目录名称不同，也可以使用绝对路径：

```bash
gemini extensions install <REPO_PATH>
```

`gemini-extension.json` 指向 `GEMINI.md`，后者导入 `@./skills/engineeringworkflow/SKILL.md`。确认扩展出现在 Gemini 的扩展列表中，再在仓库里执行冒烟验证。

### GitHub Copilot CLI

注册仓库本地 marketplace 并安装其中的插件：

```bash
copilot plugin marketplace add <REPO_PATH>/.agents/plugins
copilot plugin install engineering-workflow@engineering-workflow
```

如果你的 Copilot CLI 版本使用交互式插件管理器，请在那里添加 `<REPO_PATH>/.agents/plugins`。确认已安装插件列表中出现 `engineering-workflow`。

![平台安装路径](docs/images/platform-installation.svg)

## 验证包结构

在仓库根目录运行离线校验器：

```bash
python scripts/validate_package.py
```

它会检查 manifest JSON、规范 Skill 路径、Gemini 导入关系以及 README/图片覆盖情况。它不会启动 Codex、Claude Code、Gemini CLI 或 Copilot CLI，因此不能证明运行时加载或自动选择行为。

平台级冒烟验证可以安装包后，在仓库中发送：

```text
Use engineering-workflow to classify this repository task, state the proving evidence, and do not edit files.
```

确认平台读取 `skills/engineeringworkflow/SKILL.md`，并选择了合适的工作流等级。

## 维护 Skill

工作流行为只应修改 `skills/engineeringworkflow/SKILL.md` 或它链接的 `references/` 文件。行为变更后：

1. 阅读 `skills/engineeringworkflow/references/pressure-scenarios.md` 中匹配的场景。
2. 详细步骤发生变化时同步更新对应参考文件。
3. 运行 `python scripts/validate_package.py`。
4. 重新加载受影响的平台插件，并只报告实际运行过的平台冒烟测试。

本仓库只包含本地包元数据。远程 marketplace 发布、版本签名、版本推广和许可证选择需要仓库所有者单独授权。
