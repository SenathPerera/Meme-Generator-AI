import React from "react";

function Sidebar({ starred }) {
  return (
    <div className="w-64 bg-gray-800 p-6 flex flex-col">
      <h1 className="text-xl font-bold text-indigo-400">MemeForge AI</h1>
      <p className="text-sm text-gray-400 mb-6">Text ➝ Template ➝ Edit ➝ Safe Download</p>

      <h2 className="text-gray-300 text-sm font-semibold mb-2">WORKFLOW</h2>
      <ol className="list-decimal list-inside space-y-1 text-gray-400 text-sm mb-6">
        <li>Enter prompt</li>
        <li>Pick a template</li>
        <li>Edit in popup</li>
        <li>Safety check & download</li>
      </ol>

      {/* History Sections */}
      <div className="flex-1 space-y-4 overflow-y-auto">
        <div>
          <h2 className="text-gray-300 text-sm font-semibold mb-2">STARRED</h2>
          {starred.length === 0 ? (
            <p className="text-gray-500 text-xs">No starred yet.</p>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {starred.map((s) => (
                <img
                  key={s.id}
                  src={s.url}
                  alt={s.name}
                  className="rounded"
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
