"use client";

import { useEffect, useState } from "react";
import { Property } from "../types/property";
import MetricsBar from "../components/MetricsBar";
import FilterBar from "../components/FilterBar";
import PropertyCard from "../components/PropertyCard";
import PasswordModal from "../components/PasswordModal";

// Load API URL dynamically from Next.js environment configurations
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [minPrice, setMinPrice] = useState(0);
  const [maxPrice, setMaxPrice] = useState(60000); // Standard starting max rent filter
  const [maxCommute, setMaxCommute] = useState(60); // Acceptable commute minutes filter
  const [selectedStatus, setSelectedStatus] = useState<string[]>([
    "Pending",
    "Interested",
    "Contacted",
  ]);
  const [showRejected, setShowRejected] = useState(false);
  const [sortBy, setSortBy] = useState("commute_asc");

  // Authentication & Security modal states
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [pendingMutation, setPendingMutation] = useState<{
    id: number;
    status: Property["status"];
  } | null>(null);

  // 1. Fetch Listings (Anonymous Read Optimization)
  const fetchListings = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/listings`);
      if (!res.ok) {
        throw new Error(`Failed to load listings: server returned status ${res.status}`);
      }
      const data = await res.json();
      // Normalize 'New' SQLite status to the typescript standard 'Pending'
      const normalized = data.map((item: Property) => ({
        ...item,
        status: item.status === "New" ? "Pending" : item.status,
      }));
      setProperties(normalized);
    } catch (err) {
      console.error("Listing fetch failed:", err);
      setErrorMessage("Could not connect to FastAPI server. Ensure python backend api.py is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, []);

  // 2. Perform Status State Mutation with password headers
  const updateStatus = async (id: number, newStatus: Property["status"], verifiedPassword: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/listings/${id}/status?status=${newStatus}`, {
        method: "POST",
        headers: {
          "X-Master-Password": verifiedPassword,
        },
      });

      if (res.status === 401) {
        // Cached credentials expired or invalid
        sessionStorage.removeItem("master_password");
        setPendingMutation({ id, status: newStatus });
        setIsAuthModalOpen(true);
        throw new Error("Credentials invalid. Re-authenticating...");
      }

      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Failed to update property status.");
      }

      // Update Local State with transition mappings
      setProperties((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status: newStatus } : item))
      );
    } catch (err: any) {
      console.error("Mutation failed:", err);
      alert(err.message || "An unexpected error occurred during database update.");
      throw err;
    }
  };

  // 3. Status Action Handler (Checks password cache first)
  const handleStatusChange = async (id: number, newStatus: Property["status"]) => {
    const cachedPassword = sessionStorage.getItem("master_password");

    if (!cachedPassword) {
      // Trigger gateway challenge
      setPendingMutation({ id, status: newStatus });
      setIsAuthModalOpen(true);
      return;
    }

    // Call update route with stored credentials
    await updateStatus(id, newStatus, cachedPassword);
  };

  // 4. Handle authentication challenge success callback
  const handleAuthSuccess = (password: string) => {
    sessionStorage.setItem("master_password", password);
    if (pendingMutation) {
      updateStatus(pendingMutation.id, pendingMutation.status, password);
      setPendingMutation(null);
    }
  };

  // 5. Client-Side Analytical Filtering & Sorting logic
  const filteredProperties = properties
    .filter((p) => {
      // Keyword Match (Title, locality/location, BHK description)
      const matchesSearch =
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.bhk.toLowerCase().includes(searchQuery.toLowerCase());

      // Price Limits Match
      const matchesPrice = p.price >= minPrice && p.price <= maxPrice;

      // Commute Limits Match
      const matchesCommute =
        p.commute_duration_mins === undefined ||
        p.commute_duration_mins <= maxCommute;

      // Status Matches
      const matchesStatus = selectedStatus.includes(p.status);

      return matchesSearch && matchesPrice && matchesCommute && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === "price_asc") return a.price - b.price;
      if (sortBy === "price_desc") return b.price - a.price;
      if (sortBy === "commute_asc") {
        return (
          (a.commute_duration_mins ?? 999) - (b.commute_duration_mins ?? 999)
        );
      }
      if (sortBy === "created_desc") {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      return 0;
    });

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white pb-24">
      {/* Decorative Glow Elements */}
      <div className="absolute top-0 left-1/4 h-[500px] w-[500px] rounded-full bg-indigo-900/10 blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 h-[400px] w-[400px] rounded-full bg-purple-900/10 blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 relative z-10">
        {/* Premium Header */}
        <header className="mb-12 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-slate-900 pb-8">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              House Hunter Hub
            </h1>
            <p className="text-slate-400 mt-2 text-sm md:text-base max-w-xl">
              Curated rental shortlist optimized against your personal daily office commute time.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => {
                sessionStorage.removeItem("master_password");
                alert("Authorization token cleared. Future mutations will re-trigger the password gate.");
              }}
              className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-300 border border-slate-800 rounded-2xl transition-colors"
            >
              Clear Session Auth
            </button>
            <button
              onClick={fetchListings}
              className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-xs text-white transition-all shadow-lg shadow-indigo-600/20"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17"/></svg>
              <span>Refresh Feed</span>
            </button>
          </div>
        </header>

        {/* Global Analytical Telemetry Cards */}
        <MetricsBar
          properties={properties}
          filteredProperties={filteredProperties}
        />

        {/* Advanced Filter Matrix */}
        <FilterBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          minPrice={minPrice}
          setMinPrice={setMinPrice}
          maxPrice={maxPrice}
          setMaxPrice={setMaxPrice}
          maxCommute={maxCommute}
          setMaxCommute={setMaxCommute}
          selectedStatus={selectedStatus}
          setSelectedStatus={setSelectedStatus}
          showRejected={showRejected}
          setShowRejected={setShowRejected}
          sortBy={sortBy}
          setSortBy={setSortBy}
        />

        {/* Content Layout Feed */}
        {loading ? (
          <div className="flex flex-col justify-center items-center h-80 gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-indigo-500 border-t-transparent" />
            <p className="text-xs text-slate-500 font-semibold tracking-wider uppercase animate-pulse">
              Retrieving normalized listings...
            </p>
          </div>
        ) : errorMessage ? (
          <div className="text-center py-20 rounded-3xl border border-rose-500/20 bg-rose-500/5 backdrop-blur-sm">
            <h3 className="text-xl font-bold text-rose-400">Database Connection Failed</h3>
            <p className="text-slate-400 mt-2 max-w-md mx-auto text-sm">{errorMessage}</p>
            <button
              onClick={fetchListings}
              className="mt-6 px-6 py-2.5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold transition-all"
            >
              Retry Connection
            </button>
          </div>
        ) : filteredProperties.length === 0 ? (
          <div className="text-center py-24 rounded-3xl border border-slate-800/80 bg-slate-900/20 backdrop-blur-sm">
            <svg className="mx-auto h-12 w-12 text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <h3 className="text-xl font-semibold text-slate-300">No properties fit these constraints</h3>
            <p className="text-slate-500 text-sm mt-1 max-w-xs mx-auto">
              Try adjusting your price filters, commute limits, or status toggles to reveal more options.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProperties.map((property, idx) => (
              <PropertyCard
                key={property.id}
                property={property}
                onStatusChange={handleStatusChange}
                index={idx}
              />
            ))}
          </div>
        )}
      </div>

      {/* Security Gateway Challenge Modal */}
      <PasswordModal
        isOpen={isAuthModalOpen}
        onClose={() => {
          setIsAuthModalOpen(false);
          setPendingMutation(null);
        }}
        onSuccess={handleAuthSuccess}
        apiBaseUrl={API_BASE_URL}
      />
    </main>
  );
}
