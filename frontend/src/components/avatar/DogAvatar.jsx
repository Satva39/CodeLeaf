import React, { useId } from "react";
import { getAvatarBackgroundColors } from "./avatarItemArtwork.js";

const FUR = {
  golden: {
    base: "#D99A50", light: "#F2BD75", shade: "#A96135", muzzle: "#F8E4C8",
    inner: "#C87972", outline: "#70472F",
  },
  cream: {
    base: "#E9D2A9", light: "#FFF0D2", shade: "#B99670", muzzle: "#FFF3DF",
    inner: "#CC8E88", outline: "#796049",
  },
  chocolate: {
    base: "#9A6043", light: "#C68A64", shade: "#67402F", muzzle: "#EBC8A6",
    inner: "#B87370", outline: "#513426",
  },
  charcoal: {
    base: "#74808D", light: "#AAB5C0", shade: "#46515D", muzzle: "#D8DDE1",
    inner: "#A96F74", outline: "#35414D",
  },
  snow: {
    base: "#E7EDF0", light: "#FFFFFF", shade: "#AAB8C2", muzzle: "#FFFFFF",
    inner: "#D18A8C", outline: "#657581",
  },
  copper: {
    base: "#C9784C", light: "#F0A271", shade: "#884630", muzzle: "#F6D6B9",
    inner: "#C87D78", outline: "#663B2C",
  },
};

const EYES = {
  brown: "#76502F",
  blue: "#438CB8",
  green: "#4C8B69",
  amber: "#B77C35",
};

const CLOTHING = {
  "blue-hoodie": { base: "#397DB9", shade: "#24577F", trim: "#B8DDF4", style: "hoodie" },
  "moon-hoodie": { base: "#555DAA", shade: "#343C78", trim: "#D1C8FF", style: "hoodie" },
  "developer-jacket": { base: "#278E83", shade: "#17665F", trim: "#B5F0DB", style: "jacket" },
  "scholar-outfit": { base: "#426A91", shade: "#2A496B", trim: "#F2E5C8", style: "scholar" },
  "warrior-outfit": { base: "#A9793E", shade: "#704B2B", trim: "#EBCB8A", style: "armor" },
  "legendary-battle-costume": { base: "#6C55A8", shade: "#43356E", trim: "#E8D8FF", style: "armor" },
  "legendary-streak-costume": { base: "#B95D51", shade: "#783B39", trim: "#FFD2A8", style: "champion" },
  "xp-master-costume": { base: "#C58A2D", shade: "#80541F", trim: "#FFE7A0", style: "champion" },
  "legendary-dog-outfit": { base: "#3E8B6B", shade: "#245B4A", trim: "#C3F1CF", style: "champion" },
  "grandmaster-outfit": { base: "#765196", shade: "#4B3469", trim: "#E6D3FF", style: "armor" },
  "emerald-dog-suit": { base: "#27865A", shade: "#15583C", trim: "#B9F2C9", style: "champion" },
};

function itemId(equipment, slot) {
  const value = equipment?.[slot];
  if (typeof value === "string") return value;
  if (value && typeof value === "object") return value.item_id || value.id || "";
  return "";
}

function DogAvatar({
  appearance = {},
  equipment = {},
  size = 280,
  className = "",
  title = "CodeLeaf dog avatar",
}) {
  const clipId = useId().replace(/:/g, "");
  const breed = appearance.breed || "classic";
  const fur = FUR[appearance.fur_color] || FUR.golden;
  const eye = EYES[appearance.eye_color] || EYES.brown;
  const backgroundId = itemId(equipment, "background");
  const background = getAvatarBackgroundColors(backgroundId);
  const hasBackground = Boolean(backgroundId);

  const headwear = itemId(equipment, "headwear");
  const glasses = itemId(equipment, "glasses");
  const shirt = itemId(equipment, "shirt");
  const outfit = itemId(equipment, "outfit");
  const clothingId = shirt || outfit;
  const clothing = CLOTHING[clothingId] || (clothingId
    ? { base: "#47789A", shade: "#2C506C", trim: "#D5E8F2", style: "jacket" }
    : null);
  const collar = itemId(equipment, "collar");
  const neckwear = itemId(equipment, "neckwear");
  const back = itemId(equipment, "back");
  const ears = itemId(equipment, "ears");
  const eyes = itemId(equipment, "eyes");
  const face = itemId(equipment, "face");
  const pants = itemId(equipment, "pants");
  const shoes = itemId(equipment, "shoes");

  const pointyEars = ["shiba", "husky", "corgi"].includes(breed) && ears !== "floppy-ears";
  const longEars = ears === "floppy-ears" || ["retriever", "bulldog"].includes(breed);
  const broadFace = breed === "bulldog";
  const husky = breed === "husky";
  const shiba = breed === "shiba";
  const corgi = breed === "corgi";
  const snoutWidth = broadFace ? 57 : husky ? 48 : 52;

  const hatIsCrown = ["golden-crown", "diamond-crown", "compiler-crown"].includes(headwear);
  const hatIsHeadset = ["coding-headset", "master-headphones"].includes(headwear);
  const clothingIsHoodie = clothing?.style === "hoodie";
  const coat = fur.base;
  const outline = fur.outline;

  return (
    <svg
      className={"dog-avatar dog-avatar-2d " + className}
      width={size}
      height={size}
      viewBox="0 0 300 300"
      role="img"
      aria-label={title}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <clipPath id={clipId + "-clip"}>
          <rect x="3" y="3" width="294" height="294" rx="28" />
        </clipPath>
      </defs>

      <g clipPath={"url(#" + clipId + "-clip)"}>
        {hasBackground && (
          <>
            <rect x="4" y="4" width="292" height="292" rx="26" fill={background[0]} />
            <circle cx="238" cy="54" r="34" fill={background[1]} opacity=".45" />
            <circle cx="62" cy="228" r="48" fill="#FFFFFF" opacity=".045" />
          </>
        )}

        {/* Back accessories sit behind the body so they feel attached to the character. */}
        {back === "pixel-wings" && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path d="M111 184 Q66 143 38 166 Q42 206 91 220 L119 207Z" fill="#66CFC5" />
            <path d="M189 184 Q234 143 262 166 Q258 206 209 220 L181 207Z" fill="#66CFC5" />
            <path d="M91 181 L55 173 L72 204 L105 208Z" fill="#B8F0D9" />
            <path d="M209 181 L245 173 L228 204 L195 208Z" fill="#B8F0D9" />
          </g>
        )}
        {(back === "hero-cape" || back === "galaxy-cape") && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path
              d="M111 166 Q150 187 189 166 L219 250 Q187 270 150 263 Q113 270 81 250Z"
              fill={back === "galaxy-cape" ? "#514A91" : "#C44F57"}
            />
            {back === "galaxy-cape" ? (
              <g fill="#F3D88B" stroke="none">
                <path d="M119 208 L123 218 L133 222 L123 226 L119 236 L115 226 L105 222 L115 218Z" />
                <circle cx="181" cy="235" r="4" />
                <circle cx="159" cy="199" r="3" />
              </g>
            ) : (
              <path d="M150 194 L150 250 M127 213 L150 224 L173 213" fill="none" stroke="#F7D6A1" strokeWidth="4" />
            )}
          </g>
        )}
        {back === "explorer-backpack" && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path d="M183 181 Q207 171 222 190 L229 236 Q218 250 190 242 L180 211Z" fill="#B77B42" />
            <path d="M190 198 Q207 190 220 200 L220 219 L190 221Z" fill="#E7B96D" />
            <path d="M198 181 Q193 162 205 157 Q220 156 221 183" fill="none" strokeWidth="7" />
            <path d="M194 222 L220 222" stroke="#70472F" strokeWidth="3" />
          </g>
        )}

        {/* Tail and feet are drawn before the torso and clothing. */}
        <path
          d={corgi
            ? "M202 209 Q248 204 247 231 Q245 251 221 239"
            : "M202 208 Q250 179 255 210 Q260 238 226 242"}
          fill="none"
          stroke={coat}
          strokeWidth="19"
          strokeLinecap="round"
        />
        <path d="M238 207 Q248 204 250 214" fill="none" stroke={fur.light} strokeWidth="6" strokeLinecap="round" />

        <path d="M111 225 Q102 247 108 267 Q116 281 139 271 L145 242Z" fill={coat} stroke={outline} strokeWidth="4" strokeLinejoin="round" />
        <path d="M189 225 Q198 247 192 267 Q184 281 161 271 L155 242Z" fill={coat} stroke={outline} strokeWidth="4" strokeLinejoin="round" />
        <ellipse cx="123" cy="270" rx="20" ry="10" fill={fur.light} stroke={outline} strokeWidth="3" />
        <ellipse cx="177" cy="270" rx="20" ry="10" fill={fur.light} stroke={outline} strokeWidth="3" />
        <path d="M110 270 L135 270 M165 270 L190 270" stroke={outline} strokeOpacity=".42" strokeWidth="2" strokeLinecap="round" />

        {/* Torso: a simple, fitted silhouette rather than a separate floating costume image. */}
        <path
          d="M102 169 Q118 157 137 160 L163 160 Q182 157 198 169 Q218 187 216 236 Q209 257 150 260 Q91 257 84 236 Q82 187 102 169Z"
          fill={coat}
          stroke={outline}
          strokeWidth="5"
          strokeLinejoin="round"
        />
        {!clothing && (
          <path d="M119 181 Q150 198 181 181 L180 240 Q150 253 120 240Z" fill={fur.light} opacity=".88" />
        )}

        {clothing && (
          <g stroke={clothing.shade} strokeWidth="4" strokeLinejoin="round">
            <path
              d="M101 177 Q116 164 135 166 L165 166 Q184 164 199 177 L219 210 L202 229 L190 215 L187 251 Q150 263 113 251 L110 215 L98 229 L81 210Z"
              fill={clothing.base}
            />
            {clothingIsHoodie && (
              <>
                <path d="M119 174 Q150 207 181 174 Q177 195 150 202 Q123 195 119 174Z" fill={clothing.shade} />
                <path d="M139 199 L136 222 M161 199 L164 222" stroke={clothing.trim} strokeWidth="3" strokeLinecap="round" />
                <path d="M127 232 Q150 239 173 232 L170 247 Q150 253 130 247Z" fill={clothing.shade} />
              </>
            )}
            {clothing.style === "jacket" && (
              <>
                <path d="M150 184 L150 252" stroke={clothing.trim} strokeWidth="4" />
                <path d="M125 194 L141 204 M175 194 L159 204" stroke={clothing.trim} strokeWidth="3" />
                <path d="M113 226 L135 226 M165 226 L187 226" stroke={clothing.trim} strokeWidth="3" strokeLinecap="round" />
              </>
            )}
            {clothing.style === "scholar" && (
              <>
                <path d="M126 174 L150 194 L174 174" fill="#F7F0DE" stroke={clothing.shade} strokeWidth="3" />
                <path d="M145 193 L150 202 L155 193 L157 228 L150 234 L143 228Z" fill="#B85F5D" stroke={clothing.shade} strokeWidth="2" />
                <path d="M118 243 L182 243" stroke={clothing.trim} strokeWidth="3" />
              </>
            )}
            {clothing.style === "armor" && (
              <>
                <path d="M116 188 Q150 207 184 188 L174 231 Q150 243 126 231Z" fill={clothing.shade} stroke={clothing.trim} strokeWidth="3" />
                <path d="M150 193 L156 209 L150 224 L144 209Z" fill={clothing.trim} stroke={clothing.shade} strokeWidth="2" />
                <path d="M110 237 Q150 246 190 237" fill="none" stroke={clothing.trim} strokeWidth="5" />
              </>
            )}
            {clothing.style === "champion" && (
              <>
                <path d="M150 191 L156 204 L170 206 L160 216 L163 230 L150 223 L137 230 L140 216 L130 206 L144 204Z" fill={clothing.trim} stroke={clothing.shade} strokeWidth="2" />
                <path d="M113 239 Q150 250 187 239" fill="none" stroke={clothing.trim} strokeWidth="4" />
              </>
            )}
          </g>
        )}

        {/* Paws overlap the sleeves, making the clothes follow the dog's anatomy. */}
        <path d="M91 211 Q79 222 87 242 Q94 253 108 243 L113 218Z" fill={coat} stroke={outline} strokeWidth="4" strokeLinejoin="round" />
        <path d="M209 211 Q221 222 213 242 Q206 253 192 243 L187 218Z" fill={coat} stroke={outline} strokeWidth="4" strokeLinejoin="round" />
        <path d="M91 237 Q99 246 107 239 M193 239 Q201 246 209 237" fill="none" stroke={fur.light} strokeWidth="3" strokeLinecap="round" />

        {pants && (
          <g stroke="#33445D" strokeWidth="4" strokeLinejoin="round">
            <path d="M109 237 Q150 249 191 237 L188 265 Q169 276 151 263 Q132 276 112 265Z" fill="#3C5C91" />
            <path d="M150 249 L150 265" stroke="#D8E5F5" strokeWidth="3" />
            <circle cx="150" cy="254" r="3" fill="#F2CB72" stroke="none" />
          </g>
        )}
        {shoes && (
          <g stroke={outline} strokeWidth="3.5" strokeLinejoin="round">
            <path d="M104 262 Q99 275 112 280 L140 280 Q146 274 138 264Z" fill={shoes === "sprint-shoes" ? "#E98E4B" : "#38516E"} />
            <path d="M162 264 Q154 274 160 280 L188 280 Q201 275 196 262Z" fill={shoes === "sprint-shoes" ? "#E98E4B" : "#38516E"} />
            <path d="M109 274 L136 274 M164 274 L191 274" fill="none" stroke="#F8F0DD" strokeWidth="3" strokeLinecap="round" />
          </g>
        )}

        {/* Ears are part of the dog's silhouette, never separate product art. */}
        {pointyEars ? (
          <g stroke={outline} strokeWidth="5" strokeLinejoin="round">
            <path d={corgi ? "M77 113 Q40 3 111 37 Q133 53 119 139Z" : "M78 112 Q52 12 113 42 Q133 62 119 139Z"} fill={coat} />
            <path d={corgi ? "M86 101 Q65 34 101 54 L108 117Z" : "M87 99 Q72 44 104 61 L108 116Z"} fill={fur.inner} stroke="none" />
            <path d={corgi ? "M223 113 Q260 3 189 37 Q167 53 181 139Z" : "M222 112 Q248 12 187 42 Q167 62 181 139Z"} fill={coat} />
            <path d={corgi ? "M214 101 Q235 34 199 54 L192 117Z" : "M213 99 Q228 44 196 61 L192 116Z"} fill={fur.inner} stroke="none" />
          </g>
        ) : (
          <g stroke={outline} strokeWidth="5" strokeLinejoin="round">
            <path d={longEars
              ? "M81 90 Q35 76 48 151 Q61 181 101 153Z"
              : "M82 91 Q48 72 52 139 Q60 164 101 151Z"} fill={coat} />
            <path d="M64 112 Q57 120 68 149 Q78 157 89 139Z" fill={fur.inner} stroke="none" />
            <path d={longEars
              ? "M219 90 Q265 76 252 151 Q239 181 199 153Z"
              : "M218 91 Q252 72 248 139 Q240 164 199 151Z"} fill={coat} />
            <path d="M236 112 Q243 120 232 149 Q222 157 211 139Z" fill={fur.inner} stroke="none" />
          </g>
        )}

        {/* Head and breed markings. Flat color blocks keep the dog readable at small sizes. */}
        <ellipse
          cx="150"
          cy={broadFace ? 132 : 130}
          rx={broadFace ? 93 : corgi ? 87 : 89}
          ry={broadFace ? 84 : 86}
          fill={coat}
          stroke={outline}
          strokeWidth="5"
        />
        {husky && (
          <path d="M150 45 Q120 76 125 145 Q137 159 150 157 Q163 159 175 145 Q180 76 150 45Z" fill="#F2F1E8" />
        )}
        {shiba && (
          <path d="M150 48 Q123 78 126 131 L150 151 L174 131 Q177 78 150 48Z" fill="#F5DCC0" />
        )}
        {corgi && (
          <path d="M80 101 Q92 54 150 48 Q208 54 220 101 Q190 83 150 82 Q110 83 80 101Z" fill={fur.light} opacity=".75" />
        )}
        {broadFace && (
          <g fill="none" stroke={fur.shade} strokeWidth="3" strokeLinecap="round" opacity=".75">
            <path d="M108 92 Q123 100 137 94 M163 94 Q177 100 192 92" />
            <path d="M110 104 Q124 111 137 105 M163 105 Q176 111 190 104" />
          </g>
        )}

        {/* Face */}
        <ellipse cx="150" cy="166" rx={snoutWidth} ry="35" fill={fur.muzzle} />
        <ellipse cx="119" cy="126" rx="13" ry="16" fill="#FFFDF7" />
        <ellipse cx="181" cy="126" rx="13" ry="16" fill="#FFFDF7" />
        <ellipse cx="121" cy="129" rx="7" ry="10" fill={eye} />
        <ellipse cx="179" cy="129" rx="7" ry="10" fill={eye} />
        <ellipse cx="122" cy="132" rx="3.2" ry="5" fill="#2E2927" />
        <ellipse cx="180" cy="132" rx="3.2" ry="5" fill="#2E2927" />
        <circle cx="124" cy="123" r="2.6" fill="#FFFFFF" />
        <circle cx="182" cy="123" r="2.6" fill="#FFFFFF" />
        <path d="M104 108 Q118 101 134 107 M166 107 Q182 101 196 108" fill="none" stroke={outline} strokeWidth="4" strokeLinecap="round" />
        <ellipse cx="150" cy="162" rx={broadFace ? 14 : 12} ry="8" fill="#343B42" />
        <path d="M150 169 Q148 181 137 185 M150 169 Q152 181 163 185" fill="none" stroke="#654637" strokeWidth="3" strokeLinecap="round" />
        <path d="M140 184 Q150 193 160 184" fill="none" stroke="#8B514B" strokeWidth="3" strokeLinecap="round" />
        <ellipse cx="111" cy="174" rx="15" ry="8" fill="#E99A91" opacity=".18" />
        <ellipse cx="189" cy="174" rx="15" ry="8" fill="#E99A91" opacity=".18" />
        <g fill={outline} opacity=".62">
          <circle cx="111" cy="174" r="1.8" />
          <circle cx="120" cy="179" r="1.5" />
          <circle cx="189" cy="174" r="1.8" />
          <circle cx="180" cy="179" r="1.5" />
        </g>

        {eyes === "starry-eyes" && (
          <g fill="#F6D66E" stroke="#9A702F" strokeWidth="1.5">
            <path d="M119 111 L123 119 L132 121 L123 125 L119 134 L115 125 L106 121 L115 119Z" />
            <path d="M181 111 L185 119 L194 121 L185 125 L181 134 L177 125 L168 121 L177 119Z" />
          </g>
        )}

        {/* Collar and bandana wrap around the neck, with the lower point following the chest. */}
        {collar && (
          <g stroke={outline} strokeWidth="3.5" strokeLinejoin="round">
            <path d="M111 190 Q150 210 189 190 L185 202 Q150 222 115 202Z" fill={collar === "fire-collar" ? "#D95C45" : collar === "programmer-collar" ? "#3F8D83" : "#C64F57"} />
            <circle cx="150" cy="211" r="6" fill="#F1C56F" />
          </g>
        )}
        {neckwear && (
          <g stroke={outline} strokeWidth="3.5" strokeLinejoin="round">
            <path d="M114 190 Q150 211 186 190 L178 209 Q150 222 122 209Z" fill={neckwear === "comet-bandana" ? "#7156B5" : neckwear === "streak-bandana" ? "#C34E4E" : "#2A966F"} />
            <path d="M126 205 L150 229 L174 205 Q170 229 150 239 Q130 229 126 205Z" fill={neckwear === "comet-bandana" ? "#9274D0" : neckwear === "streak-bandana" ? "#E97968" : "#45B88A"} />
            <path d="M142 215 L150 220 L158 215" fill="none" stroke="#E8F4D8" strokeWidth="2.5" strokeLinecap="round" />
          </g>
        )}

        {/* Glasses follow the eye line and use simple flat frames. */}
        {glasses === "cyber-visor" ? (
          <g stroke="#253747" strokeWidth="4" strokeLinejoin="round">
            <path d="M91 116 Q150 104 209 116 L205 145 Q150 158 95 145Z" fill="#4A9DC0" fillOpacity=".88" />
            <path d="M103 124 L132 124 M168 124 L197 124" stroke="#D9F8FF" strokeWidth="4" strokeLinecap="round" />
          </g>
        ) : glasses ? (
          <g fill="none" stroke={glasses === "golden-battle-glasses" ? "#C58D37" : "#35485A"} strokeWidth="5">
            {glasses === "golden-battle-glasses" ? (
              <>
                <circle cx="119" cy="130" r="20" />
                <circle cx="181" cy="130" r="20" />
              </>
            ) : (
              <>
                <rect x="94" y="112" width="49" height="35" rx="12" />
                <rect x="157" y="112" width="49" height="35" rx="12" />
              </>
            )}
            <path d="M143 126 Q150 121 157 126" />
            <path d="M94 124 L84 120 M206 124 L216 120" strokeWidth="4" />
          </g>
        ) : null}

        {face === "xp-champion-accessory" && (
          <g stroke="#8E672C" strokeWidth="3">
            <circle cx="211" cy="177" r="14" fill="#F0C34F" />
            <path d="M204 177 L209 182 L219 170" fill="none" stroke="#FFF8D8" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
          </g>
        )}

        {/* Headwear rests on the head silhouette; headphones wrap around both ears. */}
        {hatIsHeadset && (
          <g fill="none" stroke={headwear === "master-headphones" ? "#7B65B5" : "#3F667F"} strokeWidth="10" strokeLinecap="round">
            <path d="M88 108 Q88 39 150 36 Q212 39 212 108" />
            <path d="M88 91 Q83 93 84 111 L84 133 Q84 145 98 145 L105 145 L105 103Z" fill={headwear === "master-headphones" ? "#9B7BD0" : "#5C91AB"} stroke={outline} strokeWidth="4" />
            <path d="M212 91 Q217 93 216 111 L216 133 Q216 145 202 145 L195 145 L195 103Z" fill={headwear === "master-headphones" ? "#9B7BD0" : "#5C91AB"} stroke={outline} strokeWidth="4" />
          </g>
        )}
        {hatIsCrown && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path d="M101 67 L106 33 L128 50 L150 24 L172 50 L194 33 L199 67Z" fill={headwear === "diamond-crown" ? "#68B9D2" : headwear === "compiler-crown" ? "#687995" : "#E5B94E"} />
            <path d="M103 67 L197 67 L191 78 L109 78Z" fill={headwear === "diamond-crown" ? "#3F91B0" : headwear === "compiler-crown" ? "#43536B" : "#BD862E"} />
            <circle cx="150" cy="55" r="5" fill="#FFF0B4" stroke="none" />
          </g>
        )}
        {headwear === "wizard-hat" && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path d="M108 70 Q139 33 127 4 Q164 13 188 70Z" fill="#5B538F" />
            <path d="M96 70 Q150 57 204 70 L198 82 Q150 91 102 82Z" fill="#3F3C70" />
            <path d="M149 32 L155 43 L167 46 L155 51 L149 63 L144 51 L132 46 L144 43Z" fill="#F2D779" stroke="none" />
          </g>
        )}
        {headwear === "graduation-hat" && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path d="M91 50 L150 26 L209 50 L150 72Z" fill="#37465D" />
            <path d="M116 62 L116 76 Q150 92 184 76 L184 62" fill="#4C5E79" />
            <path d="M204 51 L207 83" stroke="#E5C46E" strokeWidth="3" />
            <circle cx="207" cy="86" r="4" fill="#E5C46E" stroke="none" />
          </g>
        )}
        {headwear && !hatIsHeadset && !hatIsCrown && headwear !== "wizard-hat" && headwear !== "graduation-hat" && (
          <g stroke={outline} strokeWidth="4" strokeLinejoin="round">
            <path d="M103 67 Q106 31 150 29 Q194 31 197 67Z" fill={headwear === "battle-champion-cap" ? "#365D82" : "#B67C43"} />
            <path d="M90 66 Q150 83 210 66 Q206 79 150 81 Q94 79 90 66Z" fill={headwear === "battle-champion-cap" ? "#294966" : "#8D5A31"} />
            {headwear === "battle-champion-cap" && <path d="M150 42 L155 51 L165 53 L157 60 L159 69 L150 64 L141 69 L143 60 L135 53 L145 51Z" fill="#E8C66C" stroke="none" />}
          </g>
        )}

        <path d="M137 153 Q150 158 163 153" fill="none" stroke="#D6AA87" strokeWidth="2" strokeLinecap="round" opacity=".65" />
      </g>
    </svg>
  );
}

export default DogAvatar;
