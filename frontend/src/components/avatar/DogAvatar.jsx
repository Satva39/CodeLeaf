import React, { useId } from "react";
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

const FUR = {
  golden: ["#f2bd68", "#c9823a", "#8b4e2b"],
  cream: ["#fff0cf", "#e8cda2", "#a77c55"],
  chocolate: ["#c4855c", "#7c452e", "#49291f"],
  charcoal: ["#aab6c4", "#657384", "#3b4658"],
  snow: ["#ffffff", "#dce7ef", "#9aabba"],
  copper: ["#f1a06e", "#b85e3e", "#723b30"],
};
const EYES = { brown: "#75451f", blue: "#328bc8", green: "#398b69", amber: "#bf812b" };
const BACKGROUNDS = {
  "aurora-background": ["#173f58", "#27315b"],
  "forest-background": ["#245342", "#142d35"],
  "pixel-lab-background": ["#443369", "#17223c"],
};
const CLOTHING = {
  "blue-hoodie": ["#4b9cef", "#1760ac"],
  "developer-jacket": ["#40c8b0", "#167b70"],
  "moon-hoodie": ["#7778d9", "#393e8e"],
  "scholar-outfit": ["#8baed0", "#426786"],
  "warrior-outfit": ["#d1a15d", "#80542c"],
  "legendary-battle-costume": ["#9d88f2", "#51418d"],
  "legendary-streak-costume": ["#e77c68", "#9e433c"],
  "xp-master-costume": ["#f4cb62", "#a87424"],
  "legendary-dog-outfit": ["#55c4a2", "#176d57"],
  "grandmaster-outfit": ["#b58be2", "#69418e"],
  "emerald-dog-suit": ["#5ad49a", "#16794e"],
};

const HEADWEAR_ART = {
  "starter-cap": explorerCap,
  "battle-champion-cap": explorerCap,
  "golden-crown": tealCrown,
  "diamond-crown": tealCrown,
  "compiler-crown": tealCrown,
  "wizard-hat": wizardHat,
  "graduation-hat": tealCrown,
  "coding-headset": codingHeadset,
  "master-headphones": codingHeadset,
};
const GLASSES_ART = {
  "developer-glasses": developerGlasses,
  "cyber-visor": cyberVisor,
  "golden-battle-glasses": cyberVisor,
};
const CLOTHING_ART = {
  "blue-hoodie": blueHoodie,
  "moon-hoodie": blueHoodie,
  "developer-jacket": developerJacket,
  "scholar-outfit": developerJacket,
  "warrior-outfit": heroCloak,
  "legendary-battle-costume": heroCloak,
  "legendary-streak-costume": heroCloak,
  "xp-master-costume": developerJacket,
  "legendary-dog-outfit": heroCloak,
  "grandmaster-outfit": heroCloak,
  "emerald-dog-suit": developerJacket,
};
const COLLAR_ART = {
  "classic-collar": redCollar,
  "programmer-collar": redCollar,
  "fire-collar": redCollar,
};
const NECKWEAR_ART = {
  "leaf-bandana": emeraldBandana,
  "streak-bandana": emeraldBandana,
  "comet-bandana": emeraldBandana,
};
const BACK_ART = {
  "explorer-backpack": explorerBackpack,
  "galaxy-cape": heroCloak,
  "hero-cape": heroCloak,
};

function itemId(equipment, slot) {
  const value = equipment?.[slot];
  if (typeof value === "string") return value;
  if (value && typeof value === "object") return value.item_id || value.id || "";
  return "";
}

function Art({ href, x, y, width, height, opacity = 1 }) {
  if (!href) return null;
  return (
    <image
      href={href}
      x={x}
      y={y}
      width={width}
      height={height}
      opacity={opacity}
      preserveAspectRatio="xMidYMid meet"
    />
  );
}

export default function DogAvatar({
  appearance = {},
  equipment = {},
  size = 280,
  className = "",
  title = "CodeLeaf dog avatar",
}) {
  const gradientId = useId().replace(/:/g, "");
  const breed = appearance.breed || "classic";
  const furStops = FUR[appearance.fur_color] || FUR.golden;
  const eye = EYES[appearance.eye_color] || EYES.brown;
  const background = BACKGROUNDS[itemId(equipment, "background")] || ["#17384b", "#101d30"];

  const headwear = itemId(equipment, "headwear");
  const glasses = itemId(equipment, "glasses");
  const shirt = itemId(equipment, "shirt");
  const outfit = itemId(equipment, "outfit");
  const clothingId = shirt || outfit;
  const clothes = CLOTHING[clothingId] || ["#6b9abc", "#345a7c"];
  const collar = itemId(equipment, "collar");
  const neckwear = itemId(equipment, "neckwear");
  const back = itemId(equipment, "back");
  const ears = itemId(equipment, "ears");
  const eyes = itemId(equipment, "eyes");
  const face = itemId(equipment, "face");
  const pants = itemId(equipment, "pants");
  const shoes = itemId(equipment, "shoes");

  const pointy = ["shiba", "husky", "corgi"].includes(breed);
  const longEars = breed === "corgi";
  const broadFace = breed === "bulldog";
  const retriever = breed === "retriever";
  const husky = breed === "husky";
  const snoutWidth = broadFace ? 58 : husky ? 47 : retriever ? 53 : 49;

  const headwearImage = HEADWEAR_ART[headwear];
  const glassesImage = GLASSES_ART[glasses];
  const clothingImage = CLOTHING_ART[clothingId];
  const collarImage = COLLAR_ART[collar];
  const bandanaImage = NECKWEAR_ART[neckwear];
  const backImage = BACK_ART[back];

  return (
    <svg
      className={`dog-avatar ${className}`}
      width={size}
      height={size}
      viewBox="0 0 300 300"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id={`${gradientId}-bg`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={background[0]} />
          <stop offset="1" stopColor={background[1]} />
        </linearGradient>
        <linearGradient id={`${gradientId}-fur`} x1="0.1" y1="0" x2="0.85" y2="1">
          <stop offset="0" stopColor={furStops[0]} />
          <stop offset=".62" stopColor={furStops[1]} />
          <stop offset="1" stopColor={furStops[2]} />
        </linearGradient>
        <linearGradient id={`${gradientId}-muzzle`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff0d9" />
          <stop offset="1" stopColor="#e7c49e" />
        </linearGradient>
        <linearGradient id={`${gradientId}-cloth`} x1="0" y1="0" x2=".8" y2="1">
          <stop offset="0" stopColor={clothes[0]} />
          <stop offset="1" stopColor={clothes[1]} />
        </linearGradient>
        <filter id={`${gradientId}-shadow`} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="7" />
        </filter>
      </defs>

      {/* Profile badge background */}
      <circle cx="150" cy="150" r="146" fill={`url(#${gradientId}-bg)`} />
      <circle cx="150" cy="150" r="130" fill="none" stroke="#b7d3df" strokeOpacity=".15" strokeWidth="2" />
      <circle cx="150" cy="150" r="117" fill="none" stroke="#d2e8ef" strokeOpacity=".08" strokeWidth="1.5" />
      <ellipse cx="150" cy="278" rx="91" ry="12" fill="#07101b" opacity=".45" filter={`url(#${gradientId}-shadow)`} />

      {/* Tail and back equipment */}
      <path
        d={breed === "corgi" ? "M205 211 Q249 213 238 238 Q229 250 210 230" : husky ? "M207 205 Q260 183 256 220 Q251 247 220 233" : "M205 209 Q246 186 252 214 Q255 235 226 239"}
        fill="none"
        stroke={`url(#${gradientId}-fur)`}
        strokeWidth={husky ? 19 : 16}
        strokeLinecap="round"
      />
      {back === "pixel-wings" && (
        <g fill="#68d3d0" stroke="#294057" strokeWidth="5" strokeLinejoin="round">
          <path d="M103 188 Q45 148 45 216 Q62 227 103 205Z" />
          <path d="M197 188 Q255 148 255 216 Q238 227 197 205Z" />
          <path d="M90 194 L56 188 L74 215Z" fill="#b3f2e4" />
          <path d="M210 194 L244 188 L226 215Z" fill="#b3f2e4" />
        </g>
      )}
      {backImage && back !== "explorer-backpack" && (
        <Art href={backImage} x={66} y={154} width={168} height={142} opacity=".98" />
      )}

      {/* Body, legs and paws */}
      <path d="M91 190 Q95 166 126 163 L174 163 Q205 166 209 190 L221 260 Q150 282 79 260Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="5" />
      <path d="M111 239 Q103 260 113 267 L140 268 L143 246Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="4" />
      <path d="M157 246 L160 268 L187 267 Q198 259 188 239Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="4" />
      <ellipse cx="124" cy="267" rx="20" ry="8" fill="#f1d5b5" opacity=".75" />
      <ellipse cx="176" cy="267" rx="20" ry="8" fill="#f1d5b5" opacity=".75" />
      <path d="M98 204 Q82 218 87 238 Q91 248 108 244 L120 207Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="4" />
      <path d="M202 204 Q218 218 213 238 Q209 248 192 244 L180 207Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="4" />
      {back === "explorer-backpack" && <Art href={explorerBackpack} x={45} y={171} width={102} height={112} opacity=".98" />}

      {/* Shirt/outfit underlay. The selected top is rendered by item ID below. */}
      {clothingId && (
        <g>
          <path d="M95 192 Q111 171 132 171 L168 171 Q189 171 205 192 L214 254 Q150 273 86 254Z" fill={`url(#${gradientId}-cloth)`} stroke="#293d56" strokeWidth="5" />
          <path d="M124 174 Q150 199 176 174" fill="none" stroke="#d6f3ff" strokeOpacity=".62" strokeWidth="4" />
          <path d="M150 191 L150 251" stroke="#f2f8ff" strokeOpacity=".6" strokeWidth="3" />
          <path d="M105 218 L120 218 M180 218 L195 218" stroke="#d7f3ff" strokeOpacity=".35" strokeWidth="3" strokeLinecap="round" />
        </g>
      )}
      {clothingImage && <Art href={clothingImage} x={68} y={156} width={164} height={135} />}
      {!clothingId && <path d="M121 179 Q150 205 179 179 L190 248 Q150 266 110 248Z" fill="#f8dfbf" opacity=".45" />}

      {pants && (
        <g>
          <path d="M107 239 Q150 249 193 239 L190 265 Q171 276 151 264 Q130 276 110 265Z" fill="#344b82" stroke="#253650" strokeWidth="4" />
          <path d="M149 248 L149 266" stroke="#c5d8ee" strokeWidth="2.5" />
          <circle cx="151" cy="254" r="3" fill="#e7c36b" />
        </g>
      )}
      {shoes && (
        <g stroke="#293b53" strokeWidth="4" strokeLinejoin="round">
          <path d="M103 258 Q99 273 111 278 L141 278 L140 264Z" fill={shoes === "sprint-shoes" ? "#ef984f" : "#334f74"} />
          <path d="M160 264 L159 278 L189 278 Q201 273 196 258Z" fill={shoes === "sprint-shoes" ? "#ef984f" : "#334f74"} />
          <path d="M109 271 L135 271 M164 271 L190 271" stroke="#d9edf7" strokeWidth="3" strokeLinecap="round" />
        </g>
      )}

      {/* Ears: breed silhouette and soft inner-ear shading */}
      {pointy ? (
        <>
          <path d={longEars ? "M75 112 Q43 2 111 39 Q132 55 114 134Z" : "M75 112 Q52 12 112 42 Q131 66 114 133Z"} fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="6" strokeLinejoin="round" />
          <path d={longEars ? "M84 99 Q66 34 100 58 L106 116Z" : "M84 99 Q72 45 103 62 L106 117Z"} fill="#b9696b" opacity=".78" />
          <path d="M225 112 Q257 2 189 39 Q168 55 186 134Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="6" strokeLinejoin="round" />
          <path d="M216 99 Q234 34 200 58 L194 116Z" fill="#b9696b" opacity=".78" />
        </>
      ) : (
        <>
          <path d="M78 104 Q40 72 48 139 Q56 169 96 151Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="6" />
          <path d="M222 104 Q260 72 252 139 Q244 169 204 151Z" fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="6" />
          <path d="M61 119 Q57 119 65 147 Q78 153 87 139Z" fill="#ba7771" opacity=".76" />
          <path d="M239 119 Q243 119 235 147 Q222 153 213 139Z" fill="#ba7771" opacity=".76" />
        </>
      )}
      {ears === "floppy-ears" && (
        <g fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="5">
          <path d="M72 103 Q22 91 46 168 Q59 185 89 155Z" />
          <path d="M228 103 Q278 91 254 168 Q241 185 211 155Z" />
        </g>
      )}

      {/* Head silhouette and soft cheek highlights */}
      <ellipse cx="150" cy="135" rx={broadFace ? 96 : 91} ry={broadFace ? 82 : 86} fill={`url(#${gradientId}-fur)`} stroke="#34445a" strokeWidth="6" />
      {husky && <path d="M150 54 Q115 80 124 144 Q139 162 150 157 Q161 162 176 144 Q185 80 150 54Z" fill="#f0f4f5" opacity=".88" />}
      {retriever && <path d="M75 120 Q86 75 121 67 Q95 109 109 153 Q84 153 75 120Z" fill="#ffe0a5" opacity=".2" />}
      <ellipse cx="112" cy="171" rx="28" ry="19" fill="#ffd6bd" opacity=".32" />
      <ellipse cx="188" cy="171" rx="28" ry="19" fill="#ffd6bd" opacity=".32" />

      {/* Face */}
      <ellipse cx="150" cy="169" rx={snoutWidth} ry="38" fill={`url(#${gradientId}-muzzle)`} />
      <ellipse cx="119" cy="130" rx="14" ry="17" fill="#fff" />
      <ellipse cx="181" cy="130" rx="14" ry="17" fill="#fff" />
      <ellipse cx="121" cy="132" rx="7" ry="10" fill={eye} />
      <ellipse cx="179" cy="132" rx="7" ry="10" fill={eye} />
      <circle cx="124" cy="127" r="3.2" fill="#fff" />
      <circle cx="182" cy="127" r="3.2" fill="#fff" />
      <path d="M102 111 Q118 100 135 108 M165 108 Q183 100 198 111" fill="none" stroke="#704c36" strokeOpacity=".55" strokeWidth="4" strokeLinecap="round" />
      {eyes === "starry-eyes" && (
        <g fill="#ffe58a" stroke="#ab792d" strokeWidth="1">
          <path d="M110 107 L114 98 L118 107 L127 111 L118 115 L114 124 L110 115 L101 111Z" />
          <path d="M173 107 L177 98 L181 107 L190 111 L181 115 L177 124 L173 115 L164 111Z" />
        </g>
      )}
      <ellipse cx="150" cy="164" rx="12" ry="8.5" fill="#26384b" />
      <path d="M150 171 Q148 185 135 186 M150 171 Q152 185 165 186" fill="none" stroke="#785044" strokeWidth="3.7" strokeLinecap="round" />
      <path d="M91 161 Q103 169 116 165 M209 161 Q197 169 184 165" fill="none" stroke="#a66b4e" strokeWidth="2.5" strokeLinecap="round" opacity=".55" />

      {/* Collar, tag and bandana layers */}
      {collar && <path d="M105 187 Q150 211 195 187 L189 204 Q150 225 111 204Z" fill={collar === "fire-collar" ? "#e05b48" : "#c94e57"} stroke="#34445a" strokeWidth="3.5" />}
      {collar && <><circle cx="150" cy="207" r="7" fill="#f2c65f" stroke="#654e3b" strokeWidth="2"/><path d="M150 204 L150 210" stroke="#79522b" strokeWidth="2"/></>}
      {neckwear && <path d="M127 195 L150 211 L173 195 L166 226 L150 239 L134 226Z" fill={neckwear === "comet-bandana" ? "#9265da" : "#279a70"} stroke="#34445a" strokeWidth="3.5" />}
      {neckwear && <path d="M142 214 L150 220 L158 214" fill="none" stroke="#e0f4d4" strokeWidth="2.5" strokeLinecap="round"/>}
      <Art href={collarImage} x={94} y={176} width={112} height={84} />
      <Art href={bandanaImage} x={94} y={176} width={112} height={86} />

      {/* Face accessory and eyewear */}
      {face === "xp-champion-accessory" && (
        <g>
          <circle cx="215" cy="172" r="17" fill="#f4c34f" stroke="#6b4e2b" strokeWidth="3.5" />
          <path d="M207 172 L213 178 L224 164" fill="none" stroke="#fff8d5" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      )}
      {glasses && !glassesImage && (
        <g fill="none" stroke="#293c53" strokeWidth="5">
          <rect x="91" y="116" width="49" height="34" rx="13" />
          <rect x="160" y="116" width="49" height="34" rx="13" />
          <path d="M140 130 Q150 125 160 130" />
        </g>
      )}
      <Art href={glassesImage} x={65} y={101} width={170} height={94} />

      {/* Headwear is the top-most layer so the visual always matches the item ID. */}
      {headwear && !headwearImage && (
        headwear === "graduation-hat" ? (
          <g stroke="#34445a" strokeWidth="4" strokeLinejoin="round">
            <path d="M99 70 L150 42 L201 70 L150 88Z" fill="#26354d" />
            <path d="M115 79 L115 93 Q150 110 185 93 L185 79" fill="#3b4962" />
            <path d="M196 70 L199 100" stroke="#e8bf56" strokeWidth="3" />
            <circle cx="199" cy="103" r="5" fill="#e8bf56" stroke="none" />
          </g>
        ) : (
          <g stroke="#34445a" strokeWidth="5" strokeLinejoin="round">
            <path d="M100 82 Q100 45 150 43 Q200 45 200 82Z" fill="#3f7fa8" />
            <path d="M91 83 Q150 99 209 83" fill="none" stroke="#e0bf68" strokeWidth="7" />
          </g>
        )
      )}
      <Art
        href={headwearImage}
        x={headwear === "wizard-hat" ? 75 : 76}
        y={headwear === "wizard-hat" ? -11 : headwear?.includes("crown") ? 4 : 5}
        width={headwear === "wizard-hat" ? 150 : 148}
        height={headwear === "wizard-hat" ? 142 : 122}
      />

      {/* Tiny achievement sparkle to make the dog feel alive */}
      <circle cx="150" cy="17" r="4.5" fill="#55dfbd" opacity=".9" />
      <path d="M235 64 L239 74 L249 78 L239 82 L235 92 L231 82 L221 78 L231 74Z" fill="#f5d36c" opacity=".82" />
      <circle cx="63" cy="83" r="3" fill="#b2e4ef" opacity=".75" />
    </svg>
  );
}
