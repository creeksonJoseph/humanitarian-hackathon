/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect } from 'react';
import { fetchLocations } from '../api/locations';

const LocationContext = createContext();

export function LocationProvider({ children }) {
    const [locations, setLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState("");

    useEffect(() => {
        const loadLocations = async () => {
            try {
                const data = await fetchLocations();
                setLocations(data);
            } catch (err) {
                console.error("Failed to load locations", err);
            }
        };
        loadLocations();
    }, []);

    return (
        <LocationContext.Provider value={{ locations, selectedLocation, setSelectedLocation }}>
            {children}
        </LocationContext.Provider>
    );
}

export function useLocation() {
    return useContext(LocationContext);
}
