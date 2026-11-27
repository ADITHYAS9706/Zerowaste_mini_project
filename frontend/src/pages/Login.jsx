
import { useState } from "react";
import { Store, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { supabase } from "../services/supabase";
import "./Login.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { data, error: authError } =
        await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

      if (authError) throw authError;

      const { data: profile, error: profileError } =
        await supabase
          .from("profiles")
          .select("user_id, full_name, role, store_id, is_active")
          .eq("user_id", data.user.id)
          .single();

      if (profileError || !profile) {
        await supabase.auth.signOut();
        throw new Error("User profile not found.");
      }

      if (!profile.is_active) {
        await supabase.auth.signOut();
        throw new Error("Your account is inactive.");
      }

      if (!profile.store_id) {
        await supabase.auth.signOut();
        throw new Error("Your account is not assigned to a store.");
      }

      if (profile.role === "manager") {
        window.location.href = "/manager";
      } else if (profile.role === "staff") {
        window.location.href = "/staff";
      } else {
        await supabase.auth.signOut();
        throw new Error("Invalid account role.");
      }

    } catch (err) {
      setError(err.message || "Unable to login. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-card">

        <div className="login-logo">
          <Store size={32} />
        </div>

        <h1>ZeroWasteNet</h1>
        <p className="login-tagline">
          Smart Grocery Inventory Management
        </p>

        <div className="login-heading">
          <h2>Welcome Back</h2>
          <p>Sign in to manage your store.</p>
        </div>

        <form onSubmit={handleLogin}>

          <label>Email Address</label>
          <div className="login-input">
            <Mail size={19} />
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <label>Password</label>
          <div className="login-input">
            <Lock size={19} />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />

            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
            </button>
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="register-prompt">
          New grocery store?
          <a href="/register"> Register for free</a>
        </p>

        <p className="login-footer">
          ZeroWasteNet © 2026
        </p>

      </section>
    </main>
  );
}
