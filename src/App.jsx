import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import ReportIncident from "./pages/ReportIncident";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Home />} />

        <Route path="/report" element={<ReportIncident />} />

        <Route path="/dashboard" element={<Dashboard />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;