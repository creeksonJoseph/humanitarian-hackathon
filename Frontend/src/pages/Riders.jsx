import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";

export default function Riders() {
    const navigate = useNavigate();
    const [riders] = useState([
        {
            id: "RC-992-ET",
            name: "Abel Mulugeta",
            initials: "AM",
            phone: "+251 911 234 567",
            status: "Available",
            location: "Bole, Sector 4",
            verified: true,
            hasImage: false
        },
        {
            id: "RC-841-ET",
            name: "Saba Gebre",
            image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCa-xNDjYFNkc9Jw1_dhm5g1Hm6fGqq2QwZsU29bNNkOD3o7L9J5V0i0KbZqPrRokDMHE9DJoZ50vFKgFS8lpCxnvxbtO5vHUbQNcpSpCXVuKoTzErIrxTWP8Ik7yAfVOpLHJvSGXK8xqax2YEdv-qG0XTLCpACHZVUKpJh2gW9SHuLNk57PugDa_bXlfOP5pOSSnk2OofB7kQufPyT1sFAM6LsMlYnKKL1rEtdL5cqBoAtU8vbclJaQHfht-296v9bhexJnQVL1g",
            phone: "+251 912 883 291",
            status: "On Job",
            location: "Arada, Sector 2",
            verified: true,
            hasImage: true
        },
        {
            id: "RC-104-ET",
            name: "Kebede Tesfaye",
            initials: "KT",
            phone: "+251 920 445 112",
            status: "Offline",
            location: "Nefas Silk, S7",
            verified: false,
            hasImage: false
        }
    ]);

    return (
        <div className="layout-container flex flex-col min-h-screen">
            <Header locations={[]} selectedLocation="" setSelectedLocation={() => {}} />

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
                            <p className="text-2xl font-display text-white">1,284</p>
                        </div>
                        <div className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px]">
                            <p className="text-emerald-500 text-[10px] uppercase font-bold tracking-widest">Currently Active</p>
                            <p className="text-2xl font-display text-white">452</p>
                        </div>
                        <div 
                            onClick={() => navigate('/pending-verifications')}
                            className="bg-card-dark border border-slate-700/50 rounded-xl px-5 py-3 min-w-[140px] cursor-pointer hover:border-amber-500/50 transition-colors group"
                        >
                            <p className="text-amber-500 text-[10px] uppercase font-bold tracking-widest group-hover:text-amber-400 transition-colors">Pending Verification</p>
                            <p className="text-2xl font-display text-white group-hover:text-amber-100 transition-colors">{riders.filter(r => !r.verified).length || 18}</p>
                        </div>
                    </div>
                </div>

                {/* Main Content Card */}
                <div className="bg-card-dark rounded-xl border border-slate-700/50 overflow-hidden">
                    {/* Navigation & Search */}
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between border-b border-slate-700/50 px-6 py-4 gap-4 bg-slate-800/30">
                        <div className="flex gap-1 p-1 bg-slate-900 rounded-lg w-fit">
                            <button className="px-6 py-2 rounded-md bg-primary text-white font-display uppercase text-sm tracking-wide">All Riders</button>
                            <button className="px-6 py-2 rounded-md text-slate-400 hover:text-white font-display uppercase text-sm tracking-wide transition-colors">Available Riders</button>
                        </div>
                        <div className="relative w-full lg:max-w-md">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">search</span>
                            <input 
                                className="w-full bg-slate-900 border-slate-700 text-slate-200 pl-10 pr-4 py-2.5 rounded-lg focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-slate-600 text-sm" 
                                placeholder="Search by name or phone number..." 
                                type="text" 
                            />
                        </div>
                    </div>

                    {/* Data Table */}
                    <div className="overflow-x-auto">
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
                                {riders.map((rider, idx) => (
                                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="size-10 rounded-lg bg-slate-700 flex items-center justify-center font-display text-lg text-white font-bold border border-slate-600 overflow-hidden">
                                                    {rider.hasImage ? (
                                                        <img alt="Rider Profile" className="h-full w-full object-cover" src={rider.image} />
                                                    ) : (
                                                        rider.initials
                                                    )}
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-1.5">
                                                        <p className="text-sm font-semibold text-white">{rider.name}</p>
                                                        {rider.verified && <span className="material-symbols-outlined text-blue-400 text-sm" title="Verified">verified</span>}
                                                    </div>
                                                    <p className="text-[11px] text-slate-500 font-medium">ID: {rider.id}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <p className="text-sm text-slate-300 font-mono">{rider.phone}</p>
                                        </td>
                                        <td className="px-6 py-4">
                                            {rider.status === "Available" && (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider">
                                                    <span className="size-1.5 rounded-full bg-emerald-500"></span>
                                                    {rider.status}
                                                </span>
                                            )}
                                            {rider.status === "On Job" && (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-500 text-[10px] font-bold uppercase tracking-wider">
                                                    <span className="size-1.5 rounded-full bg-amber-500"></span>
                                                    {rider.status}
                                                </span>
                                            )}
                                            {rider.status === "Offline" && (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 text-slate-500 text-[10px] font-bold uppercase tracking-wider">
                                                    <span className="size-1.5 rounded-full bg-slate-500"></span>
                                                    {rider.status}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2 text-slate-400">
                                                <span className="material-symbols-outlined text-sm">location_on</span>
                                                <span className="text-sm">{rider.location}</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Footer */}
                    <div className="flex items-center justify-between px-6 py-4 bg-slate-800/20 border-t border-slate-700/50">
                        <p className="text-xs text-slate-500 font-medium">Showing 1-{riders.length} of 1,284 riders</p>
                        <div className="flex gap-2">
                            <button className="p-1 text-slate-400 hover:text-white disabled:opacity-30" disabled>
                                <span className="material-symbols-outlined">chevron_left</span>
                            </button>
                            <button className="px-3 py-1 rounded bg-primary/20 text-primary text-xs font-bold">1</button>
                            <button className="px-3 py-1 rounded hover:bg-slate-800 text-slate-400 text-xs font-bold transition-colors">2</button>
                            <button className="px-3 py-1 rounded hover:bg-slate-800 text-slate-400 text-xs font-bold transition-colors">3</button>
                            <span className="text-slate-600">...</span>
                            <button className="px-3 py-1 rounded hover:bg-slate-800 text-slate-400 text-xs font-bold transition-colors">129</button>
                            <button className="p-1 text-slate-400 hover:text-white">
                                <span className="material-symbols-outlined">chevron_right</span>
                            </button>
                        </div>
                    </div>
                </div>
            </main>


        </div>
    );
}
