"use client";

import React, { useState } from "react";
import { Property } from "../types/property";

interface PropertyCardProps {
  property: Property;
  onStatusChange: (id: number, newStatus: Property["status"]) => Promise<void>;
  index: number;
}

export default function PropertyCard({ property, onStatusChange, index }: PropertyCardProps) {
  const [loadingStatus, setLoadingStatus] = useState<Property["status"] | null>(null);

  // Commute styling depending on proximity
  const getCommuteColor = (mins?: number) => {
    if (mins === undefined) return "text-slate-400";
    if (mins <= 30) return "text-emerald-400";
    if (mins <= 45) return "text-amber-400";
    return "text-rose-400";
  };

  const getStatusBadgeStyle = (status: Property["status"]) => {
    switch (status) {
      case "Interested":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "Contacted":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      case "Rejected":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/20";
    }
  };

  const handleAction = async (newStatus: Property["status"]) => {
    setLoadingStatus(newStatus);
    try {
      await onStatusChange(property.id, newStatus);
    } catch (err) {
      console.error("Mutation failed:", err);
    } finally {
      setLoadingStatus(null);
    }
  };

  // Google Maps search query link based on location description/coordinates
  const mapSearchUrl = property.latitude && property.longitude
    ? `https://www.google.com/maps/search/?api=1&query=${property.latitude},${property.longitude}`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(property.location + ", Bangalore")}`;

  return (
    <div
      className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/40 hover:bg-slate-900/60 shadow-xl backdrop-blur-md transition-all duration-300 hover:-translate-y-1.5 hover:border-indigo-500/30 hover:shadow-indigo-500/5 animate-fade-in"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Glow Effect */}
      <div className="absolute -top-20 -right-20 h-40 w-40 rounded-full bg-indigo-500/5 blur-2xl group-hover:bg-indigo-500/10 transition-colors" />

      {/* Main Content */}
      <div className="p-6">
        {/* Badges Bar */}
        <div className="flex items-center justify-between gap-2 mb-4">
          <div className="flex gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-3xs font-bold uppercase tracking-wider bg-slate-950 text-slate-400 border border-slate-800">
              {property.source}
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-3xs font-bold uppercase tracking-wider bg-slate-950 text-indigo-400 border border-slate-800/80">
              {property.bhk}
            </span>
          </div>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-3xs font-bold uppercase tracking-wider border ${getStatusBadgeStyle(property.status)}`}>
            {property.status}
          </span>
        </div>

        {/* Title */}
        <a
          href={property.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group/title block mb-3"
        >
          <h3 className="text-lg font-bold text-white leading-snug group-hover/title:text-indigo-400 transition-colors line-clamp-2">
            {property.title}
          </h3>
        </a>

        {/* Localized Map Search */}
        <a
          href={mapSearchUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-xs text-slate-500 hover:text-indigo-400 transition-colors mb-6"
        >
          <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          <span className="truncate max-w-[200px]">{property.location}</span>
        </a>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-950/40 rounded-2xl p-3.5 border border-slate-800/60">
            <p className="text-3xs text-slate-500 uppercase font-bold tracking-wider mb-1">Rent</p>
            <p className="text-base font-extrabold text-white">₹{property.price.toLocaleString()}</p>
          </div>
          <div className="bg-slate-950/40 rounded-2xl p-3.5 border border-slate-800/60">
            <p className="text-3xs text-slate-500 uppercase font-bold tracking-wider mb-1">Commute</p>
            <p className={`text-base font-extrabold ${getCommuteColor(property.commute_duration_mins)}`}>
              {property.commute_duration_mins !== undefined ? `${property.commute_duration_mins} min` : "N/A"}
            </p>
          </div>
          <div className="bg-slate-950/40 rounded-2xl p-3.5 border border-slate-800/60">
            <p className="text-3xs text-slate-500 uppercase font-bold tracking-wider mb-1">Deposit</p>
            <p className="text-base font-bold text-slate-300">₹{property.deposit.toLocaleString()}</p>
          </div>
          <div className="bg-slate-950/40 rounded-2xl p-3.5 border border-slate-800/60">
            <p className="text-3xs text-slate-500 uppercase font-bold tracking-wider mb-1">Area Size</p>
            <p className="text-base font-bold text-slate-300">{property.area_sqft ? `${property.area_sqft} sqft` : "N/A"}</p>
          </div>
        </div>
      </div>

      {/* Selection Mutators Footer */}
      <div className="px-6 py-4 border-t border-slate-800/60 bg-slate-950/20 flex gap-2">
        {property.status !== "Interested" && (
          <button
            onClick={() => handleAction("Interested")}
            disabled={loadingStatus !== null}
            className="flex-1 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600/10 hover:bg-emerald-600 border border-emerald-500/20 hover:border-emerald-500 text-emerald-400 hover:text-white transition-all duration-200"
          >
            {loadingStatus === "Interested" ? (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
            ) : (
              "Interested"
            )}
          </button>
        )}

        {property.status !== "Contacted" && (
          <button
            onClick={() => handleAction("Contacted")}
            disabled={loadingStatus !== null}
            className="flex-1 py-2.5 rounded-xl text-xs font-semibold bg-indigo-600/10 hover:bg-indigo-600 border border-indigo-500/20 hover:border-indigo-500 text-indigo-400 hover:text-white transition-all duration-200"
          >
            {loadingStatus === "Contacted" ? (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
            ) : (
              "Contacted"
            )}
          </button>
        )}

        {property.status !== "Rejected" && (
          <button
            onClick={() => handleAction("Rejected")}
            disabled={loadingStatus !== null}
            className="flex-1 py-2.5 rounded-xl text-xs font-semibold bg-rose-600/10 hover:bg-rose-600 border border-rose-500/20 hover:border-rose-500 text-rose-400 hover:text-white transition-all duration-200"
          >
            {loadingStatus === "Rejected" ? (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-rose-400 border-t-transparent" />
            ) : (
              "Reject"
            )}
          </button>
        )}
      </div>
    </div>
  );
}
