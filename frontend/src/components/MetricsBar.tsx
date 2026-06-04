"use client";

import React from "react";
import { Property } from "../types/property";

interface MetricsBarProps {
  properties: Property[];
  filteredProperties: Property[];
}

export default function MetricsBar({ properties, filteredProperties }: MetricsBarProps) {
  // Telemetry 1: Total Tracked
  const totalTracked = properties.length;

  // Telemetry 2: Active Listings (Not Rejected)
  const activeCount = properties.filter((p) => p.status !== "Rejected").length;

  // Telemetry 3: Safest/Shortest Commute (min commute of active properties)
  const activeProperties = properties.filter((p) => p.status !== "Rejected" && p.commute_duration_mins !== undefined);
  const minCommute = activeProperties.length > 0
    ? Math.min(...activeProperties.map((p) => p.commute_duration_mins || 0))
    : null;

  // Telemetry 4: Average Rental Price of currently filtered options
  const displayedProperties = filteredProperties;
  const avgRent = displayedProperties.length > 0
    ? Math.round(displayedProperties.reduce((acc, p) => acc + p.price, 0) / displayedProperties.length)
    : 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
      {/* Tile 1: Total Tracked */}
      <div className="group relative rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80">
        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
          <svg className="h-24 w-24 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Tracked</p>
            <h4 className="text-2xl font-bold text-white mt-1">{totalTracked} Properties</h4>
          </div>
        </div>
      </div>

      {/* Tile 2: Active Shortlist */}
      <div className="group relative rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80">
        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
          <svg className="h-24 w-24 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Listings</p>
            <h4 className="text-2xl font-bold text-white mt-1">{activeCount} Listings</h4>
          </div>
        </div>
      </div>

      {/* Tile 3: Safest Commute */}
      <div className="group relative rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80">
        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
          <svg className="h-24 w-24 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Safest Commute</p>
            <h4 className="text-2xl font-bold text-amber-400 mt-1">
              {minCommute !== null ? `${minCommute} mins` : "N/A"}
            </h4>
          </div>
        </div>
      </div>

      {/* Tile 4: Average Rent */}
      <div className="group relative rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md transition-all duration-300 hover:border-slate-700/60 hover:bg-slate-900/80">
        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
          <svg className="h-24 w-24 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z"/></svg>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <span className="text-lg font-bold">₹</span>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Average Rent</p>
            <h4 className="text-2xl font-bold text-white mt-1">
              {avgRent > 0 ? `₹${avgRent.toLocaleString()}` : "N/A"}
            </h4>
          </div>
        </div>
      </div>
    </div>
  );
}
