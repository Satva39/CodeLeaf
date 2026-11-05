import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../lib/apiClient.js";
import { API_BASE } from "../../lib/demoState.js";

const CACHE_TTL_MS = 30_000;
const REQUEST_TIMEOUT_MS = 12_000;

export const DEFAULT_DOG_AVATAR = {
  appearance: { breed: "classic", fur_color: "golden", eye_color: "brown" },
  equipment: {},
  catalog: [],
  achievements: [],
  owned_item_ids: [],
};

const DogAvatarContext = createContext({
  dogAvatar: DEFAULT_DOG_AVATAR,
  dogAvatarLoading: false,
  dogAvatarError: "",
  refreshDogAvatar: async () => DEFAULT_DOG_AVATAR,
  updateDogAvatar: () => {},
});

function normalizeDogAvatar(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const equipment = source.equipment && typeof source.equipment === "object" && !Array.isArray(source.equipment)
    ? { ...source.equipment }
    : {};
  // Compatibility with historical records that could have a jacket and full
  // outfit enabled simultaneously. A shirt/jacket is the user's active choice.
  if (equipment.shirt && equipment.outfit) delete equipment.outfit;
  return {
    ...DEFAULT_DOG_AVATAR,
    ...source,
    appearance: { ...DEFAULT_DOG_AVATAR.appearance, ...(source.appearance || {}) },
    equipment,
    catalog: Array.isArray(source.catalog) ? source.catalog : [],
    achievements: Array.isArray(source.achievements) ? source.achievements : [],
    owned_item_ids: Array.isArray(source.owned_item_ids) ? source.owned_item_ids : [],
  };
}

export function DogAvatarProvider({ children }) {
  const [dogAvatar, setDogAvatar] = useState(DEFAULT_DOG_AVATAR);
  const [dogAvatarLoading, setDogAvatarLoading] = useState(true);
  const [dogAvatarError, setDogAvatarError] = useState("");
  const dogAvatarRef = useRef(DEFAULT_DOG_AVATAR);
  const requestVersion = useRef(0);
  const lastLoadedAt = useRef(0);
  const inFlightRequest = useRef(null);

  const refreshDogAvatar = useCallback(async ({ force = false } = {}) => {
    const now = Date.now();
    if (!force && lastLoadedAt.current && now - lastLoadedAt.current < CACHE_TTL_MS) {
      return dogAvatarRef.current;
    }
    if (inFlightRequest.current) return inFlightRequest.current;

    const version = ++requestVersion.current;
    const controller = new AbortController();
    const timeoutHandle = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    setDogAvatarLoading(!lastLoadedAt.current);
    setDogAvatarError("");

    const request = (async () => {
      try {
        const response = await apiFetch(`${API_BASE}/api/me/avatar`, {
          credentials: "include",
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({}));

        if (response.status === 401) {
          if (version === requestVersion.current) {
            dogAvatarRef.current = DEFAULT_DOG_AVATAR;
            setDogAvatar(DEFAULT_DOG_AVATAR);
            lastLoadedAt.current = Date.now();
            setDogAvatarError("");
          }
          return DEFAULT_DOG_AVATAR;
        }
        if (!response.ok) {
          const message = typeof payload.detail === "string"
            ? payload.detail
            : `Your profile dog could not be loaded (HTTP ${response.status}).`;
          throw new Error(message);
        }

        const next = normalizeDogAvatar(payload);
        if (version === requestVersion.current) {
          dogAvatarRef.current = next;
          setDogAvatar(next);
          lastLoadedAt.current = Date.now();
          setDogAvatarError("");
        }
        return next;
      } catch (error) {
        if (version === requestVersion.current) {
          const message = controller.signal.aborted
            ? `Your profile dog request timed out after ${Math.round(REQUEST_TIMEOUT_MS / 1000)} seconds.`
            : error?.message || "Your profile dog could not be loaded.";
          setDogAvatarError(message);
          // Keep the last good dog visible instead of replacing it with a blank
          // default avatar during a transient API or network failure.
        }
        return dogAvatarRef.current;
      } finally {
        window.clearTimeout(timeoutHandle);
        if (inFlightRequest.current === request) inFlightRequest.current = null;
        if (version === requestVersion.current) setDogAvatarLoading(false);
      }
    })();

    inFlightRequest.current = request;
    return request;
  }, []);

  const updateDogAvatar = useCallback((next) => {
    // A confirmed mutation supersedes any older in-flight GET response.
    requestVersion.current += 1;
    inFlightRequest.current = null;
    const current = dogAvatarRef.current;
    const merged = normalizeDogAvatar({
      ...current,
      ...(next || {}),
      appearance: { ...current.appearance, ...(next?.appearance || {}) },
      equipment: next?.equipment && typeof next.equipment === "object"
        ? next.equipment
        : current.equipment,
    });
    dogAvatarRef.current = merged;
    lastLoadedAt.current = Date.now();
    setDogAvatar(merged);
    setDogAvatarError("");
    setDogAvatarLoading(false);
    return merged;
  }, []);

  useEffect(() => {
    void refreshDogAvatar({ force: true });
    const handleAuthChange = (event) => {
      requestVersion.current += 1;
      inFlightRequest.current = null;
      lastLoadedAt.current = 0;
      dogAvatarRef.current = DEFAULT_DOG_AVATAR;
      setDogAvatar(DEFAULT_DOG_AVATAR);
      setDogAvatarError("");
      if (event?.detail?.authenticated === false) {
        setDogAvatarLoading(false);
      } else {
        void refreshDogAvatar({ force: true });
      }
    };
    const handleAvatarChange = (event) => {
      if (event?.detail?.dogAvatar) updateDogAvatar(event.detail.dogAvatar);
      else void refreshDogAvatar({ force: true });
    };
    window.addEventListener("codeleaf:auth-changed", handleAuthChange);
    window.addEventListener("codeleaf:dog-avatar-changed", handleAvatarChange);
    return () => {
      window.removeEventListener("codeleaf:auth-changed", handleAuthChange);
      window.removeEventListener("codeleaf:dog-avatar-changed", handleAvatarChange);
      requestVersion.current += 1;
    };
  }, [refreshDogAvatar, updateDogAvatar]);

  const value = useMemo(() => ({
    dogAvatar,
    dogAvatarLoading,
    dogAvatarError,
    refreshDogAvatar,
    updateDogAvatar,
  }), [dogAvatar, dogAvatarLoading, dogAvatarError, refreshDogAvatar, updateDogAvatar]);

  return <DogAvatarContext.Provider value={value}>{children}</DogAvatarContext.Provider>;
}

export function useDogAvatar() {
  return useContext(DogAvatarContext);
}
