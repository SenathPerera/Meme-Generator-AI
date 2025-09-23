











from fastapi import FastAPI

app = FastAPI(title="Meme Idea Agent", version="2.0")

@app.get("/meme-generator")
async def meme_generator_status():
    return {"status": "ok", "agent": "meme_idea", "sources": len(SOURCES)}  # SOURCES added in next commit








