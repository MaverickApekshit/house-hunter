"use client";

import React, { useState } from "react";

interface FilterBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  minPrice: number;
  setMinPrice: (val: number) => void;
  maxPrice: number;
  setMaxPrice: (val: number) => void;
  maxCommute: number;
  setMaxCommute: (val: number) => void;
  selectedStatus: string[];
  setSelectedStatus: (status: string[] | ((prev: string[]) => string[])) => void;
  showRejected: boolean;
  setShowRejected: (val: boolean) => void;
  sortBy: string;
  setSortBy: (val: string) => void;
}

export default function FilterBar({
  searchQuery,
  setSearchQuery,
  minPrice,
  setMinPrice,
  maxPrice,
  setMaxPrice,
  maxCommute,
  setMaxCommute,
  selectedStatus,
  setSelectedStatus,
  showRejected,
  setShowRejected,
  sortBy,
  setSortBy,
}: FilterBarProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const toggleStatus = (statusVal: string) => {
    setSelectedStatus((prev) =>
      prev.includes(statusVal)
        ? prev.filter((s) => s !== statusVal)
        : [...prev, statusVal]
    );
  };

  const clearFilters = () => {
    setSearchQuery("");
    setMinPrice(0);
    setMaxPrice(100000);
    setMaxCommute(60);
    setSelectedStatus(["Pending", "Interested", "Contacted"]);
    setShowRejected(false);
    setSortBy("commute_asc");
  };

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6 mb-8 backdrop-blur-md">
      {/* Primary Row: Search & Sort & Advanced toggle */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center justify-between">
        {/* Search Input */}
        <div className="relative flex-1 max-w-lg">
          <span className="absolute inset-y-0 left-0 flex items-center pl-4 text-slate-500">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </span>
          <input
            type="text"
            placeholder="Search by title, location, or configurations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-2xl border border-slate-800 bg-slate-950/60 pl-11 pr-4 py-3 text-sm text-white placeholder-slate-500 transition-all focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/15"
          />
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-3">
          <label htmlFor="sort" className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Sort
          </label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm text-slate-300 transition-all focus:border-indigo-500 focus:outline-none"
          >
            <option value="commute_asc">Commute: Shortest</option>
            <option value="price_asc">Rent: Low to High</option>
            <option value="price_desc">Rent: High to Low</option>
            <option value="created_desc">Newly Listed</option>
          </select>

          {/* Advanced Filter Toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`flex items-center gap-2 rounded-2xl border py-3 px-4 text-sm font-semibold transition-all ${
              showAdvanced
                ? "border-indigo-500/30 bg-indigo-500/10 text-indigo-400"
                : "border-slate-800 bg-slate-950/40 text-slate-400 hover:text-slate-200"
            }`}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Advanced Filter Expandable Section */}
      <div
        className={`grid grid-cols-1 gap-6 md:grid-cols-3 pt-6 mt-6 border-t border-slate-800/80 transition-all duration-300 ${
          showAdvanced ? "opacity-100 max-h-[800px]" : "opacity-0 max-h-0 overflow-hidden pt-0 mt-0 border-t-0"
        }`}
      >
        {/* Sliders Area */}
        <div className="space-y-5">
          {/* Price Constraint */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Max Rental Price</span>
              <span className="text-sm font-bold text-white">₹{maxPrice.toLocaleString()}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100000"
              step="5000"
              value={maxPrice}
              onChange={(e) => setMaxPrice(Number(e.target.value))}
              className="w-full accent-indigo-500 h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-2xs text-slate-600 mt-1">
              <span>₹0</span>
              <span>₹100,000</span>
            </div>
          </div>

          {/* Commute Threshold Constraint */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Max Commute Duration</span>
              <span className="text-sm font-bold text-amber-400">{maxCommute} mins</span>
            </div>
            <input
              type="range"
              min="10"
              max="120"
              step="5"
              value={maxCommute}
              onChange={(e) => setMaxCommute(Number(e.target.value))}
              className="w-full accent-amber-500 h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-2xs text-slate-600 mt-1">
              <span>10 mins</span>
              <span>120 mins</span>
            </div>
          </div>
        </div>

        {/* Status Checkbox Tags */}
        <div className="space-y-4">
          <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400">Status Categorization</span>
          <div className="flex flex-wrap gap-2">
            {["Pending", "Interested", "Contacted"].map((statusVal) => {
              const active = selectedStatus.includes(statusVal);
              return (
                <button
                  key={statusVal}
                  type="button"
                  onClick={() => toggleStatus(statusVal)}
                  className={`px-4 py-2 rounded-2xl text-xs font-semibold border transition-all ${
                    active
                      ? "border-indigo-500 bg-indigo-500/10 text-white"
                      : "border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  {statusVal}
                </button>
              );
            })}
          </div>

          {/* Toggle for Rejected Properties */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Show Rejected Listings</span>
            <button
              type="button"
              onClick={() => {
                setShowRejected(!showRejected);
                // Dynamically append/remove from active pills
                setSelectedStatus((prev) =>
                  !showRejected
                    ? [...prev, "Rejected"]
                    : prev.filter((s) => s !== "Rejected")
                );
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                showRejected ? "bg-indigo-600" : "bg-slate-800"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  showRejected ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>

        {/* Reset Panel */}
        <div className="flex flex-col justify-end">
          <button
            type="button"
            onClick={clearFilters}
            className="w-full text-center py-3.5 rounded-2xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 font-semibold text-sm transition-all hover:bg-slate-900/50"
          >
            Reset Active Filters
          </button>
        </div>
      </div>
    </div>
  );
}
