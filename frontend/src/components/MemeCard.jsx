// components/MemeCard.jsx
import React from "react";

export default function MemeCard({ template, onEdit, onStar, starred }) {
  const { name, url, source } = template;
  return (
    <div className="flex flex-col">
      <div className="relative">
        <img
          src={url}
          alt={name}
          className="w-full rounded-lg shadow-lg border border-gray-700"
          onError={(e) => {
            e.currentTarget.src =
              "https://via.placeholder.com/600x600.png?text=Image+unavailable";
          }}
        />
        <button
          className={`absolute top-2 right-2 px-2 py-1 rounded text-xs ${
            starred ? "bg-yellow-400 text-black" : "bg-gray-800 text-gray-200"
          }`}
          onClick={onStar}
          title={starred ? "Unstar" : "Star"}
        >
          ★
        </button>
      </div>
      <div className="mt-2 font-semibold text-gray-200">{name}</div>
      <div className="text-xs text-gray-500">{source}</div>
      <button
        onClick={onEdit}
        className="mt-2 px-3 py-2 rounded bg-indigo-500 hover:bg-indigo-600 text-white text-sm"
      >
        Edit
      </button>
    </div>
  );
}
