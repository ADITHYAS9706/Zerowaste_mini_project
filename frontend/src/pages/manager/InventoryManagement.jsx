import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownToLine,
  CalendarClock,
  ChevronRight,
  CircleCheck,
  Package,
  Search,
  SlidersHorizontal,
  Warehouse,
} from "lucide-react";
import "./InventoryManagement.css";

const FILTERS = [
  { id: "all", label: "All stock" },
  { id: "low", label: "Low stock" },
  { id: "near", label: "Near expiry" },
  { id: "expired", label: "Expired" },
];

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function getDaysUntilExpiry(value) {
  if (!value) return null;
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((date.getTime() - today.getTime()) / 86400000);
}

function formatDate(value) {
  if (!value) return "Date not recorded";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function quantity(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString("en-IN") : "—";
}

function getKey(value) {
  return value === null || value === undefined ? "" : String(value);
}

function buildInventoryRows(data) {
  const inventory = asArray(data.inventory);
  const products = asArray(data.products);
  const stores = asArray(data.stores);
  const batches = asArray(data.batches);

  const productById = new Map(products.map((item) => [getKey(item.product_id), item]));
  const storeById = new Map(stores.map((item) => [getKey(item.store_id), item]));

  return inventory.map((item, index) => {
    const product = productById.get(getKey(item.product_id));
    const store = storeById.get(getKey(item.store_id));
    const matchingBatches = batches
      .filter((batch) => {
        const sameProduct = getKey(batch.product_id) === getKey(item.product_id);
        const batchStore = getKey(batch.store_id);
        const inventoryStore = getKey(item.store_id);
        const sameStore = !batchStore || !inventoryStore || batchStore === inventoryStore;
        return sameProduct && sameStore && Number(batch.quantity_remaining ?? 0) > 0;
      })
      .map((batch) => ({ ...batch, daysLeft: getDaysUntilExpiry(batch.expiry_date) }))
      .sort((a, b) => {
        if (a.daysLeft === null) return 1;
        if (b.daysLeft === null) return -1;
        return a.daysLeft - b.daysLeft;
      });

    const nearBatches = matchingBatches.filter(
      (batch) => batch.daysLeft !== null && batch.daysLeft >= 0 && batch.daysLeft <= 7
    );
    const expiredBatches = matchingBatches.filter(
      (batch) => batch.daysLeft !== null && batch.daysLeft < 0
    );
    const nearestBatch = matchingBatches.find((batch) => batch.daysLeft !== null);

    return {
      ...item,
      _key: `${getKey(item.store_id)}-${getKey(item.product_id)}-${index}`,
      _productName: product?.product_name || item.product_name || `Product ${item.product_id ?? "—"}`,
      _category: product?.category || item.category || "Uncategorised",
      _unit: product?.unit || item.unit || "units",
      _storeName: store?.store_name || item.store_name || `Store ${item.store_id ?? "—"}`,
      _batches: matchingBatches,
      _nearBatches: nearBatches,
      _expiredBatches: expiredBatches,
      _nearestBatch: nearestBatch,
      _quantity: Number(item.available_quantity ?? 0),
    };
  });
}

function Status({ row, threshold }) {
  if (row._quantity <= threshold) {
    return <span className="inv-status low">Low stock</span>;
  }
  if (row._expiredBatches.length > 0) {
    return <span className="inv-status expired">Expired stock</span>;
  }
  if (row._nearBatches.length > 0) {
    return <span className="inv-status near">Near expiry</span>;
  }
  return <span className="inv-status healthy">In stock</span>;
}

export default function InventoryManagement({ data, onRegisterBatch, onViewBatches }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [lowStockThreshold, setLowStockThreshold] = useState(10);

  const rows = useMemo(() => buildInventoryRows(data), [data]);
  const totalUnits = rows.reduce((sum, row) => sum + (Number.isFinite(row._quantity) ? row._quantity : 0), 0);
  const lowRows = rows.filter((row) => row._quantity <= lowStockThreshold);
  const nearRows = rows.filter((row) => row._nearBatches.length > 0);
  const expiredRows = rows.filter((row) => row._expiredBatches.length > 0);

  const visibleRows = useMemo(() => {
    const key = search.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesSearch = !key || [
        row._productName,
        row._category,
        row._storeName,
        row.product_id,
        row.store_id,
      ].some((value) => String(value ?? "").toLowerCase().includes(key));

      const matchesFilter =
        filter === "all" ||
        (filter === "low" && row._quantity <= lowStockThreshold) ||
        (filter === "near" && row._nearBatches.length > 0) ||
        (filter === "expired" && row._expiredBatches.length > 0);

      return matchesSearch && matchesFilter;
    });
  }, [rows, search, filter, lowStockThreshold]);

  const filterCounts = {
    all: rows.length,
    low: lowRows.length,
    near: nearRows.length,
    expired: expiredRows.length,
  };

  return (
    <div className="inventory-management">
      <section className="inv-page-heading">
        <div>
          <span className="dashboard-eyebrow">MANAGER WORKSPACE</span>
          <h2>Inventory management</h2>
          <p>Monitor stock levels across your registered stores and review batch expiry risk.</p>
        </div>
        <button className="primary-button inv-add-button" type="button" onClick={onRegisterBatch}>
          <ArrowDownToLine size={17} /> Receive stock
        </button>
      </section>

      <section className="inv-stat-grid" aria-label="Inventory summary">
        <article className="inv-stat-card">
          <span className="inv-stat-icon green"><Package size={19} /></span>
          <span className="inv-stat-label">Inventory records</span>
          <strong>{quantity(rows.length)}</strong>
          <small>Product and store entries</small>
        </article>
        <article className="inv-stat-card">
          <span className="inv-stat-icon blue"><Warehouse size={19} /></span>
          <span className="inv-stat-label">Available units</span>
          <strong>{quantity(totalUnits)}</strong>
          <small>Sum of available quantities</small>
        </article>
        <article className="inv-stat-card">
          <span className="inv-stat-icon orange"><AlertTriangle size={19} /></span>
          <span className="inv-stat-label">Low-stock records</span>
          <strong>{quantity(lowRows.length)}</strong>
          <small>At or below {lowStockThreshold} units</small>
        </article>
        <article className="inv-stat-card">
          <span className="inv-stat-icon purple"><CalendarClock size={19} /></span>
          <span className="inv-stat-label">Expiry attention</span>
          <strong>{quantity(nearRows.length + expiredRows.length)}</strong>
          <small>{nearRows.length} near expiry · {expiredRows.length} expired</small>
        </article>
      </section>

      <section className="panel inv-records-panel">
        <div className="inv-toolbar">
          <div>
            <h3>Stock by product and store</h3>
            <p>Inventory quantities are read from the existing inventory API. Expiry details are matched from batch records.</p>
          </div>
          <label className="inv-search search-box">
            <Search size={17} />
            <input
              type="search"
              placeholder="Search product, category or store"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
        </div>

        <div className="inv-filter-toolbar">
          <div className="inv-filter-tabs" role="group" aria-label="Filter inventory">
            {FILTERS.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`inv-filter-tab ${filter === item.id ? "selected" : ""}`}
                onClick={() => setFilter(item.id)}
              >
                {item.label}<span>{filterCounts[item.id]}</span>
              </button>
            ))}
          </div>
          <label className="inv-threshold-control">
            <SlidersHorizontal size={15} />
            <span>Low-stock limit</span>
            <input
              type="number"
              min="0"
              max="999999"
              value={lowStockThreshold}
              onChange={(event) => setLowStockThreshold(Math.max(0, Number(event.target.value) || 0))}
              aria-label="Low stock threshold in units"
            />
          </label>
        </div>

        {visibleRows.length > 0 ? (
          <>
            <div className="table-wrap inv-desktop-table">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Store</th>
                    <th>Available</th>
                    <th>Expiry tracking</th>
                    <th>Stock status</th>
                    <th aria-label="Open batch details" />
                  </tr>
                </thead>
                <tbody>
                  {visibleRows.map((row) => (
                    <tr key={row._key}>
                      <td>
                        <div className="inv-product-cell">
                          <span className="inv-product-icon"><Package size={17} /></span>
                          <span><strong>{row._productName}</strong><small>{row._category} · ID {row.product_id ?? "—"}</small></span>
                        </div>
                      </td>
                      <td><span className="inv-store-name">{row._storeName}</span><small className="inv-muted">ID {row.store_id ?? "—"}</small></td>
                      <td><strong className="inv-quantity">{quantity(row._quantity)}</strong><small className="inv-muted">{row._unit}</small></td>
                      <td>
                        {row._nearestBatch ? (
                          <span className="inv-expiry-info">
                            <strong>{row._nearestBatch.daysLeft < 0 ? "Expired" : row._nearestBatch.daysLeft === 0 ? "Expires today" : formatDate(row._nearestBatch.expiry_date)}</strong>
                            <small>{row._batches.length} active batch record{row._batches.length === 1 ? "" : "s"}</small>
                          </span>
                        ) : <span className="inv-muted">No batch dates</span>}
                      </td>
                      <td><Status row={row} threshold={lowStockThreshold} /></td>
                      <td><button className="inv-row-action" type="button" onClick={onViewBatches} aria-label={`View batches for ${row._productName}`}><ChevronRight size={18} /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="inv-mobile-list">
              {visibleRows.map((row) => (
                <article className="inv-mobile-card" key={row._key}>
                  <div className="inv-mobile-card-top">
                    <span className="inv-product-icon"><Package size={17} /></span>
                    <div className="inv-mobile-product"><strong>{row._productName}</strong><small>{row._category} · ID {row.product_id ?? "—"}</small></div>
                    <Status row={row} threshold={lowStockThreshold} />
                  </div>
                  <div className="inv-mobile-details">
                    <span><small>Available</small><strong>{quantity(row._quantity)} {row._unit}</strong></span>
                    <span><small>Store</small><strong>{row._storeName}</strong></span>
                    <span><small>Nearest expiry</small><strong>{row._nearestBatch ? formatDate(row._nearestBatch.expiry_date) : "Not recorded"}</strong></span>
                  </div>
                  <button type="button" className="inv-mobile-link" onClick={onViewBatches}>View batch records <ChevronRight size={15} /></button>
                </article>
              ))}
            </div>
          </>
        ) : (
          <div className="inv-empty-state">
            <span><CircleCheck size={24} /></span>
            <strong>{rows.length === 0 ? "No inventory records yet" : "No matching inventory records"}</strong>
            <p>{rows.length === 0 ? "When inventory is recorded for a store, its product quantities will appear here." : "Try another search term or choose a different inventory filter."}</p>
            {rows.length === 0 && <button className="secondary-button" type="button" onClick={onRegisterBatch}>Register an incoming batch</button>}
            {rows.length > 0 && <button className="secondary-button" type="button" onClick={() => { setSearch(""); setFilter("all"); }}>Clear filters</button>}
          </div>
        )}

        <div className="inv-table-footer">
          <span>Showing {visibleRows.length} of {rows.length} inventory records</span>
          <button type="button" className="inv-footer-link" onClick={onViewBatches}>Review batch history <ChevronRight size={15} /></button>
        </div>
      </section>

      <div className="inv-info-note">
        <AlertTriangle size={17} />
        <p><strong>Stock update note:</strong> This screen currently reads inventory and batch data. “Receive stock” opens the existing batch registration form; direct stock adjustment and sales deduction require corresponding backend endpoints.</p>
      </div>
    </div>
  );
}
