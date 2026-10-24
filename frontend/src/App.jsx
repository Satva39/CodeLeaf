import { useEffect } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { ArrowRight, Compass } from "lucide-react";
import { Header } from "./components/layout/Header.jsx";
import Footer from "./components/layout/Footer.jsx";
import { EmptyState, PageShell } from "./components/common.jsx";
import HomePage from "./pages/HomePage.jsx";
import LessonPage from "./pages/LessonPage.jsx";
import TutorialsPage from "./pages/TutorialsPage.jsx";
import ProgressPage from "./pages/ProgressPage.jsx";
import ReviewPage from "./pages/ReviewPage.jsx";
import LeaderboardPage from "./pages/LeaderboardPage.jsx";
import BookmarksPage from "./pages/BookmarksPage.jsx";
import CertificatesPage from "./pages/CertificatesPage.jsx";
import ExamPage from "./pages/ExamPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import PlansPage from "./pages/PlansPage.jsx";
import ProjectsPage from "./pages/ProjectsPage.jsx";
import ProjectGuidePage from "./pages/ProjectGuidePage.jsx";
import PlaygroundPage from "./pages/PlaygroundPage.jsx";
import ChallengesPage from "./pages/ChallengesPage.jsx";
import ReferencePage from "./pages/ReferencePage.jsx";
import CourseDirectoryPage from "./pages/CourseDirectoryPage.jsx";
import CourseLandingPage from "./pages/CourseLandingPage.jsx";
import ContentStudioPage from "./pages/ContentStudioPage.jsx";
import PortfolioPage from "./pages/PortfolioPage.jsx";
import LearningHubPage from "./pages/LearningHubPage.jsx";

function LegacyReferenceRedirect() {
  const location = useLocation();
  const legacyPath = location.pathname.replace(
    /^\/references(?=\/)/,
    "/reference",
  );
  return (
    <Navigate to={`${legacyPath}${location.search}${location.hash}`} replace />
  );
}

export default function App() {
  const location = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);

  return (
    <div className="app-root">
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tutorials" element={<TutorialsPage />} />
        <Route path="/courses/:courseSlug" element={<CourseLandingPage />} />
        <Route
          path="/learn/:courseSlug/:lessonSlug?"
          element={<LessonPage />}
        />
        <Route
          path="/references"
          element={<CourseDirectoryPage collection="references" />}
        />
        <Route
          path="/reference/:courseSlug/:referenceSlug?"
          element={<ReferencePage />}
        />
        <Route
          path="/references/:courseSlug/:referenceSlug?"
          element={<LegacyReferenceRedirect />}
        />
        <Route path="/dashboard" element={<ProgressPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/learning-hub" element={<LearningHubPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/portfolio/:username" element={<PortfolioPage />} />
        <Route path="/content-studio" element={<ContentStudioPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
        <Route path="/bookmarks" element={<BookmarksPage />} />
        <Route path="/certificates" element={<CertificatesPage />} />
        <Route path="/exam/:examSlug" element={<ExamPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="/register" element={<AuthPage />} />
        <Route path="/forgot-password" element={<AuthPage />} />
        <Route path="/verify-email" element={<AuthPage />} />
        <Route path="/verify-email-change" element={<AuthPage />} />
        <Route path="/reset-password" element={<AuthPage />} />
        <Route path="/plans" element={<PlansPage />} />
        <Route
          path="/projects"
          element={<CourseDirectoryPage collection="projects" />}
        />
        <Route
          path="/projects/:courseSlug/:projectSlug"
          element={<ProjectGuidePage />}
        />
        <Route path="/projects/:courseSlug" element={<ProjectsPage />} />
        <Route path="/playground" element={<PlaygroundPage />} />
        <Route
          path="/practice"
          element={<CourseDirectoryPage collection="practice" />}
        />
        <Route path="/practice/:courseSlug" element={<ChallengesPage />} />
        <Route
          path="/challenges"
          element={<Navigate to="/practice" replace />}
        />
        <Route
          path="*"
          element={
            <PageShell>
              <EmptyState
                icon={Compass}
                title="Page not found"
                detail="The page you are looking for has not been created in this base scaffold."
                action={
                  <Link to="/" className="button button-primary">
                    Go home <ArrowRight size={15} />
                  </Link>
                }
              />
            </PageShell>
          }
        />
      </Routes>
      <Footer />
    </div>
  );
}
