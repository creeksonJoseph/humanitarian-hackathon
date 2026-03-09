import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function AppLayout() {
    return (
        <div className="flex h-screen bg-[#0B1121] overflow-hidden text-slate-300 font-sans">
            <Sidebar />
            <div className="flex-1 overflow-y-auto">
                <Outlet />
            </div>
        </div>
    );
}
