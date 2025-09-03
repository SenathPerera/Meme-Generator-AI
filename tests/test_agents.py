from agents.meme_generator_agent import MemeGeneratorAgent
import os

def test_meme_generator():
        # Initialize agent with smaller font size for testing
    agent = MemeGeneratorAgent(font_size=30)

    # Paths for test template and output
    template_path = "tests/sample_template.jpg"   # sample image for testing
    output_path = "tests/test_meme.jpg"           # generated meme output

    # Run the meme generator
    output_file = agent.generate_meme(
        template_path=template_path,
        top_text="Top Caption",
        bottom_text="Bottom Caption",
        output_path=output_path
    )

    # Check if output file exists
    assert os.path.exists(output_file), "Meme output file was not created!"

    # Clean up generated test file (optional: keeps repo clean)
    if os.path.exists(output_file):
        os.remove(output_file)
