import { Link } from "react-router-dom";

export default function Hazards({ hazards, handleClear, isLoading }) {
    const displayHazards = hazards.slice(0, 5);

    if (isLoading) {
        return (
            <section className="bg-slate-panel overflow-hidden border border-slate-700 flex flex-col">
                <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2 text-amber-500">
                        <span className="material-symbols-outlined">warning</span>
                        ACTIVE HAZARDS
                    </h2>
                    <span className="bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded text-xs font-bold">...</span>
                </div>
                <div className="p-6 text-center space-y-2">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mx-auto"></div>
                    <p className="text-slate-500 text-sm">Loading hazards...</p>
                </div>
                <div className="p-4 border-t border-slate-700 flex justify-center bg-slate-800/30 w-full">
                    <Link to="/hazards" className="text-sm font-medium text-amber-500 hover:text-amber-400 uppercase tracking-wide flex items-center gap-1 transition-colors">
                        View All Hazards
                        <span className="material-symbols-outlined text-sm">arrow_forward</span>
                    </Link>
                </div>
            </section>
        );
    }

    if (hazards.length === 0) {
        return (
            <section className="bg-slate-panel overflow-hidden border border-slate-700 flex flex-col">
                <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2 text-amber-500">
                        <span className="material-symbols-outlined">warning</span>
                        ACTIVE HAZARDS
                    </h2>
                    <span className="bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded text-xs font-bold">0 Total</span>
                </div>
                <div className="p-6 text-center space-y-2">
                    <span className="material-symbols-outlined text-slate-500 text-3xl">report_problem</span>
                    <p className="text-slate-500 text-sm">No active hazards reported.</p>
                </div>
                <div className="p-4 border-t border-slate-700 flex justify-center bg-slate-800/30 w-full">
                    <Link to="/hazards" className="text-sm font-medium text-amber-500 hover:text-amber-400 uppercase tracking-wide flex items-center gap-1 transition-colors">
                        View All Hazards
                        <span className="material-symbols-outlined text-sm">arrow_forward</span>
                    </Link>
                </div>
            </section>
        );
    }

    return (
        <section className="bg-slate-panel overflow-hidden border border-slate-700 flex flex-col">
            <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2 text-amber-500">
                    <span className="material-symbols-outlined">warning</span>
                    ACTIVE HAZARDS
                </h2>
                <span className="bg-amber-500/20 text-amber-500 px-2 py-0.5 rounded text-xs font-bold">{hazards.length} Total</span>
            </div>
            <div className="p-6 space-y-4 flex-1 overflow-y-auto">
                {displayHazards.map(hazard => (
                    <div key={hazard.id} className="p-4 bg-slate-800 border-l-4 border-amber-500 space-y-3">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-[10px] text-amber-500 font-bold uppercase oswald">#{hazard.id} - {hazard.status}</p>
                                <h4 className="font-bold text-slate-100">{(hazard.hazard_type || "").replace("_", " ")}</h4>
                            </div>
                            <span className="text-[10px] text-slate-500 font-mono">{new Date(hazard.reported_at).toLocaleTimeString()}</span>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs text-slate-400 flex items-center gap-1">
                                <span className="material-symbols-outlined text-sm">route</span> Route Code: {hazard.route_description}
                            </p>
                            <p className="text-xs text-slate-400 flex items-center gap-1">
                                <span className="material-symbols-outlined text-sm">person</span> By: {hazard.reported_by_number}
                            </p>
                        </div>
                        <button 
                            onClick={() => handleClear(hazard.id)}
                            className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-2 rounded transition-colors flex items-center justify-center gap-2 text-sm uppercase oswald tracking-wider"
                        >
                            <span className="material-symbols-outlined text-sm">done_all</span> Clear Hazard
                        </button>
                    </div>
                ))}
            </div>
            <div className="p-4 border-t border-slate-700 flex justify-center bg-slate-800/30">
                <Link to="/hazards" className="text-sm font-medium text-amber-500 hover:text-amber-400 uppercase tracking-wide flex items-center gap-1 transition-colors">
                    View All Hazards
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </Link>
            </div>
        </section>
    );
}
