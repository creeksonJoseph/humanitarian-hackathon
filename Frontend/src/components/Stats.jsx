export default function Stats({ stats }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-red-600 p-6 shadow-lg shadow-red-900/20 border border-red-500/30">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-red-100 text-sm font-medium uppercase tracking-wider oswald">Active SOS Jobs</p>
                        <h3 className="text-4xl font-bold text-white mt-1">{stats.active_sos}</h3>
                    </div>
                    <span className="material-symbols-outlined text-white/50 text-4xl">emergency_share</span>
                </div>
                <div className="mt-4 flex items-center text-red-100 text-xs">
                    <span className="material-symbols-outlined text-xs mr-1">trending_up</span>
                    <span>Tracking live</span>
                </div>
            </div>
            
            <div className="bg-emerald-500 p-6 shadow-lg shadow-emerald-900/20 border border-emerald-400/30">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-emerald-50 text-sm font-medium uppercase tracking-wider oswald">Available Riders</p>
                        <h3 className="text-4xl font-bold text-white mt-1">{stats.available_riders}</h3>
                    </div>
                    <span className="material-symbols-outlined text-white/50 text-4xl">pedal_bike</span>
                </div>
                <div className="mt-4 flex items-center text-emerald-50 text-xs">
                    <span className="material-symbols-outlined text-xs mr-1">check_circle</span>
                    <span>Ready for dispatch</span>
                </div>
            </div>

            <div className="bg-amber-500 p-6 shadow-lg shadow-amber-900/20 border border-amber-400/30">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-amber-50 text-sm font-medium uppercase tracking-wider oswald">Active Hazards</p>
                        <h3 className="text-4xl font-bold text-white mt-1">{stats.active_hazards}</h3>
                    </div>
                    <span className="material-symbols-outlined text-white/50 text-4xl">warning</span>
                </div>
                <div className="mt-4 flex items-center text-amber-50 text-xs">
                    <span className="material-symbols-outlined text-xs mr-1">report_problem</span>
                    <span>Requires attention</span>
                </div>
            </div>

            <div className="bg-slate-panel p-6 shadow-lg border border-slate-700">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-slate-400 text-sm font-medium uppercase tracking-wider oswald">Total Riders</p>
                        <h3 className="text-4xl font-bold text-white mt-1">{stats.total_riders}</h3>
                    </div>
                    <span className="material-symbols-outlined text-slate-600 text-4xl">groups</span>
                </div>
                <div className="mt-4 flex items-center text-slate-400 text-xs">
                    <span className="material-symbols-outlined text-xs mr-1">info</span>
                    <span>Combined fleet strength</span>
                </div>
            </div>
        </div>
    );
}
