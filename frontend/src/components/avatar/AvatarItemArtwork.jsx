import DogAvatar from "./DogAvatar.jsx";
import { getAvatarBackgroundStyle } from "./avatarItemArtwork.js";

/**
 * Show every cosmetic on the same flat 2D dog used by the live preview.
 * This makes it clear how an item is actually worn instead of showing a
 * separate glossy product render that can look unrelated to the character.
 */
export default function AvatarItemArtwork({ item, className = "" }) {
  if (!item?.slot || !item?.id) {
    return <span className={"avatar-item-artwork " + className} aria-hidden="true" />;
  }

  const equipment = { [item.slot]: item.id };
  const background = item.slot === "background" ? getAvatarBackgroundStyle(item.id) : "";

  return (
    <span
      className={"avatar-item-artwork " + (background ? "is-background-artwork " : "") + className}
      style={background ? { background } : undefined}
      aria-hidden="true"
    >
      <DogAvatar
        appearance={{ breed: "classic", fur_color: "golden", eye_color: "brown" }}
        equipment={equipment}
        size={126}
        title={item.name + " shown on the CodeLeaf dog"}
      />
    </span>
  );
}
