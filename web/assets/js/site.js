// The public address of the site and the contact email, from VITE_SITE_URL and VITE_CONTACT_EMAIL in .env.
export const SITE_URL = import.meta.env.VITE_SITE_URL || "https://torko.in";
export const CONTACT_EMAIL = import.meta.env.VITE_CONTACT_EMAIL || "hello@otee.dev";
export const SITE_HOST = new URL(SITE_URL).hostname;
export const CF_ANALYTICS_TOKEN = import.meta.env.VITE_CF_ANALYTICS_TOKEN || "";
