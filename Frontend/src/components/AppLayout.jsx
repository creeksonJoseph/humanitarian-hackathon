import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppLayout() {
    return (
        <div className="flex flex-col h-screen overflow-hidden text-slate-300 font-sans">
            <Header />
            <div className="flex flex-1 overflow-hidden bg-[#0B1121]">
                <Sidebar />
                <div className="flex-1 overflow-y-auto">
                    <Outlet />
                </div>
            </div>
        </div>
    );
}
