"""Gradio interface for NEOEX. Presentation is separated from math modules."""
from __future__ import annotations
import html
import random
import re
import json
from pathlib import Path
from functools import lru_cache
import sympy as sp
import gradio as gr

from .properties import PROPERTIES, PROPERTY_ORDER
from .algebra import build_algebra_steps
from .graphs import build_graph_spec, analyze_function, evaluate, X, to_javascript
from .parser import parse_math, parse_equation, parse_inequality, format_math_latex, ExpressionError
from .domain import real_domain_latex
from .exercises import make_question


CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');
:root { --bg:#050916; --panel:#0b1428; --panel2:#101d36; --line:rgba(91,154,212,.25); --cyan:#35d8ff; --blue:#397bff; --purple:#b58cff; --pink:#ff4f9a; --red:#ff657e; --green:#67f79a; --text:#e9f2ff; --muted:#91a4c4; }
body, .gradio-container { background:radial-gradient(ellipse at 12% 0%,rgba(28,74,145,.20),transparent 35%),radial-gradient(ellipse at 90% 15%,rgba(113,47,151,.13),transparent 32%),var(--bg)!important; color:var(--text)!important; font-family:Inter,sans-serif!important; }
.gradio-container { max-width:1500px!important; }
footer { display:none!important; }
#neoex-header { padding:22px 8px 16px; border-bottom:1px solid var(--line); margin-bottom:18px; }
.neoex-kicker { color:var(--cyan); font:600 11px 'JetBrains Mono'; letter-spacing:.28em; text-transform:uppercase; }
.neoex-logo { font:800 clamp(36px,5vw,58px)/.95 'Barlow Condensed',sans-serif; letter-spacing:.08em; color:#f5f9ff; text-shadow:0 0 22px rgba(53,216,255,.23); }
.neoex-logo span { color:var(--cyan); }
.neoex-sub { color:#a9b8d2; font:600 12px 'JetBrains Mono'; letter-spacing:.22em; margin-top:8px; }
.neoex-by { color:#7589aa; font:11px 'JetBrains Mono'; margin-top:10px; }
.gradio-container .tabs { border-bottom:1px solid var(--line)!important; }
.gradio-container button[role=tab] { color:#8fa5c9!important; font:700 12px 'JetBrains Mono'!important; letter-spacing:.1em; border:0!important; background:transparent!important; }
.gradio-container button[role=tab][aria-selected=true] { color:var(--cyan)!important; border-bottom:2px solid var(--cyan)!important; }
.gradio-container .block, .gradio-container .form, .gradio-container .panel { background:rgba(9,18,37,.88)!important; border:1px solid var(--line)!important; border-radius:14px!important; box-shadow:0 8px 26px rgba(0,0,0,.13)!important; }
.gradio-container input:not([type=radio]):not([type=checkbox]), .gradio-container textarea, .gradio-container select { background:#071126!important; color:#edf5ff!important; border:1px solid rgba(89,145,202,.42)!important; border-radius:9px!important; }
.gradio-container input[type=radio], .gradio-container input[type=checkbox] { accent-color:var(--cyan)!important; background:transparent!important; border:0!important; width:18px!important; height:18px!important; cursor:pointer!important; }
.gradio-container [role=radio][aria-checked=true], .gradio-container label:has(input[type=radio]:checked) { background:rgba(53,216,255,.14)!important; border-color:var(--cyan)!important; color:#f5fbff!important; box-shadow:0 0 12px rgba(53,216,255,.12)!important; }
.gradio-container [role=radio] { cursor:pointer!important; transition:background .18s ease,border-color .18s ease,box-shadow .18s ease!important; }
.gradio-container label, .gradio-container .wrap label { color:#b9c9e3!important; }
.gradio-container .prose, .gradio-container p, .gradio-container li { color:#c9d6e9; }
.gradio-container .secondary { background:#122544!important; color:#bdd7f4!important; border:1px solid rgba(53,216,255,.20)!important; }
.gradio-container button.primary { background:linear-gradient(100deg,#126c9d,#4b48ac)!important; border:1px solid rgba(53,216,255,.52)!important; color:white!important; box-shadow:0 0 18px rgba(53,216,255,.14)!important; }
.gradio-container button.stop { background:#401b34!important; }
.section-title { font:700 24px 'Barlow Condensed',sans-serif; letter-spacing:.08em; color:#f3f7ff; margin:8px 0 2px; }
.section-sub { color:var(--muted); font-size:13px; margin-bottom:12px; }
.micro-label { color:var(--cyan); font:600 10px 'JetBrains Mono'; text-transform:uppercase; letter-spacing:.18em; }
.panel-title { color:#c9d9f2; font:700 12px 'JetBrains Mono'; letter-spacing:.1em; text-transform:uppercase; }
.stage-shell { min-height:280px; padding:22px; background:linear-gradient(140deg,rgba(13,28,55,.96),rgba(6,13,29,.98)); border:1px solid rgba(62,172,222,.3); border-radius:16px; position:relative; overflow:hidden; }
.stage-shell:before { content:''; position:absolute; inset:0; pointer-events:none; background:linear-gradient(115deg,transparent 30%,rgba(76,192,255,.035),transparent 70%); }
.stage-top { display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:34px; color:#8098bc; font:11px 'JetBrains Mono'; }
.stage-number { color:var(--cyan); letter-spacing:.15em; }
.math-display { min-height:105px; display:flex; align-items:center; justify-content:center; gap:12px; flex-wrap:wrap; color:#f4f8ff; font:600 clamp(25px,3vw,40px) 'JetBrains Mono',monospace; position:relative; z-index:1; text-align:center; }
.math-display sup { font-size:.58em; vertical-align:super; margin-left:2px; line-height:0; }
.exp-pink,.pink { color:#ff7bd5!important; }
.exp-blue,.blue { color:#66a7ff!important; }
.exp-cyan,.cyan { color:#45e6ff!important; }
.exp-gold,.gold { color:#ffc66d!important; }
.formula-plate { display:inline-flex; align-items:center; justify-content:center; flex-wrap:wrap; gap:7px; padding:20px 28px; border:1px solid rgba(53,216,255,.20); border-radius:15px; background:linear-gradient(130deg,rgba(13,32,61,.78),rgba(16,18,47,.60)); box-shadow:inset 0 0 24px rgba(53,216,255,.035),0 8px 24px rgba(0,0,0,.12); }
.equation-token { display:inline-block; animation:tokenRise .52s cubic-bezier(.2,.8,.2,1) both; animation-delay:var(--reveal-delay,0s); }
.equation-operator { display:inline-block; color:#9db4d5; padding:0 .10em; animation:tokenRise .42s ease both; }
.animated-equation sup { animation:exponentPulse 1.7s ease-in-out infinite alternate; }
.stage-shell:after { content:''; position:absolute; top:0; left:-45%; width:35%; height:2px; background:linear-gradient(90deg,transparent,var(--cyan),transparent); box-shadow:0 0 16px var(--cyan); animation:scanLine 4.6s linear infinite; }
@keyframes tokenRise { from {opacity:0;transform:translateY(12px) scale(.92);filter:blur(2px)} to {opacity:1;transform:translateY(0) scale(1);filter:blur(0)} }
@keyframes exponentPulse { from {filter:drop-shadow(0 0 1px currentColor);transform:translateY(-1px)} to {filter:drop-shadow(0 0 7px currentColor);transform:translateY(-3px)} }
@keyframes scanLine { 0%{left:-45%;opacity:0} 8%{opacity:.8} 75%{opacity:.6} 100%{left:115%;opacity:0} }
.base { color:#dff5ff; }
.exp-purple,.purple { color:var(--purple)!important; }
.exp-red,.red { color:var(--red)!important; }
.factor { display:inline-flex; align-items:center; justify-content:center; min-width:32px; min-height:36px; font-weight:700; padding:3px 4px; border-radius:8px; animation:factorIn .48s cubic-bezier(.2,.7,.2,1) both; }
.operator { color:#abb8cc; padding:0 3px; }
.result { color:var(--green); text-shadow:0 0 15px rgba(103,247,154,.3); }
.condition { color:var(--pink); font-size:.86em; }
.factor-group { display:flex; flex-direction:column; align-items:center; padding:0 10px; min-width:120px; }
.factor-row { display:flex; align-items:center; justify-content:center; gap:6px; flex-wrap:wrap; }
.brace { width:100%; min-width:95px; height:13px; border-bottom:2px solid currentColor; border-left:2px solid currentColor; border-right:2px solid currentColor; margin-top:8px; position:relative; border-radius:0 0 4px 4px; transform-origin:top; animation:braceIn .42s ease .65s both; }
@keyframes braceIn { from { opacity:0; transform:scaleY(.1); } to { opacity:1; transform:scaleY(1); } }
.group-label { font:700 17px 'JetBrains Mono'; margin-top:7px; }
.grouped-stage { display:flex; justify-content:center; align-items:flex-start; gap:26px; flex-wrap:wrap; }
.stage-legend { display:flex; justify-content:center; gap:18px; flex-wrap:wrap; margin-top:22px; color:#879bbb; font:10px 'JetBrains Mono'; letter-spacing:.04em; text-transform:uppercase; }
.stage-legend span { display:inline-flex; align-items:center; gap:7px; }
.legend-dot { width:8px; height:8px; border-radius:50%; display:inline-block; box-shadow:0 0 9px currentColor; }
.purple-dot { background:#b58cff; color:#b58cff; } .red-dot { background:#ff657e; color:#ff657e; } .pink-dot { background:#ff7bd5; color:#ff7bd5; }
@keyframes factorIn { from { opacity:0; transform:translateY(14px) scale(.86); } to { opacity:1; transform:translateY(0) scale(1); } }
.stage-shell .math-display > * { animation:factorIn .42s ease both; }
.counter { color:#91a7ca; font:11px 'JetBrains Mono'; }
.explain { min-height:64px; color:#c7d5e9; background:rgba(22,39,69,.54); border-left:2px solid var(--cyan); padding:12px 15px; border-radius:0 10px 10px 0; line-height:1.6; }
.syntax-card { padding:14px 16px; background:rgba(17,32,59,.58); border:1px solid var(--line); border-radius:12px; color:#bdcce2; font-size:12px; line-height:1.7; }
.syntax-card code { color:#66dcff; background:#07152c; padding:2px 5px; border-radius:4px; }
.syntax-line { display:flex; align-items:center; flex-wrap:wrap; gap:9px; padding:4px 0; border-bottom:1px solid rgba(91,154,212,.10); }
.syntax-line b { min-width:105px; color:#e0ebfa; }
.syntax-line > span { color:var(--cyan); font-weight:800; }
.syntax-line strong { color:#f2f7ff; font-size:14px; }
.syntax-frac { display:inline-grid; text-align:center; vertical-align:middle; line-height:1.25; }
.syntax-frac i:first-child { border-bottom:1px solid #d9e8ff; padding:0 5px 3px; font-style:normal; }
.syntax-frac i:last-child { padding-top:2px; font-style:normal; }
.syntax-foot { margin-top:12px; color:#9eb1ce; font-size:11px; line-height:1.65; }
.preview-card { background:#071329; border:1px solid rgba(53,216,255,.30); border-radius:12px; padding:18px 20px; min-height:78px; display:flex; align-items:center; justify-content:center; color:#eff7ff; font-size:clamp(20px,2.1vw,29px); text-align:center; overflow-x:auto; }
.domain-preview { width:100%; margin-top:14px; padding:12px 15px; border:1px solid rgba(181,140,255,.25); border-left:3px solid var(--purple); border-radius:9px; background:rgba(20,28,57,.62); text-align:left; }
.domain-preview-label { color:#bda5ff; font:600 10px 'JetBrains Mono'; letter-spacing:.14em; text-transform:uppercase; margin-bottom:6px; }
.domain-preview-formula { color:#f0f5ff; font-size:clamp(16px,1.7vw,22px); overflow-x:auto; padding:3px 0; }
.domain-preview-note { color:#9fb2d0; font-size:11px; line-height:1.55; margin-top:5px; }

.gradio-container textarea { min-height:104px!important; padding:15px 16px!important; font-size:17px!important; line-height:1.55!important; resize:vertical!important; }
.gradio-container input:not([type=radio]):not([type=checkbox]) { min-height:46px!important; padding:10px 13px!important; font-size:16px!important; }
.algebra-step-card { min-height:250px; margin:8px 0; padding:22px 25px; border:1px solid rgba(53,216,255,.28); border-radius:15px; background:linear-gradient(145deg,rgba(11,25,49,.98),rgba(6,13,29,.98)); box-shadow:inset 0 0 28px rgba(53,216,255,.04); }
.algebra-step-top { color:var(--cyan); font:600 11px 'JetBrains Mono'; letter-spacing:.14em; text-transform:uppercase; }
.algebra-step-title { margin-top:14px; color:#f5f8ff; font:700 21px 'Barlow Condensed',sans-serif; letter-spacing:.035em; }
.algebra-equation { min-height:100px; display:flex; justify-content:center; align-items:center; padding:20px 4px; color:#f5f8ff; font-size:clamp(21px,2.8vw,32px); overflow-x:auto; }
.algebra-explanation { border-left:2px solid var(--purple); padding:11px 15px; background:rgba(25,34,66,.45); border-radius:0 9px 9px 0; line-height:1.65; color:#cbd8ec; }
.exercise-options fieldset { display:grid!important; grid-template-columns:repeat(auto-fit,minmax(230px,1fr))!important; gap:10px!important; }
.exercise-options label { min-height:54px!important; padding:13px 15px!important; border:1px solid rgba(91,154,212,.30)!important; border-radius:11px!important; background:rgba(9,23,45,.92)!important; color:#edf5ff!important; font-size:16px!important; }
.exercise-options label:has(input:checked) { background:rgba(53,216,255,.14)!important; border-color:var(--cyan)!important; box-shadow:0 0 14px rgba(53,216,255,.13)!important; }
.exercise-level label { min-height:42px!important; padding:8px 15px!important; }
.exercise-options [role=radio] { min-height:54px!important; padding:13px 15px!important; border:1px solid rgba(91,154,212,.30)!important; border-radius:11px!important; background:rgba(9,23,45,.92)!important; color:#edf5ff!important; font-size:16px!important; }
.exercise-options [role=radio][aria-checked=true] { background:rgba(53,216,255,.14)!important; border-color:var(--cyan)!important; box-shadow:0 0 14px rgba(53,216,255,.13)!important; }
.exercise-prompt { line-height:1.7; }
.exercise-prompt sup { color:#ff7bd5; font-size:.68em; }

.analysis-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr)); gap:12px; align-items:stretch; width:100%; min-width:0; }
.exercise-prompt { padding:22px; font-size:21px; color:#f1f7ff; background:linear-gradient(120deg,rgba(12,29,55,.9),rgba(13,19,43,.9)); border:1px solid var(--line); border-radius:12px; }
.exercise-option-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:10px 0; }
.exercise-choice { padding:14px 16px; border:1px solid var(--line); border-radius:10px; background:#09172d; color:#e7f1ff; font-size:17px; }
.exercise-letter { color:var(--cyan); font:700 12px 'JetBrains Mono'; margin-right:8px; }
.analysis-item { box-sizing:border-box; min-width:0; min-height:112px; padding:14px 16px; border:1px solid var(--line); border-radius:11px; background:rgba(12,25,47,.8); display:flex; flex-direction:column; align-items:flex-start; justify-content:flex-start; overflow:hidden; }
.analysis-name { color:#6acff2; font:600 10px/1.4 'JetBrains Mono'; text-transform:uppercase; letter-spacing:.08em; white-space:normal; overflow-wrap:anywhere; width:100%; }
.analysis-value { color:#e0ebfa; margin-top:9px; font-size:14px; line-height:1.55; min-width:0; width:100%; max-width:100%; overflow-wrap:anywhere; white-space:normal; }
.analysis-value.analysis-math { overflow-x:auto; overflow-y:hidden; padding:2px 0 5px; }
.analysis-value.analysis-math mjx-container { display:block!important; max-width:100%!important; overflow-x:auto!important; overflow-y:hidden!important; margin:0!important; padding:1px 0 4px; }
.analysis-text { color:#e0ebfa; margin-top:9px; width:100%; min-width:0; font:500 13px/1.6 Inter,sans-serif; white-space:normal; overflow-wrap:break-word; word-break:normal; }
.analysis-item.analysis-wide { grid-column:1 / -1; min-height:92px; }
.footer-neoex { text-align:center; border-top:1px solid var(--line); margin-top:26px; padding:16px; color:#657da2; font:10px 'JetBrains Mono'; letter-spacing:.12em; }

/* NEOEX: generous spacing, neon exponent identity and animated block algebra. */
.property-info { padding:20px 23px!important; line-height:1.7; color:#dceaff; }
.property-info strong { color:#f8fbff; display:block; margin-bottom:7px; font-size:15px; }
.property-info .rule-line { color:#83dfff; margin-bottom:6px; font-size:16px; }
.property-info p { margin:5px 0 0; color:#b9cbe4; }
.gradio-container .prose { padding:10px 14px!important; }
.gradio-container .block .prose p, .gradio-container .block .prose h1, .gradio-container .block .prose h2, .gradio-container .block .prose h3 { margin-left:4px!important; margin-right:4px!important; }
.gradio-container .block .prose p { line-height:1.7!important; }
.syntax-card { padding:18px 20px!important; line-height:1.95!important; }
.syntax-line { padding:7px 0!important; }
.gradio-container textarea { padding:17px 18px!important; min-height:132px!important; line-height:1.65!important; }
.gradio-container .input-container, .gradio-container .wrap { min-width:0; }
.math-display sup[class*="exp-"] { filter:drop-shadow(0 0 5px currentColor); }
.math-display sup.exp-blue { color:#63aaff!important; text-shadow:0 0 5px #2588ff,0 0 13px rgba(53,139,255,.9),0 0 22px rgba(53,139,255,.45)!important; }
.math-display sup.exp-red { color:#ff617d!important; text-shadow:0 0 5px #ff405f,0 0 13px rgba(255,64,95,.9),0 0 22px rgba(255,64,95,.45)!important; }
.math-display sup.exp-cyan { color:#40eaff!important; text-shadow:0 0 5px #20dfff,0 0 14px rgba(32,223,255,.9)!important; }
.math-display sup.exp-gold { color:#ffd36b!important; text-shadow:0 0 5px #ffba36,0 0 14px rgba(255,186,54,.9)!important; }
.math-display sup.exp-purple { color:#c39aff!important; text-shadow:0 0 5px #a36cff,0 0 14px rgba(163,108,255,.9)!important; }
.math-display sup.exp-pink { color:#ff83d0!important; text-shadow:0 0 5px #ff4fc0,0 0 14px rgba(255,79,192,.9)!important; }
.power-visual { width:min(100%,920px); margin:0 auto; display:flex; flex-direction:column; align-items:center; gap:20px; position:relative; z-index:2; }
.power-equation { font:700 clamp(34px,5vw,58px) 'JetBrains Mono',monospace; color:#eef7ff; text-align:center; padding:14px 22px; border:1px solid rgba(71,181,255,.3); background:rgba(4,13,31,.65); border-radius:16px; box-shadow:inset 0 0 25px rgba(53,216,255,.06),0 0 22px rgba(53,216,255,.07); animation:factorIn .5s ease both; }
.power-equation sup { font-size:.55em; vertical-align:super; line-height:0; }
.power-base { color:#eef7ff!important; }
.power-inner-note { color:#8ecff4; text-align:center; font:600 11px 'JetBrains Mono'; letter-spacing:.10em; line-height:1.7; text-transform:uppercase; max-width:850px; padding:0 10px; text-shadow:0 0 10px rgba(53,216,255,.16); }
.power-blue { color:#63aaff!important; text-shadow:0 0 5px #2588ff,0 0 13px rgba(53,139,255,.95),0 0 24px rgba(53,139,255,.6); }
.power-red { color:#ff617d!important; text-shadow:0 0 5px #ff405f,0 0 13px rgba(255,64,95,.95),0 0 24px rgba(255,64,95,.55); }
.power-gold { color:#ffd36b!important; text-shadow:0 0 5px #ffba36,0 0 14px rgba(255,186,54,.95); }
.power-block-grid { display:flex; align-items:stretch; justify-content:center; gap:15px; width:100%; flex-wrap:wrap; }
.power-block { min-width:145px; flex:1 1 145px; max-width:230px; border:1px solid rgba(255,97,125,.65); border-radius:14px; padding:15px 12px; background:linear-gradient(145deg,rgba(65,20,49,.34),rgba(10,20,43,.94)); box-shadow:0 0 12px rgba(255,75,110,.12),inset 0 0 15px rgba(255,75,110,.05); animation:blockBloom .55s cubic-bezier(.2,.8,.2,1) both; animation-delay:var(--delay,0s); }
.power-block-label { text-align:center; color:#ff8296; font:600 10px 'JetBrains Mono'; letter-spacing:.12em; margin-bottom:12px; }
.power-block-math { text-align:center; font:700 clamp(25px,3vw,36px) 'JetBrains Mono'; color:#ecf5ff; white-space:nowrap; }
.power-block-math sup { font-size:.55em; }
.power-factor-row { display:flex; align-items:center; justify-content:center; gap:7px; flex-wrap:wrap; font:700 clamp(25px,3vw,34px) 'JetBrains Mono'; }
.power-factor { min-width:34px; padding:7px 8px; border-radius:9px; text-align:center; background:rgba(50,128,255,.12); border:1px solid rgba(99,170,255,.35); color:#63aaff; text-shadow:0 0 8px rgba(53,139,255,.9); box-shadow:inset 0 0 12px rgba(53,139,255,.10),0 0 10px rgba(53,139,255,.13); animation:factorIn .5s cubic-bezier(.2,.8,.2,1) both; animation-delay:var(--delay,0s); }
.power-dot { color:#b9cbe4; padding:0 1px; }
.power-group-label { color:#ff8296; font:600 10px 'JetBrains Mono'; text-transform:uppercase; letter-spacing:.1em; text-align:center; margin-top:11px; }
.power-count-grid { display:grid; grid-template-columns:repeat(2,minmax(150px,240px)); gap:14px; justify-content:center; width:100%; }
.power-count-card { border:1px solid rgba(53,216,255,.32); border-radius:12px; padding:16px; text-align:center; background:rgba(8,24,49,.9); animation:blockBloom .55s ease both; }
.power-count-number { display:block; font:800 34px 'Barlow Condensed'; margin-bottom:5px; color:#f4f8ff; }
.power-count-caption { color:#a9bddb; font:11px 'JetBrains Mono'; letter-spacing:.07em; text-transform:uppercase; }
.power-equivalence { color:#eaf5ff; font:700 clamp(24px,4vw,36px) 'JetBrains Mono'; text-align:center; padding:8px; animation:tokenRise .5s ease both; }
@keyframes blockBloom { from { opacity:0; transform:translateY(14px) scale(.93); filter:brightness(.65); } to { opacity:1; transform:translateY(0) scale(1); filter:brightness(1); } }
.algebra-step-card { animation:stepEnter .42s cubic-bezier(.2,.8,.2,1) both; }
.algebra-step-stack .algebra-step-card { min-height:unset; margin:10px 0; padding:18px 21px; }
.algebra-step-stack .algebra-step-title { margin-top:7px; }
.algebra-step-stack .algebra-equation { min-height:64px; padding:12px 8px!important; }
.algebra-step-stack .algebra-explanation { line-height:1.7; }
@keyframes stepEnter { from {opacity:0;transform:translateY(10px);filter:blur(2px)} to {opacity:1;transform:translateY(0);filter:blur(0)} }
.algebra-equation { overflow-x:auto; padding:24px 12px!important; }
.math-preview-title { color:var(--cyan); font:600 10px 'JetBrains Mono'; letter-spacing:.16em; text-align:left; width:100%; margin-bottom:10px; }
.preview-card { flex-direction:column; align-items:stretch; padding:20px 24px!important; min-height:100px!important; }
.preview-card .math-preview-formula { min-height:58px; display:flex; align-items:center; justify-content:center; overflow-x:auto; width:100%; }
.exercise-solution { margin-top:12px; padding:18px; border:1px solid rgba(53,216,255,.28); border-radius:14px; background:rgba(8,19,39,.86); }
.exercise-solution-verdict { font:700 14px 'JetBrains Mono'; padding:9px 12px; border-radius:9px; background:rgba(53,216,255,.08); margin-bottom:12px; }
.exercise-solution-step { padding:14px 14px 12px; margin:10px 0; border:1px solid rgba(91,154,212,.20); border-radius:11px; background:rgba(15,29,53,.72); animation:stepEnter .4s ease both; }
.exercise-solution-step h4 { color:#e8f2ff; margin:0 0 8px; font:700 16px 'Barlow Condensed'; letter-spacing:.04em; }
.exercise-solution-formula { color:#f6fbff; font-size:clamp(18px,2.3vw,26px); text-align:center; padding:9px 2px; overflow-x:auto; }
.exercise-solution-explanation { color:#bdcde4; line-height:1.65; padding:5px 4px 0; }
.exercise-final { border-color:rgba(103,247,154,.35); box-shadow:0 0 14px rgba(103,247,154,.07); }
@media(max-width:700px){ .power-count-grid{grid-template-columns:1fr 1fr}.power-block{min-width:120px;padding:12px 7px}.power-factor-row{gap:4px}.power-factor{min-width:27px;padding:6px 5px}.property-info{padding:13px!important} }


/* MathJax CHTML draws the fraction bar on the top edge of mjx-line.
   Never reset border-top: doing so makes every fraction look like two stacked terms. */
mjx-container mjx-mfrac mjx-line,
mjx-container mjx-mfrac > mjx-frac > mjx-line,
mjx-container mjx-mfrac > mjx-frac > mjx-dbox > mjx-dtable > mjx-line {
  display:block!important;
  box-sizing:border-box!important;
  width:100%!important;
  min-height:2px!important;
  height:2px!important;
  margin:.12em -.1em!important;
  border:0!important;
  border-top:2px solid #f0f6ff!important;
  background:transparent!important;
  opacity:1!important;
  overflow:visible!important;
}
.algebra-equation mjx-container mjx-mfrac mjx-line { border-top:2px solid #f5f8ff!important; }
.algebra-equation mjx-container[display="true"] { margin:0!important; min-width:max-content; }
.algebra-equation mjx-mfrac { color:#f5f8ff!important; }
.algebra-explanation mjx-container { color:#e5efff!important; }
.neoex-graph-placeholder { min-height:180px; display:grid; place-items:center; color:#8ea7cd; font:600 12px 'JetBrains Mono'; letter-spacing:.08em; border:1px dashed rgba(53,216,255,.22); border-radius:12px; background:rgba(8,19,39,.42); padding:20px; text-align:center; }
.neoex-live-graph-shell { width:100%; padding:16px; border:1px solid rgba(53,216,255,.28); border-radius:16px; background:linear-gradient(145deg,rgba(8,19,39,.98),rgba(5,12,28,.98)); box-shadow:inset 0 0 28px rgba(53,216,255,.035); }
.neoex-graph-top { display:grid; grid-template-columns:minmax(0,1fr) minmax(300px,1.25fr); gap:12px; margin-bottom:12px; }
.neoex-graph-function,.neoex-live-readout { min-width:0; padding:13px 15px; border:1px solid rgba(91,154,212,.22); border-radius:11px; background:rgba(15,29,54,.88); }
.neoex-graph-function { color:#eaf4ff; overflow-x:auto; }
.neoex-graph-function .graph-function-label,.neoex-readout-label { display:block; color:#39ddff; font:700 10px 'JetBrains Mono'; letter-spacing:.14em; text-transform:uppercase; margin-bottom:7px; }
.neoex-live-readout { display:flex; flex-direction:column; justify-content:center; gap:5px; color:#eaf4ff; font-size:14px; }
.neoex-live-readout .readout-line { line-height:1.6; overflow-x:auto; }
.neoex-live-readout .readout-line strong { color:#72f5a4; }
.neoex-live-readout .readout-substitution { color:#d5e5fa; font-size:clamp(14px,1.5vw,18px); }
.neoex-live-readout .readout-result { color:#72f5a4!important; font-weight:800; white-space:nowrap; }
.neoex-live-readout .readout-result mjx-container { color:#72f5a4!important; }
.neoex-plot-area .cursor-grab { cursor:grab!important; }
.neoex-plot-area { width:100%; min-height:440px; touch-action:none; user-select:none; -webkit-user-select:none; position:relative; }
.neoex-plot-loading { position:absolute; inset:0; display:grid; place-items:center; color:#8ea7cd; font:600 12px 'JetBrains Mono'; letter-spacing:.08em; pointer-events:none; }
.neoex-plot-area .neoex-draggable-point { position:absolute!important; z-index:40!important; display:block; width:22px; height:22px; padding:0!important; margin:0!important; transform:translate(-50%,-50%); border:2px solid #effff5!important; border-radius:50%!important; background:#67f79a!important; box-shadow:0 0 0 4px rgba(103,247,154,.16),0 0 16px rgba(103,247,154,.9)!important; cursor:grab!important; touch-action:none!important; user-select:none!important; outline:none!important; }
.neoex-plot-area .neoex-draggable-point:hover,.neoex-plot-area .neoex-draggable-point.is-dragging { background:#a0ffc0!important; box-shadow:0 0 0 7px rgba(103,247,154,.22),0 0 24px rgba(103,247,154,1)!important; cursor:grabbing!important; }
.neoex-plot-area .neoex-draggable-point:focus-visible { outline:2px solid #35d8ff!important; outline-offset:5px!important; }
.neoex-plot-area .modebar { opacity:.78; }
.neoex-graph-controls { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px; }
.neoex-control-card { min-width:0; padding:13px 15px; border:1px solid rgba(91,154,212,.22); border-radius:11px; background:rgba(15,29,54,.72); }
.neoex-control-title { color:#48dcff; font:700 10px 'JetBrains Mono'; letter-spacing:.12em; text-transform:uppercase; margin-bottom:9px; }
.neoex-control-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.neoex-control-row label { color:#9fb4d3; font-size:11px; }
.neoex-control-row input[type=number] { width:82px; min-height:34px; background:#071126; border:1px solid rgba(89,145,202,.42); border-radius:7px; color:#eef6ff; padding:5px 8px; }
.neoex-graph-controls button { border:1px solid rgba(53,216,255,.35); border-radius:8px; color:#eaf6ff; background:#123055; padding:7px 12px; cursor:pointer; font-weight:700; }
.neoex-point-range { display:grid; grid-template-columns:1fr auto; align-items:center; gap:9px; margin-top:10px; }
.neoex-point-range input[type=range] { width:100%; accent-color:#67f79a; cursor:ew-resize; }
.neoex-current-x { display:inline-flex; align-items:center; gap:5px; color:#67f79a!important; font:700 12px 'JetBrains Mono'; white-space:nowrap; }
.neoex-current-x input { width:82px!important; min-width:70px!important; padding:5px 7px!important; color:#72f5a4!important; background:rgba(5,17,32,.92)!important; border:1px solid rgba(103,247,154,.48)!important; border-radius:7px!important; font:700 12px 'JetBrains Mono'!important; text-align:center; }
.neoex-current-x input:focus { outline:2px solid rgba(103,247,154,.26)!important; border-color:#67f79a!important; box-shadow:0 0 12px rgba(103,247,154,.15)!important; }
.neoex-graph-status { min-height:16px; margin-top:7px; color:#9fb4d3; font-size:11px; }
/* Graph math is rendered as Unicode text server-side: no raw TeX in this area. */
.neoex-plain-math,.analysis-math-text { font-family:"Cambria Math","STIX Two Math",Georgia,serif!important; font-size:clamp(17px,1.7vw,22px); line-height:1.55; letter-spacing:.01em; color:#f0f6ff; overflow-wrap:anywhere; }
.neoex-canvas-domain .neoex-plain-math { font-size:15px; }
.analysis-math-text { font-size:clamp(15px,1.4vw,19px); }
@media(max-width:760px){ .neoex-graph-top,.neoex-graph-controls{grid-template-columns:1fr}.neoex-live-graph-shell{padding:10px}.neoex-plot-area{min-height:360px}.neoex-control-row input[type=number]{width:72px} }
@media(max-width:760px){ .analysis-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:10px}.analysis-item{min-height:96px;padding:12px 13px}.analysis-item.analysis-wide{grid-column:1 / -1}.analysis-value{font-size:13px} }
@media(max-width:460px){ .analysis-grid{grid-template-columns:1fr}.analysis-item.analysis-wide{grid-column:auto} }

.neoex-canvas-shell { width:100%; min-width:0; padding:14px; border:1px solid rgba(53,216,255,.28); border-radius:16px; background:linear-gradient(145deg,rgba(8,19,39,.98),rgba(5,12,28,.98)); box-sizing:border-box; }
.neoex-canvas-top { display:grid; grid-template-columns:minmax(0,1fr) minmax(260px,1fr); gap:12px; margin-bottom:12px; }
.neoex-canvas-function,.neoex-canvas-readout { min-width:0; padding:12px 14px; border:1px solid rgba(91,154,212,.22); border-radius:11px; background:rgba(15,29,54,.88); color:#eaf4ff; overflow-wrap:anywhere; }
.neoex-canvas-label { display:block; color:#39ddff; font:700 10px 'JetBrains Mono'; letter-spacing:.14em; margin-bottom:7px; }
.neoex-canvas-readout { display:flex; flex-direction:column; gap:5px; justify-content:center; }
.neoex-canvas-readout .readout-x { color:#72f5a4; font:700 14px 'JetBrains Mono'; }
.neoex-canvas-readout .readout-y { color:#eef6ff; font-size:clamp(16px,1.7vw,20px); font-weight:700; line-height:1.65; overflow-wrap:anywhere; }
.neoex-canvas-readout .readout-y sup { font-size:.66em; line-height:0; vertical-align:super; }
.neoex-canvas-wrap { width:100%; height:clamp(350px,52vw,520px); min-height:320px; overflow:hidden; border:1px solid rgba(53,216,255,.2); border-radius:12px; background:#050d20; touch-action:none; }
.neoex-canvas-wrap canvas { display:block; width:100%!important; height:100%!important; min-width:0; max-width:100%; box-sizing:border-box; cursor:crosshair; touch-action:none; outline:none; }
.neoex-canvas-wrap canvas:focus-visible { outline:2px solid #35d8ff; outline-offset:-3px; }
.neoex-canvas-wrap canvas.is-dragging { cursor:grabbing; }
.neoex-canvas-output { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px; }
.neoex-canvas-output > div { min-width:0; padding:10px 12px; border-radius:9px; border:1px solid rgba(91,154,212,.2); background:rgba(15,29,54,.72); color:#c9d9f2; font-size:12px; line-height:1.6; overflow-wrap:anywhere; }
.neoex-canvas-output strong { color:#43e5ff; display:block; font:700 10px 'JetBrains Mono'; margin-bottom:5px; letter-spacing:.1em; }
.neoex-canvas-controls { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:10px; }
.neoex-canvas-card { min-width:0; padding:12px; border:1px solid rgba(91,154,212,.22); border-radius:10px; background:rgba(15,29,54,.72); }
.neoex-canvas-card-title { color:#48dcff; font:700 10px 'JetBrains Mono'; letter-spacing:.11em; margin-bottom:9px; }
.neoex-canvas-card .control-row { display:flex; align-items:center; flex-wrap:wrap; gap:7px; margin:5px 0; }
.neoex-canvas-card label { color:#a9bddc; font-size:11px; }
.neoex-canvas-card input[type=number],.neoex-canvas-card input[type=text] { width:78px; min-width:60px; min-height:32px; padding:4px 7px; background:#071126; color:#eef6ff; border:1px solid rgba(89,145,202,.42); border-radius:7px; }
.neoex-canvas-card input[type=range] { width:100%; accent-color:#67f79a; cursor:ew-resize; }
.neoex-canvas-card button { border:1px solid rgba(53,216,255,.35); border-radius:8px; color:#eaf6ff; background:#123055; padding:7px 10px; cursor:pointer; font-weight:700; font-size:11px; }
.neoex-canvas-card input[type=checkbox] { accent-color:#35d8ff; }
.neoex-canvas-card .green-x { color:#67f79a; font:700 12px 'JetBrains Mono'; white-space:nowrap; }
.neoex-canvas-card .green-x input { border-color:rgba(103,247,154,.52); color:#72f5a4; font-family:'JetBrains Mono'; text-align:center; }
.neoex-canvas-status { color:#91a9cc; font-size:11px; min-height:17px; margin-top:6px; }
@media(max-width:950px){ .neoex-canvas-controls{grid-template-columns:repeat(2,minmax(0,1fr))}.neoex-canvas-top{grid-template-columns:1fr 1fr} }
@media(max-width:650px){ .neoex-canvas-controls,.neoex-canvas-top,.neoex-canvas-output{grid-template-columns:1fr}.neoex-canvas-shell{padding:9px}.neoex-canvas-wrap{height:380px}.neoex-canvas-card input[type=number],.neoex-canvas-card input[type=text]{width:72px} }


@media(max-width:700px){ .stage-shell{padding:14px;min-height:240px}.math-display{font-size:24px}.formula-plate{padding:15px 12px;max-width:100%}.algebra-step-card{padding:16px;min-height:220px}.algebra-step-title{font-size:19px}.gradio-container textarea{min-height:90px!important}.exercise-options fieldset{grid-template-columns:1fr!important}.gradio-container .tabs{overflow-x:auto} }
"""



MATHJAX_BUNDLE = Path(__file__).with_name("assets") / "mathjax" / "tex-svg-full.js"
MATHJAX_ASSET_DIR = MATHJAX_BUNDLE.parent.resolve()
from urllib.parse import quote as _url_quote
MATHJAX_SCRIPT_URL = "/gradio_api/file=" + _url_quote(str(MATHJAX_BUNDLE.resolve()), safe="/:")

MATHJAX_HEAD = f"""
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['\\\\(','\\\\)'], ['$','$']], displayMath: [['\\\\[','\\\\]'], ['$$','$$']] }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'], enableMenu: false }},
  svg: {{ fontCache: 'global' }},
  startup: {{
    typeset: false,
    ready: function () {{
      MathJax.startup.defaultReady();
      window.__NEOEX_MATHJAX_READY__ = true;
      window.dispatchEvent(new Event('neoex-mathjax-ready'));
    }}
  }}
}};
</script>
<script defer src="{MATHJAX_SCRIPT_URL}" onerror="window.dispatchEvent(new Event('neoex-mathjax-failed'))"></script>
<script>
(function(){{
  'use strict';
  const selector = [
    '.preview-card', '.analysis-value', '.exercise-prompt', '.exercise-options',
    '.algebra-step-card', '.syntax-card', '.exercise-solution', '.property-info',
    '.neoex-canvas-math', '.neoex-canvas-domain-math', '.domain-preview-formula',
    '.math-preview-formula'
  ].join(',');
  const pending = new Set();
  let observer = null, mathReady = !!window.__NEOEX_MATHJAX_READY__;
  let flushing = false, scheduled = false, failed = false, fallbackTimer = null;

  function fallback(item){{
    if(!item || !item.isConnected || item.dataset.neoexMathRendered === 'fallback') return;
    const value = item.getAttribute('data-neoex-tex-fallback');
    if(value === null) return;
    item.textContent = value;
    item.classList.add('neoex-math-fallback');
    item.dataset.neoexMathRendered = 'fallback';
  }}
  function failAll(){{
    if(failed) return;
    failed = true;
    if(fallbackTimer !== null) clearTimeout(fallbackTimer);
    document.querySelectorAll('[data-neoex-tex-fallback]').forEach(fallback);
    pending.clear();
  }}
  function collect(root){{
    if(!root || root.nodeType !== 1) return;
    const add = item => {{
      if(!item || !item.isConnected || item.dataset.neoexMathRendered === 'fallback' || item.dataset.neoexMathBusy === '1') return;
      pending.add(item);
    }};
    if(root.matches && root.matches(selector)) add(root);
    if(root.querySelectorAll) root.querySelectorAll(selector).forEach(add);
  }}
  function schedule(){{
    if(!mathReady || failed || scheduled || flushing || !pending.size) return;
    scheduled = true;
    requestAnimationFrame(flush);
  }}
  async function flush(){{
    scheduled = false;
    if(!mathReady || failed || flushing) return;
    flushing = true;
    try{{
      if(window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) await window.MathJax.startup.promise;
      while(pending.size){{
        const batch = Array.from(pending); pending.clear();
        for(const item of batch){{
          if(!item.isConnected || item.dataset.neoexMathRendered === 'fallback') continue;
          try{{
            item.dataset.neoexMathBusy = '1';
            if(window.MathJax.typesetClear) window.MathJax.typesetClear([item]);
            await window.MathJax.typesetPromise([item]);
            item.dataset.neoexMathRendered = '1';
          }}catch(error){{
            console.warn('NEOEX: falha na renderização matemática.', error);
            fallback(item);
          }}finally{{ delete item.dataset.neoexMathBusy; }}
        }}
      }}
    }}catch(error){{
      console.warn('NEOEX: MathJax não concluiu a inicialização.', error);
      failAll();
    }}finally{{ flushing = false; schedule(); }}
  }}
  function startObserver(){{
    if(observer || !document.body) return;
    observer = new MutationObserver(records => {{
      for(const record of records){{
        const target = record.target && (record.target.nodeType === 1 ? record.target : record.target.parentElement);
        if(target && target.closest && target.closest('mjx-container,mjx-assistive-mml,.neoex-canvas-wrap,[data-neoex-math-busy="1"]')) continue;
        const added = Array.from(record.addedNodes || []);
        const onlyMathJax = added.length > 0 && added.every(node => node.nodeType === 1 && (
          (node.matches && node.matches('mjx-container,mjx-assistive-mml')) ||
          (node.querySelector && node.querySelector('mjx-container,mjx-assistive-mml'))
        ));
        if(onlyMathJax) continue;
        added.forEach(collect);
        if(target) collect(target);
      }}
      schedule();
    }});
    observer.observe(document.body, {{childList:true, subtree:true}});
    collect(document.documentElement);
  }}
  function onReady(){{
    if(!window.MathJax || !window.MathJax.typesetPromise) return;
    mathReady = true;
    if(fallbackTimer !== null) clearTimeout(fallbackTimer);
    startObserver(); collect(document.documentElement); schedule();
  }}
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startObserver, {{once:true}});
  else startObserver();
  window.addEventListener('neoex-mathjax-ready', onReady);
  window.addEventListener('neoex-mathjax-failed', failAll, {{once:true}});
  if(window.__NEOEX_MATHJAX_READY__) onReady();
  fallbackTimer = setTimeout(() => {{ if(!mathReady) failAll(); }}, 12000);
  window.NEOEX_typeset = function(root){{ collect(root); schedule(); }};
  window.NEOEX_mathFallback = failAll;

  // Auto-pair grouping delimiters in the algebra editor; Backspace remains native.
  document.addEventListener('keydown', function(event){{
    const target = event.target;
    if(!target || !(target.matches('textarea') || target.matches('input')) || !target.closest('#neoex-algebra-input')) return;
    const pairs = {{'(':')','[':']','{{': '}}'}};
    const close = pairs[event.key];
    if(close && !event.ctrlKey && !event.metaKey && !event.altKey){{
      const start = target.selectionStart, end = target.selectionEnd, value = target.value;
      event.preventDefault();
      target.setRangeText(event.key + value.slice(start,end) + close, start, end, 'end');
      target.setSelectionRange(start+1,start+1);
      target.dispatchEvent(new Event('input',{{bubbles:true}}));
      return;
    }}
    if([')',']','}}'].includes(event.key) && target.selectionStart === target.selectionEnd){{
      const at = target.selectionStart;
      if(target.value[at] === event.key){{ event.preventDefault(); target.setSelectionRange(at+1,at+1); }}
    }}
  }}, true);
}})();
</script>
"""

_GRAPH_RUNTIME = Path(__file__).with_name("graph_runtime.js").read_text(encoding="utf-8")
MATHJAX_HEAD += "\n<script>\n" + _GRAPH_RUNTIME + "\n</script>"
GRAPH_HTML_JS_ON_LOAD = r"""
if(window.NEOEX_attachGraphHost) window.NEOEX_attachGraphHost(element);
else window.addEventListener('neoex-runtime-ready', function(){ window.NEOEX_attachGraphHost && window.NEOEX_attachGraphHost(element); }, {once:true});
"""

def _animate_formula_markup(formula: str) -> str:
    """Color every superscript and reveal individual mathematical tokens."""
    palette = ("blue", "red", "cyan", "pink", "gold", "purple")
    exponent_index = 0
    sup_pattern = re.compile(r"<sup(?P<attrs>[^>]*)>(?P<body>.*?)</sup>", re.I | re.S)

    def color_sup(match):
        nonlocal exponent_index
        attrs = match.group("attrs") or ""
        classes = re.search(r"class=['\"]([^'\"]*)['\"]", attrs)
        existing = classes.group(1) if classes else ""
        color = palette[exponent_index % len(palette)]
        exponent_index += 1
        if not re.search(r"exp-(purple|red|pink|blue|cyan|gold)", existing):
            if classes:
                attrs = attrs[:classes.start(1)] + existing + " exp-" + color + attrs[classes.end(1):]
            else:
                attrs += f" class='exp-{color}'"
        body = match.group("body")
        # An exponent may itself contain a sum or product (e.g. -5+3 or 3·2).
        # Color each constituent exponent separately so the origins remain visible.
        if not re.search(r"class=['\"][^'\"]*exp-(purple|red|pink|blue|cyan|gold)", body):
            token_pattern = re.compile(r"(?<![A-Za-z0-9])([+−-]?\s*(?:\d+(?:/\d+)?|[A-Za-z]+))(?![A-Za-z0-9])")
            body_parts = []
            last = 0
            inner_index = 0
            for token_match in token_pattern.finditer(body):
                body_parts.append(body[last:token_match.start()])
                inner_color = palette[inner_index % len(palette)]
                body_parts.append(f"<span class='exp-{inner_color}'>{token_match.group(1)}</span>")
                inner_index += 1
                last = token_match.end()
            body_parts.append(body[last:])
            body = "".join(body_parts)
        return f"<sup{attrs}>{body}</sup>"

    superscript_translation = {
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "⁻": "-", "⁺": "+", "⁽": "(", "⁾": ")",
        "ⁿ": "n", "ᵐ": "m", "ˣ": "x", "ʸ": "y",
    }
    superscript_chars = "".join(superscript_translation)
    unicode_sup = re.compile(rf"(?<=[A-Za-z0-9)])([{re.escape(superscript_chars)}]+)")
    formula = unicode_sup.sub(
        lambda match: "<sup>" + "".join(superscript_translation[ch] for ch in match.group(1)) + "</sup>",
        formula,
    )
    formula = sup_pattern.sub(color_sup, formula)
    # Animate text nodes without touching authored HTML tags or attributes.
    parts = re.split(r"(<[^>]+>)", formula)
    token_index = 0
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        tokens = re.split(r"(\s+|[=+−\-·/*()])", part)
        decorated = []
        for token in tokens:
            if not token or token.isspace():
                decorated.append(token)
            elif token in {"·", "*", "/", "+", "−", "-", "=", "(", ")"}:
                symbol = "·" if token == "*" else token
                decorated.append(f"<span class='equation-operator' style='--reveal-delay:{token_index*.055:.3f}s'>{symbol}</span>")
                token_index += 1
            else:
                decorated.append(f"<span class='equation-token' style='--reveal-delay:{token_index*.055:.3f}s'>{token}</span>")
                token_index += 1
        parts[i] = "".join(decorated)
    return "".join(parts)


def _power_of_power_visual(index: int) -> str:
    def blue(delay=0):
        return f"<span class='power-factor power-blue' style='--delay:{delay:.2f}s'>5</span>"
    dot = "<span class='power-dot'>·</span>"
    if index == 0:
        return "<div class='power-visual'><div class='power-equation'><span class='power-red'>(</span><span class='power-base'>5<sup class='power-blue'>2</sup></span><span class='power-red'>)</span><sup class='power-red'>3</sup></div><div class='power-inner-note'>AZUL: 2 FATORES POR BLOCO · VERMELHO: 3 BLOCOS</div></div>"
    if index == 1:
        blocks = "".join(f"<div class='power-block' style='--delay:{i*.14:.2f}s'><div class='power-block-label'>BLOCO {i+1} / 3</div><div class='power-block-math'><span class='power-red'>(</span><span class='power-base'>5<sup class='power-blue'>2</sup></span><span class='power-red'>)</span></div></div>" for i in range(3))
        return f"<div class='power-visual'><div class='power-equivalence'><span class='power-red'>(</span><span class='power-base'>5<sup class='power-blue'>2</sup></span><span class='power-red'>)</span><sup class='power-red'>3</sup> → três cópias</div><div class='power-block-grid'>{blocks}</div><div class='power-inner-note'>O EXPOENTE EXTERNO 3 CRIA TRÊS BLOCOS IGUAIS</div></div>"
    if index == 2:
        blocks = "".join(f"<div class='power-block' style='--delay:{i*.18:.2f}s'><div class='power-block-label'>BLOCO {i+1} / 3</div><div class='power-factor-row'>{blue(i*.12)}{dot}{blue((i+.5)*.12)}</div><div class='power-group-label'>2 fatores azuis</div></div>" for i in range(3))
        return f"<div class='power-visual'><div class='power-inner-note'>ABRIMOS CADA EXPOENTE 2: CADA BLOCO VIRA 5 · 5</div><div class='power-block-grid'>{blocks}</div></div>"
    if index == 3:
        blocks = "".join(f"<div class='power-block' style='--delay:{i*.14:.2f}s'><div class='power-block-label'>GRUPO {i+1} · ORIGEM EXTERNA 3</div><div class='power-factor-row'>{blue(i*.08)}{dot}{blue((i+.5)*.08)}</div><div class='power-group-label'>2 fatores</div></div>" for i in range(3))
        return f"<div class='power-visual'><div class='power-block-grid'>{blocks}</div><div class='power-equivalence'><span class='power-blue'>2 fatores por bloco</span> × <span class='power-red'>3 blocos</span></div></div>"
    if index == 4:
        factors = "".join(blue(i*.09) + (dot if i < 5 else "") for i in range(6))
        return f"<div class='power-visual'><div class='power-inner-note'>OS PARÊNTESES SE ABREM; AS SEIS BASES PERMANECEM AZUIS</div><div class='power-equation' style='width:100%'><div class='power-factor-row'>{factors}</div></div></div>"
    if index == 5:
        return "<div class='power-visual'><div class='power-count-grid'><div class='power-count-card'><span class='power-count-number power-blue'>2</span><span class='power-count-caption'>fatores por bloco</span></div><div class='power-count-card'><span class='power-count-number power-red'>3</span><span class='power-count-caption'>blocos iguais</span></div></div><div class='power-equivalence'>2 + 2 + 2 = 6</div><div class='power-equivalence'><span class='power-blue'>2</span> · <span class='power-red'>3</span> = <span class='power-gold'>6</span></div></div>"
    if index == 6:
        return "<div class='power-visual'><div class='power-equation'>5<sup><span class='power-blue'>2</span><span class='power-red'> · 3</span></sup> = 5<sup class='power-gold'>6</sup></div><div class='power-inner-note'>EXPOENTE INTERNO × EXPOENTE EXTERNO = EXPOENTE TOTAL</div></div>"
    return "<div class='power-visual'><div class='power-equation'>5<sup class='power-gold'>6</sup> = <span style='color:#70f4a0;text-shadow:0 0 14px #45ff99'>15 625</span></div><div class='power-inner-note'>TRÊS BLOCOS DE DOIS FATORES = SEIS FATORES</div></div>"


def _prop_stage_html(prop_key: str, example_label: str, index: int) -> str:
    example = next(e for e in PROPERTIES[prop_key].examples if e.label == example_label)
    step = example.steps[index]
    total = len(example.steps)
    visual = step.visual
    formula = step.formula
    # Flagship demonstrations use dedicated factor/block visuals.
    canonical = prop_key == "mult" and example_label == "3³ · 3⁵"
    nested_power = prop_key == "power" and example_label == "(5²)³"
    factor = lambda color, delay: f"<span class='factor {color}' style='animation-delay:{delay:.2f}s'>3</span>"
    if nested_power:
        display = _power_of_power_visual(index)
    elif canonical and visual == "grouped":
        purple_factors = "<span class='equation-operator'>·</span>".join(factor("purple", i*.12) for i in range(3))
        red_factors = "<span class='equation-operator'>·</span>".join(factor("red", i*.12) for i in range(5))
        display = f"""
        <div class='grouped-stage'>
          <div class='factor-group' style='color:#b58cff'><div class='factor-row'>{purple_factors}</div><div class='brace'></div><div class='group-label'>3</div><div class='micro-label'>fatores · origem roxa</div></div>
          <div class='factor-group' style='color:#ff657e'><div class='factor-row'>{red_factors}</div><div class='brace'></div><div class='group-label'>5</div><div class='micro-label'>fatores · origem vermelha</div></div>
        </div>"""
    elif canonical and visual == "first_factors":
        display = "<div class='math-display animated-equation'>" + " <span class='equation-operator'>·</span> ".join(factor("purple", i*.12) for i in range(3)) + "</div>"
    elif canonical and visual == "second_factors":
        display = "<div class='math-display animated-equation'>" + " <span class='equation-operator'>·</span> ".join(factor("red", i*.12) for i in range(5)) + "</div>"
    elif canonical and visual == "joined":
        display = "<div class='math-display animated-equation'>" + " <span class='equation-operator'>·</span> ".join([factor("purple", i*.12) for i in range(3)] + [factor("red", (i+3)*.12) for i in range(5)]) + "</div>"
    else:
        decorated = _animate_formula_markup(formula or "\\text{Observe os grupos de fatores}")
        display = f"<div class='math-display animated-equation'><div class='formula-plate'>{decorated}</div></div>"
    safe_title = html.escape(step.title)
    if prop_key == "power":
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#63aaff;color:#63aaff'></i> expoente interno · fatores</span><span><i class='legend-dot red-dot'></i> expoente externo · blocos</span><span><i class='legend-dot' style='background:#ffd36b;color:#ffd36b'></i> resultado</span></div>"
    elif prop_key == "mult":
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#b58cff;color:#b58cff'></i> primeira potência</span><span><i class='legend-dot red-dot'></i> segunda potência</span><span><i class='legend-dot' style='background:#67f79a;color:#67f79a'></i> fatores reunidos</span></div>"
    elif prop_key == "div":
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#ff657e;color:#ff657e'></i> numerador</span><span><i class='legend-dot' style='background:#63aaff;color:#63aaff'></i> denominador</span><span><i class='legend-dot' style='background:#67f79a;color:#67f79a'></i> fatores restantes</span></div>"
    else:
        legend = "<div class='stage-legend'><span><i class='legend-dot' style='background:#63aaff;color:#63aaff'></i> expoente / fator de origem</span><span><i class='legend-dot red-dot'></i> segundo grupo</span><span><i class='legend-dot' style='background:#ffd36b;color:#ffd36b'></i> transformação final</span></div>"
    return f"""<div class='stage-shell'>
      <div class='stage-top'><span class='stage-number'>NEOEX / LABORATÓRIO DE POTÊNCIAS</span><span>{index+1:02d} / {total:02d}</span></div>
      <div class='micro-label' style='text-align:center;margin-bottom:22px'>{safe_title}</div>
      {display}
      {legend}
    </div>"""


def _prop_text(prop_key, example_label, index):
    example = next(e for e in PROPERTIES[prop_key].examples if e.label == example_label)
    step = example.steps[index]
    return step.explanation, f"ETAPA {index+1} DE {len(example.steps)} · {step.title}"


def _property_header(prop_key):
    item = PROPERTIES[prop_key]
    rule_math = {
        "mult": r"a^m\cdot a^n=a^{m+n}",
        "div": r"\frac{a^m}{a^n}=a^{m-n},\quad a\ne0",
        "power": r"(a^m)^n=a^{mn}",
        "product": r"(ab)^n=a^n b^n",
        "quotient": r"\left(\frac{a}{b}\right)^n=\frac{a^n}{b^n},\quad b\ne0",
        "zero": r"a^0=1,\quad a\ne0",
        "negative": r"a^{-n}=\frac{1}{a^n},\quad a\ne0",
        "fractional": r"a^{m/n}=\sqrt[n]{a^m}",
    }[prop_key]
    return (
        "<div class='property-info'>"
        f"<strong>{html.escape(item.label)}</strong>"
        f"<div class='rule-line'><span>Regra:</span> \\({rule_math}\\)</div>"
        f"<p>{html.escape(item.note)}</p>"
        "</div>"
    )


def _analysis_markdown(rows, point=None, point_x=None):
    """Render graph-analysis formulas as readable Unicode, never raw TeX.

    The graph area must remain legible even when a browser blocks or delays
    MathJax. Other sections can still use MathJax for richer typesetting.
    """
    prose_fields = {"Crescimento / decrescimento", "Continuidade", "Comportamento"}
    wide_fields = {
        "Comportamento nos extremos",
        "Crescimento / decrescimento", "Continuidade",
    }
    cells = []
    for name, value in rows:
        name_html = html.escape(str(name))
        value_str = str(value)
        is_prose = name in prose_fields or (
            name == "Assíntotas" and not any(token in value_str for token in ("\\", "=", "^", "_"))
        )
        card_class = "analysis-item analysis-wide" if name in wide_fields else "analysis-item"
        if is_prose:
            if name == "Assíntotas" and value_str.startswith(r"\text{") and value_str.endswith("}"):
                value_str = value_str[len(r"\text{"):-1]
            value_html = f"<div class='analysis-text'>{html.escape(value_str)}</div>"
        else:
            # Render a safe Unicode representation immediately; graph analysis
            # should never expose TeX source if MathJax is delayed or unavailable.
            readable = _latex_fragment_to_plain_text(value_str)
            value_html = f"<div class='analysis-value analysis-math-text'>{html.escape(readable)}</div>"
        cells.append(f"<div class='{card_class}'><div class='analysis-name'>{name_html}</div>{value_html}</div>")
    if point is not None:
        value = f"{point:.6g}"
        cells.append(
            "<div class='analysis-item'><div class='analysis-name'>Ponto selecionado</div>"
            f"<div class='analysis-text'>x = {point_x:.4g}; g(x) = {value}</div></div>"
        )
    return "<div class='analysis-grid'>" + "".join(cells) + "</div>"


_SUPERSCRIPT_CHARS = str.maketrans({
    "0":"⁰", "1":"¹", "2":"²", "3":"³", "4":"⁴", "5":"⁵", "6":"⁶", "7":"⁷", "8":"⁸", "9":"⁹",
    "+":"⁺", "-":"⁻", "=":"⁼", "(":"⁽", ")":"⁾", "n":"ⁿ", "i":"ⁱ", "x":"ˣ", "y":"ʸ", "m":"ᵐ",
})
_SUBSCRIPT_CHARS = str.maketrans({"0":"₀", "1":"₁", "2":"₂", "3":"₃", "4":"₄", "5":"₅", "6":"₆", "7":"₇", "8":"₈", "9":"₉", "+":"₊", "-":"₋", "i":"ᵢ", "n":"ₙ", "x":"ₓ"})


def _latex_fragment_to_plain_text(value: str) -> str:
    """Convert common TeX fragments into readable Unicode for graph cards.

    The graph tab uses this representation immediately, so a delayed or blocked
    MathJax script can never expose raw TeX source in its function or analysis UI.
    """
    text = str(value).replace(r"\(", "").replace(r"\)", "")
    text = text.replace(r"\[", "").replace(r"\]", "")
    text = text.replace(r"\left", "").replace(r"\right", "")
    text = text.replace(r"\big", "").replace(r"\Big", "")
    text = text.replace(r"\,", " ").replace(r"\;", " ").replace(r"\quad", " ").replace(r"\qquad", " ")
    text = text.replace(r"\!", "")

    macro_map = {
        r"\Longrightarrow": "⇒", r"\longrightarrow": "→", r"\Rightarrow": "⇒", r"\rightarrow": "→",
        r"\cdot": "·", r"\times": "×", r"\div": "÷", r"\neq": "≠", r"\ne": "≠",
        r"\geq": "≥", r"\ge": "≥", r"\leq": "≤", r"\le": "≤", r"\approx": "≈",
        r"\infty": "∞", r"\pi": "π", r"\mathbb{R}": "ℝ", r"\mathbb{Z}": "ℤ",
        r"\mathbb{N}": "ℕ", r"\emptyset": "∅", r"\varnothing": "∅", r"\setminus": "∖", r"\notin": "∉", r"\in": "∈", r"\land": " e ", r"\lor": " ou ",
    }
    for source, target in sorted(macro_map.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)

    # Preserve escaped set braces while removing TeX's grouping braces later.
    text = text.replace(r"\{", "\uE000").replace(r"\}", "\uE001")
    text = re.sub(r"\\(?:text|mathrm|operatorname)\{([^{}]*)\}", r"\1", text)

    # Convert TeX fractions with balanced groups, including nested powers/fractions.
    def read_tex_group(source: str, start: int):
        if start >= len(source) or source[start] != "{":
            return None, start
        depth = 0
        for cursor in range(start, len(source)):
            if source[cursor] == "{":
                depth += 1
            elif source[cursor] == "}":
                depth -= 1
                if depth == 0:
                    return source[start + 1:cursor], cursor + 1
        return None, start

    def convert_nested_fractions(source: str) -> str:
        output = []
        cursor = 0
        while cursor < len(source):
            token = None
            for candidate in (r"\dfrac", r"\tfrac", r"\frac"):
                if source.startswith(candidate + "{", cursor):
                    token = candidate
                    break
            if token is None:
                output.append(source[cursor])
                cursor += 1
                continue
            numerator, after_num = read_tex_group(source, cursor + len(token))
            denominator, after_den = read_tex_group(source, after_num) if numerator is not None else (None, after_num)
            if numerator is None or denominator is None:
                output.append(source[cursor])
                cursor += 1
                continue
            num = convert_nested_fractions(numerator)
            den = convert_nested_fractions(denominator)
            output.append(f"({num})/({den})")
            cursor = after_den
        return "".join(output)

    text = convert_nested_fractions(text)

    text = re.sub(r"\\sqrt\[([^\]]+)\]\{([^{}]+)\}", lambda m: f"raiz {m.group(1)} de ({m.group(2)})", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", lambda m: f"√({m.group(1)})", text)

    def superscript(match):
        body = match.group(1)
        mapped = body.translate(_SUPERSCRIPT_CHARS)
        return mapped if all(ch in "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣʸᵐ,." for ch in mapped) else f"^({body})"

    def subscript(match):
        body = match.group(1)
        mapped = body.translate(_SUBSCRIPT_CHARS)
        return mapped if all(ch in "₀₁₂₃₄₅₆₇₈₉₊₋ᵢₙₓ" for ch in mapped) else f"_({body})"

    text = re.sub(r"\^\{([^{}]+)\}", superscript, text)
    text = re.sub(r"\^([+-]?\d+|[A-Za-z])", lambda m: m.group(1).translate(_SUPERSCRIPT_CHARS), text)
    text = re.sub(r"_\{([^{}]+)\}", subscript, text)
    text = re.sub(r"_([A-Za-z0-9])", lambda m: m.group(1).translate(_SUBSCRIPT_CHARS), text)

    # Remaining TeX grouping braces are typographical grouping, not set braces.
    text = re.sub(r"\{([^{}]*)\}", r"\1", text)
    text = text.replace("\uE000", "{").replace("\uE001", "}")
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    text = text.replace("\\", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _explanation_html(explanation: str) -> str:
    return html.escape(_latex_fragment_to_plain_text(explanation))


def _steps_markdown(steps, index):
    title, formula, explanation = steps[index]
    formula = formula or r"\text{Transformação em andamento}"
    formula = formula.replace(r"\frac", r"\dfrac")
    safe_title = html.escape(title)
    safe_explanation = _explanation_html(explanation)
    return (
        f"<div class='algebra-step-card'>"
        f"<div class='algebra-step-top'>NEOEX · ETAPA {index+1:02d} / {len(steps):02d}</div>"
        f"<div class='algebra-step-title'>{safe_title}</div>"
        f"<div class='algebra-equation'>\\[\\displaystyle {formula}\\]</div>"
        f"<div class='algebra-explanation'>{safe_explanation}</div>"
        f"</div>"
    )


def _steps_stack_html(steps):
    """Render every algebra transformation as an exercise-style vertical card."""
    if not steps:
        return "<div class='algebra-step-card'>Nenhuma etapa disponível.</div>"
    cards = []
    total = len(steps)
    for index, (title, formula, explanation) in enumerate(steps, start=1):
        safe_title = html.escape(title)
        safe_explanation = _explanation_html(explanation)
        formula = formula or r"\text{Transformação em andamento}"
        formula = formula.replace(r"\frac", r"\dfrac")
        cards.append(
            "<div class='algebra-step-card'>"
            f"<div class='algebra-step-top'>NEOEX · ETAPA {index:02d} / {total:02d}</div>"
            f"<div class='algebra-step-title'>{safe_title}</div>"
            f"<div class='algebra-equation'>\\[\\displaystyle {formula}\\]</div>"
            f"<div class='algebra-explanation'>{safe_explanation}</div>"
            "</div>"
        )
    return "<div class='algebra-step-stack'>" + "".join(cards) + "</div>"


def _domain_preview_html(expr):
    formula, explanation = real_domain_latex(expr)
    return (
        "<div class='domain-preview'>"
        "<div class='domain-preview-label'>DOMÍNIO REAL</div>"
        f"<div class='domain-preview-formula'>\\({formula}\\)</div>"
        f"<div class='domain-preview-note'>{html.escape(explanation)}</div>"
        "</div>"
    )


def _algebra_preview(text):
    try:
        expr = parse_math(text, preserve_division=True, preserve_structure=True)
        rendered = format_math_latex(text)
        return (
            "<div class='preview-card'>"
            "<div class='math-preview-title'>EXPRESSÃO MATEMÁTICA FORMATADA</div>"
            f"<div class='math-preview-formula'>\\[{rendered}\\]</div>"
            f"{_domain_preview_html(expr)}"
            "</div>",
            "Expressão reconhecida. A notação matemática e o domínio real são atualizados a partir do que está no campo.",
        )
    except Exception as exc:
        return (
            "<div class='preview-card' style='color:#ff9aaa'>A pré-visualização aparecerá quando a expressão estiver sintaticamente completa.</div>",
            html.escape(str(exc)),
        )


@lru_cache(maxsize=128)
def _graph_preview(text):
    """Live graph preview in Unicode math; never expose TeX source in this tab."""
    try:
        expr = parse_math(text, preserve_division=True, preserve_structure=True)
        rendered = format_math_latex(text)
        function_display = html.escape(_latex_fragment_to_plain_text(r"g(x) = " + rendered))
        domain_formula, domain_explanation = real_domain_latex(expr)
        domain_display = html.escape(_latex_fragment_to_plain_text(domain_formula))
        explanation_display = html.escape(domain_explanation)
        return (
            "<div class='preview-card graph-preview-card'>"
            "<div class='math-preview-title'>FUNÇÃO FORMATADA</div>"
            f"<div class='math-preview-formula neoex-plain-math'>{function_display}</div>"
            "<div class='domain-preview'>"
            "<div class='domain-preview-label'>DOMÍNIO REAL</div>"
            f"<div class='domain-preview-formula neoex-plain-math'>{domain_display}</div>"
            f"<div class='domain-preview-note'>{explanation_display}</div>"
            "</div></div>"
        )
    except Exception as exc:
        return f"<div class='preview-card' style='color:#ff9aaa'>Função ainda incompleta: {html.escape(str(exc))}</div>"

def _pt_number(value):
    rounded = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return rounded.replace(".", ",") if rounded else "0"


def _safe_payload_json(spec):
    """Encode only JSON-compatible graph instructions, never raw executable input."""
    payload = {
        "function_js": spec["function_js"],
        "expression_plain": spec.get("expression_plain", spec.get("expression", "g(x)")),
        "domain_plain": _latex_fragment_to_plain_text(spec.get("domain_tex", "")),
        "constant_function": bool(spec.get("constant_function", False)),
        "constant_value": spec.get("constant_value"),
        "x_min": float(spec["x_min"]),
        "x_max": float(spec["x_max"]),
        "x_point": float(spec["x_point"]),
        "roots": [float(value) for value in spec.get("roots", [])],
        "critical_points": [float(value) for value in spec.get("critical_points", [])],
        "excluded_points": [float(value) for value in spec.get("excluded_points", [])],
        "roots_all": bool(spec.get("roots_all", False)),
        "compare": spec.get("compare", []),
        "line_y": float(spec.get("line_y", 0.0)),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    import base64
    return base64.b64encode(encoded).decode("ascii")


def _live_graph_html(spec):
    """Build a light, dependency-free Canvas graph with GeoGebra-like tools."""
    point_min = float(spec["x_min"])
    point_max = float(spec["x_max"])
    x_point = float(spec["x_point"])
    point_y = spec.get("y_point")
    encoded = _safe_payload_json(spec)
    readout_y = "fora do domínio real" if point_y is None else _pt_number(point_y)
    readout_x = _pt_number(x_point)
    expression_tex = spec["expression_tex"]
    domain_tex = spec.get("domain_tex", r"D_x=\text{não determinado automaticamente}")
    # The graph module uses immediate Unicode/HTML text for formulas. This
    # avoids a blank/raw-TeX header when MathJax is blocked in a Colab iframe.
    function_display = html.escape(_latex_fragment_to_plain_text(r"g(x) = " + expression_tex))
    domain_display = html.escape(_latex_fragment_to_plain_text(domain_tex))
    return f"""
    <div class="neoex-canvas-shell" data-neoex-graph="1" data-config="{encoded}">
      <div class="neoex-canvas-top">
        <div class="neoex-canvas-function">
          <span class="neoex-canvas-label">FUNÇÃO REPRESENTADA</span>
          <div class="neoex-canvas-math neoex-plain-math">{function_display}</div>
          <div class="neoex-canvas-domain">Domínio real: <span class="neoex-canvas-domain-math neoex-plain-math">{domain_display}</span></div>
        </div>
        <div class="neoex-canvas-readout">
          <span class="neoex-canvas-label">PONTO EM TEMPO REAL</span>
          <div class="readout-x" data-role="readout-x">x = {html.escape(readout_x)}</div>
          <div class="readout-y" data-role="readout-y">g({html.escape(readout_x)}) = {html.escape(readout_y)}</div>
        </div>
      </div>

      <div class="neoex-canvas-wrap">
        <canvas data-role="graph-canvas" tabindex="0" aria-label="Plano cartesiano interativo. Arraste o ponto verde, a reta horizontal ou o plano. Use o scroll para zoom."></canvas>
      </div>

      <div class="neoex-canvas-output">
        <div><strong>RAÍZES NO INTERVALO</strong><span data-role="roots-output">Calculando raízes…</span></div>
        <div><strong>INTERSEÇÕES COM A RETA HORIZONTAL</strong><span data-role="intersections-output">Movimente a reta para encontrar pontos com a mesma imagem.</span></div>
      </div>

      <div class="neoex-canvas-controls">
        <div class="neoex-canvas-card">
          <div class="neoex-canvas-card-title">PONTO MÓVEL · INTERVALO DE x</div>
          <div class="control-row">
            <label>mínimo</label><input data-role="point-min" type="number" step="any" value="{point_min:g}">
            <label>máximo</label><input data-role="point-max" type="number" step="any" value="{point_max:g}">
            <button type="button" data-role="apply-point-range">Aplicar</button>
          </div>
          <div class="control-row" style="margin-top:10px">
            <input data-role="point-slider" type="range" min="{point_min:g}" max="{point_max:g}" value="{x_point:g}" step="0.001">
          </div>
          <div class="control-row">
            <label class="green-x">x = <input data-role="current-x" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" aria-label="Digite a coordenada x do ponto móvel" value="{html.escape(readout_x, quote=True)}"></label>
            <span class="neoex-canvas-status" data-role="graph-status">Arraste o ponto verde, use a barra ou digite o valor de x.</span>
          </div>
        </div>

        <div class="neoex-canvas-card">
          <div class="neoex-canvas-card-title">RETA HORIZONTAL · y = c</div>
          <div class="control-row">
            <label><input data-role="line-toggle" type="checkbox" checked> mostrar reta</label>
            <label><input data-role="roots-toggle" type="checkbox" checked> mostrar raízes</label>
          </div>
          <div class="control-row">
            <label>valor de y</label><input data-role="line-y" type="text" inputmode="decimal" value="{float(spec.get('line_y', 0.0)):g}">
          </div>
          <div class="control-row">
            <input data-role="line-slider" type="range" min="-10" max="10" step="0.01" value="{float(spec.get('line_y', 0.0)):g}">
          </div>
          <div class="neoex-canvas-status">Arraste a linha violeta para cima ou para baixo. Os pontos A, B, C… mostram as interseções.</div>
        </div>

        <div class="neoex-canvas-card">
          <div class="neoex-canvas-card-title">ENQUADRAMENTO DOS EIXOS</div>
          <div class="control-row">
            <label>x mín.</label><input data-role="axis-xmin" type="number" step="any" value="{point_min:g}">
            <label>x máx.</label><input data-role="axis-xmax" type="number" step="any" value="{point_max:g}">
          </div>
          <div class="control-row">
            <label>y mín.</label><input data-role="axis-ymin" type="number" step="any" placeholder="auto">
            <label>y máx.</label><input data-role="axis-ymax" type="number" step="any" placeholder="auto">
          </div>
          <div class="control-row">
            <label><input data-role="grid-toggle" type="checkbox" checked> grade</label>
            <button type="button" data-role="apply-axes">Aplicar eixos</button>
            <button type="button" data-role="reset-view">Reenquadrar</button>
          </div>
          <div class="neoex-canvas-status">Scroll: zoom · Arrastar vazio: deslocar plano · Duplo clique: reenquadrar.</div>
        </div>
      </div>
    </div>
    """


def _render_graph(expression, compare, x_point=2.0, point_min=-8.0, point_max=8.0):
    spec = build_graph_spec(expression, point_min, point_max, x_point)
    compare_specs = []
    for index, item in enumerate((compare or "").split(";")):
        item = item.strip()
        if not item:
            continue
        comp = parse_math(item)
        if len(comp.free_symbols - {X}) > 0:
            raise ExpressionError("As funções de comparação também devem usar apenas x.")
        compare_specs.append({"label": f"h{index+1}(x)", "function_js": to_javascript(comp)})
    spec["compare"] = compare_specs
    rows = analyze_function(expression, point_min, point_max)
    graph_html = _live_graph_html(spec)
    analysis = _analysis_markdown(rows)
    state = {"mode": "normal", "expression": expression, "compare": compare,
             "x_point": spec["x_point"], "point_min": point_min, "point_max": point_max}
    return graph_html, analysis, state


def _render_parameter_graph(a, b, h, k, x_point=2.0, point_min=-8.0, point_max=8.0):
    a, b, h, k = map(float, (a, b, h, k))
    if b <= 0 or abs(b - 1) < 1e-9:
        raise ExpressionError("Para a função exponencial real usual, b deve ser positivo e diferente de 1.")
    def n(value):
        return format(float(value), ".15g")
    source = f"({n(a)})*({n(b)})^(x-({n(h)}))+({n(k)})"
    spec = build_graph_spec(source, point_min, point_max, x_point)
    spec["line_y"] = k
    rows = [
        ("Modelo", rf"g(x)={n(a)}\cdot {n(b)}^{{x-({n(h)})}}+({n(k)})"),
        ("Domínio", r"\mathbb R"),
        ("Imagem", f"({k:g}, +∞)" if a > 0 else f"(−∞, {k:g})" if a < 0 else f"{{{k:g}}}"),
        ("Assíntota horizontal", rf"y={n(k)}"),
        ("Comportamento", "crescente" if (b > 1 and a > 0) or (0 < b < 1 and a < 0) else "decrescente" if (b > 1 and a < 0) or (0 < b < 1 and a > 0) else "constante"),
    ]
    return _live_graph_html(spec), _analysis_markdown(rows), {
        "mode": "parameter", "a": a, "b": b, "h": h, "k": k,
        "expression": source, "compare": "", "x_point": spec["x_point"],
        "point_min": point_min, "point_max": point_max,
    }


def _superscript_html(value: str) -> str:
    mapping = {"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹","-":"⁻","+":"⁺","x":"ˣ","y":"ʸ","n":"ⁿ","i":"ⁱ","(":"⁽",")":"⁾"}
    return "".join(mapping.get(ch, ch) for ch in value)


def _pretty_exercise_text(value: str) -> str:
    safe = html.escape(str(value))
    safe = re.sub(r"\^\(([^)]*)\)", lambda m: f"<sup>{html.escape(m.group(1))}</sup>", safe)
    safe = re.sub(r"\^([+-]?\d+|[A-Za-z])", lambda m: f"<sup>{html.escape(m.group(1))}</sup>", safe)
    safe = safe.replace("*", " · ")
    return safe


def _pretty_exercise_choice(value: str) -> str:
    safe = str(value).replace("*", " · ")
    safe = re.sub(r"\^\(([^)]*)\)", lambda m: _superscript_html(m.group(1)), safe)
    safe = re.sub(r"\^([+-]?\d+|[A-Za-z])", lambda m: _superscript_html(m.group(1)), safe)
    return safe


def _exercise_prompt(q):
    return f"<div class='exercise-prompt'>◆ &nbsp; {_pretty_exercise_text(q['prompt'])}</div>"


def _exercise_radio_choices(q):
    letters = "ABCD"
    return [(f"{letters[i]}   ·   {_pretty_exercise_choice(value)}", letters[i]) for i, value in enumerate(q['options'])]


def _exercise_solution_html(q, selected, correct):
    selected_text = q["options"]["ABCD".index(selected)]
    correct_letter = "ABCD"[q["options"].index(q["answer"])]
    if correct:
        verdict = "<span style='color:#70f4a0'>✓ RESPOSTA CORRETA</span>"
    else:
        verdict = (
            "<span style='color:#ff8296'>✕ RESPOSTA INCORRETA</span>"
            f"<div class='exercise-solution-explanation'>Você marcou <b>{html.escape(_pretty_exercise_choice(selected_text))}</b>. "
            f"A alternativa correta é <b>{correct_letter}</b>: <b>{html.escape(_pretty_exercise_choice(q['answer']))}</b>.</div>"
        )
    solution_steps = q.get("solution_steps", [])
    cards = []
    for index, (title, formula, explanation) in enumerate(solution_steps, 1):
        final_class = " exercise-final" if index == len(solution_steps) else ""
        cards.append(
            f"<div class='exercise-solution-step{final_class}'>"
            f"<h4>ETAPA {index:02d} · {html.escape(title)}</h4>"
            f"<div class='exercise-solution-formula'>\\[{formula}\\]</div>"
            f"<div class='exercise-solution-explanation'>{html.escape(explanation)}</div>"
            "</div>"
        )
    return (
        "<div class='exercise-solution'>"
        f"<div class='exercise-solution-verdict'>{verdict}</div>"
        "<h3 style='color:#eaf5ff;margin:8px 0 12px'>Resolução explicada, etapa por etapa</h3>"
        + "".join(cards)
        + "</div>"
    )


def build_app():
    prop_keys = [(PROPERTIES[k].label,k) for k in PROPERTY_ORDER]
    first_prop = PROPERTY_ORDER[0]
    first_example = PROPERTIES[first_prop].examples[0].label
    first_step = _prop_stage_html(first_prop, first_example, 0)
    first_text, first_counter = _prop_text(first_prop, first_example, 0)
    initial_question = make_question("Básico")
    # Graphs are deliberately lazy-loaded. The Canvas renderer initializes
    # only after the user opens the graph laboratory.
    initial_graph_html = "<div class='neoex-graph-placeholder'>Abra esta aba para inicializar o laboratório gráfico.</div>"
    initial_analysis = "<div class='analysis-grid'><div class='analysis-item analysis-wide'><div class='analysis-name'>ANÁLISE MATEMÁTICA</div><div class='analysis-text'>A análise será calculada quando o primeiro gráfico for carregado.</div></div></div>"
    initial_state = None

    with gr.Blocks(title="NEOEX — EXPONENCIAL LAB") as demo:
        gr.HTML("""<div id='neoex-header'><div class='neoex-kicker'>Laboratório matemático interativo</div><div class='neoex-logo'>NEO<span>EX</span></div><div class='neoex-sub'>EXPONENCIAL LAB</div><div class='neoex-by'>DESENVOLVIDO POR PH - Δ</div></div>""")
        with gr.Tabs():
            with gr.Tab("01 · PROPRIEDADES"):
                gr.Markdown("<div class='section-title'>PROPRIEDADES DA POTENCIAÇÃO</div><div class='section-sub'>Observe os fatores surgirem, serem agrupados e transformados. Avance no seu próprio ritmo.</div>")
                with gr.Row():
                    prop_choice = gr.Dropdown(choices=prop_keys, value=first_prop, label="PROPRIEDADE", scale=2)
                    prop_example = gr.Dropdown(choices=[e.label for e in PROPERTIES[first_prop].examples], value=first_example, label="EXEMPLO", scale=2)
                prop_rule = gr.HTML(_property_header(first_prop))
                prop_stage = gr.HTML(first_step)
                prop_explain = gr.Markdown(first_text, elem_classes=["explain"])
                prop_counter = gr.Markdown(first_counter, elem_classes=["counter"])
                with gr.Row():
                    prop_start = gr.Button("INICIAR DEMONSTRAÇÃO", variant="primary")
                    prop_prev = gr.Button("← PASSO ANTERIOR")
                    prop_next = gr.Button("PRÓXIMO PASSO →", variant="primary")
                    prop_reset = gr.Button("REINICIAR")
                with gr.Row():
                    prop_play = gr.Button("▶ REPRODUZIR", variant="secondary")
                    prop_pause = gr.Button("Ⅱ PAUSAR", variant="secondary")
                    prop_speed = gr.Dropdown(choices=[("Muito rápido · 0,6 s",0.6),("Rápido · 1,0 s",1.0),("Normal · 1,5 s",1.5),("Lento · 2,0 s",2.0),("Muito lento · 3,0 s",3.0)], value=1.5, label="INTERVALO ENTRE ETAPAS", interactive=True)
                prop_idx = gr.State(0)
                timer = gr.Timer(value=1.5, active=False)

                def prop_select(pk, ex=None):
                    exs = [e.label for e in PROPERTIES[pk].examples]
                    chosen = ex if ex in exs else exs[0]
                    return gr.Dropdown(choices=exs, value=chosen), _property_header(pk), 0, _prop_stage_html(pk,chosen,0), *_prop_text(pk,chosen,0)

                def prop_example_select(pk, ex):
                    return 0, _prop_stage_html(pk,ex,0), *_prop_text(pk,ex,0)

                def prop_move(pk, ex, idx, delta):
                    example = next(e for e in PROPERTIES[pk].examples if e.label == ex)
                    new = max(0,min(len(example.steps)-1,idx+delta))
                    return new, _prop_stage_html(pk,ex,new), *_prop_text(pk,ex,new)

                prop_choice.change(prop_select, [prop_choice,prop_example], [prop_example,prop_rule,prop_idx,prop_stage,prop_explain,prop_counter])
                prop_example.change(prop_example_select, [prop_choice,prop_example], [prop_idx,prop_stage,prop_explain,prop_counter])
                prop_start.click(lambda pk,ex: (0,_prop_stage_html(pk,ex,0),*_prop_text(pk,ex,0),gr.Timer(active=False)), [prop_choice,prop_example], [prop_idx,prop_stage,prop_explain,prop_counter,timer])
                prop_prev.click(lambda pk,ex,i: (*prop_move(pk,ex,i,-1),gr.Timer(active=False)), [prop_choice,prop_example,prop_idx], [prop_idx,prop_stage,prop_explain,prop_counter,timer])
                prop_next.click(lambda pk,ex,i: (*prop_move(pk,ex,i,1),gr.Timer(active=False)), [prop_choice,prop_example,prop_idx], [prop_idx,prop_stage,prop_explain,prop_counter,timer])
                prop_reset.click(lambda pk,ex: (0,_prop_stage_html(pk,ex,0),*_prop_text(pk,ex,0),gr.Timer(active=False)), [prop_choice,prop_example], [prop_idx,prop_stage,prop_explain,prop_counter,timer])
                prop_play.click(lambda speed: gr.Timer(value=float(speed),active=True), prop_speed, timer)
                prop_pause.click(lambda: gr.Timer(active=False), None, timer)
                prop_speed.change(lambda speed: gr.Timer(value=float(speed),active=False), prop_speed, timer)
                def tick(pk, ex, idx, speed):
                    example = next(e for e in PROPERTIES[pk].examples if e.label == ex)
                    new = min(len(example.steps)-1,idx+1)
                    active = new < len(example.steps)-1
                    return new,_prop_stage_html(pk,ex,new),*_prop_text(pk,ex,new),gr.Timer(value=float(speed),active=active)
                timer.tick(tick,[prop_choice,prop_example,prop_idx,prop_speed],[prop_idx,prop_stage,prop_explain,prop_counter,timer])

            with gr.Tab("02 · ÁLGEBRA"):
                gr.Markdown("<div class='section-title'>LABORATÓRIO ALGÉBRICO</div><div class='section-sub'>Insira uma expressão, acompanhe a pré-visualização e examine as transformações.</div>")
                with gr.Row():
                    with gr.Column(scale=3):
                        alg_examples = gr.Dropdown(choices=["(x² − x³)/(x³ + x⁵)", "x³ + x²", "(x + 2)³", "(x³ + 2x²)/(x + 2)", "2²ˣ − 5·2ˣ + 4", "Expressão personalizada"], value="(x² − x³)/(x³ + x⁵)", label="EXEMPLOS PREPARADOS")
                        alg_input = gr.Textbox(value="(x^2-x^3)/(x^3+x^5)", label="EXPRESSÃO MATEMÁTICA", lines=4, elem_id="neoex-algebra-input", placeholder="Ex.: (x^2-x^3)/(x^3+x^5)", info="Use ^ para expoentes. Parênteses, colchetes e chaves são fechados automaticamente; veja a expressão formatada logo abaixo.")
                        alg_preview = gr.HTML(r"<div class='preview-card'>\(\frac{x^2-x^3}{x^3+x^5}\)</div>")
                        alg_status = gr.Markdown("Sintaxe reconhecida")
                        alg_operation = gr.Dropdown(choices=["Simplificar","Fatorar","Desenvolver","Colocar em evidência","Simplificar fração","Resolver equação","Resolver inequação"], value="Simplificar", label="OPERAÇÃO")
                        alg_run = gr.Button("EXECUTAR TRANSFORMAÇÃO", variant="primary")
                    with gr.Column(scale=2):
                        gr.HTML("""<div class='syntax-card'><div class='panel-title'>GUIA DE SINTAXE</div><div class='syntax-line'><b>Expoente</b> <code>2^3</code> <span>→</span> <strong>2³</strong></div><div class='syntax-line'><b>Multiplicação</b> <code>2*3</code> <span>→</span> <strong>2 · 3</strong></div><div class='syntax-line'><b>Divisão</b> <code>(x^2+1)/(x+1)</code> <span>→</span> <strong class='syntax-frac'><i>x² + 1</i><i>x + 1</i></strong></div><div class='syntax-line'><b>Raiz</b> <code>sqrt(16)</code> <span>→</span> <strong>√16</strong></div><div class='syntax-line'><b>Parênteses</b> <code>(x+2)^3</code> <span>→</span> <strong>(x+2)³</strong></div><div class='syntax-line'><b>Funções</b> <code>sin(x)</code> <span>→</span> <strong>sin(x)</strong></div><div class='syntax-foot'>Use * para multiplicar e explicite a multiplicação: <code>2*x</code>. Variáveis podem ser letras como x, y, a ou b. A entrada é interpretada por um analisador matemático restrito; não executa código Python.</div></div>""")
                gr.Markdown("### Resolução explicada, etapa por etapa")
                alg_step = gr.HTML("<div class='algebra-step-card'>As transformações aparecerão aqui após executar a operação.</div>")
                alg_count = gr.Markdown("Aguardando expressão", elem_classes=["counter"])
                def algebra_input_changed(source):
                    preview, status = _algebra_preview(source)
                    return preview, status, gr.update(value="Expressão personalizada")
                alg_preview_event = alg_input.input(algebra_input_changed,[alg_input],[alg_preview,alg_status,alg_examples],trigger_mode="always_last")
                def choose_alg_example(label):
                    if label == "Expressão personalizada":
                        return gr.skip(), gr.skip(), gr.skip()
                    mapping = {
                        "(x² − x³)/(x³ + x⁵)":"(x^2-x^3)/(x^3+x^5)",
                        "x³ + x²":"x^3+x^2", "(x + 2)³":"(x+2)^3",
                        "(x³ + 2x²)/(x + 2)":"(x^3+2*x^2)/(x+2)",
                        "2²ˣ − 5·2ˣ + 4":"2^(2x)-5*2^x+4"
                    }
                    value=mapping[label]
                    preview,status=_algebra_preview(value)
                    return value,preview,status
                alg_examples.change(choose_alg_example,alg_examples,[alg_input,alg_preview,alg_status])
                def run_alg(source, operation):
                    try:
                        steps, result, restrictions = build_algebra_steps(source, operation)
                        count = rf"{len(steps)} etapas apresentadas · resultado: \({result}\)"
                        return _steps_stack_html(steps), count
                    except Exception as exc:
                        message = html.escape(str(exc))
                        return f"<div class='algebra-step-card' style='border-color:#ff7188'>Não foi possível executar: {message}</div>", "Verifique a entrada. A expressão não foi transformada."
                alg_run.click(run_alg,[alg_input,alg_operation],[alg_step,alg_count])

            with gr.Tab("03 · GRÁFICOS") as graph_tab:
                gr.Markdown("<div class='section-title'>GRÁFICOS E COMPORTAMENTO DAS FUNÇÕES</div><div class='section-sub'>Digite uma função de uma variável, mova o ponto verde, investigue as raízes e desloque a reta horizontal para descobrir quais abscissas produzem a mesma imagem.</div>")
                with gr.Row():
                    with gr.Column(scale=3):
                        graph_examples=gr.Dropdown(choices=[("2ˣ","2^x"),("3ˣ","3^x"),("(1/2)ˣ","(1/2)^x"),("x²","x^2"),("x³","x^3"),("x⁴ − 3x² + 2","x^4-3x^2+2"),("1/x","1/x"),("xˣ","x^x"),("(2²x + 3xˣ)/(4x²)","(2^2x + 3x^x)/4x^2"),("x² + 2","x^2+2"),("2ˣ + 3","2^x+3")],value="2^x",label="FUNÇÕES PREPARADAS")
                        graph_input=gr.Textbox(value="2^x",label="g(x) =",lines=2,info="A expressão será convertida para notação matemática na pré-visualização.")
                        graph_preview=gr.HTML("<div class='preview-card graph-preview-card'><div class='math-preview-title'>FUNÇÃO FORMATADA</div><div class='math-preview-formula neoex-plain-math'>g(x) = 2ˣ</div></div>")
                        graph_compare=gr.Textbox(value="",label="COMPARAR COM (separe por ;)",placeholder="x^2; 3^x")
                        graph_button=gr.Button("GERAR GRÁFICO E ANÁLISE",variant="primary")
                    with gr.Column(scale=2):
                        gr.HTML("""<div class='syntax-card'><div class='panel-title'>SINTAXE DE FUNÇÕES</div><div class='syntax-line'><b>Exponencial</b> <code>2^x</code> <span>→</span> <strong>2ˣ</strong></div><div class='syntax-line'><b>Potência e produto</b> <code>2^2x</code> <span>→</span> <strong>2² · x</strong></div><div class='syntax-line'><b>Expoente variável</b> <code>3x^x</code> <span>→</span> <strong>3 · xˣ</strong></div><div class='syntax-line'><b>Polinômio</b> <code>x^5-3x^2+2</code> <span>→</span> <strong>grau 5</strong></div><div class='syntax-line'><b>Fração monomial</b> <code>a/4x^2</code> <span>→</span> <strong>a/(4x²)</strong></div><div class='syntax-line'><b>Funções</b> <code>sqrt(x), sin(x), log(x)</code> <span>→</span> <strong>√x, sen x, ln x</strong></div><div class='syntax-foot'>Convenção: a multiplicação implícita liga-se antes de ÷. Assim, a/4x² é lido como a/(4x²). Use parênteses para deixar outra agrupação explícita. O gráfico é desenhado em Canvas, sem Canvas ou biblioteca externa de gráficos.</div></div>""")
                graph_plot=gr.HTML(initial_graph_html, js_on_load=GRAPH_HTML_JS_ON_LOAD, elem_id="neoex-graph-output")
                graph_analysis=gr.HTML(initial_analysis)
                graph_state=gr.State(initial_state)
                graph_loaded=gr.State(False)
                graph_preview_event=graph_input.input(
                    _graph_preview, [graph_input], [graph_preview],
                    trigger_mode="always_last", show_progress="hidden",
                    concurrency_id="neoex-graph-preview", concurrency_limit=1,
                )
                def render_graph_outputs(source, compare):
                    try:
                        graph_html, analysis_html, state = _render_graph(source, compare)
                        return graph_html, analysis_html, state, True
                    except Exception as exc:
                        message = html.escape(str(exc))
                        error_graph = (
                            "<div class='neoex-graph-placeholder' role='alert'>"
                            f"Não foi possível gerar o gráfico: {message}</div>"
                        )
                        error_analysis = (
                            "<div class='analysis-grid'><div class='analysis-item analysis-wide'>"
                            f"<div class='analysis-name'>ERRO AO CONSTRUIR O GRÁFICO</div><div class='analysis-text'>{message}</div>"
                            "</div></div>"
                        )
                        return error_graph, error_analysis, None, False

                def choose_graph(label, compare):
                    preview = _graph_preview(label)
                    graph_outputs = render_graph_outputs(label, compare)
                    return (label, preview, *graph_outputs)

                graph_examples.change(
                    choose_graph, [graph_examples, graph_compare],
                    [graph_input, graph_preview, graph_plot, graph_analysis, graph_state, graph_loaded],
                    show_progress="hidden", trigger_mode="always_last",
                    concurrency_id="neoex-graph-compute", concurrency_limit=1,
                )
                # When the user finishes editing the function (blur/Enter),
                # rebuild the actual graph as well as the live preview.
                graph_input.change(
                    render_graph_outputs, [graph_input, graph_compare],
                    [graph_plot, graph_analysis, graph_state, graph_loaded],
                    show_progress="hidden", trigger_mode="always_last",
                    concurrency_id="neoex-graph-compute", concurrency_limit=1,
                )
                graph_input.submit(
                    render_graph_outputs, [graph_input, graph_compare],
                    [graph_plot, graph_analysis, graph_state, graph_loaded],
                    show_progress="hidden", trigger_mode="always_last",
                    concurrency_id="neoex-graph-compute", concurrency_limit=1,
                )
                graph_compare.change(
                    render_graph_outputs, [graph_input, graph_compare],
                    [graph_plot, graph_analysis, graph_state, graph_loaded],
                    show_progress="hidden", trigger_mode="always_last",
                    concurrency_id="neoex-graph-compute", concurrency_limit=1,
                )

                def load_graph_on_first_open(already_loaded):
                    if already_loaded:
                        return gr.skip(), gr.skip(), gr.skip(), True
                    return render_graph_outputs("2^x", "")

                # First graph computation happens only after the user opens this tab.
                graph_tab.select(
                    load_graph_on_first_open, [graph_loaded],
                    [graph_plot, graph_analysis, graph_state, graph_loaded],
                    show_progress="hidden", trigger_mode="once",
                    concurrency_id="neoex-graph-compute", concurrency_limit=1,
                )
                graph_button.click(
                    render_graph_outputs, [graph_input, graph_compare],
                    [graph_plot, graph_analysis, graph_state, graph_loaded],
                    show_progress="minimal", trigger_mode="always_last",
                    concurrency_id="neoex-graph-compute", concurrency_limit=1,
                )
                with gr.Accordion("LABORATÓRIO DE PARÂMETROS EXPONENCIAIS",open=False):
                    gr.Markdown(r"Modelo: \(g(x)=a\cdot b^{(x-h)}+k\). A linha tracejada indica a assíntota horizontal \(y=k\).")
                    with gr.Row():
                        p_a=gr.Slider(-4,4,value=1,step=0.1,label="a · escala / reflexão")
                        p_b=gr.Slider(0.2,4,value=2,step=0.1,label="b · base (b ≠ 1)")
                    with gr.Row():
                        p_h=gr.Slider(-5,5,value=0,step=0.1,label="h · deslocamento horizontal")
                        p_k=gr.Slider(-5,5,value=0,step=0.1,label="k · deslocamento vertical")
                    p_button=gr.Button("APLICAR PARÂMETROS",variant="primary")
                    p_note=gr.Markdown("Ajuste os controles e clique em APLICAR PARÂMETROS para redesenhar a curva; assim evitamos recálculos a cada movimento do mouse.")
                    def safe_parameter(a,b,h,k,state):
                        state = state or {}
                        xp = float(state.get("x_point",2.0))
                        pmin = float(state.get("point_min",-8.0))
                        pmax = float(state.get("point_max",8.0))
                        xp = min(pmax,max(pmin,xp))
                        try:
                            graph_html, analysis_html, updated_state = _render_parameter_graph(a,b,h,k,xp,pmin,pmax)
                            return graph_html, analysis_html, updated_state, True
                        except Exception as exc:
                            return gr.skip(),f"<div class='analysis-grid'><div class='analysis-item analysis-wide'><div class='analysis-name'>ERRO NOS PARÂMETROS</div><div class='analysis-text'>{html.escape(str(exc))}</div></div></div>",gr.skip(),True
                    p_button.click(
                        safe_parameter,[p_a,p_b,p_h,p_k,graph_state],
                        [graph_plot,graph_analysis,graph_state,graph_loaded],
                        show_progress="minimal", trigger_mode="always_last",
                        concurrency_id="neoex-graph-compute", concurrency_limit=1,
                    )

            with gr.Tab("04 · EXERCÍCIOS"):
                gr.Markdown("<div class='section-title'>EXERCÍCIOS</div><div class='section-sub'>Escolha o nível, marque uma alternativa e acompanhe a resolução comentada.</div>")
                exercise_level=gr.Radio(choices=["Básico","Intermediário","Difícil"],value="Básico",label="NÍVEL DE DIFICULDADE",interactive=True,elem_classes=["exercise-level"])
                exercise_new=gr.Button("SORTEAR NOVA QUESTÃO",variant="primary")
                exercise_prompt=gr.HTML(_exercise_prompt(initial_question))
                exercise_options=gr.Radio(choices=_exercise_radio_choices(initial_question),value=None,label="ALTERNATIVAS · SELECIONE UMA RESPOSTA",interactive=True,elem_classes=["exercise-options"])
                exercise_check=gr.Button("CORRIGIR RESPOSTA",variant="primary")
                exercise_feedback=gr.HTML("<div class='exercise-solution'>Escolha uma alternativa e clique em corrigir para ver a resolução completa.</div>")
                exercise_state=gr.State(initial_question)
                def new_exercise(level):
                    q=make_question(level)
                    return q,_exercise_prompt(q),gr.update(choices=_exercise_radio_choices(q),value=None),"Nova questão carregada. Marque uma alternativa."
                exercise_new.click(new_exercise,exercise_level,[exercise_state,exercise_prompt,exercise_options,exercise_feedback])
                exercise_level.change(new_exercise,exercise_level,[exercise_state,exercise_prompt,exercise_options,exercise_feedback])
                def check_exercise(q,choice):
                    if not choice:
                        return "<div class='exercise-solution'>Selecione uma alternativa antes de corrigir.</div>"
                    selected = q["options"]["ABCD".index(choice)]
                    return _exercise_solution_html(q, choice, selected == q["answer"])
                exercise_check.click(check_exercise,[exercise_state,exercise_options],[exercise_feedback])


        gr.HTML("<div class='footer-neoex'>LABORATÓRIO INTERATIVO DE MATEMÁTICA · VERSÃO 1.9 · DESENVOLVIDO POR PH - Δ</div>")
    # Bound concurrency so multiple expensive graph requests cannot saturate
    # the Colab runtime or freeze the whole application queue.
    demo.queue(max_size=8, default_concurrency_limit=1)
    return demo
