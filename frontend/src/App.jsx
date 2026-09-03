import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import ReportIncident from "./pages/ReportIncident";
import Dashboard from "./pages/Dashboard";
import IncidentDetails from "./pages/IncidentDetails";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Home />} />

        <Route path="/report" element={<ReportIncident />} />

        <Route path="/dashboard" element={<Dashboard />} />

        <Route path="/incident" element={<IncidentDetails />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;