import fs from "node:fs";
import assert from "node:assert/strict";

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), "utf8");
const context = read("../src/components/avatar/DogAvatarContext.jsx");
const editor = read("../src/components/avatar/DogAvatarEditor.jsx");
const dog = read("../src/components/avatar/DogAvatar.jsx");
const profile = read("../src/pages/ProfilePage.jsx");
const header = read("../src/components/layout/Header.jsx");
const backend = read("../../backend/app/games_routes.py");
const gamification = read("../../backend/app/gamification.py");

assert.match(context, /CACHE_TTL_MS = 30_000/, "dog state is cached across profile/header consumers");
assert.match(context, /inFlightRequest/, "concurrent dog requests are deduplicated");
assert.match(context, /REQUEST_TIMEOUT_MS = 12_000/, "dog API reads have a bounded timeout");
assert.match(context, /Keep the last good dog visible/, "temporary errors do not replace the saved dog with a default");
assert.match(context, /dogAvatarError/, "avatar load failures can be retried by the editor");
assert.doesNotMatch(editor, /apiFetch\(\`\$\{API_BASE\}\/api\/me\/avatar\`/, "the editor does not issue a duplicate avatar GET");
assert.match(editor, /useDogAvatar/, "the editor and header share the same avatar state");
assert.match(editor, /equipmentForItem/, "item previews normalize the visible clothing layer");
assert.match(editor, /<DogAvatar[\s\S]*?equipment=\{previewEquipment\}/, "each catalog item is previewed on the actual dog renderer");
assert.match(dog, /shirt \|\| outfit/, "the shared renderer gives the selected shirt/jacket a consistent visible layer");
assert.match(dog, /blue-hoodie/, "clothing item IDs have explicit artwork mapping");
assert.match(dog, /developer-jacket/, "jacket item IDs have explicit artwork mapping");
assert.match(profile, /timeoutMs: 8_000/, "profile account reads have bounded timeouts");
assert.match(profile, /Retry account loading/, "profile can recover from a temporary account API failure");
assert.match(header, /timeoutMs: 8_000/, "header session checks do not wait indefinitely");
assert.match(backend, /equipment\.pop\("outfit", None\)/, "equipping a shirt clears an overlapping full outfit");
assert.match(backend, /equipment\.pop\("shirt", None\)/, "equipping a full outfit clears an overlapping shirt");
assert.match(gamification, /def _completed_course_count[\s\S]*?group_by\(Module\.course_id\)[\s\S]*?having\(completed_lessons >= func\.count\(Lesson\.id\)\)/, "completed-course achievement checks use one aggregate query");

for (const asset of [
  "explorer-cap.webp", "teal-crown.webp", "wizard-hat.webp", "coding-headset.webp",
  "developer-glasses.webp", "cyber-visor.webp", "blue-hoodie.webp", "developer-jacket.webp",
  "red-collar.webp", "emerald-bandana.webp", "explorer-backpack.webp", "hero-cloak.webp",
]) {
  assert.ok(fs.existsSync(new URL(`../src/assets/avatar/items/${asset}`, import.meta.url)), `missing generated accessory art: ${asset}`);
}

console.log("Dog avatar consistency and profile-loading contracts passed.");
