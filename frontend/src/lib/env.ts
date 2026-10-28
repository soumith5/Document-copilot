const requiredEnvVars = {
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
    VITE_SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
  } satisfies Record<string, string | undefined>
  
  const missing = Object.entries(requiredEnvVars)
    .filter(([, value]) => !value)
    .map(([key]) => key)
  
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variable(s): ${missing.join(", ")}. ` +
        `Check frontend/.env against frontend/.env.example.`
    )
  }
  
  export const env = Object.freeze({
    apiBaseUrl: requiredEnvVars.VITE_API_BASE_URL as string,
    supabaseUrl: requiredEnvVars.VITE_SUPABASE_URL as string,
    supabaseAnonKey: requiredEnvVars.VITE_SUPABASE_ANON_KEY as string,
  })