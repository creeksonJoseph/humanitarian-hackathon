import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
    LayoutDashboard, 
    Users, 
    ShieldAlert, 
    TriangleAlert, 
    RadioReceiver,
    ChevronLeft,
    ChevronRight,
    Map
} from "lucide-react";

export default function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();

    const navItems = [
        { path: "/", label: "Dashboard", icon: LayoutDashboard },
        { path: "/riders", label: "Riders", icon: Users },
        { path: "/pending-verifications", label: "Verifications", icon: ShieldAlert },
        { path: "/hazards", label: "Hazards", icon: TriangleAlert },
        { path: "/sos", label: "SOS Feed", icon: RadioReceiver },
    ];

    return (
        <aside 
            className={`bg-slate-panel border-r border-slate-700/50 flex flex-col transition-all duration-300 relative ${collapsed ? 'w-20' : 'w-64'}`}
        >

            {/* Collapse Toggle */}
            <button 
                onClick={() => setCollapsed(!collapsed)}
                className="absolute -right-3 top-24 bg-slate-800 border border-slate-700/50 rounded-full p-1 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors z-10"
            >
                {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>

            {/* Navigation Links */}
            <nav className="flex-1 py-6 px-3 space-y-2 overflow-y-auto">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            title={collapsed ? item.label : undefined}
                            className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors group ${
                                isActive 
                                    ? 'bg-primary/10 text-primary font-medium' 
                                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                            }`}
                        >
                            <Icon size={20} className={isActive ? "text-primary" : "group-hover:text-white"} />
                            {!collapsed && (
                                <span className="oswald tracking-wide uppercase text-sm">{item.label}</span>
                            )}
                        </Link>
                    );
                })}
            </nav>
            
            {!collapsed && (
                <div className="p-4 border-t border-slate-700/50">
                     <p className="text-xs text-slate-500 text-center font-mono">OC-CMD v1.0.0</p>
                </div>
            )}
        </aside>
    );
}
