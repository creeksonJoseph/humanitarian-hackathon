import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Riders from "./pages/Riders";
import PendingVerifications from "./pages/PendingVerifications";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/riders" element={<Riders />} />
                <Route path="/pending-verifications" element={<PendingVerifications />} />
            </Routes>
        </Router>
    );
}

export default App;
