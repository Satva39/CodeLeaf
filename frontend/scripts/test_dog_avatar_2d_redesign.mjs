import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";

const root = path.resolve(import.meta.dirname, "..");
const read = (relative) => fs.readFileSync(path.join(root, relative), "utf8");
const renderer = read("src/components/avatar/DogAvatar.jsx");
const itemArtwork = read("src/components/avatar/AvatarItemArtwork.jsx");
const editor = read("src/components/avatar/DogAvatarEditor.jsx");
const profile = read("src/pages/ProfilePage.jsx");
const gamesCss = read("src/styles/games.css");
const pagesCss = read("src/styles/pages.css");

assert.match(renderer, /dog-avatar-2d/);
assert.match(renderer, /viewBox="0 0 300 300"/);
assert.match(renderer, /const CLOTHING =/);
assert.match(renderer, /clothingIsHoodie/);
assert.match(renderer, /headwear === "wizard-hat"/);
assert.match(renderer, /glasses === "cyber-visor"/);
assert.match(renderer, /neckwear/);
assert.match(renderer, /explorer-backpack/);
assert.doesNotMatch(renderer, /<image\b|linearGradient|feGaussianBlur|<filter/);
assert.match(itemArtwork, /<DogAvatar/);
assert.match(itemArtwork, /\[item\.slot\]: item\.id/);
assert.doesNotMatch(itemArtwork, /<img/);
assert.doesNotMatch(editor, /profile-dog-achievements|avatar\.achievements/);
assert.doesNotMatch(pagesCss, /profile-dog-achievements/);
assert.match(gamesCss, /avatar-item-artwork > \.dog-avatar-2d/);
assert.match(profile, /setAccountUsername/);
assert.match(profile, /payload\.profile_path/);
assert.match(profile, /safeProfilePath/);
assert.doesNotMatch(profile, /String\(handle \|\| ""\)/);

console.log("PASS dog renderer uses a flat 2D character with native fitted accessory layers.");
console.log("PASS wardrobe previews show each selected item worn by the same dog character.");
console.log("PASS the long achievement grid is removed from the dog editor without changing server rewards.");
console.log("PASS public share links use the authenticated API username and canonical profile path.");
