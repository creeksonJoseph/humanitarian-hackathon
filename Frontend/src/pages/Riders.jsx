import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchRiders } from "../api/riders";
import { fetchStats } from "../api/stats";
import { useLocation } from "../context/LocationContext";

export default function Riders() {
    const navigate = useNavigate();
    const { selectedLocation } = useLocation();
    const [riders, setRiders] = useState([]);
    const [stats, setStats] = useState({ total_riders: 0, available_riders: 0 });
    const [isLoading, setIsLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [activeTab, setActiveTab] = useState("all");
    const [searchQuery, setSearchQuery] = useState("");

    const loadData = async () => {
        setIsLoading(true);
        try {
            const [ridersRes, statsRes] = await Promise.all([
                fetchRiders(activeTab, selectedLocation, searchQuery, page, 50).catch(() => null),
                fetchStats(selectedLocation).catch(() => null)
            ]);

            if (ridersRes) {
                setRiders(ridersRes.data || []);
                setTotalPages(ridersRes.total_pages || 1);
            }
            if (statsRes) setStats(statsRes);
        } catch (error) {
            console.error("Error fetching riders data:", error);
        } finally {
            setIsLoading(false);
        }
    };

    // Reset pagination when filter changes
    useEffect(() => {
        setPage(1);
    }, [activeTab, searchQuery, selectedLocation]);

    useEffect(() => {
         
        loadData();
        const interval = setInterval(loadData, 5000);
        return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, activeTab, searchQuery, selectedLocation]);
    return (
        <div className="layout-container flex flex-col min-h-screen">
            <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
                    <div>
                        <h1 className="text-4xl font-display uppercase font-bold tracking-tight text-slate-900 dark:text-white">Rider Management</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1 font-body">Real-time oversight of emergency response logistics and personnel.</p>
                    </div>
                    {/* KPI Bar */}
                    <div className="flex flex-wrap gap-4">
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-slate-400 text-[10px] uppercase font-bold tracking-widest">Total Registered</p>
                            <p className="text-2xl font-display text-white">{stats.total_riders}</p>
                        </div>
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-emerald-500 text-[10px] uppercase font-bold tracking-widest">Currently Available</p>
                            <p className="text-2xl font-display text-white">{stats.available_riders}</p>
                        </div>
                        <div 
                            onClick={() => navigate('/pending-verifications')}
                            className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px] cursor-pointer hover:border-amber-500/50 transition-colors group"
                        >
                            <p className="text-amber-500 text-[10px] uppercase font-bold tracking-widest group-hover:text-amber-400 transition-colors">Pending Verification</p>
                            <p className="text-2xl font-display text-white group-hover:text-amber-100 transition-colors">{stats.pending_riders || 0}</p>
                        </div>
                    </div>
                </div>

                {/* Main Content Card */}
                <div className="bg-card-dark rounded-xl border border-slate-700/50 overflow-hidden flex flex-col min-h-[500px]">
                    {/* Navigation & Search */}
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between border-b border-slate-700/50 px-6 py-4 gap-4 bg-slate-800/30">
                        <div className="flex gap-1 p-1 bg-slate-900 rounded-lg w-fit">
                            <button 
                                onClick={() => setActiveTab("all")}
                                className={`px-4 py-2 rounded-md font-display uppercase text-sm tracking-wide transition-colors ${activeTab === 'all' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
                            >
                                All Riders
                            </button>
                            <button 
                                onClick={() => setActiveTab("available")}
                                className={`px-4 py-2 rounded-md font-display uppercase text-sm tracking-wide transition-colors ${activeTab === 'available' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
                            >
                                Available Riders
                            </button>
                        </div>
                        <div className="relative max-w-sm w-full">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xl">search</span>
                            <input 
                                type="text"
                                placeholder="Search riders by name or phone..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg py-2 pl-10 pr-4 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            />
                        </div>
                    </div>

                    {/* Data Table */}
                    <div className="overflow-x-auto flex-1">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-800/50 text-slate-400 uppercase text-[10px] font-bold tracking-[0.1em]">
                                    <th className="px-6 py-4 border-b border-slate-700/50">Rider Profile</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Contact Info</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Current Status</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Last Known Location</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {isLoading && riders.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" className="px-6 py-8 text-center text-slate-400">Loading rider roster...</td>
                                    </tr>
                                ) : riders.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" className="px-6 py-8 text-center text-slate-400">No riders found.</td>
                                    </tr>
                                ) : (
                                    riders.map((rider) => (
                                        <tr key={rider.phone} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="size-10 rounded-lg bg-slate-700 flex items-center justify-center font-display text-lg text-white font-bold border border-slate-600 overflow-hidden">
                                                        {rider.name ? rider.name.substring(0, 2).toUpperCase() : "??"}
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-1.5">
                                                            <p className="text-sm font-semibold text-white">{rider.name}</p>
                                                            {rider.is_verified && <span className="material-symbols-outlined text-blue-400 text-sm" title="Verified">verified</span>}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <p className="text-sm text-slate-300 font-mono">{rider.phone}</p>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${rider.status === 'AVAILABLE' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-rose-500/10 text-rose-500 border-rose-500/20'}`}>
                                                    {rider.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2 text-slate-400">
                                                    <span className="material-symbols-outlined text-sm">location_on</span>
                                                    <span className="text-sm">{rider.current_location} ({rider.location_code})</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                    {/* Pagination Controls */}
                    <div className="flex items-center justify-between border-t border-slate-700/50 px-6 py-4 bg-slate-800/20">
                        <span className="text-sm text-slate-400">Page {page} of {totalPages}</span>
                        <div className="flex gap-2">
                            <button 
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1 || isLoading}
                                className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
                            >
                                Previous
                            </button>
                            <button 
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page >= totalPages || isLoading}
                                className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
