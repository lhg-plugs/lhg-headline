#!/usr/bin/env python3
"""lhg-headline 硬门：发布前校验标题合规（blocker 拦截）。

触发：PreToolUse / Bash。脚本先判断本次 Bash 命令是否为"发布意图"
（命令含 publish/发布/wechatsync/post/push 等发布关键词），不是则
0 开销直接放行；是则查找当前目录下的 titles.json 并跑审计脚本。

校验项：复用 scripts/audit/headline_audit.py，有 blocker 即拦截。

逃生方式（按推荐度排序）：
  1. 修好标题后重新发布（推荐）。
  2. 紧急情况：LHG_HL_HOOKS_OFF=1 <发布命令>（单次豁免本次 hook）。
  3. /plugin disable lhg-headline（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错（找不到标题文件、审计脚本异常等）时 fail-open
直接放行，不因插件自身故障骚扰用户；真正的门禁在
/lhg-headline:headline-audit。找不到 titles.json 时只做提醒式放行
（additionalContext），不拦截——因为用户可能在发布与本插件无关的内容。
零第三方依赖。
"""

import json
import os
import re
import subprocess
import sys

PUBLISH_RE = re.compile(
    r"(?<![\w-])(publish|发布|wechatsync|post-article|send-post|push-article)\b",
    re.I,
)
TITLE_NAMES = ("titles.json",)


def find_titles(project_dir):
    for name in TITLE_NAMES:
        p = os.path.join(project_dir, name)
        if os.path.isfile(p):
            return p
    try:
        cands = [f for f in os.listdir(project_dir)
                 if f.endswith(".titles.json")
                 and os.path.isfile(os.path.join(project_dir, f))]
    except OSError:
        return None
    if len(cands) == 1:
        return os.path.join(project_dir, cands[0])
    return None


def audit(plugin_root, target):
    """返回 (blockers, problems)。内部出错抛异常→调用方 fail-open。"""
    script = os.path.join(plugin_root, "scripts", "audit",
                          "headline_audit.py")
    r = subprocess.run(
        [sys.executable, script, "--target", target, "--format", "json"],
        capture_output=True, text=True, timeout=60)
    data = json.loads(r.stdout)
    blockers = [f for f in data.get("findings", [])
                if f.get("severity") == "blocker"]
    return blockers


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_HL_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # 非发布命令：快速放行
    if not PUBLISH_RE.search(command):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    titles_path = find_titles(project_dir)

    if titles_path is None:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": (
                    "提醒：本次发布未在当前目录找到 titles.json。"
                    "如果是用 lhg-headline 定的标题，请先跑 "
                    "/lhg-headline:headline-audit 确认 blocker 清零；"
                    "否则跳过此提醒。"
                ),
            }
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 0

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.join(
        project_dir)
    # hook 文件位于 <plugin>/hooks/ 下，plugin root 为其父目录
    here = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(here)

    try:
        blockers = audit(plugin_root, titles_path)
    except Exception:
        return 0  # 审计自身出错：fail-open

    if not blockers:
        return 0

    lines = [
        "发布被 lhg-headline 硬门拦截：标题审计发现 %d 个 blocker，改写后再发布。"
        % len(blockers),
        "标题文件：%s" % titles_path,
        "",
    ]
    for b in blockers[:10]:
        lines.append("- [%s] %s" % (b["rule_id"], b["title"]))
    if len(blockers) > 10:
        lines.append("…另有 %d 个" % (len(blockers) - 10))
    lines += [
        "",
        "修复方式：按 lhg-hl-compliance 改写（blocker 不许豁免）；",
        "紧急豁免（单次）：LHG_HL_HOOKS_OFF=1 <发布命令>",
    ]
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(lines),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
