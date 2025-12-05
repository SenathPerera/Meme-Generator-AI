import React, { useEffect, useRef, useState } from "react";
import axios from "axios";

export default function MemeEditorModal({
  isOpen,
  onClose,
  template,
  context,
  apiBase,
  safetyLevel,
}) {
  const containerRef = useRef(null);
  const imgRef = useRef(null);
  const [ideas, setIdeas] = useState([]);
  const [boxes, setBoxes] = useState([]);
  const [dragIndex, setDragIndex] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [showAd, setShowAd] = useState(false);
  const [adWatched, setAdWatched] = useState(false);

  // Build two default boxes from a caption string (Top // Bottom)
  const boxesFromCaption = (cap) => {
    const txt = String(cap || "").trim();
    if (!txt) return [];
    const parts = txt.split("//").map((s) => s.trim()).filter(Boolean);
    const out = [];
    // If caption includes explicit top//bottom, create two boxes; otherwise create exactly one.
    if (parts.length >= 2) {
      out.push({ text: parts[0], x: 0.05, y: 0.06, width: 0.9, align: "center", font_scale: 0.07, uppercase: true });
      out.push({ text: parts[1], x: 0.05, y: 0.85, width: 0.9, align: "center", font_scale: 0.07, uppercase: true });
    } else if (parts.length === 1) {
      out.push({ text: parts[0], x: 0.05, y: 0.85, width: 0.9, align: "center", font_scale: 0.07, uppercase: true });
    }
    return out.slice(0, 2);
  };

  // Prefill ideas and default caption boxes when opening
  useEffect(() => {
    if (!isOpen) return;
    setBoxes(boxesFromCaption(template?.caption));
    setAdWatched(false);
    (async () => {
      try {
        const { data } = await axios.get(`${apiBase}/ideas`, {
          params: { prompt: context, template: template?.name || "general", safety_level: safetyLevel },
        });
        setIdeas(data?.ideas || []);
      } catch (e) {
        setIdeas([]);
      }
    })();
  }, [isOpen, context, apiBase, template]);

  const pxToNorm = (px, total) => Math.min(1, Math.max(0, px / Math.max(1, total)));
  const normToPx = (norm, total) => Math.round(norm * total);

  const onDropCaption = (e) => {
    e.preventDefault();
    const text = e.dataTransfer.getData("text/plain");
    if (!text || !imgRef.current) return;

    const rect = imgRef.current.getBoundingClientRect();
    const xPx = e.clientX - rect.left;
    const yPx = e.clientY - rect.top;
    const W = rect.width;
    const H = rect.height;

    const box = {
      text,
      x: pxToNorm(xPx, W),
      y: pxToNorm(yPx, H),
      width: 0.6,
      align: "center",
      font_scale: 0.06,
      uppercase: true,
    };
    setBoxes((prev) => [...prev, box]);
  };
  const allowDrop = (e) => e.preventDefault();

  const onMouseDownBox = (i, e) => {
    if (!imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const bx = boxes[i];
    const xPx = normToPx(bx.x, rect.width);
    const yPx = normToPx(bx.y, rect.height);
    setDragOffset({ x: e.clientX - xPx, y: e.clientY - yPx });
    setDragIndex(i);
  };
  const onMouseMove = (e) => {
    if (dragIndex === null || !imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const nx = pxToNorm(e.clientX - rect.left - dragOffset.x, rect.width);
    const ny = pxToNorm(e.clientY - rect.top - dragOffset.y, rect.height);
    setBoxes((prev) => {
      const next = [...prev];
      next[dragIndex] = { ...next[dragIndex], x: nx, y: ny };
      return next;
    });
  };
  const onMouseUp = () => setDragIndex(null);

  const updateBox = (i, patch) => {
    setBoxes((prev) => {
      const next = [...prev];
      next[i] = { ...next[i], ...patch };
      return next;
    });
  };
  const removeBox = (i) => {
    setBoxes((prev) => prev.filter((_, idx) => idx !== i));
  };

  const generate = () => {
    if (!template || boxes.length === 0) return;
    setShowAd(true);
  };

  const handleAdEnd = async () => {
    setShowAd(false);
    try {
      // Use the original uncaptioned template if available
      const baseTemplate = {
        id: template?.id,
        name: template?.name,
        source: template?.source,
        url: template?._original_url || template?.url,
      };
      const { data } = await axios.post(`${apiBase}/generate`, {
        template: baseTemplate,
        boxes,
        context,
        safety_level: safetyLevel,
      });
      const outPath = data?.path || "";
      if (outPath) {
        const toPublicUrl = (p) => (String(p).startsWith("http") ? p : `${apiBase}/${String(p || "").replace(/^\/?/, "")}`);
        const url = toPublicUrl(outPath);
        try {
          window.open(url, "_blank", "noopener,noreferrer");
        } catch (err) {
          // Fallback when pop-up is blocked
          console.warn("Popup blocked; redirecting to image URL.", err);
          window.location.href = url;
        }
      }
      onClose?.();
    } catch (e) {
      console.error("Generate failed", e);
      alert("Failed to render meme. See console for details.");
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
    >
      {showAd && (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center text-white">
          <video
            width="640"
            autoPlay
            onEnded={handleAdEnd}
            className="rounded-lg shadow-lg border border-gray-700"
          >
            <source src="/ads/ad.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <p className="mt-4 text-lg text-center">Please watch the ad to generate your meme...</p>
        </div>
      )}

      <div className="bg-gray-900 w-full max-w-5xl xl:max-w-6xl max-h-[90vh] rounded-2xl border border-gray-700 shadow-xl overflow-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div>
            <div className="text-lg font-semibold text-indigo-300">Edit Meme</div>
            <div className="text-xs text-gray-400">{template?.name} — {template?.source}</div>
          </div>
          <button onClick={onClose} className="px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-200 text-sm">
            Close
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
          <div className="lg:col-span-2">
            <div
              ref={containerRef}
              className="relative bg-gray-800 rounded-xl p-2 border border-gray-700 max-h-[70vh] overflow-hidden"
              onDrop={onDropCaption}
              onDragOver={allowDrop}
            >
              <img
                ref={imgRef}
                src={template?._original_url || template?.url}
                alt={template?.name}
                className="w-full max-h-[70vh] object-contain rounded"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/700x600.png?text=Template+unavailable";
                }}
              />
              {imgRef.current && boxes.map((b, i) => {
                const rect = imgRef.current.getBoundingClientRect();
                const left = `${b.x * 100}%`;
                const top = `${b.y * 100}%`;
                const width = `${b.width * 100}%`;
                const fontSize = `${Math.max(14, Math.round(b.font_scale * rect.width))}px`;
                const textAlign = b.align;
                return (
                  <div
                    key={i}
                    className="absolute cursor-move select-none"
                    style={{ left, top, width }}
                    onMouseDown={(e) => onMouseDownBox(i, e)}
                  >
                    <div
                      className="px-2 py-1 rounded"
                      style={{
                        fontSize,
                        color: "white",
                        fontWeight: 800,
                        textTransform: b.uppercase ? "uppercase" : "none",
                        textAlign,
                        textShadow: `
                          -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000,
                          0 -2px 0 #000, 0 2px 0 #000, -2px 0 0 #000, 2px 0 0 #000
                        `,
                        background: "rgba(0,0,0,0.0)",
                      }}
                    >
                      {b.text}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 space-y-3">
              {boxes.map((b, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <input
                    className="flex-1 px-2 py-1 rounded bg-gray-800 border border-gray-700"
                    value={b.text}
                    onChange={(e) => updateBox(i, { text: e.target.value })}
                  />
                  <label className="flex items-center gap-1">
                    Size
                    <input
                      type="range"
                      min={0.03}
                      max={0.12}
                      step={0.005}
                      value={b.font_scale}
                      onChange={(e) => updateBox(i, { font_scale: parseFloat(e.target.value) })}
                    />
                  </label>
                  <select
                    className="px-2 py-1 rounded bg-gray-800 border border-gray-700"
                    value={b.align}
                    onChange={(e) => updateBox(i, { align: e.target.value })}
                  >
                    <option value="left">left</option>
                    <option value="center">center</option>
                    <option value="right">right</option>
                  </select>
                  <label className="flex items-center gap-1">
                    Upper
                    <input
                      type="checkbox"
                      checked={b.uppercase}
                      onChange={(e) => updateBox(i, { uppercase: e.target.checked })}
                    />
                  </label>
                  <button
                    onClick={() => removeBox(i)}
                    className="px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white"
                  >
                    Delete
                  </button>
                </div>
              ))}
              <div className="text-xs text-gray-500">
                Tip: drag an idea from the right panel onto the image; then drag to reposition.
              </div>
              <div>
                <button
                  onClick={generate}
                  className="mt-2 px-4 py-2 rounded bg-indigo-500 hover:bg-indigo-600 text-white text-sm"
                >
                  Generate Meme
                </button>
              </div>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold text-cyan-300 mb-2">AI Caption Ideas</div>
            <div className="flex flex-col gap-2 max-h-[70vh] overflow-y-auto pr-1">
              {ideas.map((cap, i) => (
                <div
                  key={i}
                  draggable
                  onDragStart={(e) => e.dataTransfer.setData("text/plain", cap)}
                  className="px-3 py-2 bg-gray-800 rounded border border-gray-700 cursor-move text-sm text-gray-100"
                  title="Drag me anywhere on the image"
                >
                  {cap}
                </div>
              ))}
              {!ideas.length && (
                <div className="text-xs text-gray-500">No ideas yet. Type your own text above.</div>
              )}
            </div>
          </div>
        </div>

        <div className="px-6 py-3 border-t border-gray-800 text-xs text-gray-500">
          You can add multiple text boxes; each is independently positioned and sized.
        </div>
      </div>
    </div>
  );
}
