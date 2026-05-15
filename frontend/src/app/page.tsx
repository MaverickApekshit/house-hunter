"use client";

import { useEffect, useState } from "react";

interface Listing {
  id: number;
  source: string;
  external_id: string;
  title: string;
  rent: number;
  deposit: number;
  area_sqft: number;
  bhk: string;
  locality: string;
  url: string;
  commute_time_mins: number;
  status: string;
}

export default function Home() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/listings")
      .then((res) => res.json())
      .then((data) => {
        setListings(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching listings:", error);
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-[#0f172a] text-slate-200 py-12 px-4 sm:px-6 lg:px-8 font-sans selection:bg-indigo-500 selection:text-white">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 text-center transform transition-all duration-700 translate-y-0 opacity-100">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 mb-4">
            House Hunter
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Your personalized, intelligent rental shortlist optimized for your daily commute.
          </p>
        </header>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500"></div>
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-20 bg-slate-800/50 rounded-2xl border border-slate-700/50 backdrop-blur-sm">
            <h3 className="text-2xl font-medium text-slate-300">No properties found</h3>
            <p className="text-slate-500 mt-2">Try running the scraper to populate the database.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.map((listing, index) => (
              <div
                key={listing.id}
                className="group relative bg-slate-800/80 rounded-2xl border border-slate-700 hover:border-indigo-500/50 overflow-hidden shadow-lg hover:shadow-indigo-500/10 transition-all duration-300 ease-out hover:-translate-y-1 backdrop-blur-sm"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {listing.source}
                    </span>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      {listing.bhk}
                    </span>
                  </div>

                  <a
                    href={listing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <h2 className="text-xl font-bold text-white mb-2 leading-tight group-hover:text-indigo-400 transition-colors line-clamp-2">
                      {listing.title}
                    </h2>
                  </a>

                  <div className="flex items-center text-slate-400 mb-6 text-sm">
                    <svg className="w-4 h-4 mr-1 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                    <span className="truncate">{listing.locality}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/50">
                      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Rent</p>
                      <p className="text-lg font-bold text-white">₹{listing.rent.toLocaleString()}</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/50">
                      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Commute</p>
                      <p className="text-lg font-bold text-amber-400">{listing.commute_time_mins} min</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/50">
                      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Deposit</p>
                      <p className="text-lg font-bold text-slate-300">₹{listing.deposit.toLocaleString()}</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/50">
                      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-1">Area</p>
                      <p className="text-lg font-bold text-slate-300">{listing.area_sqft || '?'} sqft</p>
                    </div>
                  </div>
                </div>

                <div className="px-6 py-4 bg-slate-900/40 border-t border-slate-800 flex justify-between items-center gap-3">
                  <a
                    href={listing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 text-center py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-indigo-500/20"
                  >
                    View Details
                  </a>
                  <button className="flex-1 py-2.5 bg-slate-800 hover:bg-rose-500/20 hover:text-rose-400 text-slate-400 rounded-lg font-medium border border-slate-700 hover:border-rose-500/30 transition-colors">
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
