# 个人决策系统（decision-system）

把一切决策数据化 → 不断进化 → AI 以"你自己的决策史"为参照给建议 → 最终在窄域内自主代决。

这是一套基于 **本地 Markdown + git + Claude Code 自定义 skill** 的个人决策方法论与工具。本仓库是**框架**（能力 + 方法 + 模板），开源、人人可用；**你自己的决策数据是另一个私有仓**，绝不进这里。

## 框架 vs 数据（重要）

| | 公开框架仓（本仓库） | 你的私有数据仓 |
|---|---|---|
| 内容 | skill、`schema.md`、`docs/`、`examples/`、`*.example.md` 模板 | 你的真实 `values.md / rules.md / models.md / log/ / reviews/` |
| 性质 | 能力 + 方法，大家共用 | 你的决策史，只属于你 |
| git | 公开 | **私有** |

skill 本身不含任何数据、不写死任何人的路径：它从配置 `~/.config/decision-system/config.json` 读取「数据仓在哪」，然后去那里读写。**第一次运行 `/decide` 会自动引导你创建私有数据仓**，无需手动配置。

## 安装

1. clone 本仓库（框架）：
   ```bash
   git clone <this-repo> ~/Desktop/Projects/decision-system
   ```
2. 安装两个 skill 到 Claude Code（推荐软链，便于以后随仓库更新）：
   ```bash
   ln -s ~/Desktop/Projects/decision-system/skills/decide ~/.claude/skills/decide
   ln -s ~/Desktop/Projects/decision-system/skills/retro ~/.claude/skills/retro
   ```
   （或直接 `cp -r` 复制，但更新框架后需重新复制。）
3. 开个新会话，对 Claude 说 `/decide 我决定了……`。**首次会引导你建私有数据仓**（默认 `~/Desktop/Projects/decisions`），并写好配置、挂好校验钩子。之后全自动。
4. （已有数据仓的老用户）手动挂一次校验钩子，commit 时自动跑 schema 校验：
   ```bash
   git -C <你的数据仓> config core.hooksPath ~/Desktop/Projects/decision-system/hooks
   ```
5. 打开你数据仓里的 `values.md`，把【示例】换成你自己的（30 分钟，是整套系统最值的投入），尤其「criteria 词表」——`/decide` 的 `criteria` 字段只从那里取。

> 换机器迁移：配置在 `~/.config/decision-system/config.json`（不在任何仓里），记得带上或收进 dotfiles；数据仓 clone 下来后重挂一次 core.hooksPath 即可。

## 怎么用（日常只有两个动作）

1. **做了决策，随口记**：`/decide 我决定了……，我猜……`。AI 自动判轻重、抽取填槽、只追问缺的关键项（尤其"预测+信心+验证日期"），写好文件并提交。
2. **每周 15 分钟复盘**：`/retro`。回填到期决策的真实结果（铁律：**结果坏 ≠ 决策错**，过程与结果分开打分）；跑校准与模式挖掘，提出新的"规则候选"。（曾叫 `/review`，为避开 Claude Code 内置的 PR review 命令改名。）

## 三层结构

- **价值层** `values.md`——你在优化什么（北极星 + 红线，亲手写，季度回看）。
- **决策解剖层** `log/`——每个决策一个 md（schema 见 `schema.md`）。
- **评估学习层** `reviews/` + `rules/`——校准、模式、规则，**进化主要发生在这里**。

`values` 是"目的地"（要去哪），`rules` 是"驾驶经验"（怎么开才到）。详见 `schema.md` 与 `docs/specs/`。

## 发动机

每个决策都带 `prediction + confidence + horizon`（预测 + 信心 + 验证日期）。这三件套让系统能**校准**你的判断、长出**规则**，也是将来 AI 给"以你为参照系"建议的根基。少了它，系统退化成普通日记。

## 成熟度阶梯（一级级挣来，不是开关）

1. **采集**：AI 当书记员 + 复盘师。
2. **建议**（约 50-100 个已回填决策后）：AI 调相似历史 + 你的规则 + 校准，给以你为参照系的建议。
3. **副驾**（规则验证稳定后）：AI 预填决策，你只点头/否决。
4. **自主代决**（通过三道门槛：校准达标 / 规则稳定 / 可逆且限额）：AI 在授权边界内自己执行。
   - 安全底线：**AI 永远不碰不可逆的人生大决策**；自动域结果变差会自动熔断降级；随时一键全停。

## 本仓库目录

```
schema.md             决策解剖权威定义
values.example.md     价值层模板（复制到你的数据仓后亲手填）
rules/rules.example.md     规则层模板
models/models.example.md   思维模型库模板
examples/             示例决策（脱敏教学用）
docs/specs/           设计文档
skills/decide         /decide skill（采集）
skills/retro          /retro skill（回填 + 复盘）
tools/validate.py     数据仓校验 + 健康度 + 校准统计脚本（零依赖）
hooks/pre-commit      数据仓校验钩子（core.hooksPath 指过来即生效）
reviews/review.example.md  周复盘固定模板（/retro 模式 B 产出格式）
tests/fixture/        CI 用迷你数据仓（schema/脚本/示例三者互锁）
```

你的私有数据仓（首次 `/decide` 自动生成）：

```
values.md  rules/rules.md  models/models.md   你的真实三层内容
log/YYYY/          决策文件
reviews/           周期复盘产物
```

## License

MIT，见 [LICENSE](LICENSE)。
