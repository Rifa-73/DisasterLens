import { useNavigate, useLocation } from "react-router-dom";
import {
  Radio,
  ArrowRight,
  Home,
  FileWarning,
  BarChart3,
} from "lucide-react";

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: "/", label: "Home", icon: Home },
    { path: "/report", label: "Report Incident", icon: FileWarning },
    { path: "/dashboard", label: "Live Dashboard", icon: BarChart3 },
  ];

  return (
    <nav className="w-full px-6 py-4 bg-white border-b border-[#DDE5DE]">
      <div className="max-w-7xl mx-auto flex items-center justify-between">

        {/* LOGO */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-xl bg-[#2F7D4A] flex items-center justify-center shadow-sm">
            <Radio className="w-5 h-5 text-white" />
          </div>

          <div className="text-left">
            <h1 className="font-bold text-lg">RNR</h1>
            <p className="text-[10px] text-[#68736B] tracking-[0.2em]">
              DISASTER INTELLIGENCE
            </p>
          </div>
        </button>

        {/* NAVIGATION */}
        <div className="hidden md:flex items-center gap-2">
          {navItems.map(({ path, label, icon: Icon }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition ${
                isActive(path)
                  ? "text-[#2F7D4A] bg-[#EAF4EC] font-medium"
                  : "text-[#68736B] hover:text-[#2F7D4A] hover:bg-[#F3F7F3]"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* REPORT */}
        <button
          onClick={() => navigate("/report")}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2F7D4A] text-white text-sm font-semibold hover:bg-[#25663C] transition"
        >
          Report
          <ArrowRight className="w-4 h-4" />
        </button>

      </div>
    </nav>
  );
}

export default Navbar;