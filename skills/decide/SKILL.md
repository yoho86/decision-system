---
name: decide
description: 把一个决策记进个人决策系统。Use when the user says /decide, 记决策, 记一下这个决定, 我决定了, 帮我记个决策, log a decision, or describes a choice they just made/are making and wants it captured. Conversational tiered capture into the user's private decision data repo.
---

# /decide —— 对话式决策采集

把用户口述的一个决策，结构化写进**用户私有的决策数据仓**。

## 路径解析（每次运行最先做）

1. 读配置 `~/.config/decision-system/config.json`，取两个路径：
   - `data_dir`：用户**私有**数据仓（存 `log/ values.md rules/ models/ reviews/`）。
   - `framework_dir`：本框架仓（存 `schema.md docs/ examples/ *.example.md`）。
2. 配置缺失或 `data_dir` 不存在 → 进入 **Step 0 引导**，完成后再继续。
3. 下文 `<DATA>` = `data_dir`，`<FW>` = `framework_dir`。
   引导里用的默认值：`<DATA>` = `~/Desktop/Projects/decisions`，`<FW>` = 本 skill 所在的框架仓。

权威 schema 见 `<FW>/schema.md`。设计见 `<FW>/docs/specs/`。

## Step 0 · 首次运行即引导建数据仓（仅在路径解析失败时）

先**别**记决策，先把数据仓建起来：
- 说明：这套系统要把你的决策史存进一个【你私有】的数据仓，**不该公开**（里面是你的真实决策）。
- 问放哪（默认 `~/Desktop/Projects/decisions`）。
- 建目录；从 `<FW>` 拷模板：`values.example.md`→`<DATA>/values.md`、`rules/rules.example.md`→`<DATA>/rules/rules.md`、`models/models.example.md`→`<DATA>/models/models.md`；建 `<DATA>/log/<当年>/`、`<DATA>/reviews/`。
- `git -C <DATA> init`；问是否现在连一个【私有】GitHub 远端做备份（可跳过）。
- 写配置 `~/.config/decision-system/config.json`：`{"data_dir": "<DATA>", "framework_dir": "<FW>"}`。
- 引导完成，**接着把用户本次要记的这个决策正常写进去**（不要让引导变成死胡同）。

## 流程

### 1. 载入上下文
读 `<DATA>/values.md`（红线 + 取舍倾向）、`<DATA>/rules/rules.md`（已验证规则）、`<DATA>/models/models.md`（在库模型）。
这三份是你判断、提醒、识别模型的依据，**每次采集都先读**。

### 2. 抽取填槽
从用户的话里抽取 schema 字段。能推断的就推断，不要逐条审问。
- **`state` 记成标签数组**，用受控词表（见 `<FW>/schema.md`）：`疲惫 饥饿 情绪激动 孤独 时间紧 被催促 怕错过 信息不足 冷静`，可补自定义标签但优先词表。用户没提状态时轻问一句（"当时是赶时间还是从容决的？"）；冷静也记——它是对照组。

### 3. 自动判 tier
- 听出**高赌注 / 不可逆 / 牵连大** → `full`。
- 否则 → `micro`。
- 边界模糊时一句话确认："这个听起来不可逆且赌注不小，走完整解剖好吗？"
- `stakes` 定档按 `<FW>/schema.md` 的锚点（后果量级，不是心理感受）；用户 `values.md` 里若有「stakes 锚点」节，以它的个人化数值为准。

### 4. 只追问"缺的关键项"
不要让用户填表。只补关键缺口，**最高优先级是预测三件套**：
> 预测什么结果？几成信心？几号能验证（horizon）？

**信心用 5 档锚点**（权威定义见 `<FW>/schema.md`）：① 搏赔率 `10` / ② 不太可能 `30` / ③ 拿不准 `50` / ④ 挺有把握 `70` / ⑤ 很有把握 `90`。锚点是辅助，用户心里有更准的数就手填档外值（封顶 90，别填 100）。
- **支持 sub-50**：投资等"小概率搏大赔率"的不对称下注，低信心（如 20）是诚实且正确的，别逼用户翻转。
- **翻转只是可选自检**：仅当是真·二元对称判断、且用户信心 <50 时，提醒一句"是不是话说反了"。
- **赔率不进 confidence**：别让用户因"赔率好"抬高信心；值不值得下注是 `process_score` + 正文推理的事，两者正交。
- **一条 prediction 只赌一件事**：用户给出复合预测（"A 会发生，而且 B 也不后悔"）时，帮他挑出**最关键、一旦错决策就崩**的那条进 frontmatter，其余放正文「预测」节。复合预测没法二值判定，会弄断校准。

micro 决策问到这三件套 + `chosen` 即可。

### 5. full 决策额外两问（质量关键）
- **关键假设**："哪个假设一旦错了，这个决策就崩？"
- **预演失败 premortem**："假设 N 个月后证明这是错的，最可能的原因是？"

### 6. 规则反哺（当场提醒）
若决策的 `state` / 条件命中 `rules.md` 里某条已验证规则，**当场提醒**：
> 提醒：你有条规则——「疲惫时不碰不可逆决策」，你刚标了"疲惫"。确定继续？

若触碰 `values.md` 的红线，直接拦下并说明。

### 6b. 模型识别与理解收集
- 从用户推理里识别用到的**思维模型**，写进决策的 `models` 字段（一个没用就 `models: []`，本身是信号）。
- **用到即收录**：模型在真实决策里被用到、且用户确认确实用了，就进入"在库模型"。**不要求用户预先写定义**——理解在实践中收集。
- **记录「应用中的理解」**：把"这次用户怎么用这个模型"用一句话、带日期、链到决策 id，追加进该模型的「应用中的理解」。这是理解的原材料。
- **对照校准参照**：若本次用法与该模型「校准参照」明显跑偏（疑似误用），**提议**用户留意，但不替他判定；改不改由用户定，记进实践记录。
- 仅当用户主动认同某个**还没用过**的模型、想先收着，才放"候选区"。
- 若用户凭直觉、没套任何模型，可轻点一句"这个能用某模型再看一眼吗"，但不强迫。
- 硬规则：自下而上、用到才收，**不批量灌入**；AI 只提议与记录，**绝不替用户判定他懂了**。

### 7. 写文件
- 确定 `id`：数 `<DATA>/log/<当年>/` 里当天已有文件数，序号 +1（`YYYY-MM-DD-NNN`）。
- 路径：`<DATA>/log/<当年>/YYYY-MM-DD-NNN-简短标题.md`。
- micro 只写 frontmatter；full 按 `<FW>/schema.md` 正文结构补全。
- 结果字段 `outcome/resolved_date/process_score/lesson` 留空，`status: open`。

### 8. 提交
`git -C <DATA> add -A && git -C <DATA> commit -m "decide: <title>"`。

### 9. 回话（简短）
一句话确认：记了什么、tier、预测+信心+验证日期。不啰嗦。
**展示用 `title`（事件名），不要甩 `id`**——id 是内部机器键，只在交叉引用时用（见 `<FW>/schema.md` 展示约定）。

## 来源：从另一个项目的上下文沉淀

当采集对象是另一个项目里的决策（典型：某产品仓 `context/decisions.md` 里 locked 的决策行）：
- **预填**：从该项目上下文（`decisions.md` 的 决策/理由 列、`brief.md` 的红队/premortem、`product.md`）抽出 `chosen / 推理与假设 / premortem`，不要让用户重打。
- **打标**：`domain` = 产品 slug；`source` = 链回那条 PRD 决策行/文件，便于溯源。
- **判 tier / stakes / reversibility**：从上下文推断，请用户确认。
- **❗仍强制预测三件套**：PRD 账本没有 `prediction / confidence / horizon`，**必须当场问用户**——这是校准燃料，预填不出来；不给就不算沉淀完成。
- **回溯老决策**：若该 locked 行很久前定、结果可能已知，标 `retrospective: true`（校准自动排除），重在喂规则/模型。
- 方向单向（外部项目 → 决策系统），只写决策数据仓、不动外部项目仓库；校准按 `domain` 分桶（产品 vs 个人分开算），跨 domain 只共享规则/模型/元偏差。

## 原则
- **低摩擦优先**：能少问就少问，micro 决策 20 秒搞定。
- **预测三件套绝不可省**——它是系统的发动机。
- 今天日期以系统实际为准（用 `date` 命令取，勿臆造）。
- 当前是成熟度阶梯第 1 阶段（采集）：你是书记员，不替用户做决策、不给建议（建议是阶段 2 `/advise` 的事，数据够了再说）。
