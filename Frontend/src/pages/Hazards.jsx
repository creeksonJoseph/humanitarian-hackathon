import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";

// Note: Replace with actual backend API URL when available
const API_BASE_URL = "http://localhost:8000/api";

export default function Hazards() {
    const navigate = useNavigate();
    const [hazards, setHazards] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [clearingId, setClearingId] = useState(null);

    const fetchHazards = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/hazards`);
            if (!response.ok) throw new Error("Failed to fetch hazards");
            const data = await response.json();
            setHazards(data);
        } catch (error) {
            console.error("Error fetching hazards:", error);
            // Fallback mock data
            setHazards([
                { id: 101, hazard_type: "FLOOD", route_description: "Ekerenyo Main Bridge (4050)", reported_by_number: "+251 911 234 567", status: "ACTIVE", reported_at: new Date().toISOString() },
                { id: 102, hazard_type: "ROAD_BLOCK", route_description: "Nyamira South Pass (4020)", reported_by_number: "+251 912 883 291", status: "UNVERIFIED", reported_at: new Date(Date.now() - 3600000).toISOString() }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchHazards();
    }, []);

    const handleClearHazard = async (id) => {
        setClearingId(id);
        try {
            const response = await fetch(`${API_BASE_URL}/hazards/${id}/clear`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            if (!response.ok) throw new Error("Failed to clear hazard");
            
            // Remove the cleared hazard from the local state
            setHazards(prev => prev.filter(h => h.id !== id));
        } catch (error) {
            console.error("Error clearing hazard:", error);
            // Fallback: Optimistic UI update for dev
            setHazards(prev => prev.filter(h => h.id !== id));
        } finally {
            setClearingId(null);
        }
    };

    // Helper function to format date
    const formatDate = (isoString) => {
        if (!isoString) return "Unknown";
        const date = new Date(isoString);
        return date.toLocaleString();
    };

    // Helper to get styled tags for hazard types
    const getHazardTypeBadge = (type) => {
        switch (type) {
            case "FLOOD":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-blue-500"></span>Flood</span>;
            case "POWER_LINES":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-500 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-amber-500"></span>Power Lines</span>;
            case "ROAD_BLOCK":
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 text-red-500 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-red-500"></span>Road Block</span>;
            default:
                return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 text-slate-400 text-[10px] font-bold uppercase tracking-wider"><span className="size-1.5 rounded-full bg-slate-500"></span>Other</span>;
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
                            <h1 className="text-4xl font-display uppercase font-bold text-white tracking-tight">Active Hazards</h1>
                        </div>
                        <p className="text-slate-400 mt-1 font-body ml-10">Monitor and clear reported obstacles and dangerous routes.</p>
                    </div>

                    {/* KPI Bar */}
                    <div className="flex flex-wrap gap-4">
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-rose-500 text-[10px] uppercase font-bold tracking-widest">Active Hazards</p>
                            <p className="text-2xl font-display text-white">{hazards.length}</p>
                        </div>
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-amber-500 text-[10px] uppercase font-bold tracking-widest">Unverified Reports</p>
                            <p className="text-2xl font-display text-white">{hazards.filter(h => h.status === 'UNVERIFIED').length}</p>
                        </div>
                    </div>
                </div>

                {/* Main Content Card */}
                <div className="bg-card-dark rounded-xl border border-slate-700/50 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-800/50 text-slate-400 uppercase text-[10px] font-bold tracking-[0.1em]">
                                    <th className="px-6 py-4 border-b border-slate-700/50">Hazard ID</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Type & Status</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Route / Location</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50">Reported By / Time</th>
                                    <th className="px-6 py-4 border-b border-slate-700/50 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {isLoading ? (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-8 text-center text-slate-400">Loading hazards...</td>
                                    </tr>
                                ) : hazards.length === 0 ? (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-8 text-center text-slate-400">No active hazards reported.</td>
                                    </tr>
                                ) : (
                                    hazards.map((hazard) => (
                                        <tr key={hazard.id} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <p className="text-sm font-semibold text-white">HZ-{hazard.id}</p>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col gap-1.5 items-start">
                                                    {getHazardTypeBadge(hazard.hazard_type)}
                                                    {hazard.status === 'UNVERIFIED' && (
                                                         <span className="text-[10px] font-bold text-amber-500 uppercase tracking-widest">UNVERIFIED (Single Report)</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2 text-slate-300">
                                                    <span className="material-symbols-outlined text-sm text-rose-500">warning</span>
                                                    <span className="text-sm font-medium">{hazard.route_description}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <p className="text-sm text-slate-300 font-mono">{hazard.reported_by_number}</p>
                                                <p className="text-[11px] text-slate-500">{formatDate(hazard.reported_at)}</p>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button 
                                                        onClick={() => handleClearHazard(hazard.id)}
                                                        disabled={clearingId === hazard.id}
                                                        className={`px-4 py-2 ${clearingId === hazard.id ? 'bg-emerald-600/50 text-emerald-200' : 'bg-slate-700 text-emerald-400 hover:bg-emerald-600 hover:text-white'} text-xs font-bold rounded-lg transition-all flex items-center gap-2`}
                                                    >
                                                         {clearingId === hazard.id ? (
                                                            <>
                                                                <span className="material-symbols-outlined text-sm animate-spin">sync</span>
                                                                Clearing...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <span className="material-symbols-outlined text-sm">check_circle</span>
                                                                Clear Hazard
                                                            </>
                                                        )}
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
}
