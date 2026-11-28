
import {
  Package,
  Store,
  Layers3,
  Warehouse,
  TrendingUp,
  Boxes,
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

export default function ManagerDashboard({
  data,
  totalStock,
  chartData,
  onNavigate,
}) {
  const cards = [
    {
      title: "Total Products",
      value: data.products.length,
      icon: Package,
      color: "green",
      note: "Registered products",
    },
    {
      title: "Total Stores",
      value: data.stores.length,
      icon: Store,
      color: "blue",
      note: "Registered locations",
    },
    {
      title: "Inventory Batches",
      value: data.batches.length,
      icon: Layers3,
      color: "orange",
      note: "Recorded batches",
    },
    {
      title: "Available Stock",
      value: Number(totalStock).toLocaleString("en-IN"),
      icon: Warehouse,
      color: "purple",
      note: "Units currently available",
    },
  ];

  const actions = [
    { id: "products", label: "Add or view products", icon: Package },
    { id: "inventory", label: "Check inventory", icon: Warehouse },
    { id: "batches", label: "Manage batches", icon: Layers3 },
    { id: "stores", label: "View registered stores", icon: Store },
  ];

  return (
    <div className="manager-dashboard">
      <NearbyStores />

      <div className="welcome-row">
        <div>
          <span className="dashboard-eyebrow">MANAGER WORKSPACE</span>
          <h2>Good to see you again!</h2>
          <p>
            Here's an overview of your grocery inventory operations.
          </p>
        </div>

        <span className="live-label">
          <span />
          Dashboard overview
        </span>
      </div>

      <div className="stats-grid">
        {cards.map((card) => {
          const Icon = card.icon;

          return (
            <div className="stat-card" key={card.title}>
              <div className={`stat-icon ${card.color}`}>
                <Icon size={22} />
              </div>

              <p>{card.title}</p>
              <h2>{card.value}</h2>
              <span>{card.note}</span>
            </div>
          );
        })}
      </div>

      <div className="dashboard-grid">
        <div className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h3>Inventory overview</h3>
              <p>Current database records by category</p>
            </div>

            <TrendingUp size={21} />
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />

                <Bar
                  dataKey="count"
                  fill="#18864f"
                  radius={[7, 7, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel quick-panel">
          <h3>Quick actions</h3>
          <p>Jump directly to an inventory section.</p>

          {actions.map((action) => {
            const Icon = action.icon;

            return (
              <button
                className="quick-link"
                key={action.id}
                onClick={() => onNavigate(action.id)}
              >
                <Icon size={19} />
                <span>{action.label}</span>
                <span className="quick-arrow">→</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="dashboard-bottom-grid">
        <div className="panel dashboard-info-panel">
          <div className="panel-heading">
            <div>
              <h3>Recent inventory batches</h3>
              <p>Latest batch records in your database</p>
            </div>

            <button
              className="text-action"
              onClick={() => onNavigate("batches")}
            >
              View all →
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Batch ID</th>
                  <th>Batch Code</th>
                  <th>Product</th>
                  <th>Remaining</th>
                </tr>
              </thead>

              <tbody>
                {data.batches.slice(0, 5).map((batch) => (
                  <tr key={batch.batch_id}>
                    <td>{batch.batch_id}</td>
                    <td>{batch.batch_code || "—"}</td>
                    <td>{batch.product_id || "—"}</td>
                    <td>{batch.quantity_remaining ?? "—"}</td>
                  </tr>
                ))}

                {data.batches.length === 0 && (
                  <tr>
                    <td colSpan="4" className="empty-cell">
                      No batch records available yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel dashboard-info-panel">
          <div className="panel-heading">
            <div>
              <h3>System overview</h3>
              <p>Current workspace information</p>
            </div>

            <Boxes size={21} />
          </div>

          <div className="system-overview-item">
            <span>Products registered</span>
            <strong>{data.products.length}</strong>
          </div>

          <div className="system-overview-item">
            <span>Inventory batches</span>
            <strong>{data.batches.length}</strong>
          </div>

          <div className="system-overview-item">
            <span>Registered stores</span>
            <strong>{data.stores.length}</strong>
          </div>

          <div className="system-overview-item">
            <span>Available stock</span>
            <strong>
              {Number(totalStock).toLocaleString("en-IN")}
            </strong>
          </div>
        </div>
      </div>
    </div>
  );
}
