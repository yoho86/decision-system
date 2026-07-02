---
name: retro
description: 回填决策结果 + 周期复盘个人决策系统。Use when the user says /retro, 复盘, 回填结果, 决策复盘, 跑校准, 周复盘, review my decisions, or wants to record outcomes / analyze their decision history in their private decision data repo. (曾用名 /review，为避开内置 PR review 命令改名)
---

# /retro —— 回填结果 + 周期复盘 + 学习

对**用户私有的决策数据仓**做结果回填与进化分析。两种模式，先问用户走哪个（或都做）。

## 路径解析（每次运行最先做）

读配置 `~/.config/decision-system/config.json`，取 `data_dir`（私有数据仓）与 `framework_dir`（框架仓）。
- 配置缺失或 `data_dir` 不存在 → 提示用户先跑一次 `/decide`（它会引导建数据仓），本 skill 不重复实现引导。
- 下文 `<DATA>` = `data_dir`，`<FW>` = `framework_dir`。权威 schema 见 `<FW>/schema.md`。
- 今天日期用 `date` 命令取，勿臆造。

## 先跑脚本（两种模式都是）

`python3 <FW>/tools/validate.py`——输出三块：① frontmatter 校验错误（有错先修再继续）② 到期未回填清单（模式 A 的输入）③ 校准与切片统计（模式 B 的输入）。**统计一律以脚本输出为准，不要手算**；脚本跑不了再退回手算并告知用户。

---

## 模式 A · 回填结果

1. 用脚本输出的"到期未回填"清单（`status: open` 且 `horizon` ≤ 今天）。
2. 逐个问用户真实结果。对每个回填：
   - `outcome`：`as-expected` / `better` / `worse` / `mixed`（真实结果 vs 当初 `prediction`）。
   - `resolved_date`：今天。
   - `process_score`（1-5）：**抛开运气，决策"过程"本身好不好**。
   - `lesson`：一句话沉淀。
   - `status: resolved`。
   - full 决策：在正文"复盘"节写"预测 vs 现实 / 过程 vs 结果 / 规则候选"。
3. **铁律——过程与结果分离**：明确告诉用户"结果坏 ≠ 决策错"。运气坏但当初信息下过程合理，`process_score` 照样给高分；反之结果好但靠瞎蒙，过程分要低。这是避免"被结果反向洗脑"的核心。
4. 提交：`git -C <DATA> commit -am "retro: 回填 N 个决策"`。

---

## 模式 B · 周期复盘（建议每周）

读全部 `resolved` 决策，跑三类分析，产出写到 `<DATA>/reviews/YYYY-Www.md` 并提交。

### 1. 校准
按 `confidence` 的 **5 档**（`10 / 30 / 50 / 70 / 90`，档外手填值归最近档）分桶，算每桶里预测**真的成真**（对二元预测 ≈ outcome `as-expected`/`better`）的实际比例，对照该档名义概率，指出哪段**系统性高估/低估**。数据以 `tools/validate.py` 输出为准；**`retrospective: true` 的决策自动排除**（后见之明污染）。
⚠️ **不对称下注**（低信心、高赔率，如投资）：低 confidence 落空本就正常，校准只看"你标 30 的事是否约 30% 成真"，**不拿 outcome 好坏评判决策对错**——决策对错归 `process_score`。

### 2. 模式挖掘
按 `state / mode / domain / stakes` 及其组合切片，找 `process_score` 系统性偏低或偏高的条件。
例："疲惫 + gut 模式" 平均分明显低于整体。`state` 是标签数组（受控词表见 `<FW>/schema.md`），按单个标签及组合切；发现同义异形标签（如"被催"vs"被催促"）提议用户归一。

### 3. 规则候选
把统计上有信号的模式写成 if-then **候选**，登记样本数与依据，列进复盘文件，并问用户是否升级进 `<DATA>/rules/rules.md`（确认才升）。
同时回测 `rules.md` 已验证规则：命中率持续下降的，建议移到"已退役"。

### 4. 价值漂移检测
若发现用户对"同类结果"的好坏判断在前后期反转（同样的 outcome，早期记为满意、近期记为不满），提示可能该更新 `<DATA>/values.md`。

### 5. 模型：理解结晶 + 效用分析
读 `<DATA>/models/models.md`，对带 `models` 字段的决策做：
- **理解结晶**：把每个模型「应用中的理解」里的多条实践记录，归纳成一句"当前小结"（用户确认才定）。理解来自实践积累，**不是预先声明**。
- **校准比对**：当前小结 vs「校准参照」vs 实战 `outcome`——若常误用某模型，说明理解有缺口，**提议**修订（用户同意才改），并补充 / 调整校准参照（可由 AI / 学科提供，**避免只凭自我理解**）。
- **效用分析**：哪些模型 → 高/低 `process_score`；多模型叠加（格栅效应）是否更优；凭直觉（`models: []`）的决策整体表现如何。
- **养护**：常用模型补踩坑；从不用的提议剪掉。模型增删一律**用户确认后**才动 `models.md`。

---

## 原则
- 样本太少（如 < 20 个 resolved）时，明说"统计还不可靠，只做趋势提示，别急着定规则"。
- 规则的增删一律**用户确认后**才动 `rules.md`。
- 复盘要短、可执行：少堆数字，多给"下一步改什么"。
- **展示用 `title`（事件名），不要甩 `id`**——id 只在文件内部交叉引用时用（见 `<FW>/schema.md` 展示约定）。
