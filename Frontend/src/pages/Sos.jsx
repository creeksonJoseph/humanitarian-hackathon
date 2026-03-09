import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { fetchSos } from "../api/sos";
import { fetchStats } from "../api/stats";

export default function Sos() {
    const navigate = useNavigate();
    const [sosCalls, setSosCalls] = useState([]);
    const [stats, setStats] = useState({ total_sos: 0, active_sos: 0 });
    const [isLoading, setIsLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const loadSosCalls = async () => {
        setIsLoading(true);
        try {
            const [sosRes, statsRes] = await Promise.all([
                // Fetching all SOS calls (active and resolved)
                fetchSos("all", "", page, 50).catch(() => null),
                fetchStats().catch(() => null)
            ]);
            
            if (sosRes) {
                setSosCalls(sosRes.data || []);
                setTotalPages(sosRes.total_pages || 1);
            }
            if (statsRes) setStats(statsRes);
        } catch (error) {
            console.error("Error fetching SOS calls:", error);
            // Fallback mock data
            setSosCalls([
                { id: 1001, caller: "+251 911 234 567", type: "MATERNITY", status: "BROADCASTING", village: "Ekerenyo Phase 2", village_code: "4050", assigned_rider: null, rider_phone: null, time: new Date().toISOString() },
                { id: 1002, caller: "+251 912 883 291", type: "INJURY", status: "CLAIMED", village: "Nyamira South", village_code: "4020", assigned_rider: "Abel Mulugeta", rider_phone: "+251 988 123 456", time: new Date(Date.now() - 1800000).toISOString() },
                { id: 1003, caller: "+251 955 667 788", type: "OTHER", status: "RESOLVED", village: "Bole Sector 4", village_code: "1010", assigned_rider: "Saba Gebre", rider_phone: "+251 922 334 455", time: new Date(Date.now() - 86400000).toISOString() }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadSosCalls();
    }, [page]);

    // Helper function to format date
    const formatDate = (isoString) => {
        if (!isoString) return "Unknown";
        const date = new Date(isoString);
        return date.toLocaleString();
    };

    // Helper to get styled tags for SOS types
    const getSosTypeBadge = (type) => {
        switch (type) {
            case "MATERNITY":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-pink-500/10 text-pink-400 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-pink-500"></span>Maternity</span>;
            case "INJURY":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-500 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-rose-500"></span>Severe Injury</span>;
            case "OTHER":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-indigo-500"></span>Other Medical</span>;
            default:
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 text-slate-400 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-slate-500"></span>Unknown</span>;
        }
    };

    // Helper to get styled tags for SOS status
    const getStatusBadge = (status) => {
        switch (status) {
            case "BROADCASTING":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/10 text-amber-500 text-[10px] font-bold uppercase tracking-wider"><span className="material-symbols-outlined text-[12px] animate-pulse">radar</span>Broadcasting</span>;
            case "CLAIMED":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-wider"><span className="material-symbols-outlined text-[12px]">motorcycle</span>Claimed</span>;
            case "RESOLVED":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold uppercase tracking-wider"><span className="material-symbols-outlined text-[12px]">check_circle</span>Resolved</span>;
            default:
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-500/10 text-slate-400 text-[10px] font-bold uppercase tracking-wider">{status}</span>;
        }
    };

    return (
        <div className="layout-container flex flex-col min-h-screen">
            <Header locations={[]} selectedLocation="" setSelectedLocation={() => {}} />

            <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                             <button 
                                onClick={() => navigate('/')}
                                className="text-slate-400 hover:text-white transition-colors"
                            >
                                <span className="material-symbols-outlined">arrow_back</span>
                            </button>
                            <h1 className="text-4xl font-display uppercase font-bold text-white tracking-tight">SOS Directory</h1>
                        </div>
                        <p className="text-slate-400 mt-1 font-body ml-10">Complete historical and active record of emergency calls.</p>
                    </div>

                    {/* KPI Bar */}
                    <div className="flex flex-wrap gap-4">
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-slate-400 text-[10px] uppercase font-bold tracking-widest">Total Logs</p>
                            <p className="text-2xl font-display text-white">{stats.total_sos}</p>
                        </div>
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-rose-500 text-[10px] uppercase font-bold tracking-widest">Active SOS</p>
                            <p className="text-2xl font-display text-white">{stats.active_sos}</p>
                        </div>
                    </div>
                </div>

                {/* Main Content Card */}
                <div className="bg-card-dark rounded-xl border border-slate-700/50 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-800/50 text-slate-400 uppercase text-[10px] font-bold tracking-[0.1em]">
                                    <th className="px-6 py-4 border-b border-slate-700/50">Job ID / Type</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Status</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Location</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Caller / Time</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Assigned Rider</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {isLoading ? (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-8 text-center text-slate-400">Loading SOS log...</td>
                                    </tr>
                                ) : sosCalls.length === 0 ? (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-8 text-center text-slate-400">No SOS records found.</td>
                                    </tr>
                                ) : (
                                    sosCalls.map((sos) => (
                                        <tr key={sos.id} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col gap-1.5 items-start">
                                                    <p className="text-sm font-semibold text-white">JOB-{sos.id}</p>
                                                    {getSosTypeBadge(sos.type)}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                {getStatusBadge(sos.status)}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2 text-slate-300">
                                                    <span className="material-symbols-outlined text-sm">location_on</span>
                                                    <span className="text-sm font-medium">{sos.village} ({sos.village_code})</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <p className="text-sm text-slate-300 font-mono">{sos.caller}</p>
                                                <p className="text-[11px] text-slate-500">{formatDate(sos.time)}</p>
                                            </td>
                                            <td className="px-6 py-4">
                                                {sos.assigned_rider ? (
                                                    <div className="flex flex-col gap-0.5">
                                                        <p className="text-sm font-semibold text-emerald-400">{sos.assigned_rider}</p>
                                                        <p className="text-[11px] text-slate-500 font-mono">{sos.rider_phone}</p>
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-slate-500 italic">None Assigned</span>
                                                )}
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
