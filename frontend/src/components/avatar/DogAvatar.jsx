import React, { useId } from "react";

const FUR = {
  golden: "#d99a4d", cream: "#f0d7ae", chocolate: "#8d5638",
  charcoal: "#596575", snow: "#f2f4f6", copper: "#bd7048",
};
const EYES = { brown: "#55331f", blue: "#3b83bf", green: "#43876b", amber: "#b47724" };
const BACKGROUNDS = {
  "aurora-background": ["#173f58", "#27315b"],
  "forest-background": ["#245342", "#142d35"],
  "pixel-lab-background": ["#443369", "#17223c"],
};
const CLOTHING = {
  "blue-hoodie": "#3279c9", "developer-jacket": "#286b5d", "moon-hoodie": "#4a4c8e",
  "scholar-outfit": "#4c6f91", "warrior-outfit": "#8b6436",
  "legendary-battle-costume": "#55488f", "legendary-streak-costume": "#a64d39",
  "xp-master-costume": "#bd8b35", "legendary-dog-outfit": "#347e68",
  "grandmaster-outfit": "#7a4b9e", "emerald-dog-suit": "#27845d",
};

export default function DogAvatar({
  appearance = {}, equipment = {}, size = 280, className = "",
  title = "CodeLeaf dog avatar",
}) {
  const gradientId = useId().replace(/:/g, "");
  const breed = appearance.breed || "classic";
  const fur = FUR[appearance.fur_color] || FUR.golden;
  const eye = EYES[appearance.eye_color] || EYES.brown;
  const headwear = equipment.headwear;
  const glasses = equipment.glasses;
  const shirt = equipment.shirt;
  const outfit = equipment.outfit;
  const collar = equipment.collar;
  const neckwear = equipment.neckwear;
  const back = equipment.back;
  const backgroundColors = BACKGROUNDS[equipment.background] || ["#1a3445", "#172337"];
  const snoutWidth = breed === "bulldog" ? 57 : breed === "husky" ? 46 : 49;
  const clothing = outfit || shirt;
  const clothesColor = CLOTHING[clothing] || "#3979a8";
  const pointy = ["shiba", "husky", "corgi"].includes(breed);
  const longEars = breed === "corgi";
  const darkMark = breed === "husky" || breed === "bulldog";

  return (
    <svg className={`dog-avatar ${className}`} width={size} height={size} viewBox="0 0 300 300" role="img" aria-label={title} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id={`${gradientId}-bg`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={backgroundColors[0]} />
          <stop offset="1" stopColor={backgroundColors[1]} />
        </linearGradient>
        <linearGradient id={`${gradientId}-fur`} x1="0" y1="0" x2="0.8" y2="1">
          <stop offset="0" stopColor={fur} />
          <stop offset="1" stopColor={fur} stopOpacity=".78" />
        </linearGradient>
      </defs>
      <circle cx="150" cy="150" r="144" fill={`url(#${gradientId}-bg)`} />
      <circle cx="150" cy="150" r="125" fill="none" stroke="#8aa6b6" strokeOpacity=".12" strokeWidth="2" />
      <path d={breed === "corgi" ? "M205 204 Q239 207 231 226 Q222 235 210 220" : breed === "husky" ? "M207 201 Q255 187 249 218 Q242 237 217 224" : "M204 203 Q238 183 245 207 Q245 224 224 229"} fill="none" stroke={fur} strokeWidth={breed === "husky" ? 17 : 13} strokeLinecap="round" />
      {back && <path d="M88 190 L42 244 L75 256 L121 215 Z" fill={back === "galaxy-cape" || back === "pixel-wings" || back === "hero-cape" ? "#6550a2" : "#3c6e84"} stroke="#1c2838" strokeWidth="5" strokeLinejoin="round" />}
      <ellipse cx="150" cy="250" rx="79" ry="19" fill="#07101c" opacity=".35" />
      <path d="M91 207 Q92 171 126 167 L174 167 Q208 171 209 207 L220 255 Q150 277 80 255 Z" fill={clothing ? clothesColor : `url(#${gradientId}-fur)`} stroke="#263246" strokeWidth="5" />
      {!clothing && <path d="M121 180 Q150 202 179 180 L190 247 Q150 266 110 247 Z" fill="#f4d5aa" opacity=".45" />}
      {back === "explorer-backpack" && <><path d="M82 197 Q55 198 61 235 L88 240 L101 210 Z" fill="#94653e" stroke="#263246" strokeWidth="4"/><rect x="62" y="211" width="28" height="23" rx="7" fill="#bf8a4f" /></>}
      <path d="M109 247 Q103 265 117 268 L139 268 L141 255 Z" fill={fur} stroke="#263246" strokeWidth="4" />
      <path d="M161 255 L163 268 L184 268 Q198 265 191 247 Z" fill={fur} stroke="#263246" strokeWidth="4" />
      {equipment.pants && <path d="M111 236 Q150 247 189 236 L190 262 Q169 271 151 261 Q132 271 110 262 Z" fill="#3f4d82" stroke="#263246" strokeWidth="3"/>}
      {equipment.shoes && <g fill={equipment.shoes === "sprint-shoes" ? "#df8d4d" : "#26364c"} stroke="#111d2d" strokeWidth="3"><path d="M105 258 Q99 267 106 276 L140 276 L140 264 Z"/><path d="M160 264 L160 276 L194 276 Q201 267 194 258 Z"/></g>}
      {collar && <path d="M106 187 Q150 209 194 187 L188 202 Q150 222 112 202 Z" fill={collar === "fire-collar" ? "#c94e32" : collar === "programmer-collar" ? "#4f6f9e" : "#c44e57"} stroke="#263246" strokeWidth="3" />}
      {neckwear && <path d="M132 200 L150 214 L169 200 L164 225 L150 236 L136 225 Z" fill={neckwear === "comet-bandana" ? "#9169d8" : "#50a88a"} stroke="#263246" strokeWidth="3" />}
      {equipment.ears && <g fill="#d6a0a2" stroke="#263246" strokeWidth="5"><path d="M73 88 Q38 61 53 118 Q60 140 82 133 Z"/><path d="M227 88 Q262 61 247 118 Q240 140 218 133 Z"/></g>}
      {/* Ears */}
      {pointy ? (
        <>
          <path d={longEars ? "M75 99 Q52 14 103 39 Q124 54 111 111 Z" : "M76 104 Q52 12 112 43 Q126 64 110 122 Z"} fill={`url(#${gradientId}-fur)`} stroke="#263246" strokeWidth="6" strokeLinejoin="round" />
          <path d={longEars ? "M83 89 Q68 40 98 55 L103 99 Z" : "M84 92 Q70 43 103 60 L105 106 Z"} fill="#bd7770" opacity=".85" />
          <path d="M224 104 Q248 12 188 43 Q174 64 190 122 Z" fill={`url(#${gradientId}-fur)`} stroke="#263246" strokeWidth="6" strokeLinejoin="round" />
          <path d="M216 92 Q230 43 197 60 L195 106 Z" fill="#bd7770" opacity=".85" />
        </>
      ) : (
        <>
          <path d="M77 99 Q41 74 51 139 Q59 161 94 145 Z" fill={`url(#${gradientId}-fur)`} stroke="#263246" strokeWidth="6" />
          <path d="M223 99 Q259 74 249 139 Q241 161 206 145 Z" fill={`url(#${gradientId}-fur)`} stroke="#263246" strokeWidth="6" />
          <path d="M64 112 Q57 112 64 145 Q76 149 83 137 Z" fill="#bd7770" opacity=".8" />
          <path d="M236 112 Q243 112 236 145 Q224 149 217 137 Z" fill="#bd7770" opacity=".8" />
        </>
      )}
      {/* Head */}
      <ellipse cx="150" cy="139" rx="91" ry="82" fill={`url(#${gradientId}-fur)`} stroke="#263246" strokeWidth="6" />
      {darkMark && <path d="M150 64 Q119 86 125 137 Q143 152 150 148 Q157 152 175 137 Q181 86 150 64 Z" fill="#eff1f0" opacity=".72" />}
      <ellipse cx="150" cy="171" rx={snoutWidth} ry="37" fill="#f6dfc3" />
      <ellipse cx="117" cy="132" rx="12" ry="15" fill="#fff" />
      <ellipse cx="183" cy="132" rx="12" ry="15" fill="#fff" />
      <ellipse cx="119" cy="134" rx="6" ry="9" fill={eye} />
      <ellipse cx="181" cy="134" rx="6" ry="9" fill={eye} />
      <circle cx="121" cy="130" r="2.6" fill="#fff" />
      <circle cx="183" cy="130" r="2.6" fill="#fff" />
      {equipment.eyes && <g fill="#fff4a7"><path d="M111 111 L114 104 L117 111 L124 114 L117 117 L114 124 L111 117 L104 114 Z"/><path d="M176 111 L179 104 L182 111 L189 114 L182 117 L179 124 L176 117 L169 114 Z"/></g>}
      <ellipse cx="150" cy="163" rx="12" ry="8" fill="#263246" />
      <path d="M150 170 Q148 183 135 183 M150 170 Q152 183 165 183" fill="none" stroke="#754a3d" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M93 159 Q104 167 116 164 M207 159 Q196 167 184 164" fill="none" stroke="#9d6548" strokeWidth="2.5" strokeLinecap="round" opacity=".6" />
      {glasses && <g fill="none" stroke={glasses === "golden-battle-glasses" ? "#e2bd58" : glasses === "cyber-visor" ? "#3ae0d0" : "#29394d"} strokeWidth="5"><rect x="91" y="119" width="48" height="31" rx="13"/><rect x="161" y="119" width="48" height="31" rx="13"/><path d="M139 132 Q150 126 161 132" /></g>}
      {equipment.headwear && (
        <g stroke="#263246" strokeWidth="5" strokeLinejoin="round">
          {headwear === "golden-crown" || headwear === "diamond-crown" || headwear === "compiler-crown" ? <path d="M105 77 L111 45 L132 64 L150 35 L168 64 L189 45 L195 77 Z" fill={headwear === "diamond-crown" ? "#71c7e6" : headwear === "compiler-crown" ? "#77c6bc" : "#e3b64f"} /> : null}
          {headwear.includes("hat") || headwear.includes("cap") || headwear === "wizard-hat" || headwear === "battle-champion-cap" ? <><path d={headwear === "wizard-hat" ? "M105 85 Q150 -3 195 85 Z" : "M99 83 Q100 49 150 48 Q200 49 201 83 Z"} fill={headwear === "wizard-hat" ? "#5d4c9a" : headwear === "graduation-hat" ? "#313d54" : "#3d7da7"}/><path d="M92 84 Q150 99 208 84" fill="none" stroke="#d0a84f" strokeWidth="7"/></> : null}
          {headwear.includes("headset") || headwear.includes("headphones") ? <><path d="M99 125 Q91 60 150 61 Q209 60 201 125" fill="none" stroke="#334d6e" strokeWidth="11"/><rect x="87" y="116" width="17" height="33" rx="7" fill="#37b79b"/><rect x="196" y="116" width="17" height="33" rx="7" fill="#37b79b"/></> : null}
        </g>
      )}
      {equipment.face && <g><circle cx="210" cy="171" r="12" fill="#f1c65a" stroke="#263246" strokeWidth="3"/><path d="M204 171 L210 177 L218 164" fill="none" stroke="#263246" strokeWidth="2.5" /></g>}
      {back === "pixel-wings" && <g fill="#63bfc3" stroke="#263246" strokeWidth="3"><path d="M93 185 Q38 157 54 223 Q69 220 93 185Z"/><path d="M207 185 Q262 157 246 223 Q231 220 207 185Z"/></g>}
      {back === "hero-cape" && <path d="M104 193 Q150 212 196 193 L224 260 Q150 284 76 260 Z" fill="#b94b50" stroke="#263246" strokeWidth="5" opacity=".92" />}
      {back === "galaxy-cape" && <path d="M107 194 Q150 211 193 194 L212 254 Q150 280 88 254 Z" fill="#4f4e9f" stroke="#263246" strokeWidth="5" opacity=".92" />}
      {back === "hero-cape" || back === "galaxy-cape" ? <path d="M146 218 L150 245 L163 226 L150 231 L137 226 Z" fill="#f0ca61"/> : null}
      <circle cx="150" cy="17" r="4" fill="#52d7b2" opacity=".8" />
    </svg>
  );
}
