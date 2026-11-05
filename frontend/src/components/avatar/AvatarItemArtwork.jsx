import { getAvatarBackgroundStyle, getAvatarItemArtwork } from "./avatarItemArtwork.js";

export default function AvatarItemArtwork({ item, className = "" }) {
  const artwork = getAvatarItemArtwork(item?.id);
  const background = item?.slot === "background" ? getAvatarBackgroundStyle(item.id) : "";

  return (
    <span
      className={`avatar-item-artwork ${background ? "is-background-artwork" : ""} ${className}`.trim()}
      style={background ? { background } : undefined}
      role="img"
      aria-label={`${item?.name || "Avatar item"} artwork`}
    >
      {artwork?.src ? (
        <img src={artwork.src} alt="" loading="lazy" style={artwork.filter ? { filter: artwork.filter } : undefined} />
      ) : background ? (
        <span className="avatar-item-artwork-glow" aria-hidden="true" />
      ) : (
        <span className="avatar-item-artwork-fallback" aria-hidden="true">{item?.icon || "✦"}</span>
      )}
    </span>
  );
}
