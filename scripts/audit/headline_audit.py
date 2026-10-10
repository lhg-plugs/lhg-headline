#!/usr/bin/env python3
"""lhg-headline 确定性标题审计：16 条规则，零第三方依赖。

扫描 titles.json（或目录下同名文件 / 纯文本标题文件），检查广告法极限词、
医疗/金融/教育绝对化表述、标题党话术、平台字数上限、emoji/标点滥用、
关键词堆砌、标题重复、标题与内容不符风险。

用法：
    python3 headline_audit.py --target <titles.json|目录> [--format json|text]
        [--platform xiaohongshu|douyin|wechat|bilibili|zhihu|shipinhao]
        [--fail-on blocker|warning|nit]

退出码：2=有 blocker，1=有 warning（无 blocker），0=干净。
规则文案均为本项目原创（标题公式与合规方法论见 skills/，独立撰写，
未复制任何第三方原文；详见仓库 ATTRIBUTION.md）。
"""

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata

VERSION = "1.0.0"
TOOL = "lhg-headline/headline-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build"}

# 平台字数上限（中文字符，含标点；2026-10 常见值）
PLATFORM_LIMITS = {
    "xiaohongshu": 20,
    "douyin": 30,
    "wechat": 64,       # 公众号；卡片单行约 16 字
    "shipinhao": 30,
    "bilibili": 40,
    "zhihu": 30,
}

# ---- 词表（启发式常用表，持续扩充；误报走豁免流程） ----
AD_SUPERLATIVES = [
    "最便宜", "最划算", "最好", "最强", "最牛", "最火", "最快", "最早", "最新",
    "第一", "首家", "首个", "首选", "顶级", "极致", "巅峰", "之最", "之首",
    "国家级", "全球", "世界级", "全国", "全网第一", "全网首家",
    "100%", "绝无仅有", "史无前例", "前无古人", "永久", "唯一",
    "点击领钱", "假一赔十",
]
# "最"单字需谨慎：只在 "最X" 形容词结构中判，排除"最后/最终/最少需要"等
AD_SUPERLATIVE_SINGLE_RE = re.compile(r"最(?![后终少多])[\u4e00-\u9fa5]{1,2}")

MED_ABSOLUTE = ["根治", "根除", "治愈", "药到病除", "无效退款", "包治百病"]
FIN_ABSOLUTE = ["必涨", "稳赚不赔", "保本", "零风险", "闭眼买", "只涨不跌",
                "保底收益", "无风险套利"]
EDU_ABSOLUTE = ["包过", "保过", "保录", "内部押题", "交钱就过"]

CLICKBAIT_BLOCKER = [
    "震惊了", "震惊！", "万万没想到", "出大事了", "不转不是中国人",
    "再不看就晚了", "不看后悔终身", "看完沉默了",
]
CLICKBAIT_HOLLOW = ["99%的人", "最后一个绝了", "最后一名震惊", "99%都不知道"]

PROMISE_WORDS = ["揭秘", "内幕", "独家", "首次披露", "惊天秘密"]
BIG_CLAIM_NUM = ["1000倍", "10000倍", "一夜暴富", "月入十万", "百万富翁",
                 "财务自由", "一夜回春"]

HOOK_WORDS = [
    "原来", "居然", "没人告诉你", "别再", "踩坑", "翻车", "血亏", "避雷",
    "?", "？", "!", "！", "打工人", "新手", "姐妹", "收藏", "第",
    "以前", "现在", "对比", "实测", "你以为", "别被",
]
AUDIENCE_WORDS = ["打工人", "新手", "姐妹", "爸妈", "妈妈", "学生党", "宝妈",
                  "职场", "创业者", "小白"]

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U0001F000-\U0001F2FF\ufe0f\u200d]"
)


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line",
                 "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return ""


def char_count(text):
    """中文字符计数：emoji 按 2 计（小红书实测占位），其余按 1 计。"""
    n = 0
    for ch in text:
        n += 2 if EMOJI_RE.match(ch) else 1
    return n


def load_titles(target):
    """返回 [(text, file, line, meta_dict)]。"""
    items = []

    def add(text, f, ln, meta=None):
        t = (text or "").strip()
        if t and not t.startswith("#"):
            items.append((t, f, ln, meta or {}))

    if os.path.isfile(target):
        files = [target]
    else:
        files = []
        for root, dirs, fns in os.walk(target):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in sorted(fns):
                low = fn.lower()
                if low == "titles.json" or low.endswith(".titles.json"):
                    files.append(os.path.join(root, fn))
                elif low.endswith((".txt", ".md")) and "title" in low:
                    files.append(os.path.join(root, fn))

    for fp in files:
        if fp.lower().endswith(".json"):
            try:
                data = json.loads(read_text(fp))
            except Exception:
                items.append(("__BADJSON__", fp, 0, {}))
                continue
            if isinstance(data, dict):
                platform = data.get("platform")
                content = data.get("content", "")
                for i, t in enumerate(data.get("titles", [])):
                    if isinstance(t, dict):
                        add(t.get("text", ""), fp, i + 1,
                            {"platform": t.get("platform", platform),
                             "content": t.get("content", content)})
                    else:
                        add(str(t), fp, i + 1,
                            {"platform": platform, "content": content})
            elif isinstance(data, list):
                for i, t in enumerate(data):
                    add(str(t) if not isinstance(t, dict)
                        else t.get("text", ""), fp, i + 1, {})
        else:
            for ln, line in enumerate(read_text(fp).split("\n"), 1):
                add(line, fp, ln)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--platform", default="xiaohongshu",
                    choices=list(PLATFORM_LIMITS))
    ap.add_argument("--fail-on", default="blocker",
                    choices=["blocker", "warning", "nit"])
    args = ap.parse_args()

    findings = []
    sev_rank = {"blocker": 3, "warning": 2, "nit": 1}

    def add(rule_id, severity, category, title, f, ln, snippet, detail):
        findings.append(Finding(rule_id, severity, category, title, f, ln,
                                snippet, detail))

    items = load_titles(args.target)
    if not items:
        print("未找到标题输入（titles.json 或 *title*.txt/md）", file=sys.stderr)
        return 2

    for text, f, ln, meta in items:
        if text == "__BADJSON__":
            add("HL-JSON-001", "blocker", "格式", "titles.json 不是合法 JSON",
                f, ln, "", "请检查 JSON 语法后重跑")
            continue
        platform = (meta.get("platform") or args.platform)
        limit = PLATFORM_LIMITS.get(platform, 20)
        content = meta.get("content", "")
        short = text if len(text) <= 30 else text[:30] + "…"

        # HL-LEN-001 平台字数上限
        if char_count(text) > limit:
            add("HL-LEN-001", "warning", "平台适配",
                "标题超 %s 字数上限（%d/%d 字）" % (platform, char_count(text), limit),
                f, ln, short, "降级改写：砍修饰留数字+结果，钩子前置")

        # HL-HOOK-001 钩子迟到
        head = text[:12]
        if not any(w in head for w in HOOK_WORDS) and not re.search(r"\d", head):
            add("HL-HOOK-001", "warning", "钩子",
                "前 12 字无钩子：读者在折叠线前看不到停留理由",
                f, ln, short, "把数字/疑问/人群词前移到前 12 字内")

        # HL-ADWORDS-001 广告法极限词
        hits = [w for w in AD_SUPERLATIVES if w in text]
        if not hits and AD_SUPERLATIVE_SINGLE_RE.search(text):
            m = AD_SUPERLATIVE_SINGLE_RE.search(text)
            hits = ["最" + m.group(0)[1:]]
        if hits:
            add("HL-ADWORDS-001", "blocker", "合规",
                "广告法极限词：%s" % "、".join(hits[:3]),
                f, ln, short, "换成可验证的限定词（如“最便宜”→“比同级便宜 30%”，须有依据）")

        # HL-MED-001 / HL-FIN-001 / HL-EDU-001 行业绝对化
        for rid, words, cat in [
                ("HL-MED-001", MED_ABSOLUTE, "医疗"),
                ("HL-FIN-001", FIN_ABSOLUTE, "金融"),
                ("HL-EDU-001", EDU_ABSOLUTE, "教育")]:
            h = [w for w in words if w in text]
            if h:
                add(rid, "blocker", "合规",
                    "%s绝对化表述：%s" % (cat, "、".join(h[:3])),
                    f, ln, short, "监管红线，必须改写为事实陈述")

        # HL-CLICKBAIT-001 标题党高危话术
        h = [w for w in CLICKBAIT_BLOCKER if w in text]
        if h:
            add("HL-CLICKBAIT-001", "blocker", "合规",
                "标题党高危话术：%s" % "、".join(h[:3]),
                f, ln, short, "承诺的信息增量须≤内容实际增量，否则改写")

        # HL-CLICKBAIT-002 悬空话术
        h = [w for w in CLICKBAIT_HOLLOW if w in text]
        if h:
            add("HL-CLICKBAIT-002", "warning", "合规",
                "悬空话术（无法验证）：%s" % "、".join(h[:3]),
                f, ln, short, "数字须有出处，否则删掉")

        # HL-NUM-001 夸张数字
        h = [w for w in BIG_CLAIM_NUM if w in text]
        if h:
            add("HL-NUM-001", "warning", "合规",
                "夸张收益表述：%s" % "、".join(h[:3]),
                f, ln, short, "做不到的承诺是最贵的标题，降级为可验证表述")

        # HL-EMOJI-001 emoji 滥用
        emojis = EMOJI_RE.findall(text)
        if len(emojis) >= 4 or re.search(
                r"([\U0001F300-\U0001FAFF\U00002600-\U000027BF]){3}", text):
            add("HL-EMOJI-001", "warning", "排版",
                "emoji 滥用（%d 个）" % len(emojis),
                f, ln, short, "1–2 个点缀即可，过多显廉价且占字数位")

        # HL-PUNCT-001 标点滥用
        if re.search(r"[!！]{3,}|\?{3,}|？{3,}", text) or \
                len(re.findall(r"[!！]", text)) >= 3:
            add("HL-PUNCT-001", "warning", "排版",
                "感叹/疑问号滥用", f, ln, short, "情绪靠钩子不靠标点，最多 1 个")

        # HL-KEYWORD-001 关键词堆砌
        words = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
        dup = [w for w in set(words)
               if words.count(w) >= 3 and len(w) >= 2]
        if dup:
            add("HL-KEYWORD-001", "warning", "排版",
                "关键词堆砌：%s 出现 ≥3 次" % "、".join(dup[:3]),
                f, ln, short, "删冗余，信息密度是点击率的朋友")

        # HL-MISMATCH-001 标题与内容不符风险
        if any(w in text for w in PROMISE_WORDS):
            if not content:
                add("HL-MISMATCH-001", "warning", "合规",
                    "承诺词（揭秘/内幕/独家）但未提供内容供核验",
                    f, ln, short, "请提供内容做“承诺三问”，或删掉承诺词")
            else:
                kw = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
                hit = sum(1 for w in kw if w in content)
                if kw and hit / len(kw) < 0.3:
                    add("HL-MISMATCH-001", "warning", "合规",
                        "标题关键词在内容中覆盖率低（%.0f%%），文不对题风险"
                        % (hit / len(kw) * 100),
                        f, ln, short, "标题承诺须在内容前 1/3 处兑现")

        # HL-FORMULA-001 无钩子公式
        has_digit = bool(re.search(r"\d", text))
        has_q = ("?" in text or "？" in text)
        has_aud = any(w in text for w in AUDIENCE_WORDS)
        has_hook = any(w in text for w in HOOK_WORDS)
        if not (has_digit or has_q or has_aud or has_hook):
            add("HL-FORMULA-001", "nit", "公式",
                "未检测到钩子元素（数字/疑问/人群/钩子词）",
                f, ln, short, "套一个公式：数字量化是最稳的起手式")

        # HL-CHAR-001 半角全角混用
        if re.search(r"[\u4e00-\u9fa5][,!?;:][\u4e00-\u9fa5]", text):
            add("HL-CHAR-001", "nit", "排版",
                "中文间夹半角标点", f, ln, short, "统一为全角标点")

    # HL-DUP-001 同一批标题互相重复
    texts = [(t, f, ln) for t, f, ln, _ in items if t != "__BADJSON__"]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            r = difflib.SequenceMatcher(None, texts[i][0],
                                        texts[j][0]).ratio()
            if r > 0.8:
                add("HL-DUP-001", "warning", "多样性",
                    "两条标题相似度 %.0f%%，疑似同一公式换词" % (r * 100),
                    texts[j][1], texts[j][2],
                    texts[j][0][:30], "换公式重出一版，不许凑数")

    findings.sort(key=lambda x: (-sev_rank[x.severity], x.rule_id))
    summary = {
        "tool": TOOL, "version": VERSION,
        "target": args.target, "platform": args.platform,
        "titles_checked": len([i for i in items if i[0] != "__BADJSON__"]),
        "rules_run": 16,
        "blocker": sum(1 for x in findings if x.severity == "blocker"),
        "warning": sum(1 for x in findings if x.severity == "warning"),
        "nit": sum(1 for x in findings if x.severity == "nit"),
    }

    if args.format == "json":
        out = {"summary": summary,
               "findings": [x.to_dict() for x in findings]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("lhg-headline 标题审计报告（%d 条标题，%d 条规则）"
              % (summary["titles_checked"], summary["rules_run"]))
        print("blocker=%d warning=%d nit=%d"
              % (summary["blocker"], summary["warning"], summary["nit"]))
        print("=" * 60)
        for x in findings:
            print("[%s] %s %s" % (x.severity.upper(), x.rule_id, x.title))
            print("    %s:%s %s" % (x.file, x.line, x.snippet))
            print("    → %s" % x.detail)
        if not findings:
            print("干净：未发现问题。")

    level = {"blocker": 3, "warning": 2, "nit": 1}[args.fail_on]
    worst = max([sev_rank[x.severity] for x in findings], default=0)
    if worst >= 3:
        return 2
    if worst == 2:
        return 1 if level <= 2 else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
