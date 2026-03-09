import { Link } from "react-router-dom";

export default function SosFeed({ sos }) {
    const displaySos = sos.slice(0, 5);

    if (sos.length === 0) {
        return (
            <section className="bg-slate-panel rounded-xl overflow-hidden border border-slate-700">
                <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                    <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary">rss_feed</span>
                        SOS FEED SECTION
                    </h2>
                </div>
                <div className="p-6 text-center space-y-2">
                    <span className="material-symbols-outlined text-slate-500 text-3xl">emergency_share</span>
                    <p className="text-slate-500 text-sm">No active SOS requests at this time.</p>
                </div>
                <div className="px-6 py-4 border-t border-slate-700 flex justify-center bg-slate-800/30 w-full">
                    <Link to="/sos" className="text-sm font-medium text-primary hover:text-red-400 uppercase tracking-wide flex items-center gap-1 transition-colors">
                        View All SOS Requests
                        <span className="material-symbols-outlined text-sm">arrow_forward</span>
                    </Link>
                </div>
            </section>
        );
    }

    return (
        <section className="bg-slate-panel rounded-xl overflow-hidden border border-slate-700 flex flex-col">
            <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
                <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">rss_feed</span>
                    SOS FEED SECTION
                </h2>
                <div className="flex p-1 bg-slate-800 rounded-lg">
                    <button className="px-4 py-1.5 text-sm font-medium rounded-md bg-primary text-white">Live SOS</button>
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase oswald tracking-widest">
                        <tr>
                            <th className="px-6 py-4 font-medium">Job ID</th>
                            <th className="px-6 py-4 font-medium">Caller</th>
                            <th className="px-6 py-4 font-medium">Type</th>
                            <th className="px-6 py-4 font-medium">Status</th>
                            <th className="px-6 py-4 font-medium">Village</th>
                            <th className="px-6 py-4 font-medium">Assigned Rider</th>
                            <th className="px-6 py-4 font-medium">Time (UTC)</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700 text-sm">
                        {displaySos.map(job => (
                            <tr key={job.id} className="hover:bg-slate-800/40 transition-colors">
                                <td className="px-6 py-4 font-mono text-slate-400">#{job.id}</td>
                                <td className="px-6 py-4 font-medium">{job.caller}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${job.type === 'MATERNITY' ? 'bg-red-600/10 text-red-500' : 'bg-amber-600/10 text-amber-500'}`}>
                                        {job.type}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <span className={`w-2 h-2 rounded-full ${job.status === 'CLAIMED' ? 'bg-emerald-500' : 'bg-red-600 animate-pulse'}`}></span>
                                        <span className={`${job.status === 'CLAIMED' ? 'text-emerald-500' : 'text-red-500'} font-semibold`}>{job.status}</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4">{job.village} ({job.village_code})</td>
                                <td className="px-6 py-4 text-slate-400">
                                    {job.assigned_rider || <span className="text-slate-500 italic">Unassigned</span>}
                                </td>
                                <td className="px-6 py-4 text-slate-400">{new Date(job.time).toLocaleTimeString()}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="px-6 py-4 border-t border-slate-700 flex justify-center bg-slate-800/30">
                <Link to="/sos" className="text-sm font-medium text-primary hover:text-red-400 uppercase tracking-wide flex items-center gap-1 transition-colors">
                    View All SOS Requests
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </Link>
            </div>
        </section>
    );
}
