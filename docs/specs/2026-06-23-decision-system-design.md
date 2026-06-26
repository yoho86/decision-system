# 个人决策系统 · 设计文档

- 日期：2026-06-23
- 状态：已确认，进入实现
- 形态：本地 Markdown + git + Claude Code 自定义 skill（方案 A）

---

## 1. 目标与愿景

把一切决策**数据化**，让系统能**不断进化**，最终让 AI 基于"我自己的决策史"给出**以我为参照系**的有价值建议，并在被验证过的、可逆、限额的窄域里**自主代我决策**。

核心现实判断：**瓶颈从来不是 AI 是否聪明，而是是否有足够多、足够诚实、且带"真实结果"的结构化决策数据。** 因此本系统 80% 的成败取决于"采集与复盘"是否被设计得让人**愿意长期坚持**。

## 2. 范围

- v1 聚焦**高频、可重复的操作决策**（最容易建反馈闭环）。
- 但采用一套**领域无关的通用框架**，任何决策都能装进同一批"槽位"，将来无痛扩展到低频大决策。

## 3. 三层框架

| 层 | 名称 | 职责 | 变化速度 | 来源 |
|---|---|---|---|---|
| 1 | 价值层 `values.md` | 我在优化什么 / 红线 / 取舍倾向 | 几乎不变 | 自上而下，我定 |
| 2 | 决策解剖层 `log/` | 统一记录任何决策的骨架 | 持续增长 | 采集 |
| 3 | 评估与学习层 `reviews/` `rules/` | 校准、模式挖掘、规则提炼 | 不断进化 | 自下而上，数据长 |

### values vs rules（最易混，必须分清）

- **value**：我想要什么 / 什么算"好"。规范性，不可被数据证伪，是尺子。例："长期复利 > 短期收入"。
- **rule**：在什么情况下我该怎么做。经验性，可被数据证伪，是手段。例："疲惫状态下不做不可逆决策——历史上这类决策 process_score 平均低 2 分"。
- 分辨测试：**能拿数据跟它吵架吗？** 能 → rule；不能、纯属取向 → value。
- 链条：`values（总） → criteria（每次取用） → outcome 拿 values 当尺子判好坏 → 长出 rules`。
- 约束：rule 必须服务于 values；values 一变，相关 rules 需重新验证。

## 4. 数据结构（决策解剖 Schema）

每个决策一个 markdown 文件，置于 `log/YYYY/YYYY-MM-DD-NNN-标题.md`。
frontmatter 机器可读（喂统计/校准），正文人可读（深度复盘）。权威定义见 `schema.md`。

关键字段：`id / title / domain / tier / stakes / reversibility / state / mode / criteria / chosen / prediction / confidence / horizon / status`，结果揭晓后回填 `outcome / process_score / lesson`。

**发动机：`prediction + confidence + horizon` 三件套**——让系统能校准、能学习，是"以我为参照系"建议的根基。没有它，系统退化成普通日记。

## 5. 分级采集（解决"高频 × 丰富骨架"的死结）

- **micro 微记录**（高频小决策，约 20 秒）：只填 frontmatter，4 个不可省 `chosen / prediction / confidence / horizon`。
- **full 完整解剖**（高赌注 / 不可逆）：完整 frontmatter + 正文（含关键假设、premortem）。
- AI 根据描述里的赌注与可逆性**自动判 tier**，只追问缺的关键项。

## 6. 工作流

### `/decide`（采集）
1. 用户说人话 → 2. AI 抽取填槽、自动判 tier → 3. 只追问缺的关键项（最优先预测三件套）→ 4. full 额外问"关键假设"与"premortem" → 5. 写文件 + 分配 id + git commit → 6. 当场调出相关 rules 提醒。

### `/review`（回填 + 复盘 + 学习）
- **模式 A 回填**：列出 horizon 已到、status: open 的决策，填 `outcome / process_score / lesson`。铁律：**过程与结果分离**（结果坏 ≠ 决策错）。
- **模式 B 周期复盘**：跑校准曲线、按 state/mode/domain/stakes 切片做模式挖掘、产出 rule 候选，写入 `reviews/YYYY-Www.md`。

## 7. 进化引擎（三条回路）

1. **校准回路**：预测 vs 现实 → 各类判断可信度 → AI 据此给判断打折/加成。
2. **模式→规则回路**：切片统计 → 规则候选 → 验证 → `rules.md`；规则持续受检，命中率掉了就退役。
3. **价值漂移检测**：对"同类结果"的好坏判断反转时，提示更新 `values.md`。

## 8. 成熟度阶梯（通往"AI 替我决"）

| 阶段 | 触发条件 | AI 角色 |
|---|---|---|
| 1 采集 | 现在起，前 8 周 | 书记员 + 复盘师 |
| 2 建议 | 约 50-100 个已回填决策后 | 顾问：调相似历史+规则+校准，给以我为参照系的建议 |
| 3 副驾 | 规则命中率达标 | 预填 chosen/prediction/confidence，我只点头/否决 |
| 4 自主代决 | 通过三道门槛 | 在授权边界内自己执行 |

### 自主代决安全设计
- **授权边界（decision mandate）**：领域 + 赌注上限 + 仅限可逆 + 金额封顶 + 必须成立的规则；越界升级。
- **三道门槛**：① 校准达标 ② 规则稳定 ③ 可逆且限额。
- **人在回路退化梯度**：事后通知 → 事前确认 → 全自动，只能逐级上移。
- **熔断 + kill switch**：结果变差/校准漂移则自动降回"事前确认"；随时一键全停。
- **全程留痕**：自动决策仍按 schema 记录（`mode: auto`），进同一学习回路、可审计。
- **底线：AI 永远不碰不可逆的人生大决策。**

## 9. 目录结构

```
~/Desktop/Projects/decisions/                      # git 仓库，事实源
  README.md                       # 系统说明
  values.md                       # 第1层 价值层
  schema.md                       # 决策解剖权威定义
  log/2026/                       # 每个决策一个 md
  reviews/                        # 周期复盘产物
  rules/rules.md                  # 经验证的个人决策规则
  examples/                       # 示例决策文件
  docs/specs/                     # 设计文档
```
采集/复盘用全局 skill：`~/.claude/skills/decide/`、`~/.claude/skills/review/`。

## 10. 实现清单（v1）

- [x] 仓库结构 + git init
- [ ] `schema.md` 权威 schema
- [ ] `values.md` 引导模板
- [ ] `rules/rules.md` 初始结构
- [ ] `examples/` 一个完整示例决策
- [ ] `README.md`
- [ ] `/decide` skill
- [ ] `/review` skill
- [ ] 首次提交

后续阶段（2/3/4）随数据积累再迭代，不在 v1 范围。
