import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Sidebar from "./components/Sidebar";
import MemeCard from "./components/MemeCard";
import MemeEditorModal from "./components/MemeEditorModal";
import Loader from "./components/Loader";

const API_BASE = "http://127.0.0.1:8000";
const toPublicUrl = (p) =>
  p?.startsWith("http") ? p : `${API_BASE}/${String(p || "").replace(/^\/?/, "")}`;

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [safetyLevel, setSafetyLevel] = useState("safe");
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMeme, setSelectedMeme] = useState(null);
  const [starred, setStarred] = useState([]);
  const [finalImageUrl, setFinalImageUrl] = useState("");
  const [showAd, setShowAd] = useState(false);
  const [queuedGeneration, setQueuedGeneration] = useState(null);
  const adRef = useRef(null);

  useEffect(() => {
    const saved = localStorage.getItem("starred");
    if (saved) setStarred(JSON.parse(saved));
  }, []);

  // While the ad is visible, block common video control keys to prevent skipping/pausing
  useEffect(() => {
    if (!showAd) return;
    const block = (e) => {
      const keys = [" ", "k", "ArrowRight", "ArrowLeft", "MediaPlayPause"]; // space, pause, scrub
      if (keys.includes(e.key)) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    window.addEventListener("keydown", block, { capture: true });
    return () => window.removeEventListener("keydown", block, { capture: true });
  }, [showAd]);

  // Enforce unskippable ad: prevent seeking, pausing, or changing speed
  useEffect(() => {
    const vid = adRef.current;
    if (!showAd || !vid) return;
    let last = 0;
    let guard = false;

    const onTime = () => {
      if (!guard) last = vid.currentTime;
    };
    const onSeeking = () => {
      guard = true;
      try { vid.currentTime = last; } catch {}
      guard = false;
    };
    const onPause = () => {
      try { vid.play().catch(() => {}); } catch {}
    };
    const onRate = () => {
      if (vid.playbackRate !== 1) vid.playbackRate = 1;
    };
    const onLoaded = () => { last = 0; try { vid.playbackRate = 1; } catch {} };

    vid.addEventListener("timeupdate", onTime);
    vid.addEventListener("seeking", onSeeking, { capture: true });
    vid.addEventListener("pause", onPause, { capture: true });
    vid.addEventListener("ratechange", onRate);
    vid.addEventListener("loadedmetadata", onLoaded);

    return () => {
      vid.removeEventListener("timeupdate", onTime);
      vid.removeEventListener("seeking", onSeeking, { capture: true });
      vid.removeEventListener("pause", onPause, { capture: true });
      vid.removeEventListener("ratechange", onRate);
      vid.removeEventListener("loadedmetadata", onLoaded);
    };
  }, [showAd]);

  const handleGenerate = async (custom) => {
    const context = (custom || prompt || "").trim();
    if (!context) return;
    setPrompt(context);
    setLoading(true);
    setFinalImageUrl("");

    try {
      const { data } = await axios.get(`${API_BASE}/templates`, {
        params: { context, k: 6, safety_level: safetyLevel },
      });
      const raw = (data || []).map((t) => ({ ...t, url: toPublicUrl(t.url) }));

      // Generate caption-placed previews for each suggested template
      const generated = await Promise.all(
        raw.map(async (t) => {
          if (!t.caption) return t;
          try {
            const payload = {
              template: { id: t.id, name: t.name, url: t.url, source: t.source },
              caption: t.caption,
              context,
              safety_level: safetyLevel,
            };
            const g = await axios.post(`${API_BASE}/generate`, payload);
            const outPath = g?.data?.path ? `${toPublicUrl(g.data.path)}?t=${Date.now()}` : t.url;
            return { ...t, url: outPath, _original_url: t.url, model_used: g?.data?.model_used || "" };
          } catch (e) {
            console.warn("Preview generation failed for template", t?.id, e);
            return t;
          }
        })
      );

      setTemplates(generated);
    } catch (err) {
      console.error("Error fetching templates:", err);
      alert("Failed to fetch templates. See console for details.");
    } finally {
      setLoading(false);
    }
  };

  const handleModalGenerate = async ({ template, top, bottom }) => {
    const caption = `${top || ""} // ${bottom || ""}`.trim();
    if (!template || !caption.replace(/\/|\s/g, "")) {
      alert("Please add some caption text.");
      return;
    }
    setShowAd(true);
    setQueuedGeneration({ template, caption });
  };

  const completeGeneration = async () => {
    if (!queuedGeneration) return;
    const { template, caption } = queuedGeneration;
    setLoading(true);
    setShowAd(false);
    setQueuedGeneration(null);
    try {
      const { data } = await axios.post(`${API_BASE}/generate`, {
        template,
        caption,
        context: prompt,
        safety_level: safetyLevel,
      });
      const url = data?.path ? `${toPublicUrl(data.path)}?t=${Date.now()}` : "";
      setFinalImageUrl(url);
      setSelectedMeme(null);
    } catch (err) {
      console.error("Error generating meme:", err);
      alert("Failed to generate meme. See console for details.");
    } finally {
      setLoading(false);
    }
  };

  const toggleStar = (template) => {
    let updated;
    if (starred.find((s) => s.id === template.id)) {
      updated = starred.filter((s) => s.id !== template.id);
    } else {
      updated = [...starred, template];
    }
    setStarred(updated);
    localStorage.setItem("starred", JSON.stringify(updated));
  };



  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <Sidebar starred={starred} />

      <div className="flex-1 overflow-y-auto p-8">
        <h1 className="text-2xl font-bold text-center text-indigo-400 mb-6">
          Enter Your Context
        </h1>

        <div className="flex justify-center mb-4">
          <input
            type="text"
            placeholder="e.g., Too many meetings, running on coffee"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-1/2 px-4 py-2 rounded-l bg-gray-800 text-gray-200 focus:outline-none"
          />
          <button
            onClick={() => handleGenerate()}
            className="px-4 py-2 rounded-r bg-indigo-500 hover:bg-indigo-600 text-white"
          >
            Generate
          </button>
        </div>

        <div className="flex justify-center mb-6 w-1/2 mx-auto">
          <label className="mr-2">Safety Filter</label>
          <select
            value={safetyLevel}
            onChange={(e) => setSafetyLevel(e.target.value)}
            className="w-full px-5 py-2 rounded bg-gray-800 text-gray-100 border border-gray-600"
          >
            <option value="safe">Safe (Default)</option>
            <option value="no_filter">No Filter</option>
            <option value="sarcastic">Sarcastic</option>
            <option value="political">Political</option>
            <option value="racist">Racist</option>
            <option value="dark_humor">Dark Humor</option>
            <option value="offensive">Offensive</option>
          </select>
        </div>

        {safetyLevel !== "safe" && (
          <div className="bg-red-400 text-white-800 text-medium border border-red-600 rounded p-3 mb-6 text-center">
            ⚠️ You have selected a non-safe mode. Content may be inappropriate or offensive to some users. We are not responsible for any legal issues!
          </div>
        )}

        {loading && <Loader />}

        {!loading && finalImageUrl && (
          <div className="max-w-3xl mx-auto mb-10">
            <h2 className="text-xl font-semibold mb-3 text-indigo-300">Latest Meme</h2>
            <img
              src={finalImageUrl}
              alt="Rendered Meme"
              className="w-full rounded-lg shadow-lg border border-gray-800"
            />
            <div className="text-sm text-gray-400 mt-2">
              Saved at: <code className="text-gray-300">{finalImageUrl}</code>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {templates.map((t, i) => (
            <div key={`${t.id}-${i}`} className="bg-gray-800 rounded-xl shadow p-4 flex flex-col border border-gray-700">
              <MemeCard
                template={t}
                onEdit={() => setSelectedMeme(t)}
                onStar={() => toggleStar(t)}
                starred={starred.some((s) => s.id === t.id)}
              />
              {t.caption && (
                <div className="mt-2 text-sm text-gray-300 line-clamp-2">{t.caption}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {selectedMeme && (
        <MemeEditorModal
          isOpen={!!selectedMeme}
          onClose={() => setSelectedMeme(null)}
          template={selectedMeme}
          context={prompt}
          apiBase={API_BASE}
          safetyLevel={safetyLevel}
          onGenerate={handleModalGenerate}
        />
      )}

      {showAd && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col items-center justify-center z-50">
          <video
            src="/ads/ad.mp4"
            autoPlay
            controls={false}
            playsInline
            disablePictureInPicture
            controlsList="nodownload noplaybackrate nofullscreen noremoteplayback"
            onContextMenu={(e) => e.preventDefault()}
            onEnded={completeGeneration}
            className="w-3/4 rounded-lg shadow-lg no-controls pointer-events-none select-none"
            ref={adRef}
          />
          <p className="text-white mt-4 text-lg font-semibold">
            🎥 Please wait... your meme will be ready after this short message.
          </p>
        </div>
      )}
    </div>
  );
}
