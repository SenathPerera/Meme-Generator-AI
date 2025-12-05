from pathlib import Path
from typing import List, Dict, Any, Optional

# Import agents
from src.agents.template_retrieval_agent import TemplateRetrievalAgent
from src.agents.meme_idea_agent import suggest_captions
from src.agents.security_compliance_agent import SecurityComplianceAgent
from src.utils.config import USE_PAID_API, OPENAI_TEXT_MODEL

from src.agents.meme_generator_agent import (
    generate_meme,            
    render_layout_on_template 
)


class MemePipeline:
    """
    Pipeline wiring together the 4 IRWA agents.
    Integrates paid OpenAI API with fallbacks to free APIs.
    """

    def __init__(self):
        self.retriever = TemplateRetrievalAgent()
        self.compliance = SecurityComplianceAgent()

        mode = "OpenAI Paid Mode" if USE_PAID_API else "Free API Mode"
        print(f"⚙️ MemeForge Pipeline initialized ({mode}, model={OPENAI_TEXT_MODEL})")

    # ---------------------------
    # Template Retrieval Agent
    # ---------------------------
    def suggest_templates(self, prompt: str, k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve meme templates relevant to a prompt."""
        return self.retriever.retrieve(prompt, top_k=k)

    # ---------------------------
    # Meme Idea Agent
    # ---------------------------
    def auto_captions(self, prompt: str, template_name: str, n: int = 5) -> List[str]:
        """Generate n caption suggestions for a given prompt and template."""
        return suggest_captions(prompt, template_name)[:n]

    # ---------------------------
    # Meme Generator Agent
    # ---------------------------
    def build_meme(self, template: Dict[str, Any], caption: str, out_dir: str = "outputs", enforce_compliance: bool = True) -> str:
        """Generate meme image with given caption, after compliance check."""
        if enforce_compliance:
            chk = self.compliance.check(caption)
            if not chk.ok:
                raise ValueError(chk.reason)

        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_path = Path(out_dir) / f"meme_{template.get('id', 'tpl')}.jpg"
        return generate_meme(template, caption, str(out_path))

    # ---------------------------
    # Security & Compliance Agent
    # ---------------------------
    def check_caption(self, caption: str):
        """Run compliance check only (without generating meme)."""
        return self.compliance.check(caption)
    
    
    def suggest_templates_from_context(self, context: str, k: int = 10):
        """
        Use OpenAI to plan search terms/tags from raw context, then retrieve.
        """
        # Your updated TemplateRetrievalAgent already exposes retrieve_from_context
        return self.retriever.retrieve_from_context(context, top_k=k)
    

def build_meme_with_layout_or_caption(self, req) -> str:
        out_dir = Path("outputs")
        out_dir.mkdir(parents=True, exist_ok=True)

        if req.boxes and req.template:
            # (Optional) compliance: join all texts and check once
            joined = " ".join([b.text for b in req.boxes if b.text])
            chk = self.compliance.check(joined)
            if not chk.ok:
                raise ValueError(chk.reason)
            out_path = out_dir / f"meme_{req.template.get('id','tpl')}_layout.jpg"
            return render_layout_on_template(req.template, [b.dict() for b in req.boxes], str(out_path))

        if req.caption and req.template:
            chk = self.compliance.check(req.caption)
            if not chk.ok:
                raise ValueError(chk.reason)
            out_path = out_dir / f"meme_{req.template.get('id','tpl')}.jpg"
            return generate_meme(req.template, req.caption, str(out_path))

        raise ValueError("Provide either {template + boxes[]} or {template + caption}.")
