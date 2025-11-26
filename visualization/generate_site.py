import html
import json
import os
import re
import shutil
from pathlib import Path

import jinja2
import pandas as pd

# ==========================================
# 1. 配置与数据加载
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "outputs" / "results" / "trivial" / "trivial_combined_results_summary.csv"
JSON_DETAILS_FILE = BASE_DIR / "outputs" / "results" / "trivial" / "trivial_combined_results_summary.json"
LOGS_ROOT = BASE_DIR / "data" / "raw" / "inference_result"
OUTPUT_DIR = Path(__file__).resolve().parent / "harbor_viz_site"
LOG_FILE_CANDIDATES = [
    "claude-code.txt",
    "trajectory.jsonl",
    "trajectory.json",
    "log.jsonl",
    "log.json",
]

if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("正在加载数据...")
df = pd.read_csv(CSV_FILE)

def build_log_dir_index(log_root: Path):
    index = {}
    if not log_root.exists():
        print(f"⚠️ 日志目录 {log_root} 不存在。")
        return index
    for entry in log_root.iterdir():
        if entry.is_dir():
            index[entry.name.lower()] = entry
    return index

LOG_DIR_INDEX = build_log_dir_index(LOGS_ROOT)

def load_detail_index(path: Path):
    if not path.exists():
        print(f"⚠️ 详情 JSON 文件 {path} 不存在。")
        return {}
    try:
        payload = json.load(path.open("r", encoding="utf-8"))
        detail_entries = payload.get("detailed_results", [])
        index = {}
        for entry in detail_entries:
            entry_id = str(entry.get("id") or "").strip()
            if entry_id:
                index[entry_id] = entry
        return index
    except Exception as exc:
        print(f"⚠️ 无法解析详情 JSON：{exc}")
        return {}

DETAIL_LOOKUP = load_detail_index(JSON_DETAILS_FILE)

# 解析日志 (复用逻辑)
def parse_logs(log_path):
    steps = []
    current_step = {}
    try:
        if log_path is None:
            return []
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    msg_type = entry.get('type')
                    if msg_type == 'assistant':
                        content = entry.get('message', {}).get('content', [])
                        for item in content:
                            if item['type'] == 'text':
                                current_step['thought'] = current_step.get('thought', "") + item['text'] + "\n"
                            elif item['type'] == 'tool_use':
                                current_step['action'] = {'name': item['name'], 'input': item['input']}
                    elif msg_type == 'user':
                        content = entry.get('message', {}).get('content', [])
                        for item in content:
                            if item.get('type') == 'tool_result':
                                current_step['observation'] = item['content']
                                steps.append(current_step)
                                current_step = {}
                except:
                    continue
        if current_step:
            steps.append(current_step)
    except FileNotFoundError:
        return []
    return steps

def clean_problem_description(text: str) -> str:
    if not text:
        return ""
    cleaned = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = cleaned.split("\n")
    if lines and lines[0].strip().lower().startswith("title:"):
        lines = lines[1:]
    cleaned = "\n".join(lines).strip()
    cleaned = cleaned.replace("\\n", "\n").replace("\\t", "    ")
    cleaned = cleaned.replace("\t", "\\t")
    for token in ("texttt", "textbf", "textit"):
        cleaned = cleaned.replace(token[1:] + "{", f"{token}{{")
    latex_map = {
        r"\leq": "≤",
        r"\geq": "≥",
        r"\le": "≤",
        r"\ge": "≥",
        r"\cdot": "·",
        r"\cdots": "…",
        r"\times": "×",
        r"\ldots": "…",
        r"\dots": "…",
        r"\pm": "±",
        r"\mp": "∓",
        r"\neq": "≠",
        r"\infty": "∞",
        r"\rightarrow": "→",
        r"\to": "→",
        r"\left": "",
        r"\right": "",
        r"\lfloor": "⌊",
        r"\rfloor": "⌋",
        r"\lceil": "⌈",
        r"\rceil": "⌉",
        r"\bmod": " mod ",
    }
    for src, dst in latex_map.items():
        cleaned = cleaned.replace(src, dst)
    style_patterns = [
        r"(?:\\)?texttt\{([^}]*)\}",
        r"(?:\\)?textbf\{([^}]*)\}",
        r"(?:\\)?textit\{([^}]*)\}",
    ]
    for pattern in style_patterns:
        cleaned = re.sub(pattern, r" \1 ", cleaned)
    cleaned = cleaned.replace("\\t", " ")
    line_items = []
    for ln in cleaned.split("\n"):
        stripped = re.sub(r"\s{2,}", " ", ln.strip())
        line_items.append(stripped)
    cleaned = "\n".join(line_items)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    starter_markers = [
        "=== STARTER CODE ===",
        "=== STARTER TEMPLATE ===",
        "=== STARTER GUIDE ===",
        "=== YOUR TASK ===",
        "=== STEP GUIDE ===",
    ]
    for marker in starter_markers:
        if marker in cleaned:
            cleaned = cleaned.split(marker)[0].strip()
    quote_glitches = [
        ("'\"'\"'", "'"),
        ("\"'\"'\"", '"'),
    ]
    for seq, replacement in quote_glitches:
        while seq in cleaned:
            cleaned = cleaned.replace(seq, replacement)
    cleaned = cleaned.replace('""', '"')

    def wrap_pow(match):
        expr = match.group(0).replace(" ", "")
        return f"${expr}$"

    cleaned = re.sub(r"(?<!\$)(\b\d+\s*\^\s*\d+\b)(?!\$)", wrap_pow, cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

def escape_text(text: str) -> str:
    if not text:
        return ""
    return html.escape(str(text))

def find_log_file_for_task(task_id: str):
    identifier = str(task_id or "").strip()
    if not identifier or not LOG_DIR_INDEX:
        return None

    parts = [part for part in identifier.split('__') if part]
    candidates = []
    if parts:
        for i in range(len(parts), 0, -1):
            candidates.append('__'.join(parts[:i]))
    else:
        candidates.append(identifier)

    for cand in candidates:
        dir_path = LOG_DIR_INDEX.get(cand.lower())
        if dir_path:
            agent_dir = dir_path / "agent"
            if not agent_dir.exists():
                continue
            for file_name in LOG_FILE_CANDIDATES:
                log_file = agent_dir / file_name
                if log_file.exists():
                    return log_file
            for candidate_file in agent_dir.glob("*"):
                if candidate_file.is_file() and candidate_file.suffix.lower() in {".txt", ".json", ".jsonl"}:
                    return candidate_file
    return None

# ==========================================
# 2. 定义模板 (重点修改了 INDEX_TEMPLATE)
# ==========================================

# 🆕 新版首页：卡片视图
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harbor Evaluation Benchmark</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']]
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
            }
        };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { background: #f1f5f9; color: #334155; font-family: 'Inter', sans-serif; }
        
        /* Card Hover Effects */
        .task-card { 
            transition: all 0.2s ease-in-out; 
            border: 1px solid #e2e8f0;
        }
        .task-card:hover { 
            transform: translateY(-4px); 
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); 
            border-color: #cbd5e1;
            cursor: pointer;
        }

        /* Score Pills */
        .score-pill { 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center;
            padding: 8px 0;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 600;
            background: #f8fafc;
        }
        .score-val { font-size: 1.1rem; font-weight: 800; line-height: 1; margin-bottom: 2px; }
        .score-label { font-size: 0.65rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.05em; }
        
        /* Color Utilities */
        .text-high { color: #16a34a; }
        .text-med { color: #ca8a04; }
        .text-low { color: #dc2626; }
        .bg-high { background-color: #f0fdf4; }

        mjx-container[jax="CHTML"][display="true"] {
            display: inline !important;
            margin: 0 0.15em !important;
        }
    </style>
</head>
<body class="min-h-screen p-8">
    
    <header class="max-w-7xl mx-auto mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
            <h1 class="text-3xl font-extrabold text-slate-800 tracking-tight">Harbor Benchmark</h1>
            <p class="text-slate-500 mt-2 text-lg">Comparing <span class="text-blue-600 font-semibold">LLM Judge</span> vs <span class="text-purple-600 font-semibold">Agent Judge</span> vs <span class="text-green-600 font-semibold">Unit Tests</span></p>
        </div>
        <div class="bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-200 text-sm font-medium text-slate-500">
            Total Tasks: <span class="text-slate-900 font-bold">{{ tasks|length }}</span>
        </div>
    </header>

    <main class="max-w-7xl mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% for task in tasks %}
            <div onclick="window.location.href='task_{{ task.safe_id }}.html'" class="task-card bg-white rounded-xl overflow-hidden flex flex-col h-full">
                
                <div class="p-5 flex-1">
                    <div class="flex justify-between items-start mb-3">
                        <span class="font-mono text-[10px] text-slate-400 bg-slate-100 px-2 py-1 rounded truncate max-w-[150px]" title="{{ task.id }}">
                            {{ task.id }}
                        </span>
                    </div>
                    <h3 class="font-bold text-lg text-slate-800 leading-snug mb-2 line-clamp-2" title="{{ task.full_title }}">
                        {{ task.title }}
                    </h3>
                    <p class="text-sm text-slate-500 line-clamp-3">
                        {{ task.description }}
                    </p>
                </div>

                <div class="p-4 bg-slate-50 border-t border-slate-100 grid grid-cols-3 gap-2">
                    <div class="score-pill {{ 'bg-green-50' if task.score_unit_value == 1.0 else '' }}">
                        <span class="score-val {{ task.color_unit }}">{{ task.score_unit_display }}</span>
                        <span class="score-label">Unit Test</span>
                    </div>
                    
                    <div class="score-pill">
                        <span class="score-val {{ task.color_llm }}">{{ task.score_llm_display }}</span>
                        <span class="score-label">LLM Judge</span>
                    </div>

                    <div class="score-pill">
                        <span class="score-val {{ task.color_agent }}">{{ task.score_agent_display }}</span>
                        <span class="score-label">Agent Judge</span>
                    </div>
                </div>

            </div>
            {% endfor %}
        </div>
    </main>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            if (window.MathJax && window.MathJax.typesetPromise) {
                MathJax.typesetPromise();
            }
        });
    </script>
</body>
</html>
"""

# 详情页模板 (保持不变，功能已完善)
DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Analysis - {{ id }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.0.2/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']]
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
            }
        };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { height: 100vh; display: flex; flex-direction: column; background: #f8fafc; overflow: hidden; }
        .layout { display: flex; flex: 1; overflow: hidden; position: relative; }
        .sidebar { width: var(--sidebar-width, 400px); min-width: 280px; max-width: 760px; background: white; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; flex-shrink: 0; }
        .resize-handle { width: 6px; cursor: col-resize; background: #e2e8f0; flex-shrink: 0; transition: background 0.2s ease; }
        .resize-handle:hover, body.resizing .resize-handle { background: #cbd5e1; }
        body.resizing { cursor: col-resize; user-select: none; }
        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f1f5f9; }
        .tab-nav { display: flex; background: white; border-bottom: 1px solid #e2e8f0; padding: 0 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); z-index: 10; }
        .tab-btn { padding: 16px 12px; margin-right: 24px; font-weight: 600; font-size: 0.95rem; color: #64748b; border-bottom: 3px solid transparent; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
        .tab-btn:hover { color: #1e293b; background: #f8fafc; }
        .tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; background: transparent; }
        .tab-content { display: none; height: 100%; overflow-y: auto; padding: 24px; padding-bottom: 100px; }
        .tab-content.active { display: block; }
        .trajectory-step { background: white; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .step-header { padding: 10px 16px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; border-radius: 8px 8px 0 0; }
        pre { margin: 0; }
        .text-high { color: #16a34a; }
        .text-med { color: #ca8a04; }
        .text-low { color: #dc2626; }

        mjx-container[jax="CHTML"][display="true"] {
            display: inline !important;
            margin: 0 0.15em !important;
        }
    </style>
</head>
<body>
    <header class="bg-slate-900 text-white px-6 py-3 flex justify-between items-center shadow-md z-20 flex-shrink-0">
        <div class="flex items-center gap-4">
            <a href="index.html" class="text-slate-400 hover:text-white transition flex items-center gap-1 font-semibold text-sm">&larr; Back to List</a>
            <div class="h-6 w-px bg-slate-700 mx-2"></div>
            <h1 class="font-bold text-lg truncate w-96">Task <span class="font-mono text-sm font-normal text-slate-400 ml-2">{{ id }}</span></h1>
        </div>
        <div class="flex gap-6 text-sm">
            <div class="flex flex-col items-end"><span class="text-slate-400 text-xs uppercase tracking-wider">Unit Test</span><span class="font-bold {{ score_color_unit }} text-lg">{{ scores.unit }}</span></div>
            <div class="flex flex-col items-end"><span class="text-slate-400 text-xs uppercase tracking-wider">LLM Judge</span><span class="font-bold {{ score_color_llm }} text-lg">{{ scores.llm }}</span></div>
            <div class="flex flex-col items-end"><span class="text-slate-400 text-xs uppercase tracking-wider">Agent Judge</span><span class="font-bold {{ score_color_agent }} text-lg">{{ scores.agent }}</span></div>
        </div>
    </header>
    <div class="layout" id="layout-shell">
        <aside class="sidebar" id="sidebar-panel">
            <div class="flex-1 overflow-y-auto p-6 scrollbar-thin">
                <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 border-b pb-2">Problem Statement</h3>
                <div id="problem-content" class="prose prose-sm prose-slate mb-8 max-w-none text-slate-700">{{ problem_desc }}</div>
                <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 border-b pb-2">Model Solution</h3>
                <div class="bg-slate-800 rounded-lg overflow-hidden text-xs shadow-inner"><pre><code class="language-python">{{ model_solution }}</code></pre></div>
            </div>
        </aside>
        <div class="resize-handle" id="sidebar-resizer" title="Drag to resize"></div>
        <main class="main">
            <div class="tab-nav">
                <button onclick="switchTab('agent')" class="tab-btn active" id="btn-agent"><span>🕵️</span> Agent Judge <span class="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded-full ml-2">Trajectory</span></button>
                <button onclick="switchTab('llm')" class="tab-btn" id="btn-llm"><span>🧠</span> LLM Judge <span class="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full ml-2">Reasoning</span></button>
                <button onclick="switchTab('unit')" class="tab-btn" id="btn-unit"><span>⚡</span> Unit Test <span class="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full ml-2">Logs</span></button>
            </div>
            <div id="tab-agent" class="tab-content active">
                <div class="max-w-4xl mx-auto">
                    <div class="bg-white p-6 rounded-lg border-l-4 border-purple-500 shadow-sm mb-8">
                        <div class="flex justify-between items-start mb-2"><h2 class="font-bold text-lg text-slate-800">Agent Verdict</h2><span class="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded border border-purple-100">Model: {{ models.agent }}</span></div>
                        <p class="text-slate-700 leading-relaxed">{{ reasoning.agent }}</p>
                    </div>
                    <div class="flex items-center justify-between mb-4"><h3 class="font-bold text-slate-700 text-sm uppercase tracking-wider">Execution Trajectory</h3>{% if not has_trajectory %}<span class="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1 rounded">⚠️ Demo: No logs available for this ID</span>{% endif %}</div>
                    {% if has_trajectory %}
                        {% for step in trajectory %}
                        <div class="trajectory-step">
                            <div class="step-header"><span class="font-bold text-xs text-slate-500">STEP {{ loop.index }}</span>{% if step.action %}<span class="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded font-bold font-mono">{{ step.action.name }}</span>{% endif %}</div>
                            <div class="p-4">
                                {% if step.thought %}<div class="mb-4"><span class="text-[10px] font-bold text-slate-400 uppercase block mb-1">Thought</span><div class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap font-sans border-l-2 border-slate-200 pl-3">{{ step.thought }}</div></div>{% endif %}
                                {% if step.action %}<div class="mb-4"><span class="text-[10px] font-bold text-slate-400 uppercase block mb-1">Action Input</span><pre class="bg-slate-50 border border-slate-200 rounded p-3 text-xs font-mono text-slate-600 overflow-x-auto"><code>{{ step.action.input }}</code></pre></div>{% endif %}
                                {% if step.observation %}<div><span class="text-[10px] font-bold text-slate-400 uppercase block mb-1">Observation</span><pre class="bg-slate-100 border border-slate-200 rounded p-3 text-xs font-mono text-slate-600 max-h-48 overflow-y-auto whitespace-pre-wrap">{{ step.observation }}</pre></div>{% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                         <div class="p-12 text-center border-2 border-dashed border-slate-300 rounded-lg bg-slate-50"><p class="text-slate-500 font-medium">No trajectory logs available for this task.</p><p class="text-slate-400 text-sm mt-2">(In this demo, only task <a href="task_2808__j8qegjl__ChgukeA.html" class="text-blue-600 underline hover:text-blue-800">2808...</a> has a real log file attached.)</p></div>
                    {% endif %}
                </div>
            </div>
            <div id="tab-llm" class="tab-content">
                <div class="max-w-3xl mx-auto">
                    <div class="bg-white p-8 rounded-lg border-l-4 border-blue-500 shadow-sm">
                        <div class="flex items-center gap-3 mb-6 border-b border-gray-100 pb-4"><span class="text-2xl">🧠</span><div><h2 class="font-bold text-xl text-slate-800">LLM Judge Assessment</h2><p class="text-sm text-slate-500">Model: {{ models.llm }}</p></div><div class="ml-auto"><span class="text-lg font-bold {{ score_color_llm }}">Score: {{ scores.llm }}</span></div></div>
                        <div class="prose prose-slate max-w-none"><p class="text-lg leading-relaxed text-slate-700 whitespace-pre-wrap">{{ reasoning.llm }}</p></div>
                    </div>
                </div>
            </div>
            <div id="tab-unit" class="tab-content">
                <div class="max-w-4xl mx-auto">
                    <div class="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                         <div class="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center"><h2 class="font-bold text-slate-700 flex items-center gap-2"><span>⚡</span> Unit Test Logs</h2><span class="bg-white border border-slate-300 text-slate-700 px-3 py-1 rounded text-sm font-bold shadow-sm">Score: {{ scores.unit }}</span></div>
                        <div class="p-0"><pre class="bg-slate-900 text-green-400 p-6 font-mono text-sm overflow-x-auto min-h-[300px]">{{ reasoning.unit }}</pre></div>
                    </div>
                </div>
            </div>
        </main>
    </div>
    <script>
        hljs.highlightAll();
        const probElem = document.getElementById('problem-content');
        if(probElem) {
            probElem.innerHTML = marked.parse(probElem.textContent);
            if (window.MathJax && window.MathJax.typesetPromise) {
                MathJax.typesetPromise([probElem]);
            }
        }
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            document.getElementById('btn-' + tabId).classList.add('active');
            if (window.MathJax && window.MathJax.typesetPromise) {
                MathJax.typesetPromise();
            }
        }

        const layoutShell = document.getElementById('layout-shell');
        const sidebarPanel = document.getElementById('sidebar-panel');
        const resizeHandle = document.getElementById('sidebar-resizer');
        const storedSidebarWidth = sidebarPanel ? localStorage.getItem('harborSidebarWidth') : null;
        if (storedSidebarWidth && sidebarPanel) {
            sidebarPanel.style.width = storedSidebarWidth;
        }

        let isDraggingSidebar = false;
        const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

        const applySidebarWidth = (clientX) => {
            if (!layoutShell || !sidebarPanel) return;
            const { left } = layoutShell.getBoundingClientRect();
            const newWidth = clamp(clientX - left, 260, 760);
            sidebarPanel.style.width = `${newWidth}px`;
            localStorage.setItem('harborSidebarWidth', sidebarPanel.style.width);
        };

        const stopResizing = () => {
            if (!isDraggingSidebar) return;
            isDraggingSidebar = false;
            document.body.classList.remove('resizing');
        };

        const startResize = (clientX) => {
            if (!sidebarPanel) return;
            isDraggingSidebar = true;
            document.body.classList.add('resizing');
            applySidebarWidth(clientX);
        };

        if (resizeHandle) {
            resizeHandle.addEventListener('mousedown', (event) => {
                event.preventDefault();
                startResize(event.clientX);
            });
            resizeHandle.addEventListener('touchstart', (event) => {
                if (event.touches.length === 1) {
                    startResize(event.touches[0].clientX);
                    event.preventDefault();
                }
            }, { passive: false });
        }

        window.addEventListener('mousemove', (event) => {
            if (!isDraggingSidebar) return;
            applySidebarWidth(event.clientX);
        });
        window.addEventListener('touchmove', (event) => {
            if (!isDraggingSidebar || event.touches.length !== 1) return;
            applySidebarWidth(event.touches[0].clientX);
        }, { passive: false });
        window.addEventListener('mouseup', stopResizing);
        window.addEventListener('touchend', stopResizing);
    </script>
</body>
</html>
"""

# ==========================================
# 3. 网站生成逻辑
# ==========================================

# 辅助函数: 颜色映射
def normalize_score(value):
    if value in (None, "", "-", "--"):
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return float(value)
    except Exception:
        return None


def format_score(value):
    if value is None:
        return "--"
    return f"{value:.2f}"


def get_score_text_color(score):
    score_value = normalize_score(score)
    if score_value is None:
        return "text-slate-400"
    if score_value >= 0.99:
        return "text-high"
    if score_value >= 0.7:
        return "text-med"
    return "text-low"

print("正在生成首页 (Card Layout)...")
tasks_data = []

for _, row in df.iterrows():
    task_id = str(row.get('ID', '')).strip()
    safe_id = task_id.replace('/', '_').replace('\\', '_')
    detail_entry = DETAIL_LOOKUP.get(task_id)

    problem_desc_source = None
    if detail_entry:
        problem_desc_source = detail_entry.get('problem_description')
    if not problem_desc_source or pd.isna(problem_desc_source):
        problem_desc_source = row.get('Problem Description', '')
    if pd.isna(problem_desc_source):
        problem_desc_source = ""
    problem_desc_str = clean_problem_description(problem_desc_source)
    desc_clean = problem_desc_str.replace('\n', ' ')

    title_line = ""
    if detail_entry and detail_entry.get('problem_title'):
        title_line = str(detail_entry['problem_title'])
    elif problem_desc_str:
        title_line = problem_desc_str.split('\n')[0]
    
    def pick_score(detail_key, csv_key):
        candidate = detail_entry.get(detail_key) if detail_entry else None
        if candidate in (None, "", "-"):
            candidate = row.get(csv_key, "")
        return normalize_score(candidate)

    unit_score = pick_score('unit_test_score', 'Unit test Scores')
    llm_score = pick_score('llm_judge_score', 'LLM Judgment Score')
    agent_score = pick_score('agent_judge_score', 'Agent Judgement Score')

    tasks_data.append({
        "id": task_id,
        "safe_id": safe_id,
        "title": title_line.replace('Title: ', '')[:60], # 优化标题提取
        "full_title": title_line,
        "description": (desc_clean[:150] + "...") if desc_clean else "",
        "score_unit_display": format_score(unit_score),
        "score_unit_value": unit_score,
        "color_unit": get_score_text_color(unit_score),
        "score_llm_display": format_score(llm_score),
        "score_llm_value": llm_score,
        "color_llm": get_score_text_color(llm_score),
        "score_agent_display": format_score(agent_score),
        "score_agent_value": agent_score,
        "color_agent": get_score_text_color(agent_score),
    })

# 生成 index.html
template_index = jinja2.Template(INDEX_TEMPLATE)
index_path = OUTPUT_DIR / "index.html"
with index_path.open("w", encoding='utf-8') as f:
    f.write(template_index.render(tasks=tasks_data))

print("正在生成详情页...")
template_detail = jinja2.Template(DETAIL_TEMPLATE)

for _, row in df.iterrows():
    task_id = str(row.get('ID', '')).strip()
    safe_id = task_id.replace('/', '_').replace('\\', '_')
    log_path = find_log_file_for_task(task_id)
    current_trajectory = parse_logs(log_path)
    detail_entry = DETAIL_LOOKUP.get(task_id)

    def pick_score_detail(detail_key, csv_key):
        candidate = detail_entry.get(detail_key) if detail_entry else None
        if candidate in (None, "", "-"):
            candidate = row.get(csv_key, "")
        return normalize_score(candidate)

    unit_score = pick_score_detail('unit_test_score', 'Unit test Scores')
    llm_score = pick_score_detail('llm_judge_score', 'LLM Judgment Score')
    agent_score = pick_score_detail('agent_judge_score', 'Agent Judgement Score')

    problem_desc = None
    if detail_entry:
        problem_desc = detail_entry.get('problem_description')
    if not problem_desc or pd.isna(problem_desc):
        problem_desc = row.get('Problem Description', '')
    if pd.isna(problem_desc):
        problem_desc = ""
    problem_desc_clean = clean_problem_description(problem_desc)

    model_solution = detail_entry.get('code_solution') if detail_entry and detail_entry.get('code_solution') else row.get('Solution (Model solution from Claude4.5haiku)', '')
    if pd.isna(model_solution):
        model_solution = ""

    html_content = template_detail.render(
        id=task_id,
        problem_desc=escape_text(problem_desc_clean),
        model_solution=escape_text(model_solution),
        scores={
            "unit": format_score(unit_score),
            "llm": format_score(llm_score),
            "agent": format_score(agent_score)
        },
        score_color_unit=get_score_text_color(unit_score),
        score_color_llm=get_score_text_color(llm_score),
        score_color_agent=get_score_text_color(agent_score),
        reasoning={
            "unit": detail_entry.get('unit_test_details') if detail_entry and detail_entry.get('unit_test_details') else row.get('Unittest details', ''),
            "llm": detail_entry.get('llm_judge_reasoning') if detail_entry and detail_entry.get('llm_judge_reasoning') else row.get('LLM Judgement Reasoning', ''),
            "agent": detail_entry.get('agent_judge_reasoning') if detail_entry and detail_entry.get('agent_judge_reasoning') else row.get('Agent Judgement Reasoning', '')
        },
        models={
            "llm": detail_entry.get('llm_model') if detail_entry and detail_entry.get('llm_model') else row.get('LLM name', ''),
            "agent": detail_entry.get('agent_model') if detail_entry and detail_entry.get('agent_model') else row.get('Agent LLM name', '')
        },
        has_trajectory=bool(current_trajectory),
        trajectory=current_trajectory
    )
    
    detail_path = OUTPUT_DIR / f"task_{safe_id}.html"
    with detail_path.open("w", encoding='utf-8') as f:
        f.write(html_content)

print("[OK] 网站生成成功！卡片风格已应用。")
print(f"请打开文件夹 '{OUTPUT_DIR}' 并双击 'index.html' 查看效果。")