import { useLocation } from '../context/LocationContext';

export default function Header() {
    const { locations, selectedLocation, setSelectedLocation } = useLocation();
    
    return (
        <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-panel px-6 py-4 sticky top-0 z-50">
            <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="bg-primary p-1.5 rounded-lg">
                        <span className="material-symbols-outlined text-white text-3xl">emergency</span>
                    </div>
                    <h1 className="oswald text-2xl font-bold tracking-wider text-slate-900 dark:text-white uppercase">OKOA ROUTE COMMAND CENTER</h1>
                </div>
                <div className="flex items-center gap-4 flex-1 justify-end">
                    <div className="relative w-full max-w-xs">
                        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">location_on</span>
                        <select 
                            value={selectedLocation} 
                            onChange={e => setSelectedLocation(e.target.value)}
                            className="w-full bg-slate-100 dark:bg-slate-800 border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary text-slate-700 dark:text-slate-200 appearance-none"
                        >
                            <option value="">Filter by Place (Global)</option>
                            {locations.map(loc => (
                                <option key={loc.code} value={loc.code}>{loc.name} ({loc.code})</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-700">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-semibold">Duty Officer</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-tighter oswald">Commander Alpha</p>
                        </div>
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center border-2 border-primary/30">
                            <span className="material-symbols-outlined text-primary">person</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
