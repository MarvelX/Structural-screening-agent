from __future__ import annotations

import json

from structural_screening_agent.localization import Language


_COLORS = {
    "module": "#79a7b8",
    "purlin": "#6a7f9b",
    "beam": "#8aa36a",
    "post": "#6f8b5a",
    "brace": "#cf8a50",
    "pile": "#7d6c5b",
    "ground": "#d9c8a6",
    "wire": "#6b5aa8",
}

_LABELS = {
    "zh": {
        "title": "PV Structure Studio",
        "subtitle": "固定支架 / 构件识别 / 风险与交付物",
        "component_list": "构件清单",
        "stage_title": "光伏固定支架",
        "stage_subtitle": "拖拽旋转模型，点击构件查看结构角色、风险和交付物。",
        "mode_fixed": "固定支架",
        "mode_tracker": "跟踪器语境",
        "mode_roof": "屋面接口",
        "layer": "结构层",
        "hide_labels": "隐藏标签",
        "show_labels": "显示标签",
        "pause_rotation": "暂停旋转",
        "auto_rotation": "自动旋转",
        "reset_view": "重置视角",
        "view_foundation": "看基础",
        "view_interface": "看接口",
        "role": "结构角色",
        "risk": "关键风险",
        "deliverable": "交付物",
        "learning_note": "学习提示",
        "learning_text": "光伏支架学习不要从单根杆件开始，而要从“组件风荷载 -> 支架传力 -> 基础抗拔 -> 地基与排水”的完整链条建立记忆。",
        "load_path": "传力链",
        "load_path_text": "组件把风、雪和自重传给檩条，檩条传给斜梁和立柱，立柱通过桩或基础进入地基。",
        "review_material": "表达素材",
        "review_material_text": "把支架、基础、场地排水和施工偏差一起看，因为光伏项目是低单价、高重复、强接口工程。",
        "boundary": "边界声明",
        "boundary_text": "本互动模型用于学习和展示，不替代厂家支架模型、结构计算书、风洞报告、地勘资料或注册工程师签章成果。",
        "pc_note": "本互动模型按桌面工作台设计。窄屏设备请回到文字说明阅读，正式演示建议使用桌面端。",
    },
    "en": {
        "title": "PV Structure Studio",
        "subtitle": "Fixed rack / component recognition / risks and deliverables",
        "component_list": "Component List",
        "stage_title": "Fixed PV Mounting Structure",
        "stage_subtitle": "Drag to rotate the model. Select a component to review its role, risks, and deliverables.",
        "mode_fixed": "Fixed Rack",
        "mode_tracker": "Tracker Context",
        "mode_roof": "Rooftop Interface",
        "layer": "Structure Layer",
        "hide_labels": "Hide Labels",
        "show_labels": "Show Labels",
        "pause_rotation": "Pause Rotation",
        "auto_rotation": "Auto Rotation",
        "reset_view": "Reset View",
        "view_foundation": "Foundation",
        "view_interface": "Interface",
        "role": "Structural Role",
        "risk": "Key Risk",
        "deliverable": "Deliverable",
        "learning_note": "Learning Note",
        "learning_text": "Review PV mounting structures as a complete chain: module wind load, rack load path, foundation uplift, ground and drainage boundary.",
        "load_path": "Load Path",
        "load_path_text": "Modules transfer wind, snow, and self-weight to rails; rails transfer loads to beams and posts; posts deliver reactions into piles or foundations.",
        "review_material": "Review Material",
        "review_material_text": "The rack, foundation, drainage, and installation tolerance should be reviewed together because PV plants are repetitive, interface-heavy projects.",
        "boundary": "Boundary Statement",
        "boundary_text": "This interactive model is for learning and demonstration only. It does not replace vendor rack models, structural calculations, wind reports, geotechnical records, or signed engineering deliverables.",
        "pc_note": "This interactive model is designed for desktop workbench use. On narrow screens, use the text summary and switch to a desktop device for demonstrations.",
    },
}

_DETAILS = {
    "zh": {
        "module": {
            "name": "光伏组件",
            "subtitle": "发电面板 / 风吸力输入",
            "role": "把风吸力、雪荷载和自重传给檩条。组件边框和夹持位置会限制支架布置。",
            "risk": "边角区风吸力、夹持不当、玻璃和边框受力、清洗与检修荷载。",
            "deliverable": "组件排布图、夹持边界、厂家安装手册核对。",
        },
        "purlin": {
            "name": "檩条 / 导轨",
            "subtitle": "组件支承线",
            "role": "承托组件并把荷载传给斜梁或横梁，是固定支架中数量最多的细长构件之一。",
            "risk": "挠度、局部屈曲、孔位偏差、压块滑移和镀锌破坏。",
            "deliverable": "檩条截面、连接节点、螺栓扭矩和长圆孔方向。",
        },
        "beam": {
            "name": "斜梁 / 横梁",
            "subtitle": "支架主受力骨架",
            "role": "汇集檩条荷载并传给立柱，决定组件倾角和整体空间刚度。",
            "risk": "弱轴稳定、节点偏心、施工安装偏差和风致振动。",
            "deliverable": "杆件表、节点详图、支架倾角和排间距。",
        },
        "post": {
            "name": "立柱",
            "subtitle": "上部结构到基础的转换",
            "role": "把支架轴力、弯矩和水平力传给基础，是支架和地基的关键接口。",
            "risk": "长细比、局部屈曲、柱脚连接、差异沉降和安装垂直度。",
            "deliverable": "立柱截面、柱脚节点、基础反力表。",
        },
        "brace": {
            "name": "斜撑",
            "subtitle": "抗侧和整体稳定",
            "role": "提高支架横向刚度，控制风荷载下的侧移和整体变形。",
            "risk": "连接松动、受压失稳、节点薄弱和施工漏装。",
            "deliverable": "斜撑布置、连接板、螺栓规格和安装检查表。",
        },
        "pile": {
            "name": "螺旋桩 / 基础",
            "subtitle": "抗拔、抗压、抗侧向",
            "role": "把支架反力传入地基，常由抗拔和水平承载控制。",
            "risk": "抗拔不足、腐蚀、冻胀、施工偏位和地层变化。",
            "deliverable": "桩型分区、试桩或拉拔要求、桩长表和防腐要求。",
        },
        "ground": {
            "name": "地基与排水",
            "subtitle": "场地条件约束",
            "role": "提供承载与排水边界，影响基础选型、道路和施工组织。",
            "risk": "冲刷、水毁、软弱层、边坡和雨季施工。",
            "deliverable": "地勘摘要、排水图、场平和水保措施。",
        },
        "wire": {
            "name": "接地与电缆",
            "subtitle": "结构-电气协同",
            "role": "把支架、组件边框、基础和电气系统连接成安全路径。",
            "risk": "接地不连续、桥架支撑冲突、检修路径不足。",
            "deliverable": "接地图、桥架支撑和接口检查表。",
        },
    },
    "en": {
        "module": {
            "name": "PV Module",
            "subtitle": "Panel surface / wind suction input",
            "role": "Transfers wind suction, snow, and self-weight to the rail lines. Frame and clamp limits affect rack layout.",
            "risk": "Corner-zone suction, poor clamping, glass and frame demand, cleaning and maintenance loads.",
            "deliverable": "Module layout, clamp boundary, and vendor installation manual review.",
        },
        "purlin": {
            "name": "Rail / Purlin",
            "subtitle": "Module support line",
            "role": "Supports the modules and transfers load to beams. It is one of the most repetitive slender members in fixed racks.",
            "risk": "Deflection, local buckling, hole tolerance, clamp slip, and galvanizing damage.",
            "deliverable": "Rail section, connection detail, bolt torque, and slotted-hole orientation.",
        },
        "beam": {
            "name": "Inclined Beam",
            "subtitle": "Primary rack frame",
            "role": "Collects rail loads and transfers them into posts while controlling tilt angle and rack stiffness.",
            "risk": "Weak-axis stability, eccentric joints, installation tolerance, and wind vibration.",
            "deliverable": "Member schedule, joint details, tilt angle, and row spacing.",
        },
        "post": {
            "name": "Post",
            "subtitle": "Rack-to-foundation transfer",
            "role": "Transfers axial force, bending, and horizontal demand into the foundation.",
            "risk": "Slenderness, local buckling, base connection, differential settlement, and verticality.",
            "deliverable": "Post section, base detail, and foundation reaction schedule.",
        },
        "brace": {
            "name": "Brace",
            "subtitle": "Lateral stability",
            "role": "Improves lateral stiffness and controls displacement under wind demand.",
            "risk": "Loose connections, compression buckling, weak gussets, and missing installation.",
            "deliverable": "Brace layout, connection plates, bolt size, and installation checklist.",
        },
        "pile": {
            "name": "Screw Pile / Foundation",
            "subtitle": "Uplift, compression, and lateral support",
            "role": "Transfers rack reactions into ground. Uplift and lateral capacity often govern.",
            "risk": "Insufficient uplift, corrosion, frost heave, installation offset, and variable strata.",
            "deliverable": "Pile zoning, pull-out test requirement, pile length schedule, and corrosion protection.",
        },
        "ground": {
            "name": "Ground and Drainage",
            "subtitle": "Site boundary condition",
            "role": "Provides bearing and drainage boundary conditions that influence foundation choice and construction planning.",
            "risk": "Scour, washout, soft layers, slopes, and wet-season installation risk.",
            "deliverable": "Geotechnical summary, drainage plan, grading plan, and erosion controls.",
        },
        "wire": {
            "name": "Grounding and Cable",
            "subtitle": "Structural-electrical interface",
            "role": "Connects racks, module frames, foundations, and electrical systems into a safe path.",
            "risk": "Discontinuous grounding, cable-tray support conflicts, and insufficient access.",
            "deliverable": "Grounding drawing, tray support detail, and interface checklist.",
        },
    },
}


def build_pv_3d_studio_html(language: Language) -> str:
    labels = _LABELS[language]
    details = {
        key: {**value, "color": _COLORS[key]}
        for key, value in _DETAILS[language].items()
    }
    payload = {
        "labels": labels,
        "details": details,
        "colors": _COLORS,
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    component_buttons = "\n".join(
        f"""
        <button class="studio-component{' is-active' if key == 'module' else ''}" type="button" data-component="{key}">
          <span class="studio-dot" style="background:{_COLORS[key]}"></span>
          <span><strong>{details[key]['name']}</strong><span>{details[key]['subtitle']}</span></span>
        </button>
        """
        for key in ("module", "purlin", "beam", "post", "brace", "pile", "ground", "wire")
    )

    return f"""
<!DOCTYPE html>
<html lang="{language}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #f5f7fa; color: #2b3138; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.studio-shell {{
  --studio-bg: #f7f6f3;
  --studio-panel: rgba(255,255,255,.9);
  --studio-line: rgba(60,66,74,.16);
  --studio-ink: #202830;
  --studio-muted: #687481;
  --studio-blue: #4779a8;
  width: min(100%, 1180px);
  margin: 0 auto;
  border: 1px solid var(--studio-line);
  border-radius: 10px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(241,245,249,.94)), var(--studio-bg);
  box-shadow: 0 14px 32px rgba(15,23,42,.06);
}}
.studio-topbar {{ display:flex; justify-content:space-between; align-items:center; gap:16px; padding:14px 16px; border-bottom:1px solid var(--studio-line); }}
.studio-brand {{ display:flex; align-items:center; gap:12px; min-width:0; }}
.studio-logo {{ width:40px; height:40px; border-radius:8px; display:grid; place-items:center; background:linear-gradient(145deg,#d9ead7,#f2da9e); color:#4f704f; font-weight:800; border:1px solid rgba(60,66,74,.12); }}
.studio-title {{ margin:0; font-size:16px; line-height:1.15; font-weight:760; color:var(--studio-ink); }}
.studio-subtitle {{ margin:3px 0 0; font-size:12px; line-height:1.35; color:var(--studio-muted); }}
.studio-tabs, .studio-chip-row, .studio-toolbar-group {{ display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; }}
.studio-tab, .studio-btn, .studio-chip {{
  border: 1px solid var(--studio-line);
  background: rgba(255,255,255,.72);
  border-radius: 8px;
  color: var(--studio-ink);
  cursor:pointer;
  font: inherit;
  font-size:12px;
  line-height:1.2;
  padding:8px 10px;
  min-height:34px;
}}
.studio-tab:hover, .studio-btn:hover, .studio-chip:hover {{ background:#fff; border-color:rgba(71,121,168,.42); }}
.studio-tab.is-active, .studio-chip.is-active {{ background:rgba(71,121,168,.13); border-color:rgba(71,121,168,.42); color:#2e5f88; }}
.studio-pc-note {{ display:none; margin:12px; border:1px solid var(--studio-line); border-radius:8px; background:rgba(255,255,255,.76); padding:12px; color:var(--studio-muted); font-size:13px; line-height:1.55; }}
.studio-grid {{ display:grid; grid-template-columns:minmax(150px,180px) minmax(0,1fr) minmax(170px,210px); gap:10px; padding:12px; }}
.studio-panel {{ border:1px solid var(--studio-line); border-radius:10px; background:var(--studio-panel); min-width:0; }}
.studio-panel-header {{ padding:14px 14px 8px; }}
.studio-panel h2, .studio-panel h3 {{ margin:0; font-size:12px; line-height:1.3; letter-spacing:.02em; color:#58616c; }}
.studio-component-list {{ display:grid; gap:7px; padding:0 10px 12px; }}
.studio-component {{ border:1px solid transparent; border-radius:8px; background:transparent; cursor:pointer; display:grid; grid-template-columns:22px minmax(0,1fr); gap:8px; padding:8px; text-align:left; }}
.studio-component.is-active {{ background:rgba(71,121,168,.12); border-color:rgba(71,121,168,.3); }}
.studio-dot {{ width:16px; height:16px; border-radius:50%; align-self:center; box-shadow:inset 0 0 0 2px rgba(255,255,255,.55); }}
.studio-component strong {{ display:block; font-size:13px; line-height:1.25; color:var(--studio-ink); }}
.studio-component span span {{ display:block; margin-top:2px; font-size:11px; line-height:1.25; color:var(--studio-muted); }}
.studio-stage {{ min-height:520px; position:relative; overflow:hidden; }}
.studio-stage-header {{ position:absolute; z-index:2; top:16px; left:16px; max-width:360px; }}
.studio-stage-title {{ margin:0; font-size:20px; line-height:1.15; font-weight:740; color:var(--studio-ink); }}
.studio-stage-sub {{ margin:7px 0 0; font-size:12px; line-height:1.45; color:var(--studio-muted); }}
.studio-canvas-wrap {{ position:absolute; inset:0; background:radial-gradient(circle at 64% 34%, rgba(116,154,96,.18), transparent 30%), linear-gradient(150deg, rgba(255,251,242,.86), rgba(232,236,240,.8)); }}
#pv-structure-canvas {{ width:100%; height:100%; min-height:420px; display:block; cursor:grab; touch-action:none; user-select:none; }}
#pv-structure-canvas:active {{ cursor:grabbing; }}
.studio-overlay {{ position:absolute; right:16px; top:16px; z-index:2; }}
.studio-toolbar {{ position:absolute; z-index:2; left:16px; right:16px; bottom:16px; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.studio-detail {{ padding:14px; }}
.studio-detail-title {{ display:flex; align-items:center; gap:10px; margin:0 0 14px; }}
.studio-detail-icon {{ width:32px; height:32px; border-radius:50%; background:var(--detail-color,#79a7b8); box-shadow:inset 0 0 0 3px rgba(255,255,255,.48); flex:0 0 auto; }}
.studio-detail h2 {{ font-size:15px; letter-spacing:0; color:var(--studio-ink); }}
.studio-detail p {{ margin:3px 0 0; font-size:12px; line-height:1.55; color:var(--studio-muted); }}
.studio-facts {{ display:grid; gap:8px; margin:14px 0; }}
.studio-fact {{ display:grid; grid-template-columns:minmax(72px,82px) minmax(0,1fr); gap:9px; font-size:12px; line-height:1.45; }}
.studio-fact span:first-child {{ color:#7c8792; }}
.studio-fact span:last-child {{ color:var(--studio-ink); overflow-wrap:anywhere; }}
.studio-notes {{ border-top:1px dashed var(--studio-line); padding-top:12px; margin-top:12px; }}
.studio-bottom {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; padding:0 12px 12px; }}
.studio-mini {{ padding:14px; }}
.studio-mini h3 {{ margin-bottom:8px; }}
.studio-mini p {{ margin:0; font-size:12px; line-height:1.6; color:var(--studio-muted); }}
@media screen and (max-width: 1020px) {{
  .studio-pc-note {{ display:block; }}
  .studio-grid, .studio-bottom {{ grid-template-columns:1fr; }}
  .studio-detail {{ display:block; }}
  .studio-stage {{ min-height:460px; }}
  .studio-topbar {{ align-items:flex-start; flex-direction:column; }}
  .studio-tabs {{ justify-content:flex-start; }}
}}
</style>
</head>
<body>
<div class="studio-shell" data-pv-structure-studio>
  <div class="studio-topbar">
    <div class="studio-brand">
      <div class="studio-logo">PV</div>
      <div>
        <p class="studio-title">{labels["title"]}</p>
        <p class="studio-subtitle">{labels["subtitle"]}</p>
      </div>
    </div>
    <div class="studio-tabs" aria-label="view modes">
      <button class="studio-tab is-active" type="button" data-mode="fixed">{labels["mode_fixed"]}</button>
      <button class="studio-tab" type="button" data-mode="tracker">{labels["mode_tracker"]}</button>
      <button class="studio-tab" type="button" data-mode="roof">{labels["mode_roof"]}</button>
    </div>
  </div>
  <div class="studio-pc-note">{labels["pc_note"]}</div>
  <div class="studio-grid">
    <aside class="studio-panel">
      <div class="studio-panel-header"><h2>{labels["component_list"]}</h2></div>
      <div class="studio-component-list">{component_buttons}</div>
    </aside>
    <section class="studio-panel studio-stage">
      <div class="studio-stage-header">
        <p class="studio-stage-title">{labels["stage_title"]}</p>
        <p class="studio-stage-sub">{labels["stage_subtitle"]}</p>
      </div>
      <div class="studio-overlay">
        <div class="studio-chip-row">
          <button class="studio-chip is-active" type="button" data-mode="fixed">{labels["layer"]}</button>
          <button class="studio-chip" type="button" data-toggle-labels>{labels["hide_labels"]}</button>
        </div>
      </div>
      <div class="studio-canvas-wrap"><canvas id="pv-structure-canvas" aria-label="{labels["stage_title"]}"></canvas></div>
      <div class="studio-toolbar">
        <div class="studio-toolbar-group">
          <button class="studio-btn" type="button" data-toggle-auto>{labels["pause_rotation"]}</button>
          <button class="studio-btn" type="button" data-reset-view>{labels["reset_view"]}</button>
        </div>
        <div class="studio-toolbar-group">
          <button class="studio-btn" type="button" data-component="pile">{labels["view_foundation"]}</button>
          <button class="studio-btn" type="button" data-component="wire">{labels["view_interface"]}</button>
        </div>
      </div>
    </section>
    <aside class="studio-panel studio-detail">
      <div class="studio-detail-title">
        <span class="studio-detail-icon" data-detail-icon></span>
        <div>
          <h2 data-detail-name>{details["module"]["name"]}</h2>
          <p data-detail-subtitle>{details["module"]["subtitle"]}</p>
        </div>
      </div>
      <div class="studio-facts">
        <div class="studio-fact"><span>{labels["role"]}</span><span data-detail-role></span></div>
        <div class="studio-fact"><span>{labels["risk"]}</span><span data-detail-risk></span></div>
        <div class="studio-fact"><span>{labels["deliverable"]}</span><span data-detail-deliverable></span></div>
      </div>
      <div class="studio-notes">
        <h3>{labels["learning_note"]}</h3>
        <p>{labels["learning_text"]}</p>
      </div>
    </aside>
  </div>
  <div class="studio-bottom">
    <div class="studio-panel studio-mini"><h3>{labels["load_path"]}</h3><p>{labels["load_path_text"]}</p></div>
    <div class="studio-panel studio-mini"><h3>{labels["review_material"]}</h3><p>{labels["review_material_text"]}</p></div>
    <div class="studio-panel studio-mini"><h3>{labels["boundary"]}</h3><p>{labels["boundary_text"]}</p></div>
  </div>
</div>
<script>
const STUDIO = {payload_json};
(function () {{
  const host = document.querySelector("[data-pv-structure-studio]");
  if (!host) return;
  const COLORS = STUDIO.colors;
  const DETAILS = STUDIO.details;
  const labels = STUDIO.labels;
  const state = {{ yaw: -0.58, pitch: 0.48, scale: 1, mode: "fixed", selected: "module", auto: true, showLabels: true, dragging: false, lastX: 0, lastY: 0, parts: [] }};
  function shade(hex, amount) {{
    const num = parseInt(hex.slice(1), 16);
    const r = Math.max(0, Math.min(255, (num >> 16) + amount));
    const g = Math.max(0, Math.min(255, ((num >> 8) & 255) + amount));
    const b = Math.max(0, Math.min(255, (num & 255) + amount));
    return `rgb(${{r}}, ${{g}}, ${{b}})`;
  }}
  function rotate(point) {{
    let {{ x, y, z }} = point;
    const cy = Math.cos(state.yaw), sy = Math.sin(state.yaw), cp = Math.cos(state.pitch), sp = Math.sin(state.pitch);
    const x1 = x * cy - z * sy;
    const z1 = x * sy + z * cy;
    return {{ x: x1, y: y * cp - z1 * sp, z: y * sp + z1 * cp }};
  }}
  function project(point, canvas) {{
    const p = rotate(point);
    const size = Math.min(canvas.width, canvas.height) * 0.13 * state.scale;
    return {{ x: canvas.width / 2 + p.x * size, y: canvas.height / 2 - p.y * size, z: p.z }};
  }}
  function cuboid(cx, cy, cz, sx, sy, sz, part, color) {{
    const x0 = cx - sx / 2, x1 = cx + sx / 2, y0 = cy - sy / 2, y1 = cy + sy / 2, z0 = cz - sz / 2, z1 = cz + sz / 2;
    const v = {{ a:{{x:x0,y:y0,z:z0}}, b:{{x:x1,y:y0,z:z0}}, c:{{x:x1,y:y1,z:z0}}, d:{{x:x0,y:y1,z:z0}}, e:{{x:x0,y:y0,z:z1}}, f:{{x:x1,y:y0,z:z1}}, g:{{x:x1,y:y1,z:z1}}, h:{{x:x0,y:y1,z:z1}} }};
    return [
      {{ points:[v.a,v.b,v.c,v.d], part, color:shade(color,-12) }},
      {{ points:[v.e,v.f,v.g,v.h], part, color:shade(color,8) }},
      {{ points:[v.d,v.c,v.g,v.h], part, color:shade(color,18) }},
      {{ points:[v.a,v.b,v.f,v.e], part, color:shade(color,-22) }},
      {{ points:[v.b,v.c,v.g,v.f], part, color:shade(color,-4) }},
      {{ points:[v.a,v.d,v.h,v.e], part, color:shade(color,4) }}
    ];
  }}
  function scene() {{
    const faces = [];
    faces.push(...cuboid(0, -0.42, 0, 7.8, 0.14, 3.9, "ground", COLORS.ground));
    const tiltDrop = state.mode === "tracker" ? 0.05 : state.mode === "roof" ? 0.18 : 0.34;
    for (let row = 0; row < 2; row += 1) {{
      for (let col = 0; col < 4; col += 1) {{
        faces.push(...cuboid(-2.7 + col * 1.8, 1.25 - row * tiltDrop, -0.65 + row * 1.2, 1.55, 0.06, 0.9, "module", COLORS.module));
      }}
    }}
    [-1.35, 0.55].forEach((z) => faces.push(...cuboid(0, 0.92, z, 7.1, 0.12, 0.12, "purlin", COLORS.purlin)));
    faces.push(...cuboid(0, 0.58, -0.9, 7.2, 0.16, 0.14, "beam", COLORS.beam));
    faces.push(...cuboid(0, 0.92, 0.9, 7.2, 0.16, 0.14, "beam", COLORS.beam));
    [-2.8, -0.9, 0.9, 2.8].forEach((x) => {{
      faces.push(...cuboid(x, 0.08, -1.05, 0.18, 1.25, 0.18, "post", COLORS.post));
      faces.push(...cuboid(x, 0.2, 0.95, 0.18, 1.45, 0.18, "post", COLORS.post));
      faces.push(...cuboid(x, -0.72, -1.05, 0.34, 0.72, 0.34, "pile", COLORS.pile));
      faces.push(...cuboid(x, -0.72, 0.95, 0.34, 0.72, 0.34, "pile", COLORS.pile));
      faces.push(...cuboid(x, 0.35, -0.05, 0.11, 1.55, 0.11, "brace", COLORS.brace));
    }});
    faces.push(...cuboid(-3.55, 0.18, 0.08, 0.08, 0.08, 2.8, "wire", COLORS.wire));
    faces.push(...cuboid(3.55, 0.18, 0.08, 0.08, 0.08, 2.8, "wire", COLORS.wire));
    return faces;
  }}
  function labelPoint(part) {{
    return ({{ module:{{x:.4,y:1.72,z:-.2}}, purlin:{{x:1.8,y:1.05,z:-1.35}}, beam:{{x:-1.6,y:.76,z:.86}}, post:{{x:-2.8,y:.55,z:.95}}, brace:{{x:.9,y:.4,z:-.1}}, pile:{{x:2.8,y:-.68,z:.95}}, ground:{{x:0,y:-.35,z:1.75}}, wire:{{x:-3.55,y:.35,z:.1}} }})[part];
  }}
  function drawLabel(ctx, canvas, text, point, color) {{
    const p = project(point, canvas);
    ctx.save(); ctx.font = "12px sans-serif"; const width = ctx.measureText(text).width + 22;
    ctx.fillStyle = "rgba(255,255,255,.88)"; ctx.strokeStyle = "rgba(63,55,40,.16)"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.roundRect(p.x - width / 2, p.y - 14, width, 28, 8); ctx.fill(); ctx.stroke();
    ctx.fillStyle = color; ctx.beginPath(); ctx.arc(p.x - width / 2 + 11, p.y, 4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#202830"; ctx.fillText(text, p.x - width / 2 + 20, p.y + 4); ctx.restore();
  }}
  function render(canvas, ctx) {{
    const width = canvas.clientWidth, height = canvas.clientHeight, ratio = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {{ canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio); }}
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "rgba(255,251,242,.55)"; ctx.fillRect(0, 0, width, height);
    state.parts = scene().map((face) => {{
      const pts = face.points.map((point) => project(point, {{ width, height }}));
      const avgZ = pts.reduce((sum, p) => sum + p.z, 0) / pts.length;
      return {{ ...face, pts, avgZ }};
    }}).sort((a, b) => a.avgZ - b.avgZ);
    state.parts.forEach((face) => {{
      ctx.save(); ctx.globalAlpha = face.part === state.selected ? 1 : .82; ctx.beginPath();
      face.pts.forEach((p, index) => index ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
      ctx.closePath(); ctx.fillStyle = face.color; ctx.strokeStyle = face.part === state.selected ? "rgba(60,75,110,.68)" : "rgba(48,42,34,.18)";
      ctx.lineWidth = face.part === state.selected ? 2.2 : .8; ctx.fill(); ctx.stroke(); ctx.restore();
    }});
    if (state.showLabels) drawLabel(ctx, {{ width, height }}, DETAILS[state.selected].name, labelPoint(state.selected), DETAILS[state.selected].color);
  }}
  function pointInPolygon(x, y, pts) {{
    let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {{
      const xi = pts[i].x, yi = pts[i].y, xj = pts[j].x, yj = pts[j].y;
      const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / ((yj - yi) || .0001) + xi);
      if (intersect) inside = !inside;
    }}
    return inside;
  }}
  function hitTest(x, y) {{
    for (let i = state.parts.length - 1; i >= 0; i -= 1) if (pointInPolygon(x, y, state.parts[i].pts)) return state.parts[i].part;
    return null;
  }}
  function selectPart(part) {{
    if (!DETAILS[part]) return;
    state.selected = part;
    host.querySelectorAll("[data-component]").forEach((button) => button.classList.toggle("is-active", button.dataset.component === part));
    const detail = DETAILS[part];
    host.querySelector("[data-detail-icon]").style.setProperty("--detail-color", detail.color);
    host.querySelector("[data-detail-name]").textContent = detail.name;
    host.querySelector("[data-detail-subtitle]").textContent = detail.subtitle;
    host.querySelector("[data-detail-role]").textContent = detail.role;
    host.querySelector("[data-detail-risk]").textContent = detail.risk;
    host.querySelector("[data-detail-deliverable]").textContent = detail.deliverable;
  }}
  const canvas = host.querySelector("#pv-structure-canvas");
  const ctx = canvas.getContext("2d");
  host.querySelectorAll("[data-component]").forEach((button) => button.addEventListener("click", () => selectPart(button.dataset.component)));
  host.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => {{ state.mode = button.dataset.mode; host.querySelectorAll("[data-mode]").forEach((item) => item.classList.toggle("is-active", item === button)); }}));
  host.querySelector("[data-reset-view]").addEventListener("click", () => {{ state.yaw = -0.58; state.pitch = 0.48; state.scale = 1; }});
  host.querySelector("[data-toggle-auto]").addEventListener("click", (event) => {{ state.auto = !state.auto; event.currentTarget.textContent = state.auto ? labels.pause_rotation : labels.auto_rotation; }});
  host.querySelector("[data-toggle-labels]").addEventListener("click", (event) => {{ state.showLabels = !state.showLabels; event.currentTarget.textContent = state.showLabels ? labels.hide_labels : labels.show_labels; }});
  canvas.addEventListener("pointerdown", (event) => {{
    state.dragging = true; state.auto = false; host.querySelector("[data-toggle-auto]").textContent = labels.auto_rotation;
    state.lastX = event.clientX; state.lastY = event.clientY; canvas.setPointerCapture(event.pointerId);
    const rect = canvas.getBoundingClientRect(); const part = hitTest(event.clientX - rect.left, event.clientY - rect.top); if (part) selectPart(part);
  }});
  canvas.addEventListener("pointermove", (event) => {{
    if (!state.dragging) return;
    state.yaw += (event.clientX - state.lastX) * .009; state.pitch = Math.max(-.8, Math.min(1.05, state.pitch + (event.clientY - state.lastY) * .007));
    state.lastX = event.clientX; state.lastY = event.clientY;
  }});
  canvas.addEventListener("pointerup", () => {{ state.dragging = false; }});
  canvas.addEventListener("wheel", (event) => {{ event.preventDefault(); state.scale = Math.max(.78, Math.min(1.32, state.scale - event.deltaY * .0007)); }}, {{ passive: false }});
  selectPart("module");
  function frame() {{ if (state.auto && !state.dragging) state.yaw += .004; render(canvas, ctx); requestAnimationFrame(frame); }}
  frame();
}})();
</script>
</body>
</html>
"""
