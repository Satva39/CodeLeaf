import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../lib/apiClient.js";
import { API_BASE } from "../../lib/demoState.js";

const DEFAULT_DOG_AVATAR = {
  appearance: { breed: "classic", fur_color: "golden", eye_color: "brown" },
  equipment: {},
  catalog: [],
  achievements: [],
  owned_item_ids: [],
};

const DogAvatarContext = createContext({
  dogAvatar: DEFAULT_DOG_AVATAR,
  dogAvatarLoading: false,
  refreshDogAvatar: async () => DEFAULT_DOG_AVATAR,
  updateDogAvatar: () => {},
});

export function DogAvatarProvider({ children }) {
  const [dogAvatar, setDogAvatar] = useState(DEFAULT_DOG_AVATAR);
  const [dogAvatarLoading, setDogAvatarLoading] = useState(true);
  const requestVersion = useRef(0);

  const refreshDogAvatar = useCallback(async () => {
    const version = ++requestVersion.current;
    setDogAvatarLoading(true);
    try {
      const response = await apiFetch(`${API_BASE}/api/me/avatar`, { credentials: "include" });
      if (response.status === 401) {
        if (version === requestVersion.current) setDogAvatar(DEFAULT_DOG_AVATAR);
        return DEFAULT_DOG_AVATAR;
      }
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Dog avatar could not be loaded.");
      }
      const next = {
        ...DEFAULT_DOG_AVATAR,
        ...payload,
        appearance: { ...DEFAULT_DOG_AVATAR.appearance, ...(payload.appearance || {}) },
        equipment: payload.equipment && typeof payload.equipment === "object" ? payload.equipment : {},
      };
      if (version === requestVersion.current) setDogAvatar(next);
      return next;
    } catch {
      // Keep the last known/default dog visible during temporary API outages.
      return DEFAULT_DOG_AVATAR;
    } finally {
      if (version === requestVersion.current) setDogAvatarLoading(false);
    }
  }, []);

  const updateDogAvatar = useCallback((next) => {
    setDogAvatar((current) => ({
      ...current,
      ...(next || {}),
      appearance: { ...current.appearance, ...(next?.appearance || {}) },
      equipment: next?.equipment && typeof next.equipment === "object" ? next.equipment : current.equipment,
    }));
  }, []);

  useEffect(() => {
    void refreshDogAvatar();
    const handleAuthChange = (event) => {
      // Invalidate in-flight reads so a previous account's dog cannot appear
      // after logout or while switching to another signed-in account.
      requestVersion.current += 1;
      setDogAvatar(DEFAULT_DOG_AVATAR);
      if (event?.detail?.authenticated === false) {
        setDogAvatarLoading(false);
      } else {
        void refreshDogAvatar();
      }
    };
    const handleAvatarChange = (event) => {
      if (event?.detail?.dogAvatar) updateDogAvatar(event.detail.dogAvatar);
      else void refreshDogAvatar();
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
    refreshDogAvatar,
    updateDogAvatar,
  }), [dogAvatar, dogAvatarLoading, refreshDogAvatar, updateDogAvatar]);

  return <DogAvatarContext.Provider value={value}>{children}</DogAvatarContext.Provider>;
}

export function useDogAvatar() {
  return useContext(DogAvatarContext);
}

export { DEFAULT_DOG_AVATAR };
