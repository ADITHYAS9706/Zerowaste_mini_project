import { useEffect, useMemo, useState } from "react";
import { AlertCircle, Plus, Search, X } from "lucide-react";

import ManagerLayout from "./pages/layouts/ManagerLayout";
import ManagerDashboard from "./pages/manager/ManagerDashboard";
import InventoryManagement from "./pages/manager/InventoryManagement";
import ProductManagement from "./pages/manager/ProductManagement";
import BatchManagement from "./pages/manager/BatchManagement";
import {
  getProducts,
  getInventory,
  getBatches,
  getStores,
  createProduct,
  updateProduct,
  deleteProduct,
  createBatch,
} from "./services/api";

import "./App.css";

const emptyData = {
  products: [],
  inventory: [],
  batches: [],
  stores: [],
};

const pageLabels = {
  dashboard: "Dashboard",
  inventory: "Inventory",
  products: "Products",
  batches: "Batches",
  sales: "Sales",
  expiry: "Expiry Management",
  forecast: "AI Forecast",
  redistribution: "Redistribution",
  community: "Store Community",
  staff: "Staff Management",
  settings: "Settings",
  stores: "Stores",
  "staff-dashboard": "Staff Dashboard",
};

function toRows(response) {
  return Array.isArray(response?.data) ? response.data : [];
}

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [data, setData] = useState(emptyData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const [products, inventory, batches, stores] = await Promise.all([
        getProducts(),
        getInventory(),
        getBatches(),
        getStores(),
      ]);

      setData({
        products: toRows(products),
        inventory: toRows(inventory),
        batches: toRows(batches),
        stores: toRows(stores),
      });
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Unable to connect to the backend. Check that FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const pageTitle = pageLabels[activePage] || "Manager Workspace";

  const filtered = useMemo(() => {
    const key = search.trim().toLowerCase();
    if (!key) {
      if (activePage === "products") return data.products;
      if (activePage === "stores") return data.stores;
      if (activePage === "batches") return data.batches;
      if (activePage === "inventory") return data.inventory;
      return [];
    }

    if (activePage === "products") {
      return data.products.filter((p) =>
        `${p.product_id ?? ""} ${p.product_name ?? ""} ${p.category ?? ""}`
          .toLowerCase()
          .includes(key)
      );
    }

    if (activePage === "stores") {
      return data.stores.filter((s) =>
        `${s.store_id ?? ""} ${s.store_name ?? ""} ${s.address ?? ""}`
          .toLowerCase()
          .includes(key)
      );
    }

    if (activePage === "batches") {
      return data.batches.filter((b) =>
        `${b.batch_id ?? ""} ${b.batch_code ?? ""} ${b.product_id ?? ""} ${b.store_id ?? ""}`
          .toLowerCase()
          .includes(key)
      );
    }

    if (activePage === "inventory") {
      return data.inventory.filter((item) =>
        `${item.store_id ?? ""} ${item.product_id ?? ""}`
          .toLowerCase()
          .includes(key)
      );
    }

    return [];
  }, [activePage, search, data]);

  async function handleCreate(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const values = Object.fromEntries(form.entries());

    if (activePage === "batches") {
      const batchCode = String(values.batch_code || "").trim().toLowerCase();
      const duplicateBatch = data.batches.some(
        (batch) => String(batch.batch_code || "").trim().toLowerCase() === batchCode
      );
      const received = Number(values.quantity_received);
      const remaining = Number(values.quantity_remaining);

      if (!values.product_id) {
        setNotice("Select a product before registering a batch.");
        return;
      }
      if (duplicateBatch) {
        setNotice("A batch with this batch code already exists. Enter a unique batch code.");
        return;
      }
      if (remaining > received) {
        setNotice("Quantity remaining cannot be greater than quantity received.");
        return;
      }
      if (
        values.manufacturing_date &&
        values.expiry_date &&
        values.manufacturing_date > values.expiry_date
      ) {
        setNotice("Expiry date must be on or after the manufacturing date.");
        return;
      }
    }

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
          unit_price: values.unit_price === "" ? 0 : Number(values.unit_price),
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
        err?.response?.data?.detail ||
          "Unable to save the record. Please check the entered values."
      );
    } finally {
      setSaving(false);
    }
  }

  function changePage(id) {
    setActivePage(id);
    setSearch("");
    setShowForm(false);
    setNotice("");
  }

  const totalStock = data.inventory.reduce(
    (sum, item) => sum + Number(item.available_quantity || 0),
    0
  );

  const chartData = [
    { name: "Products", count: data.products.length },
    { name: "Inventory rows", count: data.inventory.length },
    { name: "Batches", count: data.batches.length },
    { name: "Stores", count: data.stores.length },
  ];

  const managementPage = ["products", "batches", "stores"].includes(activePage);
  const moduleComingSoon = !managementPage &&
    !["dashboard", "staff-dashboard", "inventory"].includes(activePage);

  return (
    <ManagerLayout
      activePage={activePage}
      onNavigate={changePage}
      onRefresh={loadData}
    >
      {error && (
        <div className="alert error" role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>
          <button type="button" onClick={loadData}>Retry</button>
        </div>
      )}

      {notice && (
        <div className="alert success" role="status">
          <span>{notice}</span>
          <button type="button" onClick={() => setNotice("")}>Dismiss</button>
        </div>
      )}

      {loading ? (
        <div className="loading manager-loading">
          <span className="loading-spinner" />
          Loading ZeroWasteNet data...
        </div>
      ) : (
        <>
          {activePage === "dashboard" && (
            <ManagerDashboard
              data={data}
              totalStock={totalStock}
              chartData={chartData}
              onNavigate={changePage}
              onRefresh={loadData}
            />
          )}

          {activePage === "inventory" && (
            <InventoryManagement
              data={data}
              onRegisterBatch={() => {
                setActivePage("batches");
                setSearch("");
                setNotice("");
                setShowForm(true);
              }}
              onViewBatches={() => changePage("batches")}
            />
          )}

          {activePage === "products" && (
            <ProductManagement
              products={data.products}
              onCreate={async (payload) => {
                await createProduct(payload);
                await loadData();
              }}
              onUpdate={async (productId, payload) => {
                await updateProduct(productId, payload);
                await loadData();
              }}
              onDelete={async (productId) => {
                await deleteProduct(productId);
                await loadData();
              }}
            />
          )}

          {activePage === "batches" && (
            <BatchManagement
              batches={data.batches}
              products={data.products}
              stores={data.stores}
              onAddBatch={() => setShowForm(true)}
            />
          )}

          {activePage === "staff-dashboard" && (
            <section className="module-placeholder">
              <div className="placeholder-icon">SD</div>
              <span className="dashboard-eyebrow">STAFF WORKSPACE</span>
              <h2>Staff Dashboard</h2>
              <p>
                This shortcut is ready. The dedicated staff layout and staff
                tools will be added in the next build step.
              </p>
              <button className="primary-button" onClick={() => changePage("dashboard")}>
                Return to Manager Dashboard
              </button>
            </section>
          )}

          {managementPage && activePage !== "products" && activePage !== "batches" && (
            <section className="panel manager-records-panel">
              <div className="panel-toolbar">
                <div>
                  <span className="dashboard-eyebrow">MANAGER WORKSPACE</span>
                  <h2>{pageTitle} Management</h2>
                  <p>View and manage records currently available in your database.</p>
                </div>

                <div className="toolbar-actions">
                  <label className="search-box">
                    <Search size={17} />
                    <input
                      type="search"
                      placeholder={`Search ${pageTitle.toLowerCase()}...`}
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />
                  </label>

                  {activePage !== "inventory" && activePage !== "stores" && (
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => setShowForm(true)}
                    >
                      <Plus size={18} />
                      Add {activePage === "products" ? "product" : "batch"}
                    </button>
                  )}
                </div>
              </div>

              {activePage === "products" && <ProductsTable rows={filtered} />}
              {activePage === "inventory" && <InventoryTable rows={filtered} />}
              {activePage === "batches" && <BatchesTable rows={filtered} />}
              {activePage === "stores" && <StoresTable rows={filtered} />}
            </section>
          )}

          {moduleComingSoon && (
            <section className="module-placeholder">
              <div className="placeholder-icon">ZW</div>
              <span className="dashboard-eyebrow">MANAGER WORKSPACE</span>
              <h2>{pageTitle}</h2>
              <p>
                This section is present in the Manager navigation. Its working
                screens and backend integration will be built as a separate step.
              </p>
              <button className="secondary-button" onClick={() => changePage("dashboard")}>
                Back to Dashboard
              </button>
            </section>
          )}
        </>
      )}

      {showForm && (
        <div className="modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Register {activePage === "products" ? "Product" : "Batch"}</h2>
                <p>Enter the information below.</p>
              </div>
              <button
                type="button"
                className="icon-button"
                aria-label="Close form"
                onClick={() => setShowForm(false)}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreate}>
              {activePage === "products" && <ProductForm />}
              {activePage === "batches" && (
                <BatchForm products={data.products} stores={data.stores} />
              )}

              <div className="form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? "Saving..." : "Save record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </ManagerLayout>
  );
}

function Table({ rows = [], columns = [], emptyMessage }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.product_id ?? row.batch_id ?? row.store_id ?? `${index}`}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(row)
                    : row[column.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length || 1} className="empty-cell">
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

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

        <span>Product *</span>

        <select name="product_id" defaultValue="" required>

          <option value="">
            Select a registered product
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
