import streamlit as st
import requests
import math
import json
from datetime import datetime

st.set_page_config(page_title="MedAssist AI — Agentic", page_icon="🩺", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<script>
setTimeout(function(){
  var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
  if(sidebar && sidebar.getAttribute('aria-expanded')==='false'){
    var btn = window.parent.document.querySelector('[data-testid="collapsedControl"] button');
    if(btn) btn.click();
  }
}, 500);
</script>""", unsafe_allow_html=True)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f0efe9; }
  [data-testid="stSidebar"] {
    background: #ffffff !important; border-right: 1px solid rgba(0,0,0,0.08) !important;
    width: 300px !important; min-width: 300px !important; transform: translateX(0) !important;
    visibility: visible !important; opacity: 1 !important; display: block !important; position: relative !important;
  }
  [data-testid="stSidebar"][aria-expanded="false"],
  [data-testid="stSidebar"][aria-expanded="false"] > div {
    transform: translateX(0) !important; width: 300px !important; min-width: 300px !important;
    visibility: visible !important; opacity: 1 !important; display: block !important;
  }
  [data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"],
  [data-testid="stSidebarNavCollapseIcon"], button[data-testid="baseButton-header"] {
    display: none !important; visibility: hidden !important;
  }
  .topbar {
    background: #ffffff; border-bottom: 1px solid rgba(0,0,0,0.08); padding: 14px 24px;
    border-radius: 10px; display: flex; align-items: center; gap: 12px;
    margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  }
  .topbar-title { font-size: 20px; font-weight: 700; color: #1a1a18; }
  .topbar-title span { color: #0F6E56; }
  .agent-step {
    background: #f7f7f5; border: 1px solid rgba(0,0,0,0.07); border-left: 3px solid #0F6E56;
    border-radius: 8px; padding: 8px 14px; margin: 4px 0; font-size: 12.5px; color: #3a3a38;
  }
  .agent-step.thinking  { border-left-color: #8E44AD; background: #faf8ff; }
  .agent-step.searching { border-left-color: #2980B9; background: #f5f9ff; }
  .agent-step.routing   { border-left-color: #E67E22; background: #fff9f4; }
  .agent-step.memory    { border-left-color: #27AE60; background: #f5fff8; }
  .agent-step.done      { border-left-color: #0F6E56; background: #f0faf6; }
  .memory-card { background: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; font-size: 13px; }
  .memory-tag { display:inline-block; background:#E1F5EE; color:#0F6E56; border-radius:20px; padding:2px 10px; font-size:11px; margin:2px; }
  .result-box { background: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; padding: 18px 20px; font-size: 14px; line-height: 1.7; margin-top: 12px; }
  .drug-tag { display: inline-flex; align-items: center; gap: 6px; background: #EEEDFE; color: #534AB7; border: 1px solid rgba(83,74,183,0.2); border-radius: 20px; padding: 3px 12px; font-size: 13px; margin: 3px; }
  .metric-card { background: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; padding: 18px; margin-bottom: 10px; }
  .section-header { font-size: 18px; font-weight: 700; color: #1a1a18; margin-bottom: 4px; }
  .section-sub { font-size: 13px; color: #5f5e5a; margin-bottom: 18px; }
  .handoff-banner { background: #FFF8E1; border: 1px solid #FFD54F; border-radius: 8px; padding: 8px 14px; font-size: 13px; color: #7a5c00; margin-bottom: 10px; }
  [data-testid="stChatInput"] textarea { min-height: 38px !important; max-height: 38px !important; height: 38px !important; padding-top: 8px !important; padding-bottom: 8px !important; font-size: 13.5px !important; overflow-y: hidden !important; resize: none !important; border-radius: 10px !important; }
  [data-testid="stChatInput"] { padding-top: 4px !important; padding-bottom: 4px !important; }
  #MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
  .stButton > button { background: #0F6E56 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 500 !important; }
  .stButton > button:hover { opacity: 0.88 !important; }
  .stTextInput input, .stNumberInput input, .stSelectbox select { border-radius: 8px !important; border: 1px solid rgba(0,0,0,0.15) !important; font-size: 13px !important; }
  .stTextArea textarea { border-radius: 8px !important; border: 1px solid rgba(0,0,0,0.15) !important; font-size: 13.5px !important; }
</style>
""", unsafe_allow_html=True)

AGENTS = {
    "General Health": {
        "icon": "🩺", "color": "#0F6E56", "desc": "General medical questions & wellness",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free", "model_label": "Llama 3.3 70B",
        "system": """You are MedAssist AI — General Health specialist agent.
You have patient memory and web search results provided to you. Use them to give thorough, personalised, evidence-based answers.
Always clarify this is educational only.
If the question clearly belongs to another specialty, add on its own line at the end:
ROUTE_TO: <AgentName> — reason: <one line>""",
        "welcome": "Hello! I'm your **General Health** agent. I plan, search, remember your history, and route to specialists. How can I help?",
        "questions": ["What are common symptoms of dehydration?", "How much sleep do adults need?", "What causes frequent headaches?"],
    },
    "Cardiology": {
        "icon": "❤️", "color": "#C0392B", "desc": "Heart health, blood pressure & circulation",
        "default_model": "deepseek/deepseek-v4-flash:free", "model_label": "DeepSeek V4 Flash",
        "system": """You are MedAssist AI — Cardiology specialist agent.
You have patient memory and web search results. Answer cardiovascular health questions thoroughly.
Always encourage consulting a cardiologist.
If outside cardiology, add: ROUTE_TO: <AgentName> — reason: <one line>""",
        "welcome": "Hello! I'm your **Cardiology** agent. I search medical literature and remember your cardiac history.",
        "questions": ["How can I lower my blood pressure naturally?", "What are symptoms of a heart attack?", "What is a healthy resting heart rate?"],
    },
    "Nutrition": {
        "icon": "🥗", "color": "#27AE60", "desc": "Diet, nutrients & healthy eating",
        "default_model": "google/gemma-4-31b-it:free", "model_label": "Gemma 4 31B",
        "system": """You are MedAssist AI — Nutrition & Dietetics specialist agent.
You have patient memory and web search results. Provide evidence-based nutritional information.
Note that a registered dietitian gives personalised advice.
If outside nutrition, add: ROUTE_TO: <AgentName> — reason: <one line>""",
        "welcome": "Hello! I'm your **Nutrition** agent. I search nutritional databases and remember your dietary preferences.",
        "questions": ["What foods are high in iron?", "What are signs of vitamin D deficiency?", "How much protein do I need daily?"],
    },
    "Mental Health": {
        "icon": "🧠", "color": "#8E44AD", "desc": "Mental wellness, stress & coping",
        "default_model": "nvidia/nemotron-3-super-120b-a12b:free", "model_label": "Nemotron 120B",
        "system": """You are MedAssist AI — Mental Health specialist agent.
You have patient memory and web search results. Be compassionate and evidence-based.
Always encourage professional support. If crisis detected, immediately provide emergency resources.
If outside mental health, add: ROUTE_TO: <AgentName> — reason: <one line>""",
        "welcome": "Hello! I'm your **Mental Health** agent. I provide supportive, research-backed information.",
        "questions": ["What are coping strategies for anxiety?", "How does stress affect the body?", "What are signs of burnout?"],
    },
    "Pediatrics": {
        "icon": "👶", "color": "#2980B9", "desc": "Child health, development & vaccines",
        "default_model": "openai/gpt-oss-120b:free", "model_label": "GPT OSS 120B",
        "system": """You are MedAssist AI — Pediatrics specialist agent.
You have patient memory and web search results. Answer child health and development questions.
Always emphasize consulting a pediatrician.
If outside pediatrics, add: ROUTE_TO: <AgentName> — reason: <one line>""",
        "welcome": "Hello! I'm your **Pediatrics** agent. I search child health resources and remember your child's profile.",
        "questions": ["When should babies start solid foods?", "What vaccines does my child need?", "How do I treat a child's fever at home?"],
    },
    "Medications": {
        "icon": "💊", "color": "#E67E22", "desc": "Drug info, side effects & interactions",
        "default_model": "deepseek/deepseek-v4-flash:free", "model_label": "DeepSeek V4 Flash",
        "system": """You are MedAssist AI — Medications specialist agent.
You have patient memory and web search results. Explain drugs, interactions, side effects. Never recommend individual doses.
Always emphasize consulting a pharmacist or doctor.
If outside medications, add: ROUTE_TO: <AgentName> — reason: <one line>""",
        "welcome": "Hello! I'm your **Medications** agent. I search drug databases and remember your medication history.",
        "questions": ["What is the difference between ibuprofen and paracetamol?", "What are common antibiotic side effects?", "How do antidepressants work?"],
    },
}

AGENT_NAMES = list(AGENTS.keys())
FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-v4-flash:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "openrouter/free",
]

def init_state():
    defaults = {
        "active_agent": "General Health",
        "tab": "💬 Chat",
        "drugs": [],
        "patient_memory": {"name": "", "age": "", "conditions": [], "medications": [], "allergies": [], "notes": []},
        "handoff_banner": None,
    }
    for agent in AGENTS:
        if f"messages_{agent}" not in st.session_state:
            st.session_state[f"messages_{agent}"] = [{"role": "assistant", "content": AGENTS[agent]["welcome"]}]
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def call_llm(messages, system_prompt, api_key, model_id, max_tokens=1500, temperature=0.7):
    if not api_key or not api_key.strip():
        raise Exception("No API key. Enter your OpenRouter key in the sidebar.")
    if not api_key.startswith("sk-or"):
        raise Exception("Invalid key format. Must start with 'sk-or-v1-'.")
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json",
               "HTTP-Referer": "https://medassist.ai", "X-Title": "MedAssist AI"}
    trial_ids = [model_id] + [m for m in FALLBACK_MODELS if m != model_id]
    last_error = "Unknown error"
    for i, tid in enumerate(trial_ids):
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                json={"model": tid, "messages": [{"role": "system", "content": system_prompt}] + messages,
                      "max_tokens": max_tokens, "temperature": temperature}, timeout=90)
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot reach OpenRouter. Check your internet connection.")
        except requests.exceptions.Timeout:
            last_error = f"Timeout on {tid}"; continue
        if resp.status_code == 401: raise Exception("Invalid/expired API key.")
        if resp.status_code == 402: raise Exception("Insufficient credits at openrouter.ai. Go to openrouter.ai → Credits to top up, or use a free-tier key with no balance needed.")
        if resp.status_code in (429, 503): last_error = f"`{tid}` rate-limited"; continue
        if resp.status_code == 404: last_error = f"`{tid}` not found"; continue
        if resp.status_code >= 500: last_error = f"Server error on `{tid}`"; continue
        if not resp.ok: last_error = f"HTTP {resp.status_code}"; continue
        data = resp.json()
        if "error" in data:
            msg = data["error"].get("message", "")
            if any(w in msg.lower() for w in ["rate","limit","quota","capacity"]):
                last_error = f"Rate limit on `{tid}`"; continue
            raise Exception(msg)
        choices = data.get("choices")
        if not choices: last_error = f"Empty response from `{tid}`"; continue
        text = choices[0]["message"]["content"]
        if i > 0: text = f"*⚡ Auto-switched to `{tid}`*\n\n" + text
        return text
    raise Exception(f"All models unavailable. Last error: {last_error}")

def web_search_medical(query, api_key, model_id):
    system = """You are a medical research assistant. Provide a thorough research summary as if you searched
PubMed, Mayo Clinic, WHO, CDC, and NHS for the query. Include key findings, statistics, current guidelines.
Cite sources naturally (e.g. 'According to WHO...', 'Mayo Clinic notes...'). Max 400 words."""
    try:
        return call_llm([{"role": "user", "content": f"Search medical sources for: {query}"}],
                        system, api_key, model_id, max_tokens=600, temperature=0.3)
    except Exception as e:
        return f"Search unavailable: {e}"

def plan_response(question, agent_name, api_key, model_id):
    system = f"""You are a medical reasoning planner for the {agent_name} specialist.
Output ONLY a JSON array of 3-5 steps: [{{"step":"name","action":"what to do","type":"think|search|recall|synthesize"}}]
No other text."""
    try:
        raw = call_llm([{"role": "user", "content": question}], system, api_key, model_id, max_tokens=400, temperature=0.2)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return [
            {"step": "Understand", "action": "Parse patient intent", "type": "think"},
            {"step": "Search", "action": "Find relevant medical information", "type": "search"},
            {"step": "Synthesize", "action": "Compose evidence-based response", "type": "synthesize"},
        ]

def detect_routing(response_text):
    if "ROUTE_TO:" in response_text:
        lines = response_text.split("\n")
        for line in lines:
            if "ROUTE_TO:" in line:
                parts = line.split("ROUTE_TO:")[-1].strip()
                sep = "—" if "—" in parts else ("-" if "-" in parts else None)
                target = parts.split(sep)[0].strip() if sep else parts.strip()
                reason = parts.split(sep)[-1].replace("reason:","").strip() if sep else "Better suited specialist"
                for name in AGENT_NAMES:
                    if name.lower() in target.lower():
                        clean = "\n".join(l for l in lines if "ROUTE_TO:" not in l).strip()
                        return name, reason, clean
    return None, None, response_text

def extract_memory(message, api_key, model_id):
    system = """Extract patient health facts. Output ONLY JSON:
{"name":"","age":"","conditions":[],"medications":[],"allergies":[],"notes":[]}
If nothing to extract, output: {}"""
    try:
        raw = call_llm([{"role": "user", "content": message}], system, api_key, model_id, max_tokens=200, temperature=0.1)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        data = json.loads(raw.strip())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def update_memory(new_data):
    mem = st.session_state.patient_memory
    if new_data.get("name"): mem["name"] = new_data["name"]
    if new_data.get("age"):  mem["age"]  = new_data["age"]
    for key in ["conditions","medications","allergies","notes"]:
        for item in new_data.get(key, []):
            if item and item not in mem[key]:
                mem[key].append(item)

def memory_prompt():
    mem = st.session_state.patient_memory
    lines = []
    if mem["name"]:       lines.append(f"Patient name: {mem['name']}")
    if mem["age"]:        lines.append(f"Age: {mem['age']}")
    if mem["conditions"]: lines.append(f"Known conditions: {', '.join(mem['conditions'])}")
    if mem["medications"]:lines.append(f"Current medications: {', '.join(mem['medications'])}")
    if mem["allergies"]:  lines.append(f"Allergies: {', '.join(mem['allergies'])}")
    if mem["notes"]:      lines.append(f"Notes: {'; '.join(mem['notes'][-5:])}")
    return "\n".join(lines) if lines else "No patient history recorded yet."

def run_agentic_pipeline(user_message, agent_name, api_key, steps_ph):
    agent = AGENTS[agent_name]
    model_id = agent["default_model"]
    steps_log = []

    def log(label, detail, kind="think"):
        steps_log.append({"label": label, "detail": detail, "kind": kind})
        with steps_ph.container():
            for s in steps_log:
                st.markdown(f'<div class="agent-step {s["kind"]}">🔹 <strong>{s["label"]}</strong> — {s["detail"]}</div>', unsafe_allow_html=True)

    log("Planning", "Breaking your question into reasoning steps…", "thinking")
    plan = plan_response(user_message, agent_name, api_key, model_id)
    log("Plan ready", " → ".join(s.get("step","?") for s in plan), "thinking")

    log("Memory recall", "Loading your patient history…", "memory")
    mem_ctx = memory_prompt()
    has_mem = any([st.session_state.patient_memory["name"], st.session_state.patient_memory["conditions"], st.session_state.patient_memory["medications"]])
    log("Memory", "Patient history loaded" if has_mem else "No prior history — building from conversation", "memory")

    log("Memory update", "Scanning message for new patient facts…", "memory")
    new_facts = extract_memory(user_message, api_key, model_id)
    if new_facts:
        update_memory(new_facts)
        log("Memory saved", f"Extracted: {', '.join(f'{k}: {v}' for k,v in new_facts.items() if v)}", "memory")
    else:
        log("Memory update", "No new facts detected", "memory")

    log("Web search", f"Searching medical sources for: '{user_message[:55]}…'", "searching")
    search_results = web_search_medical(user_message, api_key, model_id)
    log("Search complete", "Medical literature retrieved", "searching")

    log("Synthesizing", "Composing evidence-based personalised response…", "thinking")

    plan_summary = " → ".join(s.get("step","?") for s in plan)
    full_system = f"""{agent["system"]}

=== PATIENT MEMORY (personalise your response with this) ===
{mem_ctx}

=== WEB SEARCH RESULTS (use as knowledge base) ===
{search_results}

=== REASONING PLAN ===
{plan_summary}

Instructions:
- Incorporate patient memory to personalise when relevant
- Reference search results naturally (e.g. "According to WHO...", "Mayo Clinic recommends...")
- Be thorough but conversational, use markdown headers
- End with a brief disclaimer
- If routing needed, add ROUTE_TO on its own line at the very end"""

    history = st.session_state[f"messages_{agent_name}"]
    response = call_llm(history, full_system, api_key, model_id, max_tokens=1500)

    route_to, route_reason, clean_response = detect_routing(response)
    if route_to:
        log("Routing", f"Handing off to {route_to} — {route_reason}", "routing")
        st.session_state.handoff_banner = {"from": agent_name, "to": route_to, "reason": route_reason}
    else:
        log("Done", "Response ready ✓", "done")
        st.session_state.handoff_banner = None

    steps_ph.empty()
    return clean_response, route_to

# SIDEBAR
with st.sidebar:
    st.markdown("### 🩺 MedAssist AI")
    st.markdown('<span style="font-size:11px;color:#0F6E56;font-weight:600;">⚡ AGENTIC MODE</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**🔑 OpenRouter API Key**")
    api_key = st.text_input("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", type="password", placeholder="sk-or-v1-...", label_visibility="collapsed", key="api_key_input")
    if api_key and api_key.startswith("sk-or"):
        st.success("✅ Connected", icon="🟢")
    elif api_key:
        st.warning("Key format looks off", icon="⚠️")
    else:
        st.caption("Get a free key at [openrouter.ai](https://openrouter.ai)")
    st.markdown("---")

    _active_sb = st.session_state.get("active_agent", "General Health")
    _ai = AGENTS[_active_sb]
    st.markdown("**🤖 Active Model**")
    st.markdown(f"""<div style="background:#f7f7f5;border:1px solid rgba(0,0,0,0.08);border-radius:8px;padding:8px 12px;font-size:12px;">
      <div style="font-weight:600;color:#1a1a18;">🧠 {_ai["model_label"]}</div>
      <div style="color:#9b9a95;margin-top:3px;font-size:10.5px;">{_ai["default_model"]}</div>
    </div>""", unsafe_allow_html=True)
    st.caption("Each specialty uses its own optimised model.")
    st.markdown("---")

    st.markdown("**🤖 Specialty Agents**")
    st.caption("Each agent: plans · searches · remembers · routes")
    for agent_name, agent_info in AGENTS.items():
        is_active = st.session_state.active_agent == agent_name
        bg = "background:#E1F5EE;border:1.5px solid #0F6E56;" if is_active else "background:#f7f7f5;border:1px solid rgba(0,0,0,0.08);"
        st.markdown(f"""<div style="{bg}border-radius:10px;padding:8px 12px;margin-bottom:5px;">
          <div style="font-size:13px;font-weight:600;color:#1a1a18;">{agent_info["icon"]} {agent_name}</div>
          <div style="font-size:11px;color:#5f5e5a;margin-top:2px;">{agent_info["desc"]}</div>
          <div style="font-size:10px;color:#9b9a95;margin-top:2px;">🧠 {agent_info["model_label"]}</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Open", key=f"agent_btn_{agent_name}", use_container_width=True, help=f"Switch to {agent_name}"):
            st.session_state.active_agent = agent_name
            st.session_state.tab = "💬 Chat"
            st.session_state.handoff_banner = None
            st.rerun()

    st.markdown("---")
    st.markdown("**🔧 Tools**")
    tab_choice = st.radio("tool", ["💬 Chat","🔍 Symptom Checker","💊 Drug Interactions","📊 BMI Calculator","🧠 Patient Memory"],
                          label_visibility="collapsed", key="tab_radio")
    st.session_state.tab = tab_choice
    st.markdown("---")

    active = st.session_state.active_agent
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state[f"messages_{active}"] = [{"role": "assistant", "content": AGENTS[active]["welcome"]}]
            st.rerun()
    with c2:
        if st.button("🧹 Clear Memory", use_container_width=True):
            st.session_state.patient_memory = {"name":"","age":"","conditions":[],"medications":[],"allergies":[],"notes":[]}
            st.rerun()
    if st.button("📥 Export Chat", use_container_width=True):
        msgs = st.session_state[f"messages_{active}"]
        lines = [f"MedAssist AI (Agentic) — {active}", datetime.now().strftime("%Y-%m-%d %H:%M"), "="*50, ""]
        for m in msgs:
            role = "You" if m["role"] == "user" else f"MedAssist ({active})"
            lines += [f"{role}:", m["content"], ""]
        lines += ["="*50, "DISCLAIMER: Educational only."]
        st.download_button("⬇️ Download", "\n".join(lines), file_name=f"medassist-{active.lower().replace(' ','-')}.txt", mime="text/plain")

# HEADER
active_agent = st.session_state.active_agent
agent = AGENTS[active_agent]
current_tab = st.session_state.tab
agent_model_id = agent["default_model"]
api_key = st.session_state.get("api_key_input", "")

TAB_META = {
    "💬 Chat":              {"icon": agent["icon"], "label": f"{active_agent} Agent",    "sublabel": agent["desc"],                              "color": agent["color"]},
    "🔍 Symptom Checker":   {"icon": "🔍",          "label": "Symptom Checker",          "sublabel": "Agentic multi-step symptom analysis",       "color": "#0F6E56"},
    "💊 Drug Interactions": {"icon": "💊",          "label": "Drug Interaction Checker", "sublabel": "Agentic drug interaction analysis",         "color": "#E67E22"},
    "📊 BMI Calculator":    {"icon": "📊",          "label": "BMI Calculator",           "sublabel": "BMI with AI health context",                "color": "#2980B9"},
    "🧠 Patient Memory":    {"icon": "🧠",          "label": "Patient Memory",           "sublabel": "View & manage your persistent health profile","color": "#8E44AD"},
}
tm = TAB_META.get(current_tab, TAB_META["💬 Chat"])

st.markdown(f"""<div class="topbar">
  <span style="font-size:26px;">{tm["icon"]}</span>
  <div>
    <div class="topbar-title">Med<span>Assist</span> AI
      <span style="font-size:11px;font-weight:500;background:#E1F5EE;color:#0F6E56;border-radius:20px;padding:2px 10px;margin-left:8px;vertical-align:middle;">⚡ AGENTIC</span>
    </div>
    <div style="font-size:11.5px;color:#5f5e5a;">
      <strong style="color:{tm["color"]};">{tm["label"]}</strong> &nbsp;·&nbsp;{tm["sublabel"]} &nbsp;·&nbsp;<em>Educational use only</em>
    </div>
  </div>
  <div style="margin-left:auto;background:#FAEEDA;border:1px solid rgba(133,79,11,0.25);border-radius:8px;padding:5px 12px;font-size:12px;color:#854F0B;">
    ⚠️ Not a substitute for professional medical advice
  </div>
</div>""", unsafe_allow_html=True)

# TAB: CHAT
if current_tab == "💬 Chat":
    msg_key = f"messages_{active_agent}"
    messages = st.session_state[msg_key]

    if st.session_state.handoff_banner:
        hb = st.session_state.handoff_banner
        st.markdown(f'<div class="handoff-banner">🔀 <strong>Agent Handoff:</strong> The <strong>{hb["from"]}</strong> agent routed you to <strong>{hb["to"]}</strong> — {hb["reason"]}</div>', unsafe_allow_html=True)
        if st.button(f"Switch to {hb['to']} Agent →"):
            st.session_state.active_agent = hb["to"]
            st.session_state.handoff_banner = None
            st.rerun()

    st.markdown(f"""<div style="background:{agent["color"]}18;border:1px solid {agent["color"]}44;border-radius:8px;
        padding:8px 14px;margin-bottom:10px;font-size:13px;color:{agent["color"]};font-weight:600;">
      {agent["icon"]} <strong>{active_agent}</strong> &nbsp;·&nbsp;
      <span style="font-weight:400;color:#5f5e5a;">{agent["desc"]}</span> &nbsp;·&nbsp;
      <span style="font-weight:400;color:#5f5e5a;">🧠 {agent["model_label"]}</span> &nbsp;·&nbsp;
      <span style="font-weight:500;color:#0F6E56;">⚡ Plans · Searches · Remembers · Routes</span>
    </div>""", unsafe_allow_html=True)

    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar=agent["icon"]):
                st.markdown(msg["content"])

    st.markdown("**Quick questions:**")
    cols = st.columns(3)
    for i, q in enumerate(agent["questions"]):
        if cols[i % 3].button(q, key=f"quick_{active_agent}_{i}", use_container_width=True):
            if not api_key:
                st.error("Please enter your OpenRouter API key in the sidebar.")
            else:
                st.session_state[msg_key].append({"role": "user", "content": q})
                steps_ph = st.empty()
                with st.spinner(f"⚡ {active_agent} agent running agentic pipeline…"):
                    try:
                        reply, _ = run_agentic_pipeline(q, active_agent, api_key, steps_ph)
                        st.session_state[msg_key].append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.session_state[msg_key].append({"role": "assistant", "content": f"⚠️ {e}"})
                st.rerun()

    user_input = st.chat_input(f"Ask the {active_agent} agent…")
    if user_input:
        if not api_key:
            st.error("Please enter your OpenRouter API key in the sidebar.")
        else:
            st.session_state[msg_key].append({"role": "user", "content": user_input})
            steps_ph = st.empty()
            with st.spinner(f"⚡ {active_agent} agent running agentic pipeline…"):
                try:
                    reply, _ = run_agentic_pipeline(user_input, active_agent, api_key, steps_ph)
                    st.session_state[msg_key].append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.session_state[msg_key].append({"role": "assistant", "content": f"⚠️ {e}"})
            st.rerun()

# TAB: PATIENT MEMORY
elif current_tab == "🧠 Patient Memory":
    st.markdown('<div class="section-header">🧠 Patient Memory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Your health profile is remembered across conversations and used by all agents to personalise responses. Agents also extract facts automatically from your messages.</div>', unsafe_allow_html=True)
    mem = st.session_state.patient_memory
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Edit Profile**")
        mem["name"] = st.text_input("Name", value=mem["name"], placeholder="e.g. Ahmed")
        mem["age"]  = st.text_input("Age",  value=mem["age"],  placeholder="e.g. 35")
        nc = st.text_input("Add condition", placeholder="e.g. Type 2 Diabetes", key="nc")
        if st.button("➕ Add Condition") and nc.strip():
            if nc.strip() not in mem["conditions"]: mem["conditions"].append(nc.strip()); st.rerun()
        nm = st.text_input("Add medication", placeholder="e.g. Metformin 500mg", key="nm")
        if st.button("➕ Add Medication") and nm.strip():
            if nm.strip() not in mem["medications"]: mem["medications"].append(nm.strip()); st.rerun()
        na = st.text_input("Add allergy", placeholder="e.g. Penicillin", key="na")
        if st.button("➕ Add Allergy") and na.strip():
            if na.strip() not in mem["allergies"]: mem["allergies"].append(na.strip()); st.rerun()
    with col2:
        st.markdown("**Current Memory**")
        conds  = "".join(f'<span class="memory-tag">{c}</span>' for c in mem["conditions"])  or '<em style="color:#9b9a95">None</em>'
        meds   = "".join(f'<span class="memory-tag">{m}</span>' for m in mem["medications"]) or '<em style="color:#9b9a95">None</em>'
        alrgs  = "".join(f'<span class="memory-tag">{a}</span>' for a in mem["allergies"])   or '<em style="color:#9b9a95">None</em>'
        st.markdown(f"""<div class="memory-card">
          <strong>👤 {mem["name"] or "Unknown"}</strong> · Age: {mem["age"] or "Unknown"}<br><br>
          <strong>🩺 Conditions:</strong><br>{conds}<br><br>
          <strong>💊 Medications:</strong><br>{meds}<br><br>
          <strong>⚠️ Allergies:</strong><br>{alrgs}
        </div>""", unsafe_allow_html=True)
        if mem["notes"]:
            st.markdown("**📝 Auto-extracted notes:**")
            for note in mem["notes"][-5:]:
                st.markdown(f'<div class="agent-step memory">📌 {note}</div>', unsafe_allow_html=True)
        st.info("💡 Agents automatically extract facts from your messages and add them here. You can also edit manually.")

# TAB: SYMPTOM CHECKER
elif current_tab == "🔍 Symptom Checker":
    st.markdown('<div class="section-header">🔍 Agentic Symptom Checker</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">The agent plans, searches medical sources, recalls your history, and reasons step-by-step.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        sc_age = st.number_input("Age", min_value=1, max_value=120, value=None, placeholder="e.g. 35")
    with col2:
        sc_sex = st.selectbox("Biological sex", ["","Male","Female","Other / prefer not to say"])
    sc_symptoms_raw = st.text_input("Symptoms (comma-separated)", placeholder="e.g. headache, fever, fatigue")
    sc_severity = st.slider("Pain / discomfort severity", 0, 10, 5)
    sc_duration = st.selectbox("Duration", ["","Less than 24 hours","1–3 days","4–7 days","1–4 weeks","More than a month"])
    sc_notes = st.text_area("Additional notes", placeholder="Optional…", height=80)

    if st.button("⚡ Run Agentic Analysis"):
        symptoms_list = [s.strip() for s in sc_symptoms_raw.split(",") if s.strip()]
        if not api_key:
            st.error("Please enter your OpenRouter API key in the sidebar.")
        elif not symptoms_list:
            st.warning("Please enter at least one symptom.")
        else:
            mem_ctx = memory_prompt()
            prompt = f"""Patient: Age {sc_age or "unknown"}, {sc_sex or "unknown sex"}
Symptoms: {", ".join(symptoms_list)} | Severity: {sc_severity}/10 | Duration: {sc_duration or "unknown"}
Notes: {sc_notes or "none"} | Patient history: {mem_ctx}
Provide: 1) Possible causes  2) Severity assessment  3) Red flags  4) Self-care  5) Recommended specialist
Use markdown headers. Be thorough and empathetic."""
            steps_ph = st.empty()
            with st.spinner("⚡ Agentic pipeline running…"):
                try:
                    steps_ph.markdown('<div class="agent-step searching">🔹 <strong>Searching</strong> — Medical literature retrieval in progress…</div>', unsafe_allow_html=True)
                    search = web_search_medical(f"symptoms: {', '.join(symptoms_list)}", api_key, agent_model_id)
                    steps_ph.markdown('<div class="agent-step done">🔹 <strong>Search complete</strong> — Synthesizing personalised response…</div>', unsafe_allow_html=True)
                    system = f"""You are a medical symptom analysis agent.
SEARCH RESULTS: {search}
PATIENT MEMORY: {mem_ctx}
Use both to provide personalised, evidence-based educational analysis."""
                    reply = call_llm([{"role": "user", "content": prompt}], system, api_key, agent_model_id, max_tokens=1800)
                    steps_ph.empty()
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown(reply)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"⚠️ {e}")

# TAB: DRUG INTERACTIONS
elif current_tab == "💊 Drug Interactions":
    st.markdown('<div class="section-header">💊 Agentic Drug Interaction Checker</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cross-references your medications with patient memory and interaction databases.</div>', unsafe_allow_html=True)
    mem_meds = st.session_state.patient_memory["medications"]
    if mem_meds and not st.session_state.drugs:
        st.info(f"💡 Found in your memory: {', '.join(mem_meds)}. Adding automatically.")
        st.session_state.drugs = list(mem_meds)
    if st.session_state.drugs:
        st.markdown("**Added medications:**")
        cols = st.columns(4)
        to_remove = None
        for i, drug in enumerate(st.session_state.drugs):
            with cols[i % 4]:
                st.markdown(f'<div class="drug-tag">💊 {drug}</div>', unsafe_allow_html=True)
                if st.button("✕", key=f"remove_drug_{i}"): to_remove = i
        if to_remove is not None:
            st.session_state.drugs.pop(to_remove); st.rerun()
        st.markdown("")
    ac, bc = st.columns([4, 1])
    with ac:
        new_drug = st.text_input("med", placeholder="Enter medication name…", label_visibility="collapsed", key="drug_input")
    with bc:
        if st.button("➕ Add", use_container_width=True):
            if new_drug.strip() and new_drug.strip() not in st.session_state.drugs:
                st.session_state.drugs.append(new_drug.strip()); st.rerun()
    st.markdown("")
    if st.button("⚡ Run Agentic Interaction Check"):
        if not api_key:
            st.error("Please enter your OpenRouter API key in the sidebar.")
        elif len(st.session_state.drugs) < 2:
            st.warning("Please add at least 2 medications.")
        else:
            mem_ctx = memory_prompt()
            drug_list = ", ".join(st.session_state.drugs)
            steps_ph = st.empty()
            with st.spinner("⚡ Searching interaction databases…"):
                try:
                    steps_ph.markdown('<div class="agent-step searching">🔹 <strong>Searching</strong> — Drug interaction databases…</div>', unsafe_allow_html=True)
                    search = web_search_medical(f"drug interactions: {drug_list}", api_key, agent_model_id)
                    steps_ph.markdown('<div class="agent-step done">🔹 <strong>Search complete</strong> — Analysing interactions…</div>', unsafe_allow_html=True)
                    prompt = f"""Check interactions between: {drug_list}. Patient history: {mem_ctx}
For each pair: severity (none/minor/moderate/major), mechanism, effects, recommendations. Include disclaimer."""
                    system = f"""You are a clinical pharmacology agent.
SEARCH RESULTS: {search}
PATIENT MEMORY: {mem_ctx}
Educational only — always recommend consulting a pharmacist."""
                    reply = call_llm([{"role": "user", "content": prompt}], system, api_key, agent_model_id, max_tokens=1800)
                    steps_ph.empty()
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown(reply)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"⚠️ {e}")

# TAB: BMI CALCULATOR
elif current_tab == "📊 BMI Calculator":
    st.markdown('<div class="section-header">📊 BMI Calculator</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Calculate your Body Mass Index and get personalised AI health context.</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: bmi_weight = st.number_input("Weight (kg)", min_value=1.0, max_value=400.0, value=None, placeholder="e.g. 70")
    with col2: bmi_height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=None, placeholder="e.g. 175")
    with col3: bmi_age    = st.number_input("Age", min_value=2, max_value=120, value=None, placeholder="e.g. 30")
    with col4: bmi_sex    = st.selectbox("Sex", ["","Male","Female"])
    if bmi_weight and bmi_height and bmi_height > 50:
        bmi = bmi_weight / math.pow(bmi_height / 100, 2)
        bmi_round = round(bmi, 1)
        if bmi < 18.5:   category, color, bar_color, emoji = "Underweight", "#185FA5", "#378ADD", "🔵"
        elif bmi < 25:   category, color, bar_color, emoji = "Normal weight", "#3B6D11", "#639922", "🟢"
        elif bmi < 30:   category, color, bar_color, emoji = "Overweight", "#854F0B", "#BA7517", "🟡"
        else:            category, color, bar_color, emoji = "Obese", "#A32D2D", "#E24B4A", "🔴"
        pct = min(max(((bmi - 10) / 35) * 100, 2), 98)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""<div class="metric-card" style="text-align:center;">
              <div style="font-size:13px;color:#5f5e5a;margin-bottom:6px;">Your BMI</div>
              <div style="font-size:52px;font-weight:800;color:{color};line-height:1;">{bmi_round}</div>
              <div style="font-size:16px;font-weight:600;color:{color};margin-top:4px;">{emoji} {category}</div>
              <div style="margin-top:14px;">
                <div style="height:8px;border-radius:20px;background:#f0efe9;overflow:hidden;">
                  <div style="height:100%;width:{pct}%;background:{bar_color};border-radius:20px;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:10px;color:#9b9a95;margin-top:4px;">
                  <span>Under</span><span>Normal</span><span>Over</span><span>Obese</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
        with c2:
            cols_range = st.columns(4)
            for i, (label, val, bg, fg) in enumerate([
                ("🔵 Underweight","< 18.5","#E6F1FB","#185FA5"),
                ("🟢 Normal","18.5–24.9","#EAF3DE","#3B6D11"),
                ("🟡 Overweight","25–29.9","#FAEEDA","#854F0B"),
                ("🔴 Obese","≥ 30","#FCEBEB","#A32D2D"),
            ]):
                with cols_range[i]:
                    st.markdown(f"""<div style="background:{bg};border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(0,0,0,0.06);">
                      <div style="font-size:10px;color:{fg};">{label}</div>
                      <div style="font-size:14px;font-weight:700;color:{fg};margin-top:3px;">{val}</div>
                    </div>""", unsafe_allow_html=True)
            st.markdown("")
            st.markdown("**⚡ Agentic AI Health Context**")
            if not api_key:
                st.caption("Enter your API key in the sidebar.")
            else:
                if st.button("Get Agentic Health Context", key="bmi_ai"):
                    mem_ctx = memory_prompt()
                    prompt = (f"BMI: {bmi_round} ({category}). Age: {bmi_age or 'unknown'}. Sex: {bmi_sex or 'unknown'}. "
                              f"Weight: {bmi_weight}kg, Height: {bmi_height}cm. Patient history: {mem_ctx}. "
                              "Provide personalised 4-5 sentence health context considering their history. One specific actionable suggestion.")
                    with st.spinner("⚡ Searching & personalising…"):
                        try:
                            search = web_search_medical(f"BMI {bmi_round} {category} health implications", api_key, agent_model_id)
                            system = f"Health information assistant. SEARCH: {search}. MEMORY: {mem_ctx}. Be concise, empathetic, personalised."
                            reply = call_llm([{"role": "user", "content": prompt}], system, api_key, agent_model_id, max_tokens=400)
                            st.info(reply)
                        except Exception as e:
                            st.error(f"⚠️ {e}")
    else:
        st.info("Enter your weight and height above to calculate your BMI.")

# FOOTER
st.markdown("---")
st.markdown("<div style='text-align:center;font-size:11.5px;color:#9b9a95;'>⚡ MedAssist AI <strong>Agentic Mode</strong> — Plans · Searches · Remembers · Routes · For <strong>educational purposes only</strong>. Always consult a qualified healthcare professional. Powered By Eng Kirollos Ashraf</div>", unsafe_allow_html=True)
