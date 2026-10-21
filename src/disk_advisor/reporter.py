import json
import webbrowser
from collections import defaultdict
from pathlib import Path

from .rules import MIGRATION_STRATEGY
from .scanner import FileRecord


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def build_report(records: list[FileRecord]) -> str:
    greens = [r for r in records if r.risk == "green"]
    migratable = [r for r in records if r.matched_rule.startswith("migratable:")]
    unknown_large = [
        r for r in records if r.category == "large" and r.matched_rule == "large_unknown_type"
    ]

    lines = ["# 磁盘扫描报告（只读，未执行任何删除/迁移）\n"]

    # ========== 绿灯 ==========
    total_green = human_size(sum(r.size for r in greens))
    lines.append(f"## 一、可安全清理的垃圾（绿灯）  合计 {total_green}\n")
    by_rule: dict[str, dict[str, int]] = defaultdict(lambda: {"size": 0, "count": 0})
    for r in greens:
        by_rule[r.matched_rule]["size"] += r.size
        by_rule[r.matched_rule]["count"] += 1
    for rule, stat in sorted(by_rule.items(), key=lambda x: -x[1]["size"]):
        lines.append(f"- **{rule}**：{stat['count']} 项，{human_size(stat['size'])}")
    lines.append(
        "\n> 这些路径属于系统或软件运行中产生的临时数据，清理后通常会自动重建。"
        "建议关闭相关程序后再清理浏览器缓存。\n"
    )

    # ========== 可迁移大文件 ==========
    total_migratable = human_size(sum(r.size for r in migratable))
    lines.append(f"## 二、建议迁移而非删除的大文件  合计 {total_migratable}\n")
    for r in sorted(migratable, key=lambda x: -x.size):
        ext = Path(r.path).suffix.lower()
        strategy = MIGRATION_STRATEGY.get(ext, "可直接剪切到其他盘")
        lines.append(f"- `{r.path}`  **{human_size(r.size)}**  \n  → {strategy}")
    lines.append(
        "\n> **迁移通用步骤**：① 关闭所有可能占用该文件的程序；"
        "② 复制（不是剪切）到目标盘；③ 校验文件数量和大小一致；"
        "④ 确认无误后删除 C 盘原文件。"
        "如果迁移的是软件会主动访问的目录，而不是普通资料文件，"
        "必须用 `mklink /J` 在原路径创建目录联接，否则软件会找不到文件。\n"
    )

    # ========== 未知大文件 ==========
    total_unknown = human_size(sum(r.size for r in unknown_large))
    lines.append(f"## 三、需要你自行判断的大文件  合计 {total_unknown}\n")
    lines.append(
        "以下文件体积较大，但不属于可自动判断的类型。**程序不给出迁移建议**，"
        "因为它们可能是软件数据库、工作库或配置依赖文件。\n"
    )
    for r in sorted(unknown_large, key=lambda x: -x.size):
        lines.append(
            f"- `{r.path}`  **{human_size(r.size)}**  \n"
            f"  属于未知类型，迁移前请在对应软件中检查是否有“更改存储位置”的设置。"
        )

    return "\n".join(lines)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><title>磁盘扫描报告</title>
<style>
  body {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    padding: 20px;
    background: #f9f9f9;
    color: #333;
  }
  
  /* 顶部控制栏 */
  .controls {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
    align-items: center;
    background: #fff;
    padding: 15px;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  .controls input, .controls select {
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
    outline: none;
  }
  .controls input { flex: 1; max-width: 400px; }
  .controls select { cursor: pointer; }
  
  /* 表格样式 */
  table {
    width: 100%;
    border-collapse: collapse;
    background: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    table-layout: fixed;
  }
  th, td { padding: 12px 10px; border-bottom: 1px solid #eee; text-align: left; }
  th {
    background: #f4f4f4;
    position: sticky;
    top: 0;
    font-weight: 600;
    cursor: pointer;
    user-select: none;
    transition: background 0.2s;
  }
  th:hover { background: #e8e8e8; }
  
  /* 表头排序箭头 */
  th.asc::after { content: " ▲"; font-size: 12px; color: #666; }
  th.desc::after { content: " ▼"; font-size: 12px; color: #666; }

  /* 列宽 */
  th:nth-child(1), td:nth-child(1) { width: 50%; word-break: break-all; }
  th:nth-child(2), td:nth-child(2) { width: 12%; text-align: right; }
  th:nth-child(3), td:nth-child(3) { width: 12%; text-align: center; }
  th:nth-child(4), td:nth-child(4) { width: 10%; text-align: center; }
  th:nth-child(5), td:nth-child(5) { width: 16%; }

  .green {
    color: #2e7d32;
    background: #e8f5e9;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 13px;
  }
  .yellow {
    color: #e65100;
    background: #fff3e0;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 13px;
  }
</style>
</head>
<body>
<h1>磁盘扫描报告</h1>
<p style="color: #666;">只读扫描，未执行删除或迁移。请根据建议手动处理文件。</p>

<div class="controls">
  <input type="text" id="search" placeholder="🔍 搜索文件路径..." oninput="applyFilters()">
  <select id="filter-cat" onchange="applyFilters()">
    <option value="all">所有类别</option>
    <option value="junk">仅垃圾文件</option>
    <option value="large">仅大文件</option>
  </select>
  <select id="filter-risk" onchange="applyFilters()">
    <option value="all">所有风险</option>
    <option value="green">绿灯（安全）</option>
    <option value="yellow">黄灯（需确认）</option>
  </select>
</div>

<table>
  <thead>
    <tr>
      <th onclick="sortTable('path')">路径</th>
      <th onclick="sortTable('size')">大小</th>
      <th onclick="sortTable('category')">类别</th>
      <th onclick="sortTable('risk')">风险</th>
      <th>处理建议</th>
    </tr>
  </thead>
  <tbody id="rows"></tbody>
</table>

<script>
  // 注入原始数据
  const rawData = __DATA__;
  let currentData = [...rawData];
  let sortCol = "";
  let sortAsc = true;

  function applyFilters() {
    const query = document.getElementById('search').value.toLowerCase();
    const cat = document.getElementById('filter-cat').value;
    const risk = document.getElementById('filter-risk').value;

    // 1. 过滤
    currentData = rawData.filter(r => {
      const matchQuery = r.path.toLowerCase().includes(query);
      const matchCat = (cat === 'all') || (r.category === cat);
      const matchRisk = (risk === 'all') || (r.risk === risk);
      return matchQuery && matchCat && matchRisk;
    });

    // 2. 排序
    if (sortCol) {
      currentData.sort((a, b) => {
        let valA = a[sortCol];
        let valB = b[sortCol];
        
        // 如果是字符串，用 localeCompare 比较
        if (typeof valA === 'string') {
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        // 如果是数值（如 size），直接相减
        return sortAsc ? valA - valB : valB - valA;
      });
    }

    render();
  }

  function sortTable(col) {
    if (sortCol === col) {
      sortAsc = !sortAsc; // 点击同一列切换升降序
    } else {
      sortCol = col;
      sortAsc = true; // 默认升序
    }
    
    // 更新表头箭头
    document.querySelectorAll('th').forEach(th => th.className = '');
    const ths = document.querySelectorAll('th');
    const colMap = { 'path': 0, 'size': 1, 'category': 2, 'risk': 3 };
    if (colMap[col] !== undefined) {
      ths[colMap[col]].className = sortAsc ? 'asc' : 'desc';
    }

    applyFilters();
  }

  function render() {
    document.getElementById('rows').innerHTML = currentData.map(r => `
      <tr>
        <td>${r.path}</td>
        <td style="text-align:right;">${r.size_str}</td>
        <td style="text-align:center;">${r.category === 'junk' ? '垃圾' : '大文件'}</td>
        <td style="text-align:center;"><span class="${r.risk}">${r.risk === 'green' ? '绿灯' : \
'黄灯'}</span></td>
        <td>${r.advice}</td>
      </tr>
    `).join('');
  }

  // 初始渲染
  render();
</script>
</body>
</html>"""


def translate_rule(rule: str) -> str:
    """把程序内部的规则代号翻译成人类听得懂的建议"""
    if rule.startswith("migratable:"):
        return "建议迁移至其他盘"
    if rule.startswith("size>="):
        return "扫描发现的大文件"
    if rule.startswith("under:") or rule == "under_temp_or_cache":
        return "临时缓存（可清理）"
    if rule == "in_user_data_dir":
        return "用户目录（需确认）"
    if rule == "large_unknown_type":
        return "未知类型（建议保留）"
    return rule


def write_html_report(records: list[FileRecord], out_path: str) -> None:
    data = []
    for r in records:
        data.append(
            {
                "path": r.path,
                "size": r.size,  # <--- 关键：保留原始数值用于正确排序
                "size_str": human_size(r.size),
                "category": r.category,
                "risk": r.risk,
                "advice": translate_rule(r.matched_rule),
            }
        )
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    Path(out_path).write_text(html, encoding="utf-8")
    # 自动用默认浏览器打开
    webbrowser.open(Path(out_path).resolve().as_uri())
