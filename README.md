<!-- About 简介（推送后填写到仓库 About 栏）：
爆款标题专家：主题/内容→多平台标题公式生成→敏感词检测→点击率打分 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-headline
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, headline, copywriting, xiaohongshu -->

# lhg-headline：爆款标题专家

> **一句话介绍**：主题/内容→多平台标题公式生成（悬念/数字/对比/痛点八大公式库）→敏感词与极限词检测→点击率 rubric 打分，一次配齐；发布前硬门自动拦截违规标题。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-headline
> /plugin install lhg-headline@lhg-plugs
> ```

## 它是什么

`lhg-headline` 是一个 Claude Code 插件（plugin 为主、skill 为辅），专为"每篇内容都要起标题"的创作者设计：

- **4 个命令**（小白入口）：`headline` 一句话出标题（公式生成→合规→打分→定稿），`headline-variants` 一稿多发逐平台改写，`headline-audit` 合规自检，`headline-optimize` 旧标题诊断改写
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：标题公式库、多平台适配、合规与敏感词检测、点击率 rubric 打分
- **3 个专家 agent**：标题撰写师、合规审查员、标题诊断优化师
- **1 个硬门 hook**：发布前自动审计标题，blocker 未清零拦截发布（可一键豁免，不骚扰）
- **16 条确定性自查规则**：广告法极限词、医疗/金融/教育绝对化、标题党话术、平台字数、emoji/标点滥用、关键词堆砌，纯 Python、零第三方依赖，秒级出结果

工作流：`headline`（出标题）→ `headline-variants`（多平台改写）→ `headline-audit`（查一遍）→ 发布；老标题没量用 `headline-optimize` 诊断。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-headline:headline` | 主题/内容→5–8 条候选→合规→打分→定稿 | `/lhg-headline:headline "年终总结写作" --platform xiaohongshu` |
| `/lhg-headline:headline-variants` | 已定稿标题→多平台逐字改写 | `/lhg-headline:headline-variants ./titles.json --platforms xiaohongshu,douyin,wechat` |
| `/lhg-headline:headline-audit` | 标题合规自检（脚本 + 人工清单） | `/lhg-headline:headline-audit ./titles.json` |
| `/lhg-headline:headline-optimize` | 旧标题诊断：拆公式→定位病因→改写→新旧打分对比 | `/lhg-headline:headline-optimize "我的周报心得"` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/headline_audit.py`（16 条规则：合规 8、平台适配 2、排版 4、公式 2），零 LLM 成本；
2. 发现分三级：**blocker**（必须改写，不许豁免，发布前 hook 会拦截）、**warning**（修或写豁免理由留痕）、**nit**（顺手修）；
3. 再按 `lhg-hl-compliance` 的"承诺三问"过一遍脚本看不懂的（标题承诺 vs 内容实际增量）。

blocker 清零才算做完；为清零改规则算作弊，不许。

## 目录结构

```
lhg-headline/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：headline / headline-variants / headline-audit / headline-optimize
├── skills/                  # 4 个平台中立 skill（公式库/平台适配/合规/打分）
├── agents/                  # 3 个专家 agent（writer / compliance-reviewer / title-optimizer）
├── hooks/                   # 1 个硬门（发布前标题审计）+ 豁免说明
├── scripts/audit/           # 16 条确定性自查规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你写完一篇内容，对着空白标题栏发呆时 → 用 `/lhg-headline:headline`，一句话出 5–8 条候选
- 一篇内容要发公众号+小红书+抖音，标题不知道怎么改时 → 用 `/lhg-headline:headline-variants`
- 标题定了但怕违规（极限词、标题党、医疗金融红线）时 → 跑 `/lhg-headline:headline-audit`
- 老标题点击率差，想知道"差在哪"时 → 用 `/lhg-headline:headline-optimize` 先诊断再改

**什么时候不用：**

- 你的标题是纯品牌 slogan（如"以数据为刃，剖市场真相"）→ 本插件是"点击率"专家，品牌口号请找品牌定位方法
- 你做的是英文内容 → 公式库与合规词表均为中文语境，英文标题逻辑不同

**风险点诚实说明：**

- **分数不是真理**：rubric 打分误差约 ±2 分，Top2 分差小的时候请都拿去实测，真实流量说了算
- **极限词库是启发式**：16 条规则的词表是自建常用表，会持续扩充但不可能穷尽；误报时按"豁免流程"留痕处理，不要直接删规则
- **脚本是安检仪，人是安检员**："标题与内容是否相符"脚本只能做关键词覆盖率启发式判断，最终判定靠人的"承诺三问"
- **平台规则会变**：字数上限表为 2026-10 常见值，发布前以平台实际显示为准；发现规则变化欢迎提 issue

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-headline](https://github.com/lhg-plugs/lhg-headline) | 主题/内容→多平台标题公式生成→敏感词检测→点击率打分 | `/plugin install lhg-headline@lhg-plugs` |
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、16 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-headline/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
