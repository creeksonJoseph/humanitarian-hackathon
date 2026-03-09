import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { LocationProvider } from "./context/LocationContext";
import Dashboard from "./pages/Dashboard";
import Riders from "./pages/Riders";
import PendingVerifications from "./pages/PendingVerifications";
import Hazards from "./pages/Hazards";
import Sos from "./pages/Sos";

function App() {
    return (
        <LocationProvider>
            <Router>
                <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/riders" element={<Riders />} />
                <Route path="/pending-verifications" element={<PendingVerifications />} />
                <Route path="/hazards" element={<Hazards />} />
                <Route path="/sos" element={<Sos />} />
            </Routes>
            </Router>
        </LocationProvider>
    );
}

export default App;
