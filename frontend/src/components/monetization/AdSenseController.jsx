import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { API_BASE } from "../../lib/demoState.js";
import { apiFetch } from "../../lib/apiClient.js";

const SCRIPT_SELECTOR = 'script[data-codeleaf-adsense="true"]';

// Auto ads are limited to public learning/content routes. In particular, the
// script is never loaded on billing, account, portfolio, code-running, or exam
// screens. Entitlement status is read from the server, never local storage.
function isAdSafeRoute(pathname) {
  return (
    pathname === "/" ||
    pathname === "/tutorials" ||
    /^\/courses\/[^/]+$/.test(pathname) ||
    /^\/learn\/[^/]+(?:\/[^/]+)?$/.test(pathname) ||
    pathname === "/references" ||
    /^\/reference\/[^/]+(?:\/[^/]+)?$/.test(pathname) ||
    /^\/references\/[^/]+(?:\/[^/]+)?$/.test(pathname)
  );
}

function loadAdSense() {
  if (document.querySelector(SCRIPT_SELECTOR)) return;
  const account = document.querySelector('meta[name="google-adsense-account"]')?.content;
  if (!account || !/^ca-pub-[0-9]+$/.test(account)) return;
  const script = document.createElement("script");
  script.async = true;
  script.crossOrigin = "anonymous";
  script.dataset.codeleafAdsense = "true";
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(account)}`;
  script.onerror = () => script.remove();
  document.head.appendChild(script);
}

export default function AdSenseController() {
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;
    const routeSafe = isAdSafeRoute(location.pathname);

    async function refresh() {
      const scriptAlreadyLoaded = Boolean(document.querySelector(SCRIPT_SELECTOR));
      // Auto ads can remain active after an SPA navigation. Reload the new
      // destination without the script rather than allowing ads on sensitive
      // pages or after a paid no-ads entitlement takes effect.
      if (!routeSafe && scriptAlreadyLoaded) {
        window.location.reload();
        return;
      }

      let adsAllowed = false;
      try {
        const response = await apiFetch(`${API_BASE}/api/me/entitlements`, {
          credentials: "include",
          cache: "no-store",
        });
        if (response.status === 401) {
          // Anonymous users are Free. A failed/non-401 API request fails closed.
          adsAllowed = true;
        } else if (response.ok) {
          const snapshot = await response.json();
          adsAllowed = snapshot?.features?.ad_free !== true;
        }
      } catch {
        adsAllowed = false;
      }

      if (cancelled) return;
      const shouldLoad = routeSafe && adsAllowed;
      const activeScript = document.querySelector(SCRIPT_SELECTOR);
      if (activeScript && !shouldLoad) {
        window.location.reload();
      } else if (shouldLoad && !activeScript) {
        loadAdSense();
      }
    }

    void refresh();
    const onRefresh = () => void refresh();
    const onVisibility = () => {
      if (document.visibilityState === "visible") onRefresh();
    };
    window.addEventListener("focus", onRefresh);
    window.addEventListener("codeleaf:membership-changed", onRefresh);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      cancelled = true;
      window.removeEventListener("focus", onRefresh);
      window.removeEventListener("codeleaf:membership-changed", onRefresh);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [location.pathname]);

  return null;
}
