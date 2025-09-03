from agents.meme_generator_agent import MemeGeneratorAgent
import os

def test_meme_generator():
    agent = MemeGeneratorAgent(font_size=30)
    output_file = agent.generate_meme(
        template_path="tests/sample_template.jpg",
        top_text="Top Caption",
        bottom_text="Bottom Caption",
        output_path="tests/test_meme.jpg"
    )
    assert os.path.exists(output_file)
