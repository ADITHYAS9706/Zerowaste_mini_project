
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL?.trim();
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();

if (!supabaseUrl || !supabaseKey) {
  throw new Error(
    "Supabase URL or publishable key is missing. Check frontend/.env"
  );
}

if (!supabaseUrl.startsWith("https://")) {
  throw new Error("Invalid Supabase URL. It must start with https://");
}

export const supabase = createClient(
  supabaseUrl,
  supabaseKey
);
