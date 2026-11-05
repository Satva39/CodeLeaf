import { Navigate } from "react-router-dom";

// Backwards-compatible route: the dog is now the user's profile picture and
// customization lives inside Edit profile rather than a separate studio page.
export default function AvatarStudioPage() {
  return <Navigate to="/profile?edit=1#dog-avatar" replace />;
}
