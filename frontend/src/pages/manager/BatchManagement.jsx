import { useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Package,
  Plus,
  Search,
  XCircle,
  Boxes,
} from "lucide-react";
import "./BatchManagement.css";

const FILTERS = [
  { id: "all", label: "All batches" },
  { id: "active", label: "Active" },
  { id: "near", label: "Near expiry" },
  { id: "expired", label: "Expired" },
  { id: "depleted", label: "Depleted" },
];

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function text(value) {
  return String(value ?? "").trim();
}

function normalise(value) {
  return text(value).toLowerCase().replace(/\s+/g, " ");
}

function parseDateOnly(value) {
  if (!value) return null;
  const parts = String(value).slice(0, 10).split("-").map(Number);
  if (parts.length !== 3 || parts.some((part) => !Number.isFinite(part))) return null;
  const [year, month, day] = parts;
  const date = new Date(year, month - 1, day);
  return Number.isNaN(date.getTime()) ? null : date;
}

function daysUntil(value) {
  const date = parseDateOnly(value);
  if (!date) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((date.getTime() - today.getTime()) / 86400000);
}

function formatDate(value) {
  const date = parseDateOnly(value);
  if (!date) return "—";
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatQuantity(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? amount.toLocaleString("en-IN") : "—";
}

function getStatus(batch) {
  const remaining = Number(batch.quantity_remaining ?? 0);
  const days = daysUntil(batch.expiry_date);
  if (remaining <= 0) return { id: "depleted", label: "Depleted", days };
  if (days !== null && days < 0) return { id: "expired", label: "Expired", days };
  if (days !== null && days <= 7) return { id: "near", label: days === 0 ? "Expires today" : "Near expiry", days };
  return { id: "active", label: "Active", days };
}

function getExpiryCaption(status) {
  if (status.days === null) return "Expiry date unavailable";
  if (status.days < 0) return `${Math.abs(status.days)} day${Math.abs(status.days) === 1 ? "" : "s"} overdue`;
  if (status.days === 0) return "Expires today";
  return `${status.days} day${status.days === 1 ? "" : "s"} remaining`;
}

function buildRows(batches, products, stores) {
  const productById = new Map(products.map((item) => [String(item.product_id ?? item.id ?? ""), item]));
  const storeById = new Map(stores.map((item) => [String(item.store_id ?? item.id ?? ""), item]));

  return batches.map((batch, index) => {
    const product = productById.get(String(batch.product_id ?? ""));
    const store = storeById.get(String(batch.store_id ?? ""));
    const status = getStatus(batch);
    return {
      ...batch,
      _key: String(batch.batch_id ?? batch.batch_code ?? index),
      _productName: product?.product_name || (batch.product_id ? `Product ${batch.product_id}` : "Product not linked"),
      _productUnit: product?.unit || "units",
      _storeName: store?.store_name || (batch.store_id ? `Store ${batch.store_id}` : "Store not assigned"),
      _status: status,
      _expiryCaption: getExpiryCaption(status),
    };
  }).sort((a, b) => {
    const aDate = parseDateOnly(a.expiry_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
    const bDate = parseDateOnly(b.expiry_date)?.getTime() ?? Number.MAX_SAFE_INTEGER;
    return aDate - bDate;
  });
}

function StatusPill({ status }) {
  return <span className={`bm-status ${status.id}`}>{status.label}</span>;
}

export default function BatchManagement({ batches = [], products = [], stores = [], dataLoading = false, onAddBatch }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const rows = useMemo(
    () => buildRows(asArray(batches), asArray(products), asArray(stores)),
    [batches, products, stores]
  );

  const counts = useMemo(() => ({
    all: rows.length,
    active: rows.filter((row) => row._status.id === "active").length,
    near: rows.filter((row) => row._status.id === "near").length,
    expired: rows.filter((row) => row._status.id === "expired").length,
    depleted: rows.filter((row) => row._status.id === "depleted").length,
  }), [rows]);

  const batchesWithStock = rows.filter((row) => Number(row.quantity_remaining ?? 0) > 0).length;
  const attentionBatches = counts.near + counts.expired;

  const filteredRows = useMemo(() => {
    const query = normalise(search);
    return rows.filter((row) => {
      const searchText = [
        row.batch_id,
        row.batch_code,
        row.product_id,
        row._productName,
        row.store_id,
        row._storeName,
      ].map(normalise).join(" ");
      const matchesSearch = !query || searchText.includes(query);
      const matchesFilter = filter === "all" || row._status.id === filter;
      return matchesSearch && matchesFilter;
    });
  }, [rows, search, filter]);

  return (
    <div className="batch-management">
      <section className="bm-page-heading">
        <div>
          <span className="bm-eyebrow">MANAGER WORKSPACE / STOCK LOTS</span>
          <h2>Batch management</h2>
          <p>Track each stock receipt separately so quantities and expiry dates remain traceable.</p>
        </div>
        <button type="button" className="bm-button bm-button-primary" onClick={onAddBatch} disabled={asArray(products).length === 0}>
          <Plus size={17} /> Add new batch
        </button>
      </section>

      {!dataLoading && asArray(products).length === 0 && (
        <div className="bm-inline-alert" role="status">
          <AlertTriangle size={17} />
          <span>Register at least one product before adding a batch. Open the Products section first.</span>
        </div>
      )}

      <section className="bm-stats-grid" aria-label="Batch summary">
        <article className="bm-stat-card">
          <span className="bm-stat-icon green"><Boxes size={19} /></span>
          <div><small>Total batches</small><strong>{dataLoading ? "—" : formatQuantity(rows.length)}</strong><span>Recorded stock lots</span></div>
        </article>
        <article className="bm-stat-card">
          <span className="bm-stat-icon blue"><Package size={19} /></span>
          <div><small>Batches with stock</small><strong>{dataLoading ? "—" : formatQuantity(batchesWithStock)}</strong><span>Records with remaining quantity</span></div>
        </article>
        <article className="bm-stat-card">
          <span className="bm-stat-icon orange"><CalendarClock size={19} /></span>
          <div><small>Expiry attention</small><strong>{dataLoading ? "—" : formatQuantity(attentionBatches)}</strong><span>{dataLoading ? "Checking expiry status" : `${counts.near} near expiry · ${counts.expired} expired`}</span></div>
        </article>
        <article className="bm-stat-card">
          <span className="bm-stat-icon purple"><CheckCircle2 size={19} /></span>
          <div><small>Active batches</small><strong>{dataLoading ? "—" : formatQuantity(counts.active)}</strong><span>More than 7 days to expiry</span></div>
        </article>
      </section>

      <section className="bm-panel panel">
        <div className="bm-toolbar">
          <div>
            <h3>Batch register</h3>
            <p>Search by batch code, product or store. The nearest expiry dates appear first.</p>
          </div>
          <label className="bm-search search-box">
            <Search size={17} />
            <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search batches…" aria-label="Search batches" />
          </label>
        </div>

        <div className="bm-filter-row" role="group" aria-label="Filter batches">
          {FILTERS.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`bm-filter ${filter === item.id ? "selected" : ""}`}
              onClick={() => setFilter(item.id)}
            >
              {item.label}<span>{counts[item.id]}</span>
            </button>
          ))}
        </div>

        {filteredRows.length > 0 ? (
          <>
            <div className="bm-desktop-table table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Batch / product</th>
                    <th>Store</th>
                    <th>Received</th>
                    <th>Remaining</th>
                    <th>Manufactured</th>
                    <th>Expiry</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((row) => (
                    <tr key={row._key}>
                      <td>
                        <div className="bm-batch-cell">
                          <span className="bm-batch-icon"><Package size={17} /></span>
                          <span><strong>{row.batch_code || row.batch_id || "Unnamed batch"}</strong><small>{row._productName} · {row.product_id || "No product ID"}</small></span>
                        </div>
                      </td>
                      <td><strong className="bm-store-name">{row._storeName}</strong><small className="bm-muted">{row.store_id || "No store ID"}</small></td>
                      <td><strong>{formatQuantity(row.quantity_received)}</strong><small className="bm-muted">{row._productUnit}</small></td>
                      <td><strong className={Number(row.quantity_remaining) <= 0 ? "bm-zero" : "bm-remaining"}>{formatQuantity(row.quantity_remaining)}</strong><small className="bm-muted">{row._productUnit}</small></td>
                      <td>{formatDate(row.manufacturing_date)}</td>
                      <td><span className="bm-expiry-date">{formatDate(row.expiry_date)}</span><small className="bm-muted">{row._expiryCaption}</small></td>
                      <td><StatusPill status={row._status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="bm-mobile-list">
              {filteredRows.map((row) => (
                <article className="bm-mobile-card" key={row._key}>
                  <div className="bm-mobile-card-heading">
                    <span className="bm-batch-icon"><Package size={17} /></span>
                    <div><strong>{row.batch_code || row.batch_id || "Unnamed batch"}</strong><small>{row._productName}</small></div>
                    <StatusPill status={row._status} />
                  </div>
                  <div className="bm-mobile-details">
                    <span><small>Remaining</small><strong>{formatQuantity(row.quantity_remaining)} {row._productUnit}</strong></span>
                    <span><small>Received</small><strong>{formatQuantity(row.quantity_received)} {row._productUnit}</strong></span>
                    <span><small>Expiry date</small><strong>{formatDate(row.expiry_date)}</strong></span>
                    <span><small>Expiry status</small><strong>{row._expiryCaption}</strong></span>
                    <span className="bm-detail-wide"><small>Store</small><strong>{row._storeName}</strong></span>
                  </div>
                </article>
              ))}
            </div>
          </>
        ) : dataLoading ? (
          <div className="bm-empty-state bm-loading-state"><span className="bm-loading-spinner" /><strong>Loading batch register</strong><p>Batch and expiry records are being retrieved.</p></div>
        ) : (
          <div className="bm-empty-state">
            <span><Clock3 size={25} /></span>
            <strong>{rows.length === 0 ? "No batches recorded yet" : "No matching batches"}</strong>
            <p>{rows.length === 0 ? "Create a batch when new stock arrives. Each batch keeps its own quantity and expiry date." : "Try another search term or select a different status filter."}</p>
            {rows.length === 0 && asArray(products).length > 0 ? (
              <button type="button" className="bm-button bm-button-primary" onClick={onAddBatch}><Plus size={16} /> Register first batch</button>
            ) : (
              <button type="button" className="bm-button bm-button-light" onClick={() => { setSearch(""); setFilter("all"); }}>Clear filters</button>
            )}
          </div>
        )}

        <div className="bm-footer"><span>Showing {filteredRows.length} of {rows.length} batches</span><span>Near expiry = 7 days or less</span></div>
      </section>

      <div className="bm-info-note">
        <AlertTriangle size={17} />
        <p><strong>Expiry handling:</strong> Batches with a remaining quantity of zero are marked Depleted. Other batches are flagged as Expired after their expiry date or Near expiry within 7 days. Sales transactions deduct eligible stock using FEFO. Batch editing and deletion are not available in the current backend workflow.</p>
      </div>
    </div>
  );
}
