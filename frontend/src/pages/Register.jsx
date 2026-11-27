
import { useState } from "react";
import {
  Store, User, Mail, Lock, Phone, MapPin, Eye, EyeOff
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { registerStore } from "../services/api";
import "./Register.css";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    store_name: "",
    full_name: "",
    email: "",
    password: "",
    phone: "",
    address: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    setForm((previous) => ({
      ...previous,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const response = await registerStore(form);

      setSuccess(
        `Your store has been registered successfully. Store ID: ${response.data.store_id}`
      );

      // Give the user time to read the success message.
      setTimeout(() => navigate("/login"), 2000);

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to register your store. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="register-page">
      <section className="register-card">
        <div className="register-logo">
          <Store size={32} />
        </div>

        <h1>Join ZeroWasteNet</h1>
        <p className="register-subtitle">
          Register your grocery store for free
        </p>

        <form onSubmit={handleSubmit}>
          <label>Store Name</label>
          <div className="register-input">
            <Store size={19} />
            <input
              name="store_name"
              placeholder="Enter your store name"
              value={form.store_name}
              onChange={handleChange}
              required
            />
          </div>

          <label>Owner / Manager Name</label>
          <div className="register-input">
            <User size={19} />
            <input
              name="full_name"
              placeholder="Enter your full name"
              value={form.full_name}
              onChange={handleChange}
              required
            />
          </div>

          <label>Email Address</label>
          <div className="register-input">
            <Mail size={19} />
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              required
            />
          </div>

          <label>Password</label>
          <div className="register-input">
            <Lock size={19} />
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              placeholder="Create a password (8 characters minimum)"
              value={form.password}
              onChange={handleChange}
              autoComplete="new-password"
              minLength={8}
              required
            />
            <button
              type="button"
              className="register-password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
            </button>
          </div>

          <label>Phone Number</label>
          <div className="register-input">
            <Phone size={19} />
            <input
              type="tel"
              name="phone"
              placeholder="Enter phone number"
              value={form.phone}
              onChange={handleChange}
              required
            />
          </div>

          <label>Store Address</label>
          <div className="register-input register-address">
            <MapPin size={19} />
            <textarea
              name="address"
              placeholder="Enter complete store address"
              value={form.address}
              onChange={handleChange}
              required
            />
          </div>

          {error && (
            <div className="register-error" role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className="register-success" role="status">
              {success}
            </div>
          )}

          <button
            className="register-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? "Registering..." : "Register Store for Free"}
          </button>
        </form>

        <p className="register-login">
          Already registered? <Link to="/login">Login</Link>
        </p>

        <p className="register-footer">
          ZeroWasteNet © 2026
        </p>
      </section>
    </main>
  );
}
