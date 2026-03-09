import { useState, useEffect, useCallback } from "react";
import Header from "../components/Header";
import Stats from "../components/Stats";
import SosFeed from "../components/SosFeed";
import RiderRoster from "../components/RiderRoster";
import Hazards from "../components/Hazards";

const API_BASE = "http://localhost:8000/api";

function Dashboard() {
    const [locations, setLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState("");
    
    const [stats, setStats] = useState({
        active_sos: 0,
        total_sos: 0,
        available_riders: 0,
        total_riders: 0,
        active_hazards: 0
    });
    
    const [sosFeed, setSosFeed] = useState([]);
    const [riders, setRiders] = useState([]);
    const [hazards, setHazards] = useState([]);

    const fetchData = useCallback(async () => {
        try {
            const locParam = selectedLocation ? `?place=${selectedLocation}` : "";
            
            const [statsRes, sosRes, ridersRes, hazardsRes] = await Promise.all([
                fetch(`${API_BASE}/stats${locParam}`),
                fetch(`${API_BASE}/sos${locParam}`),
                fetch(`${API_BASE}/riders${locParam}`),
                fetch(`${API_BASE}/hazards${locParam}`),
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (sosRes.ok) setSosFeed(await sosRes.json());
            if (ridersRes.ok) setRiders(await ridersRes.json());
            if (hazardsRes.ok) setHazards(await hazardsRes.json());
            
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, [selectedLocation]);

    const fetchLocations = async () => {
        try {
            const res = await fetch(`${API_BASE}/locations`);
            if (res.ok) setLocations(await res.json());
        } catch (error) {
            console.error(error);
        }
    }

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        fetchLocations();
    }, []);

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleClearHazard = async (id) => {
        try {
            await fetch(`${API_BASE}/hazards/${id}/clear`, { method: "POST" });
            fetchData();
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <>
            <Header locations={locations} selectedLocation={selectedLocation} setSelectedLocation={setSelectedLocation} />
            <main className="max-w-[1600px] mx-auto p-6 space-y-6">
                <Stats stats={stats} />
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 space-y-6">
                        <SosFeed sos={sosFeed} />
                        <RiderRoster riders={riders} />
                    </div>
                    <aside className="space-y-6">
                        <Hazards hazards={hazards} handleClear={handleClearHazard} />
                    </aside>
                </div>
            </main>
        </>
    );
}

export default Dashboard;
