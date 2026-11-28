import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Package,
  RefreshCw,
  ShoppingCart,
  Warehouse,
  ArrowLeftRight,
  Store,
} from "lucide-react";
import { getSales } from "../../services/api";
import "./ManagerDashboard.css";

const asArray = (value) => Array.isArray(value) ? value : [];
const fmt = (value) => (Number(value) || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });
const money = (value) => `₹${(Number(value) || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

function daysUntil(value) {
  if (!value) return null;
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((date.getTime() - today.getTime()) / 86400000);
}

function dateLabel(value) {
  if (!value) return "Date not recorded";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

function Stat({ label, value, hint, icon: Icon, tone = "green", onClick }) {
  const content = <>
    <span className={`md-stat-icon ${tone}`}><Icon size={19} /></span>
    <span className="md-stat-copy"><small>{label}</small><strong>{value}</strong><span>{hint}</span></span>
    {onClick && <ArrowRight className="md-stat-arrow" size={16} />}
  </>;
  return onClick ? <button type="button" className="md-stat-card is-clickable" onClick={onClick}>{content}</button> : <article className="md-stat-card">{content}</article>;
}

function SectionTitle({ title, detail, action }) {
  return <div className="md-section-title"><div><h3>{title}</h3><p>{detail}</p></div>{action}</div>;
}

function Empty({ icon: Icon = CheckCircle2, title, detail }) {
  return <div className="md-empty"><Icon size={23} /><strong>{title}</strong><span>{detail}</span></div>;
}

const shortcuts = [
  { id: "inventory", title: "Review inventory", detail: "Stock by product and location", icon: Warehouse, tone: "green" },
  { id: "products", title: "Product catalogue", detail: "Names, categories and prices", icon: Package, tone: "blue" },
  { id: "batches", title: "Receive stock", detail: "Register a delivery and expiry", icon: ArrowDownToLine, tone: "purple" },
  { id: "sales", title: "Record a sale", detail: "Capture sales and deduct FEFO stock", icon: ShoppingCart, tone: "orange" },
  { id: "expiry", title: "Expiry action list", detail: "Prioritise lots due soon or expired", icon: CalendarClock, tone: "red" },
  { id: "forecast", title: "Demand forecast", detail: "Review the saved 7-day outlook", icon: BrainCircuit, tone: "blue" },
  { id: "redistribution", title: "Redistribute stock", detail: "Match surplus with store shortages", icon: ArrowLeftRight, tone: "purple" },
  { id: "community", title: "Store community", detail: "Share stock and review purchase interest", icon: Store, tone: "green" },
];

export default function ManagerDashboard({ data = {}, totalStock = 0, onNavigate = () => {}, onRefresh = () => {}, loading = false }) {
  const products = asArray(data.products);
  const inventory = asArray(data.inventory);
  const batches = asArray(data.batches);
  const stores = asArray(data.stores);
  const productById = useMemo(() => new Map(products.map((item) => [String(item.product_id), item])), [products]);
  const storeById = useMemo(() => new Map(stores.map((item) => [String(item.store_id), item])), [stores]);
  const [recentSales, setRecentSales] = useState([]);
  const [salesLoading, setSalesLoading] = useState(true);
  const [salesUnavailable, setSalesUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    setSalesLoading(true);
    getSales(6)
      .then((response) => {
        if (active) {
          setRecentSales(asArray(response.data));
          setSalesUnavailable(false);
        }
      })
      .catch(() => {
        if (active) {
          setRecentSales([]);
          setSalesUnavailable(true);
        }
      })
      .finally(() => { if (active) setSalesLoading(false); });
    return () => { active = false; };
  }, []);

  const riskBatches = useMemo(() => batches
    .map((batch) => ({ ...batch, daysLeft: daysUntil(batch.expiry_date) }))
    .filter((batch) => Number(batch.quantity_remaining || 0) > 0 && batch.daysLeft !== null && batch.daysLeft <= 7)
    .sort((a, b) => a.daysLeft - b.daysLeft), [batches]);

  const lowStock = useMemo(() => inventory
    .filter((row) => Number(row.available_quantity || 0) <= 10)
    .sort((a, b) => Number(a.available_quantity || 0) - Number(b.available_quantity || 0)), [inventory]);

  const activeBatches = batches.filter((batch) => Number(batch.quantity_remaining || 0) > 0).length;
  const stockUnits = inventory.length ? totalStock : batches.reduce((sum, batch) => sum + Number(batch.quantity_remaining || 0), 0);
  const expiredCount = riskBatches.filter((batch) => batch.daysLeft < 0).length;
  const nearCount = riskBatches.length - expiredCount;
  const recentBatches = [...batches].sort((a, b) => String(b.created_at || b.batch_id || "").localeCompare(String(a.created_at || a.batch_id || ""))).slice(0, 5);

  return (
    <div className="manager-home">
      <section className="md-hero">
        <div className="md-hero-copy">
          <span className="md-eyebrow">MANAGER OVERVIEW</span>
          <h2>Keep stock moving. Reduce waste.</h2>
          <p>Your daily control centre for inventory, sales, expiry actions and store-to-store coordination.</p>
        </div>
        <div className="md-hero-actions">
          <button type="button" className="md-button md-button-light" onClick={onRefresh}><RefreshCw size={15} /> Refresh data</button>
          <button type="button" className="md-button md-button-primary" onClick={() => onNavigate("sales")}><ShoppingCart size={15} /> Record sale</button>
        </div>
      </section>

      {loading && <div className="md-loading-hint"><span className="md-mini-spinner" /> Loading your latest product, stock and batch records…</div>}

      <section className="md-stat-grid" aria-label="Store performance summary">
        <Stat label="Product catalogue" value={loading ? "—" : fmt(products.length)} hint="Registered products" icon={Package} tone="green" onClick={() => onNavigate("products")} />
        <Stat label="Stock on hand" value={loading ? "—" : fmt(stockUnits)} hint="Units across inventory" icon={Warehouse} tone="blue" onClick={() => onNavigate("inventory")} />
        <Stat label="Live stock lots" value={loading ? "—" : fmt(activeBatches)} hint="Batches with quantity remaining" icon={ClipboardList} tone="purple" onClick={() => onNavigate("batches")} />
        <Stat label="Expiry actions" value={loading ? "—" : fmt(riskBatches.length)} hint={`${expiredCount} expired · ${nearCount} due within 7 days`} icon={AlertTriangle} tone={riskBatches.length ? "orange" : "green"} onClick={() => onNavigate("expiry")} />
      </section>

      <section className="md-section">
        <SectionTitle title="Quick actions" detail="Open the task you need without searching through the menu." />
        <div className="md-shortcut-grid">
          {shortcuts.map((item) => {
            const Icon = item.icon;
            return <button type="button" key={item.id} className="md-shortcut" onClick={() => onNavigate(item.id)}>
              <span className={`md-shortcut-icon ${item.tone}`}><Icon size={19} /></span>
              <span className="md-shortcut-copy"><strong>{item.title}</strong><small>{item.detail}</small></span>
              <ArrowRight size={16} className="md-shortcut-arrow" />
            </button>;
          })}
        </div>
      </section>

      <div className="md-two-column">
        <section className="md-panel">
          <SectionTitle title="Expiry action queue" detail="Lots with stock that is expired or expires within 7 days." action={<button type="button" className="md-link-button" onClick={() => onNavigate("expiry")}>View all <ArrowRight size={14} /></button>} />
          {loading ? <div className="md-inline-loading">Loading expiry queue…</div> : riskBatches.length ? <div className="md-priority-list">
            {riskBatches.slice(0, 5).map((batch) => {
              const product = productById.get(String(batch.product_id));
              const store = storeById.get(String(batch.store_id));
              const expired = batch.daysLeft < 0;
              return <div className="md-priority-row" key={batch.batch_id ?? batch.batch_code}>
                <span className={`md-priority-icon ${expired ? "danger" : "warning"}`}><AlertTriangle size={16} /></span>
                <span className="md-priority-copy"><strong>{product?.product_name || `Product ${batch.product_id || "—"}`}</strong><small>{batch.batch_code || `Batch ${batch.batch_id}`} · {store?.store_name || "Store not assigned"} · {fmt(batch.quantity_remaining)} remaining</small></span>
                <span className={`md-priority-pill ${expired ? "danger" : "warning"}`}>{expired ? `${Math.abs(batch.daysLeft)}d overdue` : batch.daysLeft === 0 ? "Today" : `${batch.daysLeft}d left`}</span>
              </div>;
            })}
          </div> : <Empty icon={CheckCircle2} title="No urgent expiry lots" detail="No batch with remaining stock is past expiry or due in the next 7 days." />}
        </section>

        <section className="md-panel">
          <SectionTitle title="Low-stock watch" detail="Inventory records at or below the 10-unit attention threshold." action={<button type="button" className="md-link-button" onClick={() => onNavigate("inventory")}>Review inventory <ArrowRight size={14} /></button>} />
          {loading ? <div className="md-inline-loading">Loading stock levels…</div> : lowStock.length ? <div className="md-low-stock-list">
            {lowStock.slice(0, 5).map((row, index) => {
              const product = productById.get(String(row.product_id));
              const store = storeById.get(String(row.store_id));
              return <div className="md-low-stock-row" key={`${row.store_id}-${row.product_id}-${index}`}>
                <span className="md-product-dot"><Package size={15} /></span>
                <span className="md-low-stock-copy"><strong>{product?.product_name || row.product_name || `Product ${row.product_id || "—"}`}</strong><small>{store?.store_name || row.store_name || "Store not assigned"}</small></span>
                <strong className="md-low-stock-value">{fmt(row.available_quantity)}</strong>
              </div>;
            })}
          </div> : <Empty icon={CheckCircle2} title="Stock levels look healthy" detail="No inventory record is at or below 10 units." />}
        </section>
      </div>

      <div className="md-two-column md-bottom-grid">
        <section className="md-panel">
          <SectionTitle title="Recent sales" detail="Latest transactions returned by the sales service." action={<button type="button" className="md-link-button" onClick={() => onNavigate("sales")}>Sales history <ArrowRight size={14} /></button>} />
          {salesLoading ? <div className="md-inline-loading">Loading recent sales…</div> : salesUnavailable ? <Empty icon={ShoppingCart} title="Sales data unavailable" detail="Check the sales service connection, or open Sales to retry." /> : recentSales.length ? <div className="md-sales-list">
            {recentSales.map((sale) => <div className="md-sale-row" key={sale.sale_id}>
              <span className="md-sale-icon"><ShoppingCart size={16} /></span>
              <span className="md-sale-copy"><strong>{sale.product_name || `Product ${sale.product_id}`}</strong><small>{sale.store_name || `Store ${sale.store_id}`} · {dateLabel(sale.sale_date)} · Qty {fmt(sale.quantity_sold)}</small></span>
              <strong className="md-sale-total">{money(sale.total_amount ?? Number(sale.quantity_sold || 0) * Number(sale.selling_price || 0))}</strong>
            </div>)}
          </div> : <Empty icon={ShoppingCart} title="No sales recorded yet" detail="Record the first sale to start building your transaction history." />}
        </section>

        <section className="md-panel">
          <SectionTitle title="Recent stock receipts" detail="Latest batches added to the inventory." action={<button type="button" className="md-link-button" onClick={() => onNavigate("batches")}>Open batches <ArrowRight size={14} /></button>} />
          {loading ? <div className="md-inline-loading">Loading batches…</div> : recentBatches.length ? <div className="md-receipts-list">
            {recentBatches.map((batch) => {
              const product = productById.get(String(batch.product_id));
              const store = storeById.get(String(batch.store_id));
              const days = daysUntil(batch.expiry_date);
              const expiring = days !== null && days <= 7;
              return <div className="md-receipt-row" key={batch.batch_id ?? batch.batch_code}>
                <span className="md-receipt-icon"><Package size={16} /></span>
                <span className="md-receipt-copy"><strong>{product?.product_name || `Product ${batch.product_id || "—"}`}</strong><small>{batch.batch_code || `Batch ${batch.batch_id}`} · {store?.store_name || "Store not assigned"}</small></span>
                <span className={`md-receipt-qty ${expiring ? "urgent" : ""}`}>{fmt(batch.quantity_remaining)}<small>remaining</small></span>
              </div>;
            })}
          </div> : <Empty icon={Package} title="No stock receipts yet" detail="Register a batch when a new delivery arrives." />}
        </section>
      </div>

      <footer className="md-footer-note"><CheckCircle2 size={15} /> Stock health is calculated from the records currently loaded. Sales and forecasting insights are shown only when their APIs return data.</footer>
    </div>
  );
}

export function StaffDashboard({ data = {}, onNavigate = () => {}, loading = false }) {
  const inventory = asArray(data.inventory);
  const batches = asArray(data.batches);
  const products = asArray(data.products);
  const lowStock = inventory.filter((row) => Number(row.available_quantity || 0) <= 10).length;
  const expiryAttention = batches.filter((batch) => Number(batch.quantity_remaining || 0) > 0 && (daysUntil(batch.expiry_date) ?? 99) <= 7).length;
  const steps = [
    { id: "inventory", title: "Check stock levels", detail: "Review available quantities before receiving or selling goods.", icon: Warehouse },
    { id: "batches", title: "Receive a delivery", detail: "Create a batch with quantity and expiry dates when stock arrives.", icon: ArrowDownToLine },
    { id: "sales", title: "Record a sale", detail: "Save the sale so eligible batch quantities are deducted using FEFO.", icon: ShoppingCart },
    { id: "expiry", title: "Handle expiry alerts", detail: "Prioritise expired and near-expiry items before they become waste.", icon: CalendarClock },
  ];
  return <div className="manager-home md-staff-home">
    <section className="md-hero md-staff-hero"><div className="md-hero-copy"><span className="md-eyebrow">STAFF WORKSPACE</span><h2>Daily store operations</h2><p>A manager-facing overview of the key tasks available to store staff.</p></div><button type="button" className="md-button md-button-primary" onClick={() => onNavigate("inventory")}><Warehouse size={15} /> Open inventory</button></section>
    <section className="md-stat-grid">
      <Stat label="Products to handle" value={loading ? "—" : fmt(products.length)} hint="Registered catalogue items" icon={Package} tone="green" onClick={() => onNavigate("products")} />
      <Stat label="Inventory records" value={loading ? "—" : fmt(inventory.length)} hint="Product and store stock rows" icon={Warehouse} tone="blue" onClick={() => onNavigate("inventory")} />
      <Stat label="Low-stock records" value={loading ? "—" : fmt(lowStock)} hint="At or below 10 units" icon={AlertTriangle} tone="orange" onClick={() => onNavigate("inventory")} />
      <Stat label="Expiry actions" value={loading ? "—" : fmt(expiryAttention)} hint="Expired or due within 7 days" icon={CalendarClock} tone="red" onClick={() => onNavigate("expiry")} />
    </section>
    <section className="md-panel">
      <SectionTitle title="Daily workflow" detail="Use these steps to keep receiving, sales and expiry records in sync." />
      <div className="md-workflow-grid">{steps.map((step, index) => { const Icon = step.icon; return <button type="button" className="md-workflow-step" key={step.id} onClick={() => onNavigate(step.id)}><span className="md-step-number">{index + 1}</span><span className="md-workflow-icon"><Icon size={19} /></span><strong>{step.title}</strong><small>{step.detail}</small><span className="md-step-link">Open task <ArrowUpRight size={14} /></span></button>; })}</div>
    </section>
    <section className="md-panel"><SectionTitle title="Operational guidance" detail="What staff actions update in ZeroWasteNet." /><div className="md-guidance-grid"><div><CheckCircle2 size={18} /><strong>Receiving stock</strong><span>Each delivery is saved as a separate batch to preserve expiry traceability.</span></div><div><CheckCircle2 size={18} /><strong>Recording sales</strong><span>The sales endpoint deducts quantity from the earliest-expiring eligible batch.</span></div><div><AlertTriangle size={18} /><strong>Expiry monitoring</strong><span>Expired and near-expiry stock must be reviewed before it is offered or sold.</span></div></div><p className="md-caveat">Individual staff activity logs and task completion tracking are not connected yet. This page summarizes current inventory records and links to the operational screens.</p></section>
  </div>;
}
