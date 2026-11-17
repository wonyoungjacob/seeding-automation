"""B. DM 전송 큐 — 전송 버튼을 누르기 직전까지를 준비한다.

인스타그램 공식 API는 처음 연락하는 사람에게 DM을 보낼 수 없다.
그래서 누구에게 보낼지 고르고, 문안을 만들고, DM 창을 여는 것까지
자동으로 하고, 붙여넣기와 전송만 사람이 한다.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .collect import load_results, normalize_username, read_text, write_csv

LOG_COLUMNS = ["계정", "채널", "연락일"]
QUEUE_COLUMNS = ["계정", "프로필 링크", "DM 링크(모바일)", "팔로워", "비고", "문안"]


def load_log(path: Path) -> dict[str, dict]:
    """연락 기록을 읽는다. 여기에 있는 계정은 큐에 다시 넣지 않는다."""
    path = Path(path)
    if not path.exists():
        return {}
    log = {}
    for row in csv.DictReader(read_text(path).splitlines()):
        username = normalize_username(row.get("계정", ""))
        if username:
            log[username] = {"계정": username, "채널": row.get("채널", ""), "연락일": row.get("연락일", "")}
    return log


def import_sent(sent_path: Path, log_path: Path) -> int:
    """큐 페이지에서 내려받은 "보낸 목록"을 연락 기록에 합친다. 새로 추가된 수를 돌려준다."""
    log = load_log(log_path)
    before = len(log)
    for username, row in load_log(sent_path).items():
        log.setdefault(username, row)
    write_csv(log_path, LOG_COLUMNS, list(log.values()))
    return len(log) - before


def render_message(template: str, username: str) -> str:
    return template.replace("{계정}", username).strip()


def pick_targets(results_path: Path, log_path: Path, limit: int) -> tuple[list[dict], int, int]:
    """DM 대상 중 아직 연락하지 않은 계정을 팔로워가 많은 순으로 limit개 고른다.

    (오늘 보낼 대상, 이미 연락해서 뺀 수, 다음으로 미룬 수)를 돌려준다.
    """
    log = load_log(log_path)
    candidates = [r for r in load_results(results_path).values() if r["다음 행동"] == "DM"]
    fresh = [r for r in candidates if r["계정"] not in log]

    def followers(row: dict) -> int:
        try:
            return int(row["팔로워"])
        except (TypeError, ValueError):
            return 0

    fresh.sort(key=followers, reverse=True)
    return fresh[:limit], len(candidates) - len(fresh), max(0, len(fresh) - limit)


def build(results_path: Path, template_path: Path, log_path: Path, out_html: Path, limit: int = 20) -> dict:
    """큐 페이지(HTML)와 같은 내용의 CSV를 만든다."""
    template = read_text(template_path)
    targets, already, later = pick_targets(results_path, log_path, limit)

    items = []
    for row in targets:
        username = row["계정"]
        items.append(
            {
                "u": username,
                "followers": row["팔로워"],
                "bio": row["소개글"],
                "note": row["비고"],
                "msg": render_message(template, username),
            }
        )

    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    data = {"created": datetime.now().strftime("%Y-%m-%d %H:%M"), "items": items}
    # 소개글은 남이 쓴 글이므로 페이지 코드로 해석되지 않게 "<"를 바꿔서 넣는다.
    payload = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    out_html.write_text(PAGE.replace("__DATA__", payload), encoding="utf-8")

    write_csv(
        out_html.with_suffix(".csv"),
        QUEUE_COLUMNS,
        [
            {
                "계정": it["u"],
                "프로필 링크": f"https://www.instagram.com/{it['u']}/",
                "DM 링크(모바일)": f"https://ig.me/m/{it['u']}",
                "팔로워": it["followers"],
                "비고": it["note"],
                "문안": it["msg"],
            }
            for it in items
        ],
    )
    return {"오늘 보낼 대상": len(items), "이미 연락해서 뺀 계정": already, "다음으로 미룬 계정": later}


PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DM 전송 큐</title>
<style>
  :root { --bg:#f6f5f1; --card:#fff; --ink:#1d1c1a; --sub:#6b6860; --line:#dedbd2; --accent:#2f5d50; --done:#e7efe9; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#161614; --card:#201f1c; --ink:#eceae3; --sub:#a09c91; --line:#35332e; --accent:#7fb8a4; --done:#1f2a25; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 system-ui, "Malgun Gothic", sans-serif; }
  header { position:sticky; top:0; background:var(--bg); border-bottom:1px solid var(--line); padding:14px 16px; z-index:1; }
  .wrap { max-width:760px; margin:0 auto; }
  h1 { font-size:20px; margin:0 0 4px; }
  .bar { display:flex; gap:12px; align-items:center; justify-content:space-between; flex-wrap:wrap; }
  #summary { color:var(--sub); margin:0; }
  .how { color:var(--sub); font-size:14px; margin:14px 16px 0; }
  main { padding:8px 16px 48px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px; margin-top:12px; }
  .card.sent { background:var(--done); }
  .top { display:flex; justify-content:space-between; gap:12px; align-items:baseline; flex-wrap:wrap; }
  .name { font-weight:700; font-size:17px; }
  .meta { color:var(--sub); font-size:14px; }
  .bio { color:var(--sub); font-size:14px; margin:6px 0 10px; overflow-wrap:anywhere; }
  textarea { width:100%; min-height:150px; border:1px solid var(--line); border-radius:8px; padding:10px; font:inherit; background:transparent; color:inherit; resize:vertical; }
  .actions { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-top:10px; }
  .btn { display:inline-block; padding:9px 14px; border-radius:8px; border:1px solid var(--accent); color:var(--accent); background:transparent; text-decoration:none; font:inherit; cursor:pointer; }
  .btn.main { background:var(--accent); color:var(--card); }
  label.sentbox { margin-left:auto; display:flex; gap:6px; align-items:center; font-size:15px; }
  .empty { color:var(--sub); padding:40px 0; text-align:center; }
</style>
</head>
<body>
<header><div class="wrap bar">
  <div><h1>DM 전송 큐</h1><p id="summary"></p></div>
  <button class="btn" id="export" type="button">보낸 목록 내려받기</button>
</div></header>
<div class="wrap">
  <p class="how">① "복사하고 열기"를 누르면 문안이 복사되고 인스타그램이 열립니다. ② 붙여넣고 전송합니다. ③ 이 페이지로 돌아오면 "보냄"에 표시되어 있습니다. 보내지 않았다면 표시를 끄세요. 문안은 보내기 전에 고칠 수 있습니다.</p>
  <main id="list"></main>
</div>
<script>
const DATA = __DATA__;
const KEY = "dm-queue:" + DATA.created;
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

function copyFrom(textarea) {
  textarea.focus();
  textarea.select();
  try { document.execCommand("copy"); } catch (e) {}
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(textarea.value).catch(function () {});
  }
}

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function refreshSummary() {
  const sent = DATA.items.filter(function (it) { return state[it.u]; }).length;
  document.getElementById("summary").textContent =
    "만든 시각 " + DATA.created + " · 보냄 " + sent + " / " + DATA.items.length;
}

function render() {
  const list = document.getElementById("list");
  if (!DATA.items.length) { list.appendChild(el("p", "empty", "오늘 보낼 대상이 없습니다.")); return; }
  DATA.items.forEach(function (it) {
    const card = el("section", "card");
    const top = el("div", "top");
    top.appendChild(el("span", "name", "@" + it.u));
    top.appendChild(el("span", "meta", (it.followers ? "팔로워 " + Number(it.followers).toLocaleString() : "") + (it.note ? " · " + it.note : "")));
    card.appendChild(top);
    if (it.bio) card.appendChild(el("p", "bio", it.bio));

    const textarea = el("textarea");
    textarea.value = it.msg;
    card.appendChild(textarea);

    const actions = el("div", "actions");
    const box = el("input"); box.type = "checkbox";
    function mark(on) {
      if (on) state[it.u] = new Date().toISOString(); else delete state[it.u];
      box.checked = !!state[it.u];
      card.classList.toggle("sent", !!state[it.u]);
      save(); refreshSummary();
    }
    function opener(label, href, cls) {
      const a = el("a", "btn " + cls, label);
      a.href = href; a.target = "_blank"; a.rel = "noopener";
      a.addEventListener("click", function () { copyFrom(textarea); mark(true); });
      return a;
    }
    const user = encodeURIComponent(it.u);
    actions.appendChild(opener("복사하고 프로필 열기 (PC)", "https://www.instagram.com/" + user + "/", "main"));
    actions.appendChild(opener("복사하고 DM 열기 (모바일)", "https://ig.me/m/" + user, ""));
    const label = el("label", "sentbox");
    box.addEventListener("change", function () { mark(box.checked); });
    label.appendChild(box); label.appendChild(document.createTextNode("보냄"));
    actions.appendChild(label);
    card.appendChild(actions);
    list.appendChild(card);
    mark(!!state[it.u]);
  });
}

document.getElementById("export").addEventListener("click", function () {
  const rows = DATA.items.filter(function (it) { return state[it.u]; });
  if (!rows.length) { alert("아직 보냄으로 표시한 계정이 없습니다."); return; }
  const lines = ["계정,채널,연락일"].concat(rows.map(function (it) {
    return it.u + ",DM," + state[it.u].slice(0, 10);
  }));
  const blob = new Blob(["\\ufeff" + lines.join("\\r\\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "sent_" + DATA.created.slice(0, 10) + ".csv";
  document.body.appendChild(a); a.click(); a.remove();
});

render();
refreshSummary();
</script>
</body>
</html>
"""
