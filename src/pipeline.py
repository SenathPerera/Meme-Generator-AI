from agents.meme_generator_agent import MemeGeneratorAgent

def run_meme_pipeline(template, caption_top, caption_bottom):
    generator = MemeGeneratorAgent()
    output_file = generator.generate_meme(
        template_path=template,
        top_text=caption_top,
        bottom_text=caption_bottom,
        
    )
    return output_file