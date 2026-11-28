import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowLeftRight,
  ArrowUpRight,
  BrainCircuit,
  CalendarClock,
  CheckCircle2,
  CircleDollarSign,
  ClipboardList,
  Package,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShoppingCart,
  Store,
  Users,
  XCircle,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  createSale,
  createStaff,
  createTransferRequest,
  decideCommunityRequest,
  getCommunityOffers,
  getCommunityRequests,
  getExpiry,
  getForecast,
  getRedistributionRecommendations,
  getSales,
  getStaff,
  getTransferRequests,
  publishCommunityOffer,
  requestCommunityOffer,
  updateStaffStatus,
  updateStore,
} from "../../services/api";
import "./ManagerModules.css";

const currency = (value) => `₹${(Number(value) || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
const number = (value) => (Number(value) || 0).toLocaleString("en-IN");
const dateLabel = (value) => {
  if (!value) return "—";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
};
const errorText = (error) => error?.response?.data?.detail || error?.message || "The request could not be completed.";

function useMessage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  function clear() { setMessage(""); setError(""); }
  return { message, error, setMessage, setError, clear };
}

function PageHeading({ eyebrow, title, description, action, icon: Icon = Package }) {
  return (
    <header className="mm-heading">
      <div className="mm-heading-icon"><Icon size={22} /></div>
      <div className="mm-heading-copy">
        <span className="mm-eyebrow">{eyebrow || "MANAGER WORKSPACE"}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {action && <div className="mm-heading-action">{action}</div>}
    </header>
  );
}

function StatCard({ label, value, note, icon: Icon = Package, tone = "green" }) {
  return (
    <article className="mm-stat-card">
      <span className={`mm-stat-icon ${tone}`}><Icon size={19} /></span>
      <div><small>{label}</small><strong>{value}</strong><span>{note}</span></div>
    </article>
  );
}

function Notice({ message, error, onDismiss }) {
  if (!message && !error) return null;
  return <div className={`mm-notice ${error ? "is-error" : "is-success"}`} role={error ? "alert" : "status"}>
    <span>{error || message}</span><button type="button" onClick={onDismiss} aria-label="Dismiss">×</button>
  </div>;
}

function LoadingLine({ text = "Loading records…" }) {
  return <div className="mm-loading"><span className="mm-spinner" />{text}</div>;
}

function EmptyState({ title = "No records found", detail = "Records will appear here when data is available." }) {
  return <div className="mm-empty"><ClipboardList size={25} /><strong>{title}</strong><span>{detail}</span></div>;
}

function DataTable({ columns, rows, emptyTitle, emptyDetail }) {
  if (!rows.length) return <EmptyState title={emptyTitle} detail={emptyDetail} />;
  return <div className="mm-table-wrap"><table className="mm-table">
    <thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
    <tbody>{rows.map((row, index) => <tr key={row.id ?? row.sale_id ?? row.batch_id ?? row.offer_id ?? row.request_id ?? row.transfer_id ?? row.user_id ?? `${index}`}>
      {columns.map((column) => <td key={column.key} data-label={column.label}>{column.render ? column.render(row) : (row[column.key] ?? "—")}</td>)}
    </tr>)}</tbody>
  </table></div>;
}

function StatusTag({ status, children }) {
  const value = String(status || "unknown").toLowerCase().replaceAll(" ", "-");
  return <span className={`mm-status ${value}`}>{children || status || "Unknown"}</span>;
}

// ------------------------------ SALES ------------------------------
export function SalesManagement({ products = [], stores = [], onRefresh = () => {} }) {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [values, setValues] = useState({ store_id: stores[0]?.store_id || "", product_id: products[0]?.product_id || "", quantity_sold: "1", selling_price: "" });
  const notice = useMessage();

  async function load() {
    setLoading(true); notice.clear();
    try { const response = await getSales(); setSales(Array.isArray(response.data) ? response.data : []); }
    catch (error) { notice.setError(errorText(error)); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (!values.store_id && stores[0]) setValues((current) => ({ ...current, store_id: stores[0].store_id }));
    if (!values.product_id && products[0]) setValues((current) => ({ ...current, product_id: products[0].product_id }));
  }, [stores, products]);

  const selectedProduct = products.find((product) => String(product.product_id) === String(values.product_id));
  const filteredSales = useMemo(() => {
    const query = search.trim().toLowerCase();
    return sales.filter((sale) => !query || [sale.sale_id, sale.product_name, sale.product_id, sale.store_name, sale.store_id].some((value) => String(value ?? "").toLowerCase().includes(query)));
  }, [sales, search]);
  const revenue = sales.reduce((sum, sale) => sum + Number(sale.total_amount ?? Number(sale.quantity_sold || 0) * Number(sale.selling_price || 0)), 0);
  const units = sales.reduce((sum, sale) => sum + Number(sale.quantity_sold || 0), 0);

  async function submit(event) {
    event.preventDefault(); notice.clear(); setSaving(true);
    try {
      await createSale({ ...values, quantity_sold: Number(values.quantity_sold), selling_price: values.selling_price === "" ? null : Number(values.selling_price) });
      setShowForm(false); setValues((current) => ({ ...current, quantity_sold: "1", selling_price: "" }));
      await load(); await onRefresh();
      notice.setMessage("Sale recorded. Eligible stock was deducted using FEFO (earliest expiry first).");
    } catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }

  return <div className="mm-page">
    <PageHeading title="Sales management" description="Record store sales, review transaction history and deduct stock from the earliest-expiring eligible batches." icon={ShoppingCart} action={<div className="mm-heading-actions"><button className="mm-button light" type="button" onClick={load} disabled={loading}><RefreshCw size={15} /> Refresh sales</button><button className="mm-button primary" onClick={() => setShowForm((open) => !open)} type="button"><Plus size={16} /> Record sale</button></div>} />
    <Notice {...notice} onDismiss={notice.clear} />
    <section className="mm-stat-grid">
      <StatCard label="Sales transactions" value={loading ? "—" : number(sales.length)} note="Transactions returned by the API" icon={ShoppingCart} />
      <StatCard label="Units sold" value={loading ? "—" : number(units)} note="Across the loaded sales history" icon={Package} tone="blue" />
      <StatCard label="Gross sales in loaded history" value={loading ? "—" : currency(revenue)} note="Based on up to 250 returned transactions" icon={CircleDollarSign} tone="purple" />
      <StatCard label="Stores represented" value={loading ? "—" : number(new Set(sales.map((sale) => sale.store_id)).size)} note="Stores with recorded sales" icon={Store} tone="orange" />
    </section>
    {showForm && <section className="mm-panel mm-form-panel">
      <div className="mm-panel-heading"><div><h3>Record a sale</h3><p>Stock is deducted in the backend after the transaction is validated.</p></div><button className="mm-close" onClick={() => setShowForm(false)} type="button">×</button></div>
      <form className="mm-form-grid" onSubmit={submit}>
        <label>Store<select required value={values.store_id} onChange={(event) => setValues((v) => ({ ...v, store_id: event.target.value }))}><option value="">Select store</option>{stores.map((store) => <option key={store.store_id} value={store.store_id}>{store.store_name} ({store.store_id})</option>)}</select></label>
        <label>Product<select required value={values.product_id} onChange={(event) => { const product = products.find((p) => String(p.product_id) === event.target.value); setValues((v) => ({ ...v, product_id: event.target.value, selling_price: product?.unit_price ?? "" })); }}><option value="">Select product</option>{products.map((product) => <option key={product.product_id} value={product.product_id}>{product.product_name}</option>)}</select></label>
        <label>Quantity sold<input required type="number" min="1" step="1" value={values.quantity_sold} onChange={(event) => setValues((v) => ({ ...v, quantity_sold: event.target.value }))} /></label>
        <label>Selling price per unit (₹)<input type="number" min="0" step="0.01" value={values.selling_price === "" ? (selectedProduct?.unit_price ?? "") : values.selling_price} onChange={(event) => setValues((v) => ({ ...v, selling_price: event.target.value }))} /></label>
        <div className="mm-form-note">Available unexpired stock is checked by the server. If the quantity is insufficient, the sale is rejected and inventory is unchanged.</div>
        <div className="mm-form-actions"><button className="mm-button light" type="button" onClick={() => setShowForm(false)}>Cancel</button><button className="mm-button primary" type="submit" disabled={saving || !products.length || !stores.length}>{saving ? "Saving…" : "Save sale"}</button></div>
      </form>
    </section>}
    <section className="mm-panel">
      <div className="mm-panel-heading"><div><h3>Sales history</h3><p>Latest transactions returned by the API (maximum 250).</p></div><label className="mm-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search product, store or ID" /></label></div>
      {loading ? <LoadingLine text="Loading sales history…" /> : <DataTable rows={filteredSales} emptyTitle="No sales records" emptyDetail="Record a sale to begin building transaction history." columns={[
        { key: "sale_id", label: "Sale ID" }, { key: "sale_date", label: "Date", render: (row) => dateLabel(row.sale_date) },
        { key: "product_name", label: "Product", render: (row) => <strong>{row.product_name || row.product_id}</strong> },
        { key: "store_name", label: "Store", render: (row) => row.store_name || row.store_id },
        { key: "quantity_sold", label: "Quantity" }, { key: "selling_price", label: "Unit price", render: (row) => currency(row.selling_price) },
        { key: "total_amount", label: "Total", render: (row) => <strong>{currency(row.total_amount)}</strong> },
      ]} />}
    </section>
  </div>;
}

// ------------------------------ EXPIRY ------------------------------
export function ExpiryManagement() {
  const [rows, setRows] = useState([]); const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); const [search, setSearch] = useState(""); const notice = useMessage();
  async function load() { setLoading(true); notice.clear(); try { const response = await getExpiry(); setRows(Array.isArray(response.data) ? response.data : []); } catch (error) { notice.setError(errorText(error)); } finally { setLoading(false); } }
  useEffect(() => { load(); }, []);
  const expired = rows.filter((row) => row.expiry_status === "expired");
  const near = rows.filter((row) => row.expiry_status === "near");
  const safe = rows.filter((row) => row.expiry_status === "safe");
  const visible = rows.filter((row) => {
    const matchesFilter = filter === "all" || row.expiry_status === filter;
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || [row.batch_code, row.product_name, row.store_name, row.product_id, row.store_id].some((value) => String(value ?? "").toLowerCase().includes(query));
    return matchesFilter && matchesSearch;
  });
  return <div className="mm-page">
    <PageHeading title="Expiry management" description="Review remaining quantities by expiry date and prioritise stock that needs immediate action." icon={CalendarClock} action={<button className="mm-button light" type="button" onClick={load}><RefreshCw size={15} /> Refresh</button>} />
    <Notice {...notice} onDismiss={notice.clear} />
    <section className="mm-stat-grid"><StatCard label="Expired stock lots" value={loading ? "—" : number(expired.length)} note="Positive quantity past expiry" icon={XCircle} tone="red" /><StatCard label="Near expiry" value={loading ? "—" : number(near.length)} note="Expires within the next 7 days" icon={AlertTriangle} tone="orange" /><StatCard label="Safe stock lots" value={loading ? "—" : number(safe.length)} note="More than 7 days remaining" icon={CheckCircle2} tone="green" /><StatCard label="Units needing attention" value={loading ? "—" : number([...expired, ...near].reduce((sum, row) => sum + Number(row.quantity_remaining || 0), 0))} note="Expired plus near-expiry units" icon={Package} tone="purple" /></section>
    <section className="mm-panel">
      <div className="mm-panel-heading"><div><h3>Expiry register</h3><p>Current date is evaluated by the database server.</p></div><label className="mm-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search product, batch or store" /></label></div>
      <div className="mm-filter-row">{[{ id: "all", label: "All lots", count: rows.length }, { id: "expired", label: "Expired", count: expired.length }, { id: "near", label: "Near expiry", count: near.length }, { id: "safe", label: "Safe", count: safe.length }].map((item) => <button type="button" key={item.id} className={`mm-filter ${filter === item.id ? "active" : ""}`} onClick={() => setFilter(item.id)}>{item.label}<span>{item.count}</span></button>)}</div>
      {loading ? <LoadingLine /> : <DataTable rows={visible} emptyTitle="No batches in this category" columns={[
        { key: "batch_code", label: "Batch", render: (row) => <strong>{row.batch_code || row.batch_id}</strong> },
        { key: "product_name", label: "Product" }, { key: "store_name", label: "Store" },
        { key: "quantity_remaining", label: "Remaining" }, { key: "expiry_date", label: "Expiry date", render: (row) => dateLabel(row.expiry_date) },
        { key: "days_to_expiry", label: "Days", render: (row) => <strong className={row.days_to_expiry < 0 ? "mm-danger-text" : row.days_to_expiry <= 7 ? "mm-warning-text" : ""}>{row.days_to_expiry < 0 ? `${Math.abs(row.days_to_expiry)} overdue` : row.days_to_expiry === 0 ? "Today" : `${row.days_to_expiry} days`}</strong> },
        { key: "expiry_status", label: "Status", render: (row) => <StatusTag status={row.expiry_status}>{row.expiry_status === "near" ? "Near expiry" : row.expiry_status}</StatusTag> },
      ]} />}
    </section>
  </div>;
}

// ------------------------------ FORECAST ------------------------------
export function ForecastManagement({ stores = [] }) {
  const [forecast, setForecast] = useState({ rows: [], is_stale: true, generated_through: null, source: "" });
  const [loading, setLoading] = useState(true); const [storeId, setStoreId] = useState(""); const notice = useMessage();
  async function load(nextStore = storeId) { setLoading(true); notice.clear(); try { const response = await getForecast(nextStore || undefined); setForecast(response.data || { rows: [] }); } catch (error) { notice.setError(errorText(error)); setForecast({ rows: [], is_stale: true }); } finally { setLoading(false); } }
  useEffect(() => { load(""); }, []);
  const rows = Array.isArray(forecast.rows) ? forecast.rows : [];
  const daily = useMemo(() => {
    const map = new Map(); rows.forEach((row) => map.set(row.forecast_date, (map.get(row.forecast_date) || 0) + Number(row.predicted_units || 0)));
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([date, units]) => ({ date: date.slice(5), units }));
  }, [rows]);
  const total = rows.reduce((sum, row) => sum + Number(row.predicted_units || 0), 0);
  const productsCount = new Set(rows.map((row) => row.product_id)).size;
  return <div className="mm-page">
    <PageHeading title="AI demand forecast" description="Review the saved 7-day demand predictions generated by the backend forecasting pipeline." icon={BrainCircuit} action={<button className="mm-button light" type="button" onClick={() => load()}><RefreshCw size={15} /> Refresh forecast</button>} />
    <Notice {...notice} onDismiss={notice.clear} />
    <section className="mm-panel mm-filter-panel"><label className="mm-select-field">Store view<select value={storeId} onChange={(event) => { setStoreId(event.target.value); load(event.target.value); }}><option value="">All stores</option>{stores.map((store) => <option value={store.store_id} key={store.store_id}>{store.store_name}</option>)}</select></label><span className="mm-source-label">Source: {forecast.source || "Backend forecast output"}</span><span className="mm-source-label">Last forecast date: {dateLabel(forecast.generated_through)}</span></section>
    {forecast.is_stale && <div className="mm-inline-warning"><AlertTriangle size={18} /><div><strong>The saved forecast is older than today.</strong><span>Refresh reloads the saved file. To generate current predictions, run your existing backend 7-day forecast pipeline first.</span></div></div>}
    <section className="mm-stat-grid"><StatCard label="Predicted units" value={loading ? "—" : number(total)} note="Sum of rows in the selected view" icon={BrainCircuit} /><StatCard label="Forecast records" value={loading ? "—" : number(rows.length)} note="Store and product prediction rows" icon={ClipboardList} tone="blue" /><StatCard label="Products forecast" value={loading ? "—" : number(productsCount)} note="Distinct products represented" icon={Package} tone="purple" /><StatCard label="Forecast horizon" value={loading ? "—" : number(daily.length)} note="Distinct forecast dates in file" icon={CalendarClock} tone="orange" /></section>
    <section className="mm-panel"><div className="mm-panel-heading"><div><h3>Daily predicted demand</h3><p>Predicted units aggregated across the selected stores and products.</p></div></div>
      {loading ? <LoadingLine /> : daily.length ? <div className="mm-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={daily} margin={{ top: 12, right: 14, left: 0, bottom: 4 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="date" /><YAxis allowDecimals={false} /><Tooltip formatter={(value) => [`${number(value)} units`, "Predicted demand"]} /><Bar dataKey="units" radius={[7, 7, 0, 0]} fill="#36845e" /></BarChart></ResponsiveContainer></div> : <EmptyState title="No forecast rows" detail="The forecast CSV is empty or has not been generated." />}
    </section>
    <section className="mm-panel"><div className="mm-panel-heading"><div><h3>Forecast details</h3><p>Product-level predicted demand for each day in the source file.</p></div></div>
      {loading ? <LoadingLine /> : <DataTable rows={rows} emptyTitle="No forecast detail available" columns={[
        { key: "forecast_date", label: "Date", render: (row) => dateLabel(row.forecast_date) }, { key: "store_name", label: "Store" },
        { key: "product_name", label: "Product" }, { key: "predicted_demand", label: "Predicted demand", render: (row) => Number(row.predicted_demand || 0).toFixed(2) },
        { key: "predicted_units", label: "Predicted units", render: (row) => `${number(row.predicted_units)} ${row.unit || "units"}` },
      ]} />}
    </section>
  </div>;
}

// ------------------------------ REDISTRIBUTION ------------------------------
export function RedistributionManagement() {
  const [data, setData] = useState({ recommendations: [], basis: "" });
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState("");
  const [search, setSearch] = useState("");
  const [transferFilter, setTransferFilter] = useState("all");
  const notice = useMessage();

  async function load() {
    setLoading(true);
    notice.clear();
    const [recommendations, transferRows] = await Promise.allSettled([getRedistributionRecommendations(), getTransferRequests()]);
    if (recommendations.status === "fulfilled") setData(recommendations.value.data || { recommendations: [] });
    else notice.setError(errorText(recommendations.reason));
    if (transferRows.status === "fulfilled") setTransfers(Array.isArray(transferRows.value.data) ? transferRows.value.data : []);
    else if (recommendations.status === "fulfilled") notice.setError(errorText(transferRows.reason));
    setLoading(false);
  }
  useEffect(() => { load(); }, []);

  const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];
  const internal = recommendations.filter((row) => row.transfer_type === "INTERNAL");
  const purchases = recommendations.filter((row) => row.transfer_type === "PURCHASE");
  const query = search.trim().toLowerCase();
  const matches = (row) => !query || [row.product_name, row.from_store_name, row.to_store_name, row.from_store, row.to_store].some((value) => String(value ?? "").toLowerCase().includes(query));
  const visibleInternal = internal.filter(matches);
  const visiblePurchases = purchases.filter(matches);
  const visibleTransfers = transfers.filter((row) => {
    const matchesSearch = !query || [row.product_name, row.from_store_name, row.to_store_name, row.status].some((value) => String(value ?? "").toLowerCase().includes(query));
    return matchesSearch && (transferFilter === "all" || String(row.status || "").toLowerCase() === transferFilter);
  });

  async function requestTransfer(row) {
    const key = `${row.product_id}-${row.from_store}-${row.to_store}`;
    setSavingKey(key);
    notice.clear();
    try {
      await createTransferRequest({ product_id: row.product_id, from_store: row.from_store, to_store: row.to_store, transfer_quantity: row.transfer_quantity, notes: `Created from recommendation. Demand basis: ${row.demand_basis}` });
      await load();
      notice.setMessage("Transfer request created. This records the request; stock is not moved until the transfer is fulfilled.");
    } catch (error) { notice.setError(errorText(error)); }
    finally { setSavingKey(""); }
  }

  return <div className="mm-page">
    <PageHeading title="Redistribution" description="Move surplus stock toward stores with projected shortages. Review each suggested source, destination and quantity before creating a transfer request." icon={ArrowLeftRight} action={<button type="button" className="mm-button light" onClick={load} disabled={loading}><RefreshCw size={15} /> Recalculate</button>} />
    <Notice {...notice} onDismiss={notice.clear} />
    <div className="mm-inline-warning"><AlertTriangle size={18} /><div><strong>Recommendations are decision support, not completed stock movements.</strong><span>Creating an internal transfer request records the proposal. The current workflow does not fulfil or deduct stock automatically.</span></div></div>
    <section className="mm-stat-grid">
      <StatCard label="Internal transfer options" value={loading ? "—" : number(internal.length)} note="A surplus store can cover a shortage" icon={ArrowLeftRight} />
      <StatCard label="External purchase needs" value={loading ? "—" : number(purchases.length)} note="No suitable donor stock found" icon={ShoppingCart} tone="orange" />
      <StatCard label="Units to transfer" value={loading ? "—" : number(internal.reduce((sum, row) => sum + Number(row.transfer_quantity || 0), 0))} note="Suggested internal movement" icon={ArrowUpRight} tone="blue" />
      <StatCard label="Units to purchase" value={loading ? "—" : number(purchases.reduce((sum, row) => sum + Number(row.transfer_quantity || 0), 0))} note="Estimated replenishment requirement" icon={ArrowDownRight} tone="purple" />
    </section>
    <section className="mm-panel">
      <div className="mm-panel-heading"><div><h3>Redistribution workspace</h3><p>{data.basis || "Recommendations use inventory and demand data returned by the backend."}</p></div><label className="mm-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search product or store" /></label></div>
      <div className="mm-panel-subsection"><div><h4>Internal transfer opportunities</h4><p>Stock available at one store can cover another store's forecast shortage.</p></div><StatusTag status="internal">{visibleInternal.length} opportunities</StatusTag></div>
      {loading ? <LoadingLine /> : <DataTable rows={visibleInternal} emptyTitle="No internal transfer is recommended" emptyDetail="No eligible surplus stock currently covers another store's projected shortage." columns={[
        { key: "product_name", label: "Product", render: (row) => <strong>{row.product_name}</strong> },
        { key: "from_store_name", label: "Surplus store" }, { key: "to_store_name", label: "Store needing stock" },
        { key: "transfer_quantity", label: "Suggested quantity", render: (row) => number(row.transfer_quantity) },
        { key: "demand_basis", label: "Demand basis", render: (row) => <span className="mm-muted">{row.demand_basis || "Demand estimate"}</span> },
        { key: "action", label: "Action", render: (row) => <button className="mm-button small primary" type="button" disabled={Boolean(savingKey)} onClick={() => requestTransfer(row)}>{savingKey === `${row.product_id}-${row.from_store}-${row.to_store}` ? "Saving…" : "Create request"}</button> },
      ]} />}
    </section>
    <section className="mm-panel">
      <div className="mm-panel-subsection"><div><h4>External purchase requirements</h4><p>Shortages that cannot be covered by another store's available surplus.</p></div><StatusTag status="purchase">{visiblePurchases.length} requirements</StatusTag></div>
      {loading ? <LoadingLine /> : <DataTable rows={visiblePurchases} emptyTitle="No external purchase requirement" emptyDetail="Current internal stock positions cover the projected shortages, or no demand records are available." columns={[
        { key: "product_name", label: "Product", render: (row) => <strong>{row.product_name}</strong> },
        { key: "to_store_name", label: "Store needing stock" }, { key: "transfer_quantity", label: "Suggested quantity", render: (row) => number(row.transfer_quantity) },
        { key: "demand_basis", label: "Demand basis", render: (row) => <span className="mm-muted">{row.demand_basis || "Demand estimate"}</span> },
        { key: "action", label: "Next step", render: () => <span className="mm-muted">Arrange supplier purchase</span> },
      ]} />}
    </section>
    <section className="mm-panel">
      <div className="mm-panel-heading"><div><h3>Transfer request history</h3><p>Track internal requests already submitted for review and fulfilment.</p></div><label className="mm-select-field mm-compact-select">Status<select value={transferFilter} onChange={(event) => setTransferFilter(event.target.value)}><option value="all">All statuses</option><option value="requested">Requested</option><option value="accepted">Accepted</option><option value="rejected">Rejected</option><option value="completed">Completed</option></select></label></div>
      {loading ? <LoadingLine /> : <DataTable rows={visibleTransfers} emptyTitle="No transfer requests yet" emptyDetail="Create a request from an internal transfer opportunity to start a movement record." columns={[
        { key: "transfer_id", label: "Request" }, { key: "product_name", label: "Product" }, { key: "from_store_name", label: "From" },
        { key: "to_store_name", label: "To" }, { key: "transfer_quantity", label: "Quantity" }, { key: "status", label: "Status", render: (row) => <StatusTag status={row.status} /> },
        { key: "created_at", label: "Created", render: (row) => dateLabel(row.created_at) },
      ]} />}
    </section>
  </div>;
}

// ------------------------------ COMMUNITY ------------------------------
export function CommunityManagement({ products = [], stores = [], batches = [] }) {
  const [offers, setOffers] = useState([]); const [requests, setRequests] = useState([]); const [loading, setLoading] = useState(true);
  const [showOffer, setShowOffer] = useState(false); const [requestOffer, setRequestOffer] = useState(null);
  const [offerValues, setOfferValues] = useState({ store_id: stores[0]?.store_id || "", product_id: products[0]?.product_id || "", batch_id: "", quantity_available: "1", unit_price: "0", pickup_deadline: "", notes: "" });
  const [requestValues, setRequestValues] = useState({ requesting_store_id: stores.find((store) => store.store_id !== requestOffer?.store_id)?.store_id || "", quantity_requested: "1", message: "" });
  const [saving, setSaving] = useState(false); const notice = useMessage();
  const [offerSearch, setOfferSearch] = useState("");
  const [requestSearch, setRequestSearch] = useState("");
  async function load() {
    setLoading(true); notice.clear();
    const [offerResponse, requestResponse] = await Promise.allSettled([getCommunityOffers(), getCommunityRequests()]);
    if (offerResponse.status === "fulfilled") setOffers(Array.isArray(offerResponse.value.data) ? offerResponse.value.data : []);
    else notice.setError(errorText(offerResponse.reason));
    if (requestResponse.status === "fulfilled") setRequests(Array.isArray(requestResponse.value.data) ? requestResponse.value.data : []);
    else if (offerResponse.status === "fulfilled") notice.setError(errorText(requestResponse.reason));
    setLoading(false);
  }
  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (!offerValues.store_id && stores[0]) setOfferValues((current) => ({ ...current, store_id: stores[0].store_id }));
    if (!offerValues.product_id && products[0]) setOfferValues((current) => ({ ...current, product_id: products[0].product_id }));
    const product = products.find((item) => String(item.product_id) === String(offerValues.product_id));
    const firstBatch = batches.find((batch) => String(batch.product_id) === String(offerValues.product_id) && String(batch.store_id) === String(offerValues.store_id) && Number(batch.quantity_remaining) > 0);
    setOfferValues((current) => ({ ...current, batch_id: current.batch_id || firstBatch?.batch_id || "", unit_price: current.unit_price === "0" && product ? String(product.unit_price || 0) : current.unit_price }));
  }, [products, batches, offerValues.product_id, offerValues.store_id]);
  const availableBatches = batches.filter((batch) => String(batch.product_id) === String(offerValues.product_id) && (!offerValues.store_id || String(batch.store_id) === String(offerValues.store_id)) && Number(batch.quantity_remaining) > 0);
  const offerQuery = offerSearch.trim().toLowerCase();
  const requestQuery = requestSearch.trim().toLowerCase();
  const visibleOffers = offers.filter((row) => !offerQuery || [row.product_name, row.store_name, row.store_id, row.status].some((value) => String(value ?? "").toLowerCase().includes(offerQuery)));
  const visibleRequests = requests.filter((row) => !requestQuery || [row.product_name, row.requesting_store_name, row.requesting_store_id, row.requesting_store_address, row.requesting_store_phone, row.message, row.status].some((value) => String(value ?? "").toLowerCase().includes(requestQuery)));
  async function publish(event) {
    event.preventDefault(); setSaving(true); notice.clear();
    try { await publishCommunityOffer({ ...offerValues, quantity_available: Number(offerValues.quantity_available), unit_price: Number(offerValues.unit_price), pickup_deadline: offerValues.pickup_deadline || null, notes: offerValues.notes || null }); setShowOffer(false); await load(); notice.setMessage("Offer published to the store community."); }
    catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }
  async function submitRequest(event) {
    event.preventDefault(); if (!requestOffer) return; setSaving(true); notice.clear();
    try { await requestCommunityOffer(requestOffer.offer_id, { ...requestValues, quantity_requested: Number(requestValues.quantity_requested), message: requestValues.message || null }); setRequestOffer(null); await load(); notice.setMessage("Purchase request submitted to the offering store."); }
    catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }
  async function decide(requestId, status) {
    setSaving(true); notice.clear();
    try { await decideCommunityRequest(requestId, status); await load(); notice.setMessage(`Request ${status}. Accepted quantities are transferred into the requesting store's inventory as a new batch.`); }
    catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }
  return <div className="mm-page">
    <PageHeading title="Store community" description="Share surplus or near-expiry stock with other stores. Review purchase interest and contact the requesting store directly." icon={Store} action={<div className="mm-heading-actions"><button className="mm-button light" type="button" onClick={load} disabled={loading}><RefreshCw size={15} /> Refresh</button><button className="mm-button primary" type="button" onClick={() => setShowOffer((open) => !open)}><Plus size={16} /> Share stock</button></div>} />
    <Notice {...notice} onDismiss={notice.clear} />
    {showOffer && <section className="mm-panel mm-form-panel"><div className="mm-panel-heading"><div><h3>Publish surplus stock</h3><p>Choose a batch with remaining quantity and set the quantity available to other stores.</p></div><button className="mm-close" type="button" onClick={() => setShowOffer(false)}>×</button></div>
      <form className="mm-form-grid" onSubmit={publish}>
        <label>Offering store<select required value={offerValues.store_id} onChange={(event) => setOfferValues((v) => ({ ...v, store_id: event.target.value, batch_id: "" }))}><option value="">Select store</option>{stores.map((store) => <option key={store.store_id} value={store.store_id}>{store.store_name}</option>)}</select></label>
        <label>Product<select required value={offerValues.product_id} onChange={(event) => setOfferValues((v) => ({ ...v, product_id: event.target.value, batch_id: "" }))}><option value="">Select product</option>{products.map((product) => <option key={product.product_id} value={product.product_id}>{product.product_name}</option>)}</select></label>
        <label>Source batch<select required value={offerValues.batch_id} onChange={(event) => setOfferValues((v) => ({ ...v, batch_id: event.target.value }))}><option value="">Select batch</option>{availableBatches.map((batch) => <option key={batch.batch_id} value={batch.batch_id}>{batch.batch_code} · {batch.quantity_remaining} remaining · expires {dateLabel(batch.expiry_date)}</option>)}</select></label>
        <label>Quantity offered<input type="number" required min="1" max={availableBatches.find((b) => String(b.batch_id) === String(offerValues.batch_id))?.quantity_remaining || undefined} value={offerValues.quantity_available} onChange={(event) => setOfferValues((v) => ({ ...v, quantity_available: event.target.value }))} /></label>
        <label>Offer price per unit (₹)<input type="number" min="0" step="0.01" required value={offerValues.unit_price} onChange={(event) => setOfferValues((v) => ({ ...v, unit_price: event.target.value }))} /></label>
        <label>Pickup deadline<input type="date" value={offerValues.pickup_deadline} onChange={(event) => setOfferValues((v) => ({ ...v, pickup_deadline: event.target.value }))} /></label>
        <label className="wide">Notes<textarea rows="2" value={offerValues.notes} onChange={(event) => setOfferValues((v) => ({ ...v, notes: event.target.value }))} placeholder="Collection instructions or product condition" /></label>
        <div className="mm-form-actions"><button className="mm-button light" type="button" onClick={() => setShowOffer(false)}>Cancel</button><button className="mm-button primary" type="submit" disabled={saving || availableBatches.length === 0}>{saving ? "Publishing…" : "Publish offer"}</button></div>
      </form>
    </section>}
    {requestOffer && <section className="mm-panel mm-form-panel"><div className="mm-panel-heading"><div><h3>Request {requestOffer.product_name}</h3><p>Offer from {requestOffer.store_name}. {requestOffer.quantity_available} units available.</p></div><button className="mm-close" type="button" onClick={() => setRequestOffer(null)}>×</button></div>
      <form className="mm-form-grid" onSubmit={submitRequest}>
        <label>Your store<select required value={requestValues.requesting_store_id} onChange={(event) => setRequestValues((v) => ({ ...v, requesting_store_id: event.target.value }))}><option value="">Select your store</option>{stores.filter((store) => String(store.store_id) !== String(requestOffer.store_id)).map((store) => <option key={store.store_id} value={store.store_id}>{store.store_name}</option>)}</select></label>
        <label>Quantity requested<input type="number" required min="1" max={requestOffer.quantity_available} value={requestValues.quantity_requested} onChange={(event) => setRequestValues((v) => ({ ...v, quantity_requested: event.target.value }))} /></label>
        <label className="wide">Message<textarea rows="2" value={requestValues.message} onChange={(event) => setRequestValues((v) => ({ ...v, message: event.target.value }))} placeholder="Optional message to the offering store" /></label>
        <div className="mm-form-actions"><button className="mm-button light" type="button" onClick={() => setRequestOffer(null)}>Cancel</button><button className="mm-button primary" type="submit" disabled={saving}>{saving ? "Submitting…" : "Submit request"}</button></div>
      </form>
    </section>}
    <section className="mm-panel">
      <div className="mm-panel-heading">
        <div><h3>Stock shared with other stores</h3><p>Open offers available for another store to request or purchase.</p></div>
        <div className="mm-panel-tools"><label className="mm-search"><Search size={16} /><input value={offerSearch} onChange={(event) => setOfferSearch(event.target.value)} placeholder="Search product or offering store" /></label><button className="mm-button light" type="button" onClick={load} disabled={loading}><RefreshCw size={14} /> Refresh</button></div>
      </div>
      {loading ? <LoadingLine text="Loading available stock…" /> : <DataTable rows={visibleOffers} emptyTitle="No stock has been shared yet" emptyDetail="Publish an offer when a batch is available for another store." columns={[
        { key: "product_name", label: "Product", render: (row) => <strong>{row.product_name || row.product_id}</strong> },
        { key: "store_name", label: "Offering store", render: (row) => <div className="mm-store-contact"><strong>{row.store_name || row.store_id}</strong><span>{row.store_id}</span></div> },
        { key: "quantity_available", label: "Available" },
        { key: "unit_price", label: "Price / unit", render: (row) => currency(row.unit_price) },
        { key: "expiry_date", label: "Expires", render: (row) => dateLabel(row.expiry_date) },
        { key: "status", label: "Status", render: (row) => <StatusTag status={row.status} /> },
        { key: "action", label: "Action", render: (row) => row.status === "open" && Number(row.quantity_available) > 0 ? <button type="button" className="mm-button small primary" disabled={!stores.some((store) => String(store.store_id) !== String(row.store_id))} onClick={() => { setRequestOffer(row); setRequestValues({ requesting_store_id: stores.find((store) => String(store.store_id) !== String(row.store_id))?.store_id || "", quantity_requested: "1", message: "" }); }}>Request stock</button> : <span className="mm-muted">Unavailable</span> },
      ]} />}
    </section>
    <section className="mm-panel">
      <div className="mm-panel-heading">
        <div><h3>Purchase requests from other stores</h3><p>Review the interested store, address, phone number, requested item and quantity.</p></div>
        <label className="mm-search"><Search size={16} /><input value={requestSearch} onChange={(event) => setRequestSearch(event.target.value)} placeholder="Search store, product or phone" /></label>
      </div>
      {loading ? <LoadingLine text="Loading purchase requests…" /> : <DataTable rows={visibleRequests} emptyTitle="No purchase requests received" emptyDetail="Requests from interested stores will appear here with their contact details." columns={[
        { key: "product_name", label: "Requested item", render: (row) => <strong>{row.product_name || "Product"}</strong> },
        { key: "requesting_store", label: "Interested store", render: (row) => <div className="mm-store-contact"><strong>{row.requesting_store_name || row.requesting_store_id}</strong><span>Store ID: {row.requesting_store_id}</span><span>{row.requesting_store_address || "Address not available"}</span>{row.requesting_store_phone ? <a href={`tel:${row.requesting_store_phone}`}>{row.requesting_store_phone}</a> : <span>Phone not available</span>}</div> },
        { key: "quantity_requested", label: "Quantity" },
        { key: "message", label: "Message", render: (row) => row.message || <span className="mm-muted">No message</span> },
        { key: "status", label: "Status", render: (row) => <StatusTag status={row.status} /> },
        { key: "action", label: "Review", render: (row) => row.status === "pending" ? <div className="mm-row-actions"><button className="mm-button small primary" type="button" disabled={saving} onClick={() => decide(row.request_id, "accepted")}>Accept</button><button className="mm-button small danger" type="button" disabled={saving} onClick={() => decide(row.request_id, "rejected")}>Reject</button></div> : <span className="mm-muted">Reviewed</span> },
      ]} />}
    </section>
    <p className="mm-footnote">Community persistence requires the one-time SQL migration in <code>backend/sql/manager_modules.sql</code>.</p>
  </div>;
}

// ------------------------------ STAFF ------------------------------
export function StaffManagement({ stores = [] }) {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [values, setValues] = useState({ full_name: "", email: "", password: "", store_id: stores[0]?.store_id || "" });
  const notice = useMessage();

  async function load() {
    setLoading(true);
    notice.clear();
    try {
      const response = await getStaff();
      setStaff(Array.isArray(response.data) ? response.data : []);
    } catch (error) { notice.setError(errorText(error)); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  useEffect(() => { if (!values.store_id && stores[0]) setValues((current) => ({ ...current, store_id: stores[0].store_id })); }, [stores]);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    notice.clear();
    try {
      await createStaff(values);
      setShowForm(false);
      setValues((current) => ({ ...current, full_name: "", email: "", password: "" }));
      await load();
      notice.setMessage("Staff account created and assigned to the selected store.");
    } catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }
  async function toggle(member) {
    setSaving(true);
    notice.clear();
    try {
      await updateStaffStatus(member.user_id, !member.is_active);
      await load();
      notice.setMessage(`${member.full_name} active status updated.`);
    } catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }

  const activeCount = staff.filter((member) => member.is_active).length;
  const unassignedCount = staff.filter((member) => !member.store_id).length;
  const query = search.trim().toLowerCase();
  const visibleStaff = staff.filter((member) => {
    const searchable = [member.full_name, member.email, member.user_id, member.role, member.store_id,
      stores.find((store) => String(store.store_id) === String(member.store_id))?.store_name].join(" ").toLowerCase();
    const matchesSearch = !query || searchable.includes(query);
    const matchesStatus = filter === "all" || (filter === "active" ? member.is_active : !member.is_active);
    return matchesSearch && matchesStatus;
  });

  return <div className="mm-page">
    <PageHeading title="Staff management" description="Create staff login accounts, assign each person to a store and manage their active status." icon={Users} action={<div className="mm-heading-actions"><button className="mm-button light" type="button" onClick={load} disabled={loading}><RefreshCw size={15} /> Refresh</button><button className="mm-button primary" type="button" onClick={() => setShowForm((open) => !open)}><Plus size={16} /> Add staff member</button></div>} />
    <Notice {...notice} onDismiss={notice.clear} />
    <section className="mm-stat-grid">
      <StatCard label="Staff profiles" value={loading ? "—" : number(staff.length)} note="Profiles with staff role" icon={Users} />
      <StatCard label="Active staff" value={loading ? "—" : number(activeCount)} note="Marked active in profiles" icon={CheckCircle2} tone="green" />
      <StatCard label="Inactive staff" value={loading ? "—" : number(staff.length - activeCount)} note="Can be reactivated" icon={XCircle} tone="orange" />
      <StatCard label="Unassigned staff" value={loading ? "—" : number(unassignedCount)} note="Need a store assignment" icon={Store} tone="blue" />
    </section>
    {showForm && <section className="mm-panel mm-form-panel">
      <div className="mm-panel-heading"><div><h3>Create staff account</h3><p>Create the login and assign the profile to the correct store. Share the temporary password securely outside this screen.</p></div><button type="button" className="mm-close" onClick={() => setShowForm(false)} aria-label="Close form">×</button></div>
      <form className="mm-form-grid" onSubmit={submit}>
        <label>Full name<input required minLength="2" maxLength="120" value={values.full_name} onChange={(event) => setValues((current) => ({ ...current, full_name: event.target.value }))} /></label>
        <label>Email<input required type="email" value={values.email} onChange={(event) => setValues((current) => ({ ...current, email: event.target.value }))} /></label>
        <label>Temporary password<input required type="password" minLength="8" autoComplete="new-password" value={values.password} onChange={(event) => setValues((current) => ({ ...current, password: event.target.value }))} /></label>
        <label>Assigned store<select required value={values.store_id} onChange={(event) => setValues((current) => ({ ...current, store_id: event.target.value }))}><option value="">Select store</option>{stores.map((store) => <option key={store.store_id} value={store.store_id}>{store.store_name}</option>)}</select></label>
        <div className="mm-form-actions"><button type="button" className="mm-button light" onClick={() => setShowForm(false)} disabled={saving}>Cancel</button><button type="submit" className="mm-button primary" disabled={saving || !stores.length}>{saving ? "Creating…" : "Create staff account"}</button></div>
      </form>
    </section>}
    <section className="mm-panel">
      <div className="mm-panel-heading"><div><h3>Staff directory</h3><p>Search by name, email, role, user ID or assigned store.</p></div><div className="mm-panel-tools"><label className="mm-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search staff directory" /></label><button className="mm-button light" type="button" onClick={load} disabled={loading}><RefreshCw size={15} /> Refresh</button></div></div>
      <div className="mm-filter-row" role="group" aria-label="Filter staff status">
        {[{ id: "all", label: "All staff", count: staff.length }, { id: "active", label: "Active", count: activeCount }, { id: "inactive", label: "Inactive", count: staff.length - activeCount }].map((item) => <button type="button" key={item.id} className={`mm-filter ${filter === item.id ? "active" : ""}`} onClick={() => setFilter(item.id)}>{item.label}<span>{item.count}</span></button>)}
      </div>
      {loading ? <LoadingLine /> : <DataTable rows={visibleStaff} emptyTitle={staff.length ? "No staff match your search" : "No staff profiles found"} emptyDetail={staff.length ? "Try another name, email or status filter." : "Create a staff account to add a team member to the directory."} columns={[
        { key: "full_name", label: "Staff member", render: (row) => <strong>{row.full_name}</strong> },
        { key: "email", label: "Email", render: (row) => row.email || <span className="mm-muted">Managed by Supabase Auth</span> },
        { key: "store_id", label: "Assigned store", render: (row) => stores.find((store) => String(store.store_id) === String(row.store_id))?.store_name || row.store_id || <StatusTag status="pending">Not assigned</StatusTag> },
        { key: "role", label: "Role", render: (row) => <StatusTag status={row.role} /> },
        { key: "is_active", label: "Status", render: (row) => <StatusTag status={row.is_active ? "active" : "inactive"}>{row.is_active ? "Active" : "Inactive"}</StatusTag> },
        { key: "action", label: "Access", render: (row) => <button type="button" className={`mm-button small ${row.is_active ? "danger" : "primary"}`} disabled={saving} onClick={() => toggle(row)}>{row.is_active ? "Set inactive" : "Set active"}</button> },
      ]} />}
    </section>
    <p className="mm-footnote">The active flag is stored in public.profiles. Authentication middleware and database row-level security must check this flag before it can enforce access restrictions.</p>
  </div>;
}

// ------------------------------ SETTINGS ------------------------------
export function SettingsManagement({ stores = [], storesLoading = false, onRefresh = () => {} }) {
  const [storeId, setStoreId] = useState(stores[0]?.store_id || ""); const [values, setValues] = useState({ store_name: "", address: "", phone: "", latitude: "", longitude: "" });
  const [saving, setSaving] = useState(false); const notice = useMessage();
  const selected = stores.find((store) => String(store.store_id) === String(storeId));
  useEffect(() => {
    if (!storeId && stores[0]) setStoreId(stores[0].store_id);
  }, [storeId, stores]);
  useEffect(() => {
    if (selected) setValues({ store_name: selected.store_name || "", address: selected.address || "", phone: selected.phone || "", latitude: selected.latitude ?? "", longitude: selected.longitude ?? "" });
  }, [storeId, stores]);
  async function submit(event) {
    event.preventDefault(); if (!selected) return; setSaving(true); notice.clear();
    const payload = { store_name: values.store_name, address: values.address, phone: values.phone, latitude: values.latitude === "" ? null : Number(values.latitude), longitude: values.longitude === "" ? null : Number(values.longitude) };
    try { await updateStore(storeId, payload); notice.setMessage("Store settings updated."); await onRefresh(); }
    catch (error) { notice.setError(errorText(error)); }
    finally { setSaving(false); }
  }
  return <div className="mm-page">
    <PageHeading title="Settings" description="Maintain the store profile used on receipts, staff assignments and store-to-store purchase requests." icon={Settings} />
    <Notice {...notice} onDismiss={notice.clear} />
    <section className="mm-panel mm-settings-panel">
      <div className="mm-panel-heading"><div><h3>Store profile</h3><p>Keep the contact and location details accurate so other stores can reach you when they submit or receive a purchase request.</p></div></div>
      {storesLoading ? <LoadingLine text="Loading store profile…" /> : stores.length === 0 ? <EmptyState title="No store profile available" detail="A store profile must be connected before these settings can be edited." /> : <form className="mm-form-grid" onSubmit={submit}>
        <label className="wide">Select store<select value={storeId} onChange={(event) => setStoreId(event.target.value)}>{stores.map((store) => <option key={store.store_id} value={store.store_id}>{store.store_name} ({store.store_id})</option>)}</select></label>
        <label>Store name<input required minLength="2" value={values.store_name} onChange={(event) => setValues((v) => ({ ...v, store_name: event.target.value }))} /></label>
        <label>Phone<input value={values.phone} onChange={(event) => setValues((v) => ({ ...v, phone: event.target.value }))} /></label>
        <label className="wide">Address<textarea required minLength="3" rows="3" value={values.address} onChange={(event) => setValues((v) => ({ ...v, address: event.target.value }))} /></label>
        <label>Latitude<input type="number" min="-90" max="90" step="any" value={values.latitude} onChange={(event) => setValues((v) => ({ ...v, latitude: event.target.value }))} /></label>
        <label>Longitude<input type="number" min="-180" max="180" step="any" value={values.longitude} onChange={(event) => setValues((v) => ({ ...v, longitude: event.target.value }))} /></label>
        <div className="mm-form-actions"><button type="submit" className="mm-button primary" disabled={saving}>{saving ? "Saving…" : "Save settings"}</button></div>
      </form>}
    </section>
    <p className="mm-footnote">The current app's manager authentication flow is still bypassed for UI development. Store-level authorization and row-level security must be enabled before deploying this to production.</p>
  </div>;
}
