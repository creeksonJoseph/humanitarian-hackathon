import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { LocationProvider } from "./context/LocationContext";
import Dashboard from "./pages/Dashboard";
import Riders from "./pages/Riders";
import PendingVerifications from "./pages/PendingVerifications";
import Hazards from "./pages/Hazards";
import Sos from "./pages/Sos";
import Login from "./pages/Login";
import AppLayout from "./components/AppLayout";

function App() {
  return (
    <LocationProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/riders" element={<Riders />} />
            <Route
              path="/pending-verifications"
              element={<PendingVerifications />}
            />
            <Route path="/hazards" element={<Hazards />} />
            <Route path="/sos" element={<Sos />} />
          </Route>
        </Routes>
      </Router>
    </LocationProvider>
  );
}

export default App;
