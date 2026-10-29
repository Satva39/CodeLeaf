import { Link } from "react-router-dom";
import { Brand } from "./Header.jsx";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-top">
        <Brand />
        <div className="footer-top-links">
          <Link to="/plans">Membership</Link>
          <Link to="/projects">Projects</Link>
          <Link to="/certificates">Certificates</Link>
          <Link to="/practice">Practice</Link>
          <Link to="/profile">Profile</Link>
          <Link to="/support">Support</Link>
        </div>
      </div>
      <div className="footer-columns">
        <div>
          <h4>Learn</h4>
          <Link to="/learn/html">HTML tutorial</Link>
          <Link to="/learn/css">CSS tutorial</Link>
          <Link to="/learn/javascript">JavaScript tutorial</Link>
          <Link to="/learn/python">Python tutorial</Link>
          <Link to="/tutorials">All courses</Link>
        </div>
        <div>
          <h4>Build</h4>
          <Link to="/projects">Guided projects</Link>
          <Link to="/playground">Playground</Link>
          <Link to="/practice">Exercises & challenges</Link>
          <Link to="/references">Reference library</Link>
        </div>
        <div>
          <h4>Track</h4>
          <Link to="/progress">My progress</Link>
          <Link to="/leaderboard">Weekly league</Link>
          <Link to="/bookmarks">Bookmarks</Link>
          <Link to="/certificates">Certificates</Link>
        </div>
        <div>
          <h4>CodeLeaf</h4>
          <Link to="/plans">Plans & pricing</Link>
          <a href="#about" onClick={(e) => e.preventDefault()}>
            About the project
          </a>
          <a href="#privacy" onClick={(e) => e.preventDefault()}>
            Privacy & cookies
          </a>
          <a href="#terms" onClick={(e) => e.preventDefault()}>
            Terms of service
          </a>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} CodeLeaf</span>
        <span>Learn visually. Practise thoughtfully. Build with care.</span>
      </div>
    </footer>
  );
}
