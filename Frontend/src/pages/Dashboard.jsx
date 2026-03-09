import { useState, useEffect, useCallback } from "react";
import Header from "../components/Header";
import Stats from "../components/Stats";
import SosFeed from "../components/SosFeed";
import RiderRoster from "../components/RiderRoster";
import Hazards from "../components/Hazards";
import { fetchStats } from "../api/stats";
import { fetchSos } from "../api/sos";
import { fetchRiders } from "../api/riders";
import { fetchHazards, clearHazard } from "../api/hazards";
import { useLocation } from "../context/LocationContext";

function Dashboard() {
    const { selectedLocation } = useLocation();
    
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
            const [statsData, sosData, ridersData, hazardsData] = await Promise.all([
                fetchStats(selectedLocation).catch(() => null),
                fetchSos("all", selectedLocation).catch(() => ({ data: [] })),
                fetchRiders("all", selectedLocation).catch(() => ({ data: [] })),
                fetchHazards(selectedLocation).catch(() => ({ data: [] }))
            ]);

            if (statsData) setStats(statsData);
            if (sosData) setSosFeed(sosData.data || []);
            if (ridersData) setRiders(ridersData.data || []);
            if (hazardsData) setHazards(hazardsData.data || []);
            
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, [selectedLocation]);
    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleClearHazard = async (id) => {
        try {
            await clearHazard(id);
            fetchData();
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <>
            <Header />
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
