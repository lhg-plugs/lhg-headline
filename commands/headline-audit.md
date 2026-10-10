---
description: 标题合规自检：极限词/标题党/医疗金融绝对化/字数/emoji/关键词堆砌 14+ 条确定性规则扫描，输出 blocker/warning/nit 三级报告。
argument-hint: [titles.json路径或目录]
---

# /lhg-headline:headline-audit —— 标题合规自检

用户输入在 `$ARGUMENTS` 中：`[titles.json 路径或目录]`。缺省扫描当前目录。

## 流程

### 1. 跑脚本
```bash
python3 scripts/audit/headline_audit.py --target <目标> --format text
```
14+ 条规则（见脚本头部规则表），零第三方依赖。exit code 语义：2=有 blocker，1=有 warning，0=干净。

### 2. 分级处理
- **blocker**（极限词/标题党/医疗金融绝对化）：必须改写，不许豁免。
- **warning**（字数临界/emoji 多/关键词堆砌/钩子迟到）：修，或按 lhg-hl-compliance 第 4 节写豁免理由留痕。
- **nit**（半角全角混用/无钩子公式）：顺手修。

### 3. 人工复核清单（脚本查不到的）
- 承诺三问：3 分钟可得性、数字有出处、无错误预期。
- 谐音规避字（"蕞"替"最"）：看到按恶意规避处理。
- 金融/医疗类：务必人工终审，脚本只是安检仪。

### 4. 交付
- blocker 清零才算过；输出合规报告（含豁免留痕记录）。

## 硬规则
- blocker 未清零发布 → 不许（发布前 hook 会拦截）。
- 为过检改规则 → 作弊，不许。
