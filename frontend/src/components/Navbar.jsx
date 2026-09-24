import { useLocation, useNavigate } from "react-router-dom";
import { Radio, ArrowRight, Home, FileWarning, BarChart3 } from "lucide-react";

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const items = [
    { path: "/", label: "Home", icon: Home },
    { path: "/report", label: "Report Incident", icon: FileWarning },
    { path: "/dashboard", label: "Live Dashboard", icon: BarChart3 },
  ];

  return (
    <nav className="border-b border-[#E4E8E2] bg-white">
      <div className="max-w-7xl mx-auto h-[68px] px-5 md:px-8 flex items-center justify-between">

        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-3 text-left"
        >
          <div className="w-9 h-9 rounded-lg bg-[#3F6546] flex items-center justify-center">
            <Radio className="w-4 h-4 text-white" />
          </div>

          <div>
            <p className="font-bold text-sm text-[#263229] leading-none">
              DisasterLens
            </p>
            <p className="text-[8px] tracking-[0.22em] text-[#809083] mt-1">
              FLOOD INTELLIGENCE
            </p>
          </div>
        </button>

        <div className="hidden md:flex items-center gap-1">
          {items.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path;

            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs transition ${
                  active
                    ? "bg-[#EEF4EC] text-[#365D3D] font-semibold"
                    : "text-[#68736B] hover:bg-[#F5F7F4]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            );
          })}
        </div>

        <button
          onClick={() => navigate("/report")}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#3F6546] text-white text-xs font-semibold hover:bg-[#315338] transition"
        >
          Report
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </nav>
  );
}

export default Navbar;