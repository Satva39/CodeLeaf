import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Code2,
  Compass,
  Crown,
  LogIn,
  Menu,
  Moon,
  Search,
  Sparkles,
  Sun,
  Terminal,
  UserRound,
  X,
} from "lucide-react";
import { useCourseCatalogState } from "../../lib/useCourseCatalog.js";
import { loadBookmarkState, resetBookmarkState } from "../../lib/bookmarkState.js";
import { API_BASE, getProfile, writeDemo } from "../../lib/demoState.js";
import { apiGetJson, invalidateApiCache } from "../../lib/apiCache.js";

export function Avatar({ size = "md", variant }) {
  const profile = getProfile();
  const v = variant || profile.avatar || "spark";
  return (
    <span
      className={`avatar avatar-${size} avatar-${v}`}
      aria-label="Profile avatar"
    >
      {v === "spark" ? (
        <Sparkles size={size === "sm" ? 15 : 22} />
      ) : v === "orbit" ? (
        <Compass size={size === "sm" ? 15 : 22} />
      ) : v === "code" ? (
        <Code2 size={size === "sm" ? 15 : 22} />
      ) : (
        <UserRound size={size === "sm" ? 15 : 22} />
      )}
    </span>
  );
}

export function Brand() {
  return (
    <Link className="brand" to="/" aria-label="CodeLeaf home">
      <span className="brand-mark">
        <Code2 size={22} />
      </span>
      <span>
        codeleaf<span className="brand-dot">.</span>
      </span>
    </Link>
  );
}

export function Header() {
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dark, setDark] = useState(() => getProfile().theme !== "light");
  // null means the session check is still in progress. This avoids briefly showing
  // the Sign in action to a returning signed-in user while /api/me is loading.
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const { courses } = useCourseCatalogState();
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    setSearchOpen(false);
    setMobileOpen(false);
  }, [location.pathname]);
  useEffect(() => {
    let active = true;
    let sessionRequestVersion = 0;
    async function checkSession() {
      const version = ++sessionRequestVersion;
      try {
        await apiGetJson(`${API_BASE}/api/me`, { credentials: "include", ttlMs: 10_000 });
        if (active && version === sessionRequestVersion) setIsAuthenticated(true);
      } catch (error) {
        if (active && version === sessionRequestVersion) setIsAuthenticated(error?.status === 401 ? false : null);
      }
    }
    const recheck = () => {
      // Clear user-scoped reads and prevent a late pre-transition response from
      // changing the session indicator after sign-in/sign-out.
      sessionRequestVersion += 1;
      invalidateApiCache("/api/me");
      resetBookmarkState();
      void loadBookmarkState();
      setIsAuthenticated(null);
      checkSession();
    };
    checkSession();
    window.addEventListener("codeleaf:auth-changed", recheck);
    return () => {
      active = false;
      window.removeEventListener("codeleaf:auth-changed", recheck);
    };
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return courses.filter((course) =>
      `${course.title} ${course.desc} ${course.category} ${course.level} ${course.slug}`.toLowerCase().includes(q),
    ).slice(0, 5);
  }, [query, courses]);
  const openFirst = () => {
    if (results[0]) navigate(`/courses/${encodeURIComponent(results[0].slug)}`);
    else if (query.trim())
      navigate(`/tutorials?q=${encodeURIComponent(query.trim())}`);
    setSearchOpen(false);
  };
  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <button
            className="icon-button mobile-menu-button"
            aria-label="Open navigation"
            onClick={() => setMobileOpen((v) => !v)}
          >
            <Menu size={21} />
          </button>
          <Brand />
          <nav
            className={`primary-nav ${mobileOpen ? "primary-nav-open" : ""}`}
            aria-label="Main navigation"
          >
            <NavLink to="/tutorials">
              Tutorials <ChevronDown size={13} />
            </NavLink>
            <NavLink to="/references">
              References <ChevronDown size={13} />
            </NavLink>
            <NavLink to="/projects">Projects</NavLink>
            <NavLink to="/practice">Practice</NavLink>
            <NavLink to="/review">Review</NavLink>
            <NavLink to="/learning-hub">Learning hub</NavLink>
            <NavLink to="/portfolio">Portfolio</NavLink>
            <NavLink to="/certificates">Certificates</NavLink>
          </nav>
          <div className="header-search">
            <Search size={16} />
            <input
              aria-label="Search tutorials"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSearchOpen(true);
              }}
              onFocus={() => setSearchOpen(true)}
              onKeyDown={(e) => {
                if (e.key === "Enter") openFirst();
                if (e.key === "Escape") setSearchOpen(false);
              }}
              placeholder="Search tutorials..."
            />
            {query && (
              <button
                className="search-clear"
                aria-label="Clear search"
                onClick={() => {
                  setQuery("");
                  setSearchOpen(false);
                }}
              >
                <X size={14} />
              </button>
            )}
            {searchOpen && query.trim() && (
              <div className="search-results">
                {results.map((c) => (
                  <button
                    key={c.slug}
                    onClick={() => {
                      navigate(`/courses/${encodeURIComponent(c.slug)}`);
                      setSearchOpen(false);
                    }}
                  >
                    <span
                      className="course-mini-icon"
                      style={{ color: c.color }}
                    >
                      {c.icon}
                    </span>
                    <span>
                      <strong>{c.title}</strong>
                      <small>{c.desc}</small>
                    </span>
                    <ChevronRight size={15} />
                  </button>
                ))}
                {!results.length && (
                  <div className="search-no-results">
                    No matching courses. Press Enter to search the catalog.
                  </div>
                )}
                <button
                  className="search-all"
                  onClick={() => {
                    navigate(`/tutorials?q=${encodeURIComponent(query)}`);
                    setSearchOpen(false);
                  }}
                >
                  Search all learning content <ArrowRight size={14} />
                </button>
              </div>
            )}
          </div>
          <div className="header-actions">
            <NavLink className="spaces-link" to="/playground">
              <Terminal size={16} /> Playground
            </NavLink>
            {isAuthenticated === false && (
              <NavLink className="signin-link" to="/login">
                <LogIn size={15} /> Sign in
              </NavLink>
            )}
            <NavLink to="/plans" className="upgrade-button">
              <Crown size={15} /> Upgrade
            </NavLink>
            <button
              className="icon-button theme-button"
              aria-label={`Switch to ${dark ? "light" : "dark"} theme`}
              onClick={() => {
                setDark((v) => {
                  const n = !v;
                  writeDemo({
                    profile: { ...getProfile(), theme: n ? "dark" : "light" },
                  });
                  return n;
                });
              }}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <Link
              to="/profile"
              className="avatar-link"
              aria-label="Open profile"
            >
              <Avatar size="sm" />
            </Link>
          </div>
        </div>
      </header>
      <div className="topicbar">
        <div className="topicbar-inner">
          {[
            "HTML",
            "CSS",
            "JavaScript",
            "Python",
            "Flask",
            "SQL",
            "React",
            "C++",
            "Java",
            "PostgreSQL",
            "Git",
            "Docker",
            "AI",
          ].map((name) => {
            const slug = name
              .toLowerCase()
              .replace("++", "pp")
              .replace(" ", "");
            const found = courses.find(
              (course) => course.title.toLowerCase() === name.toLowerCase() || course.slug === slug,
            );
            return (
              <Link key={name} to={found ? `/courses/${encodeURIComponent(found.slug)}` : "/tutorials"}>
                {name}
              </Link>
            );
          })}
          <Link className="all-topics" to="/tutorials">
            All topics <ArrowRight size={13} />
          </Link>
        </div>
      </div>
    </>
  );
}
