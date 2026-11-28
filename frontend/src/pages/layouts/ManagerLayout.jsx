
import { useState } from "react";
import {
  LayoutDashboard,
  Package,
  Warehouse,
  Layers3,
  ShoppingCart,
  CalendarClock,
  BrainCircuit,
  ArrowLeftRight,
  Store,
  Users,
  Settings,
  RefreshCw,
  Boxes,
  Menu,
  X,
  UserRound,
} from "lucide-react";

const managerNavigation = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "inventory", label: "Inventory", icon: Warehouse },
  { id: "products", label: "Products", icon: Package },
  { id: "batches", label: "Batches", icon: Layers3 },
  { id: "sales", label: "Sales", icon: ShoppingCart },
  { id: "expiry", label: "Expiry Management", icon: CalendarClock },
  { id: "forecast", label: "AI Forecast", icon: BrainCircuit },
  { id: "redistribution", label: "Redistribution", icon: ArrowLeftRight },
  { id: "community", label: "Store Community", icon: Store },
  { id: "staff", label: "Staff Management", icon: Users },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "stores", label: "Stores", icon: Store },
];

export default function ManagerLayout({
  activePage = "dashboard",
  onNavigate,
  onRefresh,
  children,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function handleNavigate(page) {
    onNavigate?.(page);
    setMobileMenuOpen(false);
  }

  return (
    <div className="app-shell manager-shell">
      {mobileMenuOpen && (
        <button
          className="mobile-sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <aside className={`sidebar manager-sidebar ${mobileMenuOpen ? "mobile-open" : ""}`}>
        <div className="brand">
          <div className="brand-icon">
            <Boxes size={23} />
          </div>
          <div>
            <h2>ZeroWasteNet</h2>
            <span>Manager workspace</span>
          </div>
          <button
            className="mobile-close-button"
            aria-label="Close menu"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <div className="nav-heading">MANAGEMENT</div>

        <nav className="navigation">
          {managerNavigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`nav-item ${activePage === item.id ? "active" : ""}`}
                onClick={() => handleNavigate(item.id)}
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="manager-staff-link">
          <button
            className="nav-item"
            onClick={() => handleNavigate("staff-dashboard")}
          >
            <UserRound size={19} />
            <span>Staff Dashboard</span>
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="status-dot" />
          Manager access
          <span>v1.0</span>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar manager-topbar">
          <div className="topbar-title">
            <button
              className="mobile-menu-button"
              aria-label="Open navigation"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu size={21} />
            </button>

            <div>
              <div className="breadcrumb">
                Manager Workspace / {managerNavigation.find((item) => item.id === activePage)?.label || "Dashboard"}
              </div>
              <h1>
                {managerNavigation.find((item) => item.id === activePage)?.label ||
                  (activePage === "staff-dashboard" ? "Staff Dashboard" : "Dashboard")}
              </h1>
            </div>
          </div>

          <div className="top-actions">
            <button
              className="icon-button"
              onClick={onRefresh}
              title="Refresh data"
              aria-label="Refresh data"
            >
              <RefreshCw size={18} />
            </button>

            <div className="profile">
              <div className="avatar">MG</div>
              <div>
                <strong>Store Manager</strong>
                <span>Manager account</span>
              </div>
            </div>
          </div>
        </header>

        <section className="content manager-content">
          {children}
        </section>
      </main>
    </div>
  );
}
