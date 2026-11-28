import { useMemo, useState } from "react";
import {
  Barcode,
  Boxes,
  Check,
  ChevronDown,
  Pencil,
  Filter,
  Package,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import "./ProductManagement.css";

function normalise(value) {
  return String(value ?? "").trim().toLowerCase().replace(/\s+/g, " ");
}

function productBarcode(product) {
  return product?.barcode ?? product?.barcode_number ?? product?.bar_code ?? "";
}

function productId(product) {
  return product?.product_id ?? product?.id;
}

function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || "Invalid value").join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  if (error?.response?.status === 404) return "Product endpoint was not found. Check the FastAPI route.";
  if (error?.response?.status === 405) return "This product action is not enabled by the backend yet.";
  return error?.message || "The request could not be completed. Please try again.";
}

function formatPrice(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? `₹${amount.toFixed(2)}` : "—";
}

function ProductForm({ initialProduct, onCancel, onSave, saving, error }) {
  const [values, setValues] = useState(() => ({
    product_name: initialProduct?.product_name ?? "",
    category: initialProduct?.category ?? "",
    barcode: productBarcode(initialProduct),
    unit: initialProduct?.unit ?? "",
    unit_price: initialProduct?.unit_price ?? "",
    base_daily_demand: initialProduct?.base_daily_demand ?? "",
  }));

  function update(name, value) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  function submit(event) {
    event.preventDefault();
    onSave({
      product_name: values.product_name.trim(),
      category: values.category.trim(),
      unit: values.unit.trim(),
      unit_price: values.unit_price === "" ? 0 : Number(values.unit_price),
      base_daily_demand:
        values.base_daily_demand === "" ? null : Number(values.base_daily_demand),
      ...(values.barcode.trim() ? { barcode: values.barcode.trim() } : {}),
    });
  }

  return (
    <div className="pm-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onCancel()}>
      <section className="pm-modal" role="dialog" aria-modal="true" aria-labelledby="pm-form-title">
        <div className="pm-modal-heading">
          <div className="pm-modal-icon"><Package size={20} /></div>
          <div>
            <span className="pm-eyebrow">PRODUCT CATALOGUE</span>
            <h3 id="pm-form-title">{initialProduct ? "Edit product" : "Register a product"}</h3>
            <p>Enter the reusable details for this product. Stock quantities are tracked separately in Batches and Inventory.</p>
          </div>
          <button type="button" className="pm-icon-button" onClick={onCancel} aria-label="Close form"><X size={19} /></button>
        </div>

        <form onSubmit={submit}>
          <div className="pm-form-grid">
            <label className="pm-field pm-field-wide">
              <span>Product name <b>*</b></span>
              <input autoFocus required minLength={2} maxLength={120} value={values.product_name} onChange={(event) => update("product_name", event.target.value)} placeholder="e.g. Fresh Apples" />
            </label>
            <label className="pm-field">
              <span>Category <b>*</b></span>
              <input required minLength={2} maxLength={60} value={values.category} onChange={(event) => update("category", event.target.value)} placeholder="e.g. Fruits" />
            </label>
            <label className="pm-field">
              <span>Barcode</span>
              <input maxLength={80} value={values.barcode} onChange={(event) => update("barcode", event.target.value)} placeholder="Scan or enter barcode" />
              <small>Optional. A barcode must be unique when supplied.</small>
            </label>
            <label className="pm-field">
              <span>Stock unit <b>*</b></span>
              <input required maxLength={30} value={values.unit} onChange={(event) => update("unit", event.target.value)} placeholder="e.g. kg, pieces, litre" />
            </label>
            <label className="pm-field">
              <span>Unit price (₹)</span>
              <input type="number" min="0" step="0.01" value={values.unit_price} onChange={(event) => update("unit_price", event.target.value)} placeholder="0.00" />
            </label>
            <label className="pm-field">
              <span>Base daily demand</span>
              <input type="number" min="0" step="0.01" value={values.base_daily_demand} onChange={(event) => update("base_daily_demand", event.target.value)} placeholder="Optional" />
              <small>Used as a starting point for demand forecasting.</small>
            </label>
          </div>

          {error && <div className="pm-form-error" role="alert">{error}</div>}
          <div className="pm-modal-actions">
            <button type="button" className="pm-button pm-button-light" onClick={onCancel} disabled={saving}>Cancel</button>
            <button type="submit" className="pm-button pm-button-primary" disabled={saving}>
              {saving ? "Saving…" : <><Check size={16} /> {initialProduct ? "Save changes" : "Register product"}</>}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function DeleteConfirmation({ product, onCancel, onConfirm, saving, error }) {
  return (
    <div className="pm-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onCancel()}>
      <section className="pm-confirm-modal" role="alertdialog" aria-modal="true" aria-labelledby="pm-delete-title">
        <div className="pm-delete-icon"><Trash2 size={22} /></div>
        <h3 id="pm-delete-title">Delete this product?</h3>
        <p><strong>{product?.product_name}</strong> will be removed from the product catalogue. This action may be blocked if batches or inventory still reference it.</p>
        {error && <div className="pm-form-error" role="alert">{error}</div>}
        <div className="pm-modal-actions">
          <button className="pm-button pm-button-light" type="button" onClick={onCancel} disabled={saving}>Cancel</button>
          <button className="pm-button pm-button-danger" type="button" onClick={onConfirm} disabled={saving}>{saving ? "Deleting…" : "Delete product"}</button>
        </div>
      </section>
    </div>
  );
}

export default function ProductManagement({ products = [], onCreate, onUpdate, onDelete }) {
  const safeProducts = Array.isArray(products) ? products : [];
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [formMode, setFormMode] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [actionNotice, setActionNotice] = useState("");

  const categories = useMemo(() => [...new Set(safeProducts.map((item) => String(item.category ?? "").trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b)), [safeProducts]);
  const filteredProducts = useMemo(() => {
    const query = normalise(search);
    return safeProducts.filter((product) => {
      const searchText = [product.product_id, product.product_name, product.category, productBarcode(product), product.unit].map((value) => normalise(value)).join(" ");
      const matchesSearch = !query || searchText.includes(query);
      const matchesCategory = categoryFilter === "all" || product.category === categoryFilter;
      return matchesSearch && matchesCategory;
    });
  }, [safeProducts, search, categoryFilter]);

  const barcodeCount = safeProducts.filter((item) => normalise(productBarcode(item))).length;
  const categoryCount = categories.length;

  function openCreate() {
    setSelectedProduct(null);
    setFormError("");
    setFormMode("create");
  }

  function openEdit(product) {
    setSelectedProduct(product);
    setFormError("");
    setFormMode("edit");
  }

  function closeForm() {
    if (saving) return;
    setFormMode(null);
    setSelectedProduct(null);
    setFormError("");
  }

  async function saveProduct(payload) {
    const currentId = formMode === "edit" ? String(productId(selectedProduct)) : "";
    const payloadBarcode = normalise(payload.barcode);
    const duplicate = safeProducts.find((product) => {
      if (formMode === "edit" && String(productId(product)) === currentId) return false;
      const existingBarcode = normalise(productBarcode(product));
      const sameBarcode = payloadBarcode && existingBarcode === payloadBarcode;
      const sameProductDetails =
        normalise(product.product_name) === normalise(payload.product_name) &&
        normalise(product.category) === normalise(payload.category) &&
        normalise(product.unit) === normalise(payload.unit);
      return sameBarcode || sameProductDetails;
    });

    if (duplicate) {
      setFormError(payloadBarcode && normalise(productBarcode(duplicate)) === payloadBarcode
        ? "A product with this barcode is already registered."
        : "A product with the same name, category and unit already exists.");
      return;
    }

    setSaving(true);
    setFormError("");
    setActionNotice("");
    try {
      if (formMode === "edit") {
        await onUpdate(productId(selectedProduct), payload);
        setActionNotice("Product details updated.");
      } else {
        await onCreate(payload);
        setActionNotice("Product registered successfully.");
      }
      setFormMode(null);
      setSelectedProduct(null);
    } catch (error) {
      setFormError(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setSaving(true);
    setFormError("");
    try {
      await onDelete(productId(deleteTarget));
      setDeleteTarget(null);
      setActionNotice("Product deleted.");
    } catch (error) {
      setFormError(getErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="product-management">
      <section className="pm-page-heading">
        <div>
          <span className="pm-eyebrow">MANAGER WORKSPACE / CATALOGUE</span>
          <h2>Product management</h2>
          <p>Maintain the products your store sells. Add incoming quantities and expiry dates in the Batches section.</p>
        </div>
        <button type="button" className="pm-button pm-button-primary pm-add-button" onClick={openCreate}><Plus size={17} /> Add product</button>
      </section>

      <section className="pm-stats-grid" aria-label="Product summary">
        <article className="pm-stat-card"><span className="pm-stat-icon green"><Package size={19} /></span><div><small>Total products</small><strong>{safeProducts.length.toLocaleString("en-IN")}</strong><span>Registered catalogue items</span></div></article>
        <article className="pm-stat-card"><span className="pm-stat-icon blue"><Boxes size={19} /></span><div><small>Categories</small><strong>{categoryCount.toLocaleString("en-IN")}</strong><span>Distinct product categories</span></div></article>
        <article className="pm-stat-card"><span className="pm-stat-icon purple"><Barcode size={19} /></span><div><small>Barcodes assigned</small><strong>{barcodeCount.toLocaleString("en-IN")}</strong><span>Products with a barcode value</span></div></article>
      </section>

      <section className="pm-catalogue panel">
        <div className="pm-catalogue-heading">
          <div><h3>Product catalogue</h3><p>Search by product, category, barcode or stock unit.</p></div>
          <span className="pm-results-count">{filteredProducts.length} of {safeProducts.length} products</span>
        </div>
        <div className="pm-filters">
          <label className="pm-search search-box"><Search size={17} /><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products…" aria-label="Search products" /></label>
          <label className="pm-category-filter"><Filter size={16} /><select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)} aria-label="Filter by category"><option value="all">All categories</option>{categories.map((category) => <option key={category} value={category}>{category}</option>)}</select><ChevronDown size={15} /></label>
        </div>

        {filteredProducts.length > 0 ? (
          <>
            <div className="pm-desktop-table table-wrap">
              <table>
                <thead><tr><th>Product</th><th>Barcode</th><th>Stock unit</th><th>Unit price</th><th>Daily demand</th><th className="pm-actions-heading">Actions</th></tr></thead>
                <tbody>{filteredProducts.map((product, index) => (
                  <tr key={productId(product) ?? `${product.product_name}-${index}`}>
                    <td><div className="pm-product-cell"><span className="pm-product-avatar"><Package size={17} /></span><span><strong>{product.product_name || "Unnamed product"}</strong><small>{product.category || "Uncategorised"} · ID {productId(product) ?? "—"}</small></span></div></td>
                    <td>{productBarcode(product) ? <span className="pm-barcode-value"><Barcode size={14} /> {productBarcode(product)}</span> : <span className="pm-muted">Not assigned</span>}</td>
                    <td><span className="pm-unit-pill">{product.unit || "—"}</span></td>
                    <td><strong className="pm-price">{formatPrice(product.unit_price)}</strong></td>
                    <td>{product.base_daily_demand ?? "—"}</td>
                    <td><div className="pm-row-actions"><button type="button" className="pm-row-button" onClick={() => openEdit(product)} aria-label={`Edit ${product.product_name}`} title="Edit product"><Pencil size={16} /></button><button type="button" className="pm-row-button danger" onClick={() => { setFormError(""); setDeleteTarget(product); }} aria-label={`Delete ${product.product_name}`} title="Delete product"><Trash2 size={16} /></button></div></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            <div className="pm-mobile-list">
              {filteredProducts.map((product, index) => (
                <article className="pm-mobile-card" key={productId(product) ?? `${product.product_name}-${index}`}>
                  <div className="pm-mobile-card-heading"><span className="pm-product-avatar"><Package size={17} /></span><div><strong>{product.product_name || "Unnamed product"}</strong><small>{product.category || "Uncategorised"}</small></div><span className="pm-price">{formatPrice(product.unit_price)}</span></div>
                  <div className="pm-mobile-details"><span><small>Barcode</small><strong>{productBarcode(product) || "Not assigned"}</strong></span><span><small>Stock unit</small><strong>{product.unit || "—"}</strong></span><span><small>Daily demand</small><strong>{product.base_daily_demand ?? "—"}</strong></span></div>
                  <div className="pm-mobile-actions"><button type="button" className="pm-button pm-button-light" onClick={() => openEdit(product)}><Pencil size={15} /> Edit</button><button type="button" className="pm-button pm-button-danger-light" onClick={() => { setFormError(""); setDeleteTarget(product); }}><Trash2 size={15} /> Delete</button></div>
                </article>
              ))}
            </div>
          </>
        ) : (
          <div className="pm-empty-state"><span><Package size={25} /></span><strong>{safeProducts.length === 0 ? "No products registered yet" : "No matching products"}</strong><p>{safeProducts.length === 0 ? "Register your first product to start building the store catalogue." : "Try another search term or category filter."}</p>{safeProducts.length === 0 ? <button type="button" className="pm-button pm-button-primary" onClick={openCreate}><Plus size={16} /> Register first product</button> : <button type="button" className="pm-button pm-button-light" onClick={() => { setSearch(""); setCategoryFilter("all"); }}>Clear filters</button>}</div>
        )}
      </section>

      <div className="pm-help-note"><Barcode size={17} /><p><strong>Product vs. batch:</strong> Register a product once. Each time new stock arrives, create a separate batch with its received quantity, manufacturing date and expiry date.</p></div>
      {actionNotice && <div className="pm-inline-success" role="status"><Check size={15} /> {actionNotice}<button type="button" onClick={() => setActionNotice("")} aria-label="Dismiss message"><X size={15} /></button></div>}

      {formMode && <ProductForm key={`${formMode}-${productId(selectedProduct) ?? "new"}`} initialProduct={selectedProduct} onCancel={closeForm} onSave={saveProduct} saving={saving} error={formError} />}
      {deleteTarget && <DeleteConfirmation product={deleteTarget} onCancel={() => !saving && setDeleteTarget(null)} onConfirm={confirmDelete} saving={saving} error={formError} />}
    </div>
  );
}
