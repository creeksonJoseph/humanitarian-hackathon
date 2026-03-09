import { Link } from "react-router-dom";

export default function RiderRoster({ riders, isLoading }) {
  const displayRiders = riders.slice(0, 5);

  if (isLoading) {
    return (
      <section className="bg-slate-panel rounded-xl overflow-hidden border border-slate-700">
        <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
          <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-500">
              sports_motorsports
            </span>
            RIDER ROSTER
          </h2>
        </div>
        <div className="p-6 text-center space-y-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto"></div>
          <p className="text-slate-500 text-sm">Loading riders...</p>
        </div>
        <div className="px-6 py-4 border-t border-slate-700 flex justify-center bg-slate-800/30 w-full">
          <Link
            to="/riders"
            className="text-sm font-medium text-emerald-500 hover:text-emerald-400 uppercase tracking-wide flex items-center gap-1 transition-colors"
          >
            View All Riders
            <span className="material-symbols-outlined text-sm">
              arrow_forward
            </span>
          </Link>
        </div>
      </section>
    );
  }

  if (riders.length === 0) {
    return (
      <section className="bg-slate-panel rounded-xl overflow-hidden border border-slate-700">
        <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
          <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-500">
              sports_motorsports
            </span>
            RIDER ROSTER
          </h2>
        </div>
        <div className="p-6 text-center space-y-2">
          <span className="material-symbols-outlined text-slate-500 text-3xl">
            sports_motorsports
          </span>
          <p className="text-slate-500 text-sm">
            No riders currently available.
          </p>
        </div>
        <div className="px-6 py-4 border-t border-slate-700 flex justify-center bg-slate-800/30 w-full">
          <Link
            to="/riders"
            className="text-sm font-medium text-emerald-500 hover:text-emerald-400 uppercase tracking-wide flex items-center gap-1 transition-colors"
          >
            View All Riders
            <span className="material-symbols-outlined text-sm">
              arrow_forward
            </span>
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-slate-panel rounded-xl overflow-hidden border border-slate-700 flex flex-col">
      <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
        <h2 className="oswald text-xl font-semibold tracking-wide flex items-center gap-2">
          <span className="material-symbols-outlined text-emerald-500">
            sports_motorsports
          </span>
          RIDER ROSTER
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase oswald tracking-widest">
            <tr>
              <th className="px-6 py-4 font-medium">Name</th>
              <th className="px-6 py-4 font-medium">Phone</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Location</th>
              <th className="px-6 py-4 font-medium">Verified</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700 text-sm">
            {displayRiders.map((rider) => (
              <tr
                key={rider.phone}
                className="hover:bg-slate-800/40 transition-colors"
              >
                <td className="px-6 py-4 font-medium">{rider.name}</td>
                <td className="px-6 py-4 text-slate-400">{rider.phone}</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium border ${rider.status === "AVAILABLE" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-red-500/10 text-red-500 border-red-500/20"}`}
                  >
                    {rider.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {rider.current_location} ({rider.location_code})
                </td>
                <td className="px-6 py-4">
                  {rider.is_verified && (
                    <span className="material-symbols-outlined text-emerald-500 text-lg">
                      verified
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-6 py-4 border-t border-slate-700 flex justify-center bg-slate-800/30">
        <Link
          to="/riders"
          className="text-sm font-medium text-emerald-500 hover:text-emerald-400 uppercase tracking-wide flex items-center gap-1 transition-colors"
        >
          View All Riders
          <span className="material-symbols-outlined text-sm">
            arrow_forward
          </span>
        </Link>
      </div>
    </section>
  );
}
