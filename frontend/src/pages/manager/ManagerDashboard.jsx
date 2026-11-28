import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CalendarClock,
  Package,
  RefreshCw,
  ShoppingBag,
  Store,
  TrendingUp,
  Warehouse,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import NearbyStores from "../../components/NearbyStores";

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function getDaysUntilExpiry(expiryDate) {
  if (!expiryDate) return null;
  const datePart = String(expiryDate).slice(0, 10);
  const expiry = new Date(`${datePart}T00:00:00`);
  if (Number.isNaN(expiry.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((expiry.getTime() - today.getTime()) / 86400000);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function ManagerDashboard({
  data = {},
  totalStock = 0,
  chartData = [],
  onNavigate = () => {},
  onRefresh = () => {},
}) {
  const products = safeArray(data.products);
  const inventory = safeArray(data.inventory);
  const batches = safeArray(data.batches);
  const stores = safeArray(data.stores);

  const expiryBatches = batches
    .map((batch) => ({ ...batch, daysLeft: getDaysUntilExpiry(batch.expiry_date) }))
    .filter((batch) => batch.daysLeft !== null)
    .filter((batch) => Number(batch.quantity_remaining ?? 0) > 0)
    .sort((a, b) => a.daysLeft - b.daysLeft);

  const expiredBatches = expiryBatches.filter((batch) => batch.daysLeft < 0);
  const nearExpiryBatches = expiryBatches.filter(
    (batch) => batch.daysLeft >= 0 && batch.daysLeft <= 7
  );

  const stats = [
    {
      label: "Registered products",
      value: products.length.toLocaleString("en-IN"),
      caption: "Product catalogue",
      icon: Package,
      tone: "green",
    },
    {
      label: "Available stock",
      value: Number(totalStock || 0).toLocaleString("en-IN"),
      caption: "Units across inventory records",
      icon: Warehouse,
      tone: "blue",
    },
    {
      label: "Inventory batches",
      value: batches.length.toLocaleString("en-IN"),
      caption: "Recorded batches",
      icon: Boxes,
      tone: "purple",
    },
    {
      label: "Expiry watch",
      value: (expiredBatches.length + nearExpiryBatches.length).toLocaleString("en-IN"),
      caption: `${expiredBatches.length} expired · ${nearExpiryBatches.length} due in 7 days`,
      icon: CalendarClock,
      tone: "orange",
    },
  ];

  const actions = [
    { id: "inventory", label: "Review inventory", detail: "Check available quantities", icon: Warehouse },
    { id: "products", label: "Manage products", detail: "Catalogue and product details", icon: Package },
    { id: "batches", label: "Manage batches", detail: "Received stock and expiry dates", icon: Boxes },
    { id: "stores", label: "View stores", detail: "Registered store locations", icon: Store },
  ];

  const chartRows = safeArray(chartData);
  const recentBatches = [...batches].slice(-5).reverse();
  const priorityBatches = expiryBatches.slice(0, 4);

  return (
    <div className="manager-dashboard">
      <div className="manager-welcome-card">
        <div>
          <span className="dashboard-eyebrow">MANAGER OVERVIEW</span>
          <h2>Good to see you again.</h2>
          <p>Here is the latest snapshot of your grocery inventory operations.</p>
        </div>
        <button className="dashboard-refresh-button" type="button" onClick={onRefresh}>
          <RefreshCw size={16} /> Refresh overview
        </button>
      </div>

      <div className="stats-grid manager-stats-grid">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <article className="stat-card manager-stat-card" key={stat.label}>
              <div className={`stat-icon ${stat.tone}`}><Icon size={21} /></div>
              <p>{stat.label}</p>
              <h2>{stat.value}</h2>
              <span>{stat.caption}</span>
            </article>
          );
        })}
      </div>

      <div className="dashboard-grid manager-primary-grid">
        <section className="panel chart-panel manager-chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Workspace data overview</h3>
              <p>Current records retrieved from your backend</p>
            </div>
            <TrendingUp size={21} />
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartRows} margin={{ top: 8, right: 10, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eaf0eb" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "#7d8e83", fontSize: 11 }} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#7d8e83", fontSize: 11 }} />
                <Tooltip cursor={{ fill: "#f3f8f4" }} />
                <Bar dataKey="count" name="Records" fill="#258653" radius={[7, 7, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel quick-panel manager-quick-panel">
          <div className="panel-heading manager-quick-heading">
            <div>
              <h3>Quick actions</h3>
              <p>Jump to a frequently used workspace</p>
            </div>
          </div>
          <div className="manager-action-list">
            {actions.map((action) => {
              const Icon = action.icon;
              return (
                <button className="manager-action-button" key={action.id} type="button" onClick={() => onNavigate(action.id)}>
                  <span className="manager-action-icon"><Icon size={18} /></span>
                  <span className="manager-action-copy"><strong>{action.label}</strong><small>{action.detail}</small></span>
                  <ArrowRight size={17} className="manager-action-arrow" />
                </button>
              );
            })}
          </div>
        </section>
      </div>

      <div className="dashboard-bottom-grid manager-lower-grid">
        <section className="panel dashboard-info-panel expiry-panel">
          <div className="panel-heading">
            <div>
              <h3>Expiry watch</h3>
              <p>Based on batch expiry dates and remaining quantities</p>
            </div>
            <button className="text-action" type="button" onClick={() => onNavigate("expiry")}>Open expiry management <ArrowRight size={14} /></button>
          </div>
          {priorityBatches.length > 0 ? (
            <div className="expiry-list">
              {priorityBatches.map((batch) => {
                const isExpired = batch.daysLeft < 0;
                const isToday = batch.daysLeft === 0;
                const label = isExpired
                  ? `Expired ${Math.abs(batch.daysLeft)} day${Math.abs(batch.daysLeft) === 1 ? "" : "s"} ago`
                  : isToday
                    ? "Expires today"
                    : `Expires in ${batch.daysLeft} day${batch.daysLeft === 1 ? "" : "s"}`;
                return (
                  <div className="expiry-row" key={batch.batch_id ?? batch.batch_code}>
                    <span className={`expiry-status-icon ${isExpired || isToday ? "urgent" : "soon"}`}><AlertTriangle size={16} /></span>
                    <span className="expiry-row-main">
                      <strong>{batch.batch_code || `Batch ${batch.batch_id ?? "—"}`}</strong>
                      <small>Product {batch.product_id ?? "not assigned"} · {Number(batch.quantity_remaining || 0).toLocaleString("en-IN")} remaining</small>
                    </span>
                    <span className={`expiry-pill ${isExpired ? "expired" : "upcoming"}`}>{label}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state-inline">
              <CalendarClock size={22} />
              <strong>No urgent expiry records found</strong>
              <span>There are no batches with remaining stock expiring in the past or within the next 7 days.</span>
            </div>
          )}
        </section>

        <section className="panel dashboard-info-panel system-panel">
          <div className="panel-heading">
            <div>
              <h3>Store operations</h3>
              <p>Current workspace totals</p>
            </div>
            <Store size={21} />
          </div>
          <div className="system-overview-item"><span>Registered products</span><strong>{products.length}</strong></div>
          <div className="system-overview-item"><span>Inventory records</span><strong>{inventory.length}</strong></div>
          <div className="system-overview-item"><span>Registered stores</span><strong>{stores.length}</strong></div>
          <div className="system-overview-item"><span>Expired batches with stock</span><strong className={expiredBatches.length ? "value-warning" : ""}>{expiredBatches.length}</strong></div>
          <div className="system-overview-item"><span>Sales data</span><strong className="value-muted">Not connected</strong></div>
        </section>
      </div>

      <section className="panel dashboard-info-panel recent-batches-panel">
        <div className="panel-heading">
          <div>
            <h3>Recent inventory batches</h3>
            <p>Latest batch records returned by the backend</p>
          </div>
          <button className="text-action" type="button" onClick={() => onNavigate("batches")}>View all batches <ArrowRight size={14} /></button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Batch</th><th>Product ID</th><th>Remaining</th><th>Expiry date</th><th>Condition</th></tr>
            </thead>
            <tbody>
              {recentBatches.map((batch) => {
                const daysLeft = getDaysUntilExpiry(batch.expiry_date);
                const condition = daysLeft === null ? "Date unavailable" : daysLeft < 0 ? "Expired" : daysLeft <= 7 ? "Near expiry" : "In date";
                const tone = daysLeft !== null && daysLeft < 0 ? "expired" : daysLeft !== null && daysLeft <= 7 ? "upcoming" : "normal";
                return (
                  <tr key={batch.batch_id ?? batch.batch_code}>
                    <td><strong>{batch.batch_code || batch.batch_id || "—"}</strong></td>
                    <td>{batch.product_id ?? "—"}</td>
                    <td>{batch.quantity_remaining ?? "—"}</td>
                    <td>{formatDate(batch.expiry_date)}</td>
                    <td><span className={`table-status ${tone}`}>{condition}</span></td>
                  </tr>
                );
              })}
              {recentBatches.length === 0 && <tr><td colSpan="5" className="empty-cell">No batch records are available yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="manager-dashboard-footer-grid">
        <div className="manager-note-card">
          <div className="manager-note-icon"><ShoppingBag size={19} /></div>
          <div><strong>Sales overview</strong><p>Sales reporting will appear here after the sales data endpoint is connected.</p></div>
          <span className="coming-soon-tag">Not connected</span>
        </div>
        <div className="manager-note-card">
          <div className="manager-note-icon"><TrendingUp size={19} /></div>
          <div><strong>AI demand forecast</strong><p>Forecast insights will appear here once the forecasting service is integrated.</p></div>
          <span className="coming-soon-tag">Not connected</span>
        </div>
      </section>

      <section className="nearby-stores manager-nearby-panel">
        <NearbyStores />
      </section>
    </div>
  );
}
