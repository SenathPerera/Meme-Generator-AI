export const BASE = "http://127.0.0.1:8000";

export async function fetchTemplates(prompt, k = 10) {
  const res = await fetch(`${BASE}/templates?prompt=${encodeURIComponent(prompt)}&k=${k}`);
  if (!res.ok) throw new Error("Failed to fetch templates");
  return res.json();
}

export async function generateMeme(template, caption) {
  const res = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template, caption }),
  });
  if (!res.ok) throw new Error("Failed to generate meme");
  return res.json(); // { path }
}

export async function checkCaption(caption) {
  const url = new URL(`${BASE}/check`);
  url.searchParams.set("caption", caption);
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error("Compliance check failed");
  return res.json();
}

export async function fetchIdeas(prompt, templateName) {
  const url = new URL(`${BASE}/ideas`);
  url.searchParams.set("prompt", prompt);
  url.searchParams.set("template", templateName);
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch ideas");
  return res.json();
}
