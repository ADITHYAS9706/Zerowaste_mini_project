
import { useEffect, useMemo, useState } from "react";
import NearbyStores from "./components/NearbyStores";

import {
  LayoutDashboard,
  Package,
  Warehouse,
  Layers3,
  Store,
  RefreshCw,
  Plus,
  Search,
  AlertCircle,
  X,
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

import {
  getProducts,
  getInventory,
  getBatches,
  getStores,
  createProduct,
  createBatch,
} from "./services/api";

import "./App.css";


const navigation = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "products", label: "Products", icon: Package },
  { id: "inventory", label: "Inventory", icon: Warehouse },
  { id: "batches", label: "Batches", icon: Layers3 },
  { id: "stores", label: "Stores", icon: Store },
];


const emptyData = {
  products: [],
  inventory: [],
  batches: [],
  stores: [],
};


function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [data, setData] = useState(emptyData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");


  // Load data from backend
  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const [products, inventory, batches, stores] =
        await Promise.all([
          getProducts(),
          getInventory(),
          getBatches(),
          getStores(),
        ]);

      setData({
        products: products.data,
        inventory: inventory.data,
        batches: batches.data,
        stores: stores.data,
      });

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to connect to the backend. Check that FastAPI is running."
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadData();
  }, []);


  const pageTitle =
    navigation.find((item) => item.id === activePage)?.label ||
    "Dashboard";


  // Search and filter records
  const filtered = useMemo(() => {
    const key = search.toLowerCase();

    if (activePage === "products") {
      return data.products.filter((p) =>
        `${p.product_id} ${p.product_name} ${p.category}`
          .toLowerCase()
          .includes(key)
      );
    }

    if (activePage === "stores") {
      return data.stores.filter((s) =>
        `${s.store_id} ${s.store_name} ${s.address || ""}`
          .toLowerCase()
          .includes(key)
      );
    }

    if (activePage === "batches") {
      return data.batches.filter((b) =>
        `${b.batch_id} ${b.batch_code} ${b.product_id || ""} ${b.store_id || ""}`
          .toLowerCase()
          .includes(key)
      );
    }

    if (activePage === "inventory") {
      return data.inventory.filter((i) =>
        `${i.store_id} ${i.product_id}`
          .toLowerCase()
          .includes(key)
      );
    }

    return [];

  }, [activePage, search, data]);


  // Create products and batches
  async function handleCreate(event) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    const values = Object.fromEntries(form.entries());

    setSaving(true);
    setNotice("");

    try {

      if (activePage === "products") {
        await createProduct({
          product_name: values.product_name,
          category: values.category,
          unit: values.unit,

          base_daily_demand:
            values.base_daily_demand === ""
              ? null
              : Number(values.base_daily_demand),

          unit_price:
            values.unit_price === ""
              ? 0
              : Number(values.unit_price),
        });
      }


      if (activePage === "batches") {
        await createBatch({
          store_id: values.store_id || null,
          product_id: values.product_id || null,
          batch_code: values.batch_code,
          quantity_received: Number(values.quantity_received),
          quantity_remaining: Number(values.quantity_remaining),
          manufacturing_date: values.manufacturing_date || null,
          expiry_date: values.expiry_date,
        });
      }


      setShowForm(false);

      setNotice(
        activePage === "products"
          ? "Product registered successfully."
          : "Batch registered successfully."
      );

      await loadData();

    } catch (err) {
      setNotice(
        err.response?.data?.detail ||
        "Unable to save the record. Please check the entered values."
      );

    } finally {
      setSaving(false);
    }
  }


  // Change dashboard page
  function changePage(id) {
    setActivePage(id);
    setSearch("");
    setShowForm(false);
    setNotice("");
  }


  // Calculate total available stock
  const totalStock = data.inventory.reduce(
    (sum, item) =>
      sum + Number(item.available_quantity || 0),
    0
  );


  const chartData = [
    { name: "Products", count: data.products.length },
    { name: "Stores", count: data.stores.length },
    { name: "Batches", count: data.batches.length },
  ];


  return (
    <div className="app-shell">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">
            <Boxes size={23} />
          </div>

          <div>
            <h2>ZeroWasteNet</h2>
            <span>Smart Inventory System</span>
          </div>

        </div>


        <div className="nav-heading">
          WORKSPACE
        </div>


        <nav className="navigation">

          {navigation.map((item) => {

            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`nav-item ${
                  activePage === item.id ? "active" : ""
                }`}
                onClick={() => changePage(item.id)}
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </button>
            );

          })}

        </nav>


        <div className="sidebar-footer">
          <div className="status-dot" />
          Inventory management
          <span>v1.0</span>
        </div>

      </aside>



      {/* MAIN CONTENT */}
      <main className="main-area">

        {/* TOP BAR */}
        <header className="topbar">

          <div>
            <div className="breadcrumb">
              Workspace / {pageTitle}
            </div>

            <h1>{pageTitle}</h1>
          </div>


          <div className="top-actions">

            <button
              className="icon-button"
              onClick={loadData}
              title="Refresh data"
            >
              <RefreshCw size={18} />
            </button>


            <div className="profile">

              <div className="avatar">
                ZW
              </div>

              <div>
                <strong>Administrator</strong>
                <span>Project workspace</span>
              </div>

            </div>

          </div>

        </header>



        {/* PAGE CONTENT */}
        <section className="content">

          {error && (
            <div className="alert error">

              <AlertCircle size={18} />

              <span>{error}</span>

              <button onClick={loadData}>
                Retry
              </button>

            </div>
          )}


          {notice && (
            <div className="alert success">

              {notice}

              <button onClick={() => setNotice("")}>
                Dismiss
              </button>

            </div>
          )}



          {loading ? (

            <div className="loading">
              Loading ZeroWasteNet data...
            </div>

          ) : (

            <>

              {/* DASHBOARD PAGE */}
              {activePage === "dashboard" && (

                <>

                  {/* LOCATION-BASED STORE SUGGESTIONS */}
                  <NearbyStores />


                  {/* EXISTING DASHBOARD */}
                  <Dashboard
                    data={data}
                    totalStock={totalStock}
                    chartData={chartData}
                    onNavigate={changePage}
                  />

                </>

              )}



              {/* MANAGEMENT PAGES */}
              {[
                "products",
                "inventory",
                "batches",
                "stores",
              ].includes(activePage) && (

                <section className="panel">

                  <div className="panel-toolbar">

                    <div>
                      <h2>{pageTitle} Management</h2>

                      <p>
                        View and manage records from your database.
                      </p>
                    </div>


                    <div className="toolbar-actions">

                      <div className="search-box">

                        <Search size={17} />

                        <input
                          placeholder="Search records..."
                          value={search}
                          onChange={(e) =>
                            setSearch(e.target.value)
                          }
                        />

                      </div>


                      {/* No manual store registration */}
                      {activePage !== "inventory" &&
                        activePage !== "stores" && (

                        <button
                          className="primary-button"
                          onClick={() => setShowForm(true)}
                        >
                          <Plus size={18} />
                          Add {activePage.slice(0, -1)}
                        </button>

                      )}

                    </div>

                  </div>



                  {activePage === "products" && (
                    <ProductsTable rows={filtered} />
                  )}

                  {activePage === "inventory" && (
                    <InventoryTable rows={filtered} />
                  )}

                  {activePage === "batches" && (
                    <BatchesTable rows={filtered} />
                  )}

                  {activePage === "stores" && (
                    <StoresTable rows={filtered} />
                  )}

                </section>

              )}

            </>

          )}

        </section>

      </main>



      {/* ADD PRODUCT / BATCH MODAL */}
      {showForm && (

        <div
          className="modal-backdrop"
          onClick={() => setShowForm(false)}
        >

          <div
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >

            <div className="modal-header">

              <div>
                <h2>
                  Register {activePage === "products" ? "Product" : "Batch"}
                </h2>

                <p>
                  Enter the information below.
                </p>
              </div>


              <button
                className="icon-button"
                onClick={() => setShowForm(false)}
              >
                <X size={20} />
              </button>

            </div>



            <form onSubmit={handleCreate}>

              {activePage === "products" && (
                <ProductForm />
              )}


              {activePage === "batches" && (
                <BatchForm
                  products={data.products}
                  stores={data.stores}
                />
              )}



              <div className="form-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving ? "Saving..." : "Save record"}
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  );
}



// ========================================
// DASHBOARD COMPONENT
// ========================================

function Dashboard({
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
    },

    {
      title: "Total Stores",
      value: data.stores.length,
      icon: Store,
      color: "blue",
    },

    {
      title: "Inventory Batches",
      value: data.batches.length,
      icon: Layers3,
      color: "orange",
    },

    {
      title: "Available Stock",
      value: totalStock.toLocaleString(),
      icon: Warehouse,
      color: "purple",
    },

  ];


  return (

    <>

      <div className="welcome-row">

        <div>
          <h2>Inventory overview</h2>

          <p>
            Monitor your grocery inventory and manage stock efficiently.
          </p>
        </div>

        <span className="live-label">
          <span />
          Connected data view
        </span>

      </div>



      {/* STATISTICS CARDS */}
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

              <span>Current database records</span>

            </div>

          );

        })}

      </div>



      {/* CHART AND QUICK ACTIONS */}
      <div className="dashboard-grid">


        <div className="panel chart-panel">

          <div className="panel-heading">

            <div>
              <h3>Database summary</h3>

              <p>
                Current record count by category
              </p>
            </div>

            <TrendingUp size={20} />

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
                  fill="#26966a"
                  radius={[6, 6, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </div>

        </div>



        <div className="panel quick-panel">

          <h3>Quick actions</h3>

          <p>
            Go directly to a management section.
          </p>


          {[
            ["products", "Manage products", Package],
            ["inventory", "View inventory", Warehouse],
            ["batches", "Manage batches", Layers3],
            ["stores", "View stores", Store],
          ].map(([id, label, Icon]) => (

            <button
              className="quick-link"
              key={id}
              onClick={() => onNavigate(id)}
            >

              <Icon size={18} />

              <span>{label}</span>

              <span className="quick-arrow">→</span>

            </button>

          ))}

        </div>

      </div>

    </>

  );

}



// ========================================
// COMMON TABLE COMPONENT
// ========================================

function Table({ columns, rows, emptyMessage }) {

  return (

    <div className="table-wrap">

      <table>

        <thead>

          <tr>
            {columns.map((column) => (
              <th key={column.key}>
                {column.label}
              </th>
            ))}
          </tr>

        </thead>


        <tbody>

          {rows.length === 0 ? (

            <tr>
              <td
                colSpan={columns.length}
                className="empty-cell"
              >
                {emptyMessage}
              </td>
            </tr>

          ) : (

            rows.map((row, index) => (

              <tr
                key={
                  row.product_id ||
                  row.store_id ||
                  row.batch_id ||
                  index
                }
              >

                {columns.map((column) => (

                  <td key={column.key}>

                    {column.render
                      ? column.render(row)
                      : (row[column.key] ?? "—")}

                  </td>

                ))}

              </tr>

            ))

          )}

        </tbody>

      </table>

    </div>

  );

}



// ========================================
// PRODUCTS TABLE
// ========================================

function ProductsTable({ rows }) {

  return (

    <Table
      rows={rows}
      emptyMessage="No products found."
      columns={[

        { key: "product_id", label: "Product ID" },

        { key: "product_name", label: "Product name" },

        { key: "category", label: "Category" },

        { key: "unit", label: "Unit" },

        { key: "base_daily_demand", label: "Daily demand" },

        {
          key: "unit_price",
          label: "Unit price",
          render: (r) =>
            `₹${Number(r.unit_price || 0).toFixed(2)}`,
        },

      ]}
    />

  );

}



// ========================================
// INVENTORY TABLE
// ========================================

function InventoryTable({ rows }) {

  return (

    <Table
      rows={rows}
      emptyMessage="No inventory records found."
      columns={[

        { key: "store_id", label: "Store ID" },

        { key: "product_id", label: "Product ID" },

        {
          key: "available_quantity",
          label: "Available quantity",
        },

      ]}
    />

  );

}



// ========================================
// BATCHES TABLE
// ========================================

function BatchesTable({ rows }) {

  return (

    <Table
      rows={rows}
      emptyMessage="No batches found."
      columns={[

        { key: "batch_id", label: "Batch ID" },

        { key: "batch_code", label: "Batch code" },

        { key: "product_id", label: "Product ID" },

        { key: "store_id", label: "Store ID" },

        { key: "quantity_received", label: "Received" },

        { key: "quantity_remaining", label: "Remaining" },

        { key: "expiry_date", label: "Expiry date" },

      ]}
    />

  );

}



// ========================================
// STORES TABLE - VIEW ONLY
// ========================================

function StoresTable({ rows }) {

  return (

    <Table
      rows={rows}
      emptyMessage="No stores found."
      columns={[

        { key: "store_id", label: "Store ID" },

        { key: "store_name", label: "Store name" },

        { key: "address", label: "Address" },

        { key: "phone", label: "Phone" },

      ]}
    />

  );

}



// ========================================
// COMMON FORM FIELD
// ========================================

function Field({
  label,
  name,
  type = "text",
  required = false,
  ...props
}) {

  return (

    <label className="form-field">

      <span>
        {label}
        {required && " *"}
      </span>

      <input
        name={name}
        type={type}
        required={required}
        {...props}
      />

    </label>

  );

}



// ========================================
// PRODUCT FORM
// ========================================

function ProductForm() {

  return (

    <div className="form-grid">

      <Field
        label="Product name"
        name="product_name"
        required
        minLength={2}
        placeholder="e.g. Fresh Apples"
      />

      <Field
        label="Category"
        name="category"
        required
        minLength={2}
        placeholder="e.g. Fruits"
      />

      <Field
        label="Unit"
        name="unit"
        required
        placeholder="e.g. kg, pieces, litre"
      />

      <Field
        label="Base daily demand"
        name="base_daily_demand"
        type="number"
        min="0"
      />

      <Field
        label="Unit price (₹)"
        name="unit_price"
        type="number"
        min="0"
        step="0.01"
      />

    </div>

  );

}



// ========================================
// BATCH FORM
// ========================================

function BatchForm({ products, stores }) {

  return (

    <div className="form-grid">


      <label className="form-field">

        <span>Product</span>

        <select name="product_id" defaultValue="">

          <option value="">
            Select product (optional)
          </option>

          {products.map((p) => (

            <option
              key={p.product_id}
              value={p.product_id}
            >
              {p.product_name} ({p.product_id})
            </option>

          ))}

        </select>

      </label>



      <label className="form-field">

        <span>Store</span>

        <select name="store_id" defaultValue="">

          <option value="">
            Select store (optional)
          </option>

          {stores.map((s) => (

            <option
              key={s.store_id}
              value={s.store_id}
            >
              {s.store_name} ({s.store_id})
            </option>

          ))}

        </select>

      </label>



      <Field
        label="Batch code"
        name="batch_code"
        required
      />

      <Field
        label="Quantity received"
        name="quantity_received"
        type="number"
        required
        min="1"
      />

      <Field
        label="Quantity remaining"
        name="quantity_remaining"
        type="number"
        required
        min="0"
      />

      <Field
        label="Manufacturing date"
        name="manufacturing_date"
        type="date"
      />

      <Field
        label="Expiry date"
        name="expiry_date"
        type="date"
        required
      />

    </div>

  );

}


export default App;
