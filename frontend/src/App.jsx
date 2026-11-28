import { lazy, Suspense, useEffect, useState } from "react";
import { AlertCircle, X } from "lucide-react";

import ManagerLayout from "./pages/layouts/ManagerLayout";
import ManagerDashboard, { StaffDashboard } from "./pages/manager/ManagerDashboard";
import InventoryManagement from "./pages/manager/InventoryManagement";
import ProductManagement from "./pages/manager/ProductManagement";
import BatchManagement from "./pages/manager/BatchManagement";
// Defer secondary Manager modules until the user opens them. This keeps the
// initial dashboard bundle smaller and avoids loading Recharts on first paint.
const SalesManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.SalesManagement })));
const ExpiryManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.ExpiryManagement })));
const ForecastManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.ForecastManagement })));
const RedistributionManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.RedistributionManagement })));
const CommunityManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.CommunityManagement })));
const StaffManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.StaffManagement })));
const SettingsManagement = lazy(() => import("./pages/manager/ManagerModules").then((module) => ({ default: module.SettingsManagement })));
import {
  createBatch,
  createProduct,
  deleteProduct,
  getBatches,
  getInventory,
  getProducts,
  getStores,
  updateProduct,
} from "./services/api";
import "./App.css";

const emptyData = { products: [], inventory: [], batches: [], stores: [] };

function responseRows(result) {
  return Array.isArray(result?.data) ? result.data : [];
}

function BatchModal({ products, stores, onClose, onSave, saving, error }) {
  const [values, setValues] = useState({
    product_id: products[0]?.product_id || "",
    store_id: stores[0]?.store_id || "",
    batch_code: "",
    quantity_received: "",
    quantity_remaining: "",
    manufacturing_date: "",
    expiry_date: "",
  });

  function set(name, value) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onSave({
      ...values,
      quantity_received: Number(values.quantity_received),
      quantity_remaining: Number(values.quantity_remaining),
      store_id: values.store_id || null,
      manufacturing_date: values.manufacturing_date || null,
    });
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="batch-modal-title">
        <div className="modal-header">
          <div><h2 id="batch-modal-title">Register stock batch</h2><p>Record each delivery separately to track its expiry.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={19} /></button>
        </div>
        <form onSubmit={submit}>
          <div className="form-grid">
            <label className="form-field">Product
              <select required value={values.product_id} onChange={(event) => set("product_id", event.target.value)}>
                <option value="">Select product</option>
                {products.map((item) => <option key={item.product_id} value={item.product_id}>{item.product_name}</option>)}
              </select>
            </label>
            <label className="form-field">Store
              <select value={values.store_id} onChange={(event) => set("store_id", event.target.value)}>
                <option value="">Not assigned</option>
                {stores.map((item) => <option key={item.store_id} value={item.store_id}>{item.store_name}</option>)}
              </select>
            </label>
            <label className="form-field">Batch code
              <input required value={values.batch_code} onChange={(event) => set("batch_code", event.target.value)} placeholder="e.g. MILK-LOT-001" />
            </label>
            <label className="form-field">Quantity received
              <input required type="number" min="1" step="1" value={values.quantity_received} onChange={(event) => set("quantity_received", event.target.value)} />
            </label>
            <label className="form-field">Quantity remaining
              <input required type="number" min="0" step="1" value={values.quantity_remaining} onChange={(event) => set("quantity_remaining", event.target.value)} />
            </label>
            <label className="form-field">Manufacturing date
              <input type="date" value={values.manufacturing_date} onChange={(event) => set("manufacturing_date", event.target.value)} />
            </label>
            <label className="form-field">Expiry date
              <input required type="date" value={values.expiry_date} onChange={(event) => set("expiry_date", event.target.value)} />
            </label>
          </div>
          {error && <div className="alert error" role="alert">{error}</div>}
          <div className="form-actions">
            <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>Cancel</button>
            <button type="submit" className="primary-button" disabled={saving || products.length === 0}>{saving ? "Saving…" : "Save batch"}</button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [data, setData] = useState(emptyData);
  const [loading, setLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [collectionLoading, setCollectionLoading] = useState({ products: true, inventory: true, batches: true, stores: true });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [showBatchForm, setShowBatchForm] = useState(false);
  const [savingBatch, setSavingBatch] = useState(false);
  const [batchError, setBatchError] = useState("");

  async function loadData() {
    if (!hasLoaded) setLoading(true);
    setError("");

    // Load each collection in parallel and publish successful responses immediately.
    // A slow or failed endpoint no longer blocks the entire Manager workspace.
    const requests = [
      ["products", getProducts],
      ["inventory", getInventory],
      ["batches", getBatches],
      ["stores", getStores],
    ];
    const results = await Promise.all(requests.map(async ([key, request]) => {
      try {
        const response = await request();
        setData((current) => ({ ...current, [key]: responseRows(response) }));
        return { key, ok: true };
      } catch (requestError) {
        return { key, ok: false, error: requestError };
      } finally {
        setCollectionLoading((current) => ({ ...current, [key]: false }));
      }
    }));

    const failed = results.filter((result) => !result.ok);
    if (failed.length === requests.length) {
      setError("Database records are unavailable. Check the FastAPI and Supabase connection, then retry.");
    } else if (failed.length > 0) {
      setError(`Some records could not be refreshed (${failed.map((result) => result.key).join(", ")}). Other Manager pages remain available.`);
    }
    setHasLoaded(true);
    setLoading(false);
  }

  useEffect(() => { loadData(); }, []);

  function changePage(page) {
    setActivePage(page);
    setNotice("");
    setShowBatchForm(false);
    setBatchError("");
  }

  async function saveBatch(payload) {
    if (payload.quantity_remaining > payload.quantity_received) {
      setBatchError("Remaining quantity cannot exceed the quantity received.");
      return;
    }
    if (payload.manufacturing_date && payload.expiry_date && payload.manufacturing_date > payload.expiry_date) {
      setBatchError("Expiry date must be on or after the manufacturing date.");
      return;
    }
    if (data.batches.some((batch) => String(batch.batch_code || "").trim().toLowerCase() === payload.batch_code.trim().toLowerCase())) {
      setBatchError("A batch with this code already exists. Use a unique batch code.");
      return;
    }
    setSavingBatch(true);
    setBatchError("");
    try {
      await createBatch(payload);
      setShowBatchForm(false);
      setNotice("Batch registered successfully.");
      await loadData();
    } catch (requestError) {
      setBatchError(requestError?.response?.data?.detail || "Unable to save this batch.");
    } finally {
      setSavingBatch(false);
    }
  }

  const totalStock = data.inventory.reduce((sum, item) => sum + Number(item.available_quantity || 0), 0);
  return (
    <ManagerLayout activePage={activePage} onNavigate={changePage} onRefresh={loadData}>
      {error && <div className="alert error" role="alert"><AlertCircle size={18} /><span>{error}</span><button type="button" onClick={loadData}>Retry</button></div>}
      {notice && <div className="alert success" role="status"><span>{notice}</span><button type="button" onClick={() => setNotice("")}>Dismiss</button></div>}

      {loading && !hasLoaded && <div className="app-data-loading" role="status"><span className="loading-spinner" /> Loading live store records. You can still navigate the Manager workspace.</div>}

      {activePage === "dashboard" && <ManagerDashboard data={data} totalStock={totalStock} onNavigate={changePage} onRefresh={loadData} loading={Object.values(collectionLoading).some(Boolean)} />}
      {activePage === "inventory" && <InventoryManagement data={data} dataLoading={collectionLoading.inventory || collectionLoading.products || collectionLoading.stores || collectionLoading.batches} onRegisterBatch={() => setShowBatchForm(true)} onViewBatches={() => changePage("batches")} />}
      {activePage === "products" && <ProductManagement products={data.products} dataLoading={collectionLoading.products} onCreate={async (payload) => { await createProduct(payload); await loadData(); }} onUpdate={async (id, payload) => { await updateProduct(id, payload); await loadData(); }} onDelete={async (id) => { await deleteProduct(id); await loadData(); }} />}
      {activePage === "batches" && <BatchManagement batches={data.batches} products={data.products} stores={data.stores} dataLoading={collectionLoading.batches || collectionLoading.products || collectionLoading.stores} onAddBatch={() => setShowBatchForm(true)} />}
      <Suspense fallback={<div className="app-module-loading" role="status"><span className="loading-spinner" /> Loading this Manager workspace…</div>}>
        {activePage === "sales" && <SalesManagement products={data.products} stores={data.stores} onRefresh={loadData} />}
        {activePage === "expiry" && <ExpiryManagement />}
        {activePage === "forecast" && <ForecastManagement stores={data.stores} />}
        {activePage === "redistribution" && <RedistributionManagement />}
        {activePage === "community" && <CommunityManagement products={data.products} stores={data.stores} batches={data.batches} />}
        {activePage === "staff" && <StaffManagement stores={data.stores} />}
        {activePage === "settings" && <SettingsManagement stores={data.stores} storesLoading={collectionLoading.stores} onRefresh={loadData} />}
      </Suspense>
      {activePage === "staff-dashboard" && <StaffDashboard data={data} onNavigate={changePage} loading={Object.values(collectionLoading).some(Boolean)} />}

      {showBatchForm && <BatchModal products={data.products} stores={data.stores} onClose={() => setShowBatchForm(false)} onSave={saveBatch} saving={savingBatch} error={batchError} />}
    </ManagerLayout>
  );
}
