# import io
# from pathlib import Path
# import streamlit as st

# from src.pipeline import MemePipeline
# from src.utils.config import (
#     APP_NAME, APP_TAGLINE, BRAND_PRIMARY, BRAND_ACCENT, LOGO_PATH
# )

# st.set_page_config(page_title=APP_NAME, layout="wide")

# # =========================
# # Global CSS
# # =========================
# st.markdown(f"""
# <style>
# :root {{
#   --brand: {BRAND_PRIMARY};
#   --accent: {BRAND_ACCENT};
# }}
# .main-header {{
#   border-left: 8px solid var(--accent);
#   padding: .6rem 1rem; margin-bottom: 1rem;
# }}
# .template-card {{
#   background: #fff; border:1px solid #e5e7eb; border-radius: 16px;
#   padding: 14px; box-shadow: 0 2px 10px rgba(0,0,0,.06);
#   margin-bottom: 1rem;
# }}
# .template-img {{
#   width: 100%; height: 360px; object-fit: cover; border-radius: 12px;
#   background:#f6f6f6;
# }}
# .btn-row {{
#   display:flex; gap:.5rem; margin-top: .75rem;
# }}
# .btn {{
#   flex:1; border:1px solid #d0d5dd; background:#fff; border-radius:10px;
#   padding:.55rem .8rem; font-weight:600; color:#111; cursor:pointer;
# }}
# .btn:hover {{ border-color: var(--accent); }}
# /* Modal overlay */
# .modal-overlay {{
#   position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 999;
# }}
# .modal {{
#   position: fixed; top: 5vh; left: 50%; transform: translateX(-50%);
#   width: min(1100px, 92vw); background: #fff; border-radius: 16px;
#   box-shadow: 0 10px 30px rgba(0,0,0,.25); z-index: 1000;
#   padding: 16px 18px 22px 18px;
# }}
# .modal-head {{
#   display:flex; align-items:center; justify-content: space-between;
#   padding: 4px 6px 12px 6px; border-bottom: 1px solid #eee; margin-bottom: 12px;
# }}
# .modal-actions {{
#   display:flex; gap:.6rem; margin-top: .75rem;
# }}
# .modal .btn {{ border-radius: 10px; }}
# .close-x {{
#   font-weight:700; cursor:pointer; color:#111; font-size: 20px;
# }}
# </style>
# """, unsafe_allow_html=True)

# # =========================
# # Header
# # =========================
# col_logo, col_title = st.columns([0.1, 0.9])
# with col_logo:
#     try:
#         st.image(LOGO_PATH, use_column_width=True)
#     except Exception:
#         st.write("")
# with col_title:
#     st.markdown(
#         f"<div class='main-header'><h1 style='margin:0;color:{BRAND_PRIMARY}'>{APP_NAME}</h1>"
#         f"<p style='margin:0;color:#667085;font-size:1.05rem'>{APP_TAGLINE}</p></div>",
#         unsafe_allow_html=True
#     )

# # =========================
# # Init
# # =========================
# pipe = MemePipeline()

# # Session state
# defaults = {
#     "prompt_val": "",
#     "results": [],
#     "cards": [],
#     "history": [],
#     "editing_idx": None,
#     "edit_lines": ["", "", "", "", "", ""],
# }
# for k, v in defaults.items():
#     if k not in st.session_state:
#         st.session_state[k] = v

# # =========================
# # Fallback templates
# # =========================
# FALLBACK_TEMPLATES = [
#     {"id": "drake", "name": "Drake Hotline Bling", "url": "https://i.imgflip.com/30b1gx.jpg", "source": "fallback"},
#     {"id": "distracted", "name": "Distracted Boyfriend", "url": "https://i.imgflip.com/1ur9b0.jpg", "source": "fallback"},
#     {"id": "twobuttons", "name": "Two Buttons", "url": "https://i.imgflip.com/1g8my4.jpg", "source": "fallback"},
# ]

# # =========================
# # Helpers
# # =========================
# def build_preview_caption(prompt: str, template_name: str) -> str:
#     ideas = pipe.auto_captions(prompt, template_name) or []
#     if ideas:
#         return ideas[0]
#     return f"{prompt} // make it meme"

# def make_preview(template: dict, caption: str, idx: int) -> str:
#     prev_dir = Path("outputs") / "previews"
#     prev_dir.mkdir(parents=True, exist_ok=True)
#     try:
#         return pipe.build_meme(template, caption, out_dir=str(prev_dir))
#     except Exception:
#         return template["url"]

# def rebuild_cards():
#     st.session_state["cards"] = []
#     prompt = st.session_state["prompt_val"]
#     for i, t in enumerate(st.session_state["results"]):
#         cap = build_preview_caption(prompt, t["name"])
#         prev = make_preview(t, cap, i)
#         st.session_state["cards"].append({
#             "template": t,
#             "caption": cap,
#             "preview": prev
#         })

# def do_search():
#     q = st.session_state["_prompt_input"].strip()
#     st.session_state["prompt_val"] = q

#     try:
#         results = pipe.suggest_templates(q, k=10)
#     except Exception as e:
#         print("Template API failed:", e)
#         results = []

#     if not results:
#         st.warning("⚠️ No templates found from API, showing fallback templates instead.")
#         results = FALLBACK_TEMPLATES

#     st.session_state["results"] = results
#     rebuild_cards()
#     st.session_state["editing_idx"] = None

# def open_editor(idx: int):
#     st.session_state["editing_idx"] = idx
#     cap = st.session_state["cards"][idx]["caption"]
#     parts = [s.strip() for s in cap.split("//") if s.strip()]
#     lines = [""] * 6
#     for i, p in enumerate(parts[:6]):
#         lines[i] = p
#     st.session_state["edit_lines"] = lines

# def update_modal_preview():
#     idx = st.session_state["editing_idx"]
#     if idx is None: return
#     card = st.session_state["cards"][idx]
#     merged = " // ".join([l.strip() for l in st.session_state["edit_lines"] if l.strip()])
#     if merged:
#         card["caption"] = merged
#     try:
#         card["preview"] = make_preview(card["template"], card["caption"], idx)
#     except Exception:
#         pass

# # =========================
# # UI
# # =========================
# tab1, tab2 = st.tabs(["🎨 Create Memes", "🖼 My Gallery"])

# with tab1:
#     st.text_input("Enter any text to get memes:", key="_prompt_input",
#                   value=st.session_state.get("prompt_val", ""),
#                   placeholder="e.g., Just finished my final PhD dissertation")
#     st.button("🔎 Find Templates", use_container_width=True, on_click=do_search)

#     if st.session_state["cards"]:
#         st.subheader("🎨 Template Suggestions")
#         cols = st.columns(2)
#         for i, card in enumerate(st.session_state["cards"]):
#             col = cols[i % 2]
#             with col:
#                 st.markdown("<div class='template-card'>", unsafe_allow_html=True)
#                 st.image(card["preview"], use_column_width=True)
#                 c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
#                 with c1:
#                     st.download_button("⬇️ Download",
#                                        data=open(card["preview"], "rb").read() if Path(card["preview"]).exists() else b"",
#                                        file_name=f"meme_{i}.jpg",
#                                        use_container_width=True)
#                 with c2:
#                     if st.button("✏️ Edit", key=f"edit_{i}", use_container_width=True):
#                         open_editor(i)
#                 with c3:
#                     st.button("📋 Copy", key=f"copy_{i}", use_container_width=True)
#                 with c4:
#                     st.button("✨ Style", key=f"style_{i}", use_container_width=True)
#                 st.markdown("</div>", unsafe_allow_html=True)

#     # Modal Editor
#     if st.session_state["editing_idx"] is not None:
#         idx = st.session_state["editing_idx"]
#         card = st.session_state["cards"][idx]

#         st.markdown("<div class='modal-overlay'></div>", unsafe_allow_html=True)
#         st.markdown("<div class='modal'>", unsafe_allow_html=True)
#         st.markdown("<div class='modal-head'><b>Edit Meme</b>"
#                     "<div class='close-x' onclick='window.parent.document.querySelector(\"button[aria-label=modal_close]\").click()'>×</div>"
#                     "</div>", unsafe_allow_html=True)

#         left, right = st.columns([1.1, 1])
#         with left:
#             for li in range(6):
#                 st.session_state["edit_lines"][li] = st.text_input(
#                     f"Caption {li+1}", value=st.session_state["edit_lines"][li], key=f"cap_line_{li}"
#                 )
#             u1, u2, u3 = st.columns([1, 1, 1])
#             with u1:
#                 if st.button("🔄 Update Preview", key="modal_update", use_container_width=True):
#                     update_modal_preview()
#             with u2:
#                 if st.button("💾 Save to Gallery", key="modal_save", use_container_width=True):
#                     st.session_state["history"].append({
#                         "prompt": st.session_state.get("prompt_val", ""),
#                         "template": card["template"]["name"],
#                         "caption": card["caption"],
#                         "path": card["preview"]
#                     })
#                     st.success("Saved to Gallery ✅")
#             with u3:
#                 if st.button("✖ Close", key="modal_close", use_container_width=True):
#                     st.session_state["editing_idx"] = None

#         with right:
#             st.caption("Live preview")
#             st.image(card["preview"], use_column_width=True)
#             st.download_button("⬇️ Download",
#                                data=open(card["preview"], "rb").read() if Path(card["preview"]).exists() else b"",
#                                file_name=f"meme_edit_{idx}.jpg",
#                                use_container_width=True)

#         st.markdown("</div>", unsafe_allow_html=True)

# with tab2:
#     st.subheader("🖼 My Gallery")
#     if not st.session_state["history"]:
#         st.info("No memes yet. Create one from the Create tab.")
#     else:
#         cols = st.columns(3)
#         for i, item in enumerate(st.session_state["history"][::-1]):
#             with cols[i % 3]:
#                 st.image(item["path"], caption=item["caption"], use_column_width=True)
#                 st.caption(f"Template: {item['template']}")
