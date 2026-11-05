import explorerCap from "../../assets/avatar/items/explorer-cap.webp";
import tealCrown from "../../assets/avatar/items/teal-crown.webp";
import wizardHat from "../../assets/avatar/items/wizard-hat.webp";
import codingHeadset from "../../assets/avatar/items/coding-headset.webp";
import developerGlasses from "../../assets/avatar/items/developer-glasses.webp";
import cyberVisor from "../../assets/avatar/items/cyber-visor.webp";
import blueHoodie from "../../assets/avatar/items/blue-hoodie.webp";
import developerJacket from "../../assets/avatar/items/developer-jacket.webp";
import redCollar from "../../assets/avatar/items/red-collar.webp";
import emeraldBandana from "../../assets/avatar/items/emerald-bandana.webp";
import explorerBackpack from "../../assets/avatar/items/explorer-backpack.webp";
import heroCloak from "../../assets/avatar/items/hero-cloak.webp";
import battleChampionCap from "../../assets/avatar/items/battle-champion-cap.webp";
import goldenCrown from "../../assets/avatar/items/golden-crown.webp";
import diamondCrown from "../../assets/avatar/items/diamond-crown.webp";
import compilerCrown from "../../assets/avatar/items/compiler-crown.webp";
import masterHeadphones from "../../assets/avatar/items/master-headphones.webp";
import goldenBattleGlasses from "../../assets/avatar/items/golden-battle-glasses.webp";
import moonHoodie from "../../assets/avatar/items/moon-hoodie.webp";
import scholarOutfit from "../../assets/avatar/items/scholar-outfit.webp";
import warriorOutfit from "../../assets/avatar/items/warrior-outfit.webp";
import legendaryBattleCostume from "../../assets/avatar/items/legendary-battle-costume.webp";
import legendaryStreakCostume from "../../assets/avatar/items/legendary-streak-costume.webp";
import xpMasterCostume from "../../assets/avatar/items/xp-master-costume.webp";
import legendaryDogOutfit from "../../assets/avatar/items/legendary-dog-outfit.webp";
import grandmasterOutfit from "../../assets/avatar/items/grandmaster-outfit.webp";
import emeraldDogSuit from "../../assets/avatar/items/emerald-dog-suit.webp";
import programmerCollar from "../../assets/avatar/items/programmer-collar.webp";
import fireCollar from "../../assets/avatar/items/fire-collar.webp";
import streakBandana from "../../assets/avatar/items/streak-bandana.webp";
import cometBandana from "../../assets/avatar/items/comet-bandana.webp";
import galaxyCape from "../../assets/avatar/items/galaxy-cape.webp";

/**
 * One item-id-to-artwork registry is shared by the wardrobe and the dog renderer.
 * Hue adjustments create distinct owned cosmetics without inventing a different
 * asset when only a color variant exists in the current catalogue.
 */
export const AVATAR_BACKGROUND_ARTWORK = Object.freeze({
  "aurora-background": {
    colors: ["#173f58", "#27315b"],
    swatch: "linear-gradient(135deg,#173f58,#27315b 55%,#9a6bd2)",
  },
  "forest-background": {
    colors: ["#245342", "#142d35"],
    swatch: "linear-gradient(135deg,#245342,#142d35 55%,#82b58a)",
  },
  "pixel-lab-background": {
    colors: ["#443369", "#17223c"],
    swatch: "linear-gradient(135deg,#443369,#17223c 55%,#5b99c8)",
  },
});

export function getAvatarBackgroundColors(itemId) {
  return AVATAR_BACKGROUND_ARTWORK[itemId]?.colors || ["#17384b", "#101d30"];
}

export function getAvatarBackgroundStyle(itemId) {
  return AVATAR_BACKGROUND_ARTWORK[itemId]?.swatch || "linear-gradient(135deg,#17384b,#101d30)";
}

export const AVATAR_ITEM_ARTWORK = Object.freeze({
  "starter-cap": { src: explorerCap },
  "battle-champion-cap": { src: battleChampionCap },
  "golden-crown": { src: goldenCrown },
  "diamond-crown": { src: diamondCrown },
  "compiler-crown": { src: compilerCrown },
  "wizard-hat": { src: wizardHat },
  "coding-headset": { src: codingHeadset },
  "master-headphones": { src: masterHeadphones },

  "developer-glasses": { src: developerGlasses },
  "cyber-visor": { src: cyberVisor },
  "golden-battle-glasses": { src: goldenBattleGlasses },

  "blue-hoodie": { src: blueHoodie },
  "moon-hoodie": { src: moonHoodie },
  "developer-jacket": { src: developerJacket },
  "scholar-outfit": { src: scholarOutfit },
  "warrior-outfit": { src: warriorOutfit },
  "legendary-battle-costume": { src: legendaryBattleCostume },
  "legendary-streak-costume": { src: legendaryStreakCostume },
  "xp-master-costume": { src: xpMasterCostume },
  "legendary-dog-outfit": { src: legendaryDogOutfit },
  "grandmaster-outfit": { src: grandmasterOutfit },
  "emerald-dog-suit": { src: emeraldDogSuit },

  "classic-collar": { src: redCollar },
  "programmer-collar": { src: programmerCollar },
  "fire-collar": { src: fireCollar },
  "leaf-bandana": { src: emeraldBandana },
  "streak-bandana": { src: streakBandana },
  "comet-bandana": { src: cometBandana },

  "explorer-backpack": { src: explorerBackpack },
  "galaxy-cape": { src: galaxyCape },
  "hero-cape": { src: heroCloak },
});

export function getAvatarItemArtwork(itemId) {
  return typeof itemId === "string" ? AVATAR_ITEM_ARTWORK[itemId] || null : null;
}
