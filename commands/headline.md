---
description: 主题/内容→多平台标题公式生成：8 大公式出 5–8 条候选→敏感词/极限词检测→点击率 rubric 打分排序，输出定稿标题。
argument-hint: [主题或内容摘要] [--platform xiaohongshu] [--count 6]
---

# /lhg-headline:headline —— 一句话出爆款标题

用户输入在 `$ARGUMENTS` 中：`[主题或内容摘要] [--platform 平台] [--count 条数]`。平台缺省 `xiaohongshu`，条数缺省 6。

全程加载 `lhg-hl-formula`（公式库）、`lhg-hl-platform`（平台适配）、`lhg-hl-compliance`（合规）、`lhg-hl-score`（打分）。标题生成可分派给 `headline-writer` agent，定稿前必须走 `headline-audit`。

## 流程

### 1. 确认输入
- 主题：用户给的一句话主题，或粘贴的内容全文/摘要（全文优先，有全文才能做"承诺三问"）。
- 只问一个最关键的问题："这篇是给谁看的？"（不知道就按"泛兴趣读者"默认走，不许连环追问）。
- 平台：`--platform` 指定；多平台需求转 `headline-variants`。

### 2. 公式生成（加载 lhg-hl-formula）
- 用 ≥3 个不同公式生成 5–8 条候选，输出 `titles.json`（含公式标注、钩子位置、字数）。
- 钩子必须落在该平台前置位内（小红书前 12–15 字）。
- 每条配 30 字内"创作要点"。

### 3. 合规扫描（加载 lhg-hl-compliance）
- 跑 `scripts/audit/headline_audit.py --target <titles.json 所在目录>`。
- blocker 项必须改写消除；warning 项修或写豁免理由（留痕）。

### 4. 打分排序（加载 lhg-hl-score）
- 五维 rubric 打分（20 分制），输出排序 + 每条一句话改写建议。
- 总分 <10 的淘汰；Top2 分差 ≤2 分建议都实测。

### 5. 交付
- 交付 `titles.json`（定稿 Top1 标 `final: true`）+ 打分表 + 合规报告。
- **发布前 hook 会自动拦截含 blocker 的标题**（见 hooks 说明）。被拦截就改标题，不要关 hook。

## 硬规则
- blocker 未清零就定稿 → 不许（这是本插件与"标题党生成器"的分界线）。
- 一次只用一个公式出 5 条 → 不许（等于没给选择）。
- 为通过自检改审计脚本规则 → 作弊，不许。
