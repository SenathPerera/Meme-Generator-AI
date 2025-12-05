import { useEffect, useState } from "react";

export default function Loader() {
  const base1 = "Oven is running";
  const base2 = "Your meme should be ready soon";
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => (t + 1) % 4), 500);
    return () => clearInterval(id);
  }, []);

  const dots = ".".repeat(tick);

  return (
    <div className="flex items-center justify-center py-20">
      <div className="flex items-center gap-4">
        <img
          src="/icons/oven.svg"
          alt="Oven"
          className="w-10 h-10 animate-spin"
        />
        <div className="text-left">
          <div className="text-xl font-semibold text-indigo-300 tracking-wide">
            {base1}
            {dots}
          </div>
          <div className="text-sm mt-1 text-gray-300">
            {base2}
            {dots}
          </div>
        </div>
      </div>
    </div>
  );
}
