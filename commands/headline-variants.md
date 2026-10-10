---
description: 一稿多发：已定稿标题→多平台逐字改写（字数/钩子位/黑话/审核红线），每平台 2–3 版。
argument-hint: [标题或titles.json路径] [--platforms xiaohongshu,douyin,wechat]
---

# /lhg-headline:headline-variants —— 多平台标题改写

用户输入在 `$ARGUMENTS` 中：`[标题或 titles.json 路径] [--platforms 平台列表]`。平台缺省 `xiaohongshu,douyin,wechat`。

加载 `lhg-hl-platform`（第 3–4 节）与 `lhg-hl-compliance`（第 4 节各平台红线）。

## 流程

### 1. 定内核
- 把原标题压缩成一句话内核（<20 字）：谁、得到什么/避开什么坑。改写全程回代检验内核不变。

### 2. 逐平台改写
- 按 lhg-hl-platform 第 3 节字数表：每平台 2–3 版。
- 改写三件套：砍字数（降级改写，不许注水）→ 钩子前置（折叠线内）→ 换平台黑话。
- 多发版本之间至少改 30% 的字，避免被判重复内容。

### 3. 逐平台合规
- 跑 `headline_audit.py --platform <平台>`（脚本按平台上限判定字数）。
- 医疗/金融类每平台单独过审，不许跨平台直发。

### 4. 交付
- 输出 `titles-<平台>.json` + "改了什么"对照表（字数/钩子位/黑话替换说明）。

## 硬规则
- 同一标题全平台通发 → 不许。
- 超字数"差不多" → 不许，超 1 个字也是超。
