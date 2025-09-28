# Meme Generator AI

An AI-powered meme generator that creates memes using AI text/image models.
It takes prompts, generates captions or meme text, overlays them on images, and outputs funny memes.

## Features

- Generate memes from user prompts
- AI-powered text generation for captions
- Use custom or included meme templates
- Save memes in PNG/JPG format
- Lightweight and easy to extend

## Installation

git clone https://github.com/SenathPerera/Meme-Generator-AI.git<br>
cd Meme-Generator-AI<br>
pip install -r requirements.txt<br>

## Configuration

Templates are stored in src/templates/. Add your own images there<br>
Captions can be auto-generated via AI models or provided manually<br>
Output memes are saved in output/ by default<br>

## Dependencies

- Listed in requirements.txt. Key packages include:
  - Pillow – image processing
  - openai – for AI text generation (if enabled)
  - requests – API calls
  - argparse – CLI usage

## Contributing

- Fork the repo<br>
- Create a branch (git checkout -b feature/your-feature)<br>
- Commit changes (git commit -m "Add new feature")<br>
- Push (git push origin feature/your-feature)<br>
- Open a Pull Request<br>
