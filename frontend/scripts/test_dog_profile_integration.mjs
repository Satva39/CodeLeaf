import fs from "node:fs";
import assert from "node:assert/strict";

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), "utf8");
const header = read("../src/components/layout/Header.jsx");
const context = read("../src/components/avatar/DogAvatarContext.jsx");
const profile = read("../src/pages/ProfilePage.jsx");
const editor = read("../src/components/avatar/DogAvatarEditor.jsx");
const app = read("../src/App.jsx");
const achievementNotice = read("../src/components/avatar/AchievementRewardNotice.jsx");
const leaderboard = read("../src/pages/LeaderboardPage.jsx");

assert.match(header, /if \(!variant \|\| variant === "dog"\)/, "default profile avatar must render the dog");
assert.match(header, /<DogAvatar/, "shared profile avatar must use the dog renderer");
assert.match(header, /useDogAvatar/, "header avatar must read account dog state");
assert.match(context, /\/api\/me\/avatar/, "shared dog state must load the authenticated avatar API");
assert.match(context, /codeleaf:dog-avatar-changed/, "customization updates must refresh shared profile pictures");
assert.match(profile, /Edit profile/, "profile must expose an Edit profile action");
assert.match(profile, /<DogAvatarEditor compact \/>/, "dog customization must live inside Edit profile");
assert.match(profile, /<Avatar size="xl" \/>/, "main profile image must use the dog avatar");
assert.doesNotMatch(profile, /AVATAR STUDIO|avatars\.map|avatarPick/, "legacy generic icon selector must be removed from profile editing");
assert.match(editor, /\/api\/me\/avatar\/appearance/, "breed and color choices must save through the existing API");
assert.match(editor, /\/api\/me\/avatar\/equipment/, "equipment must use the ownership-checked existing API");
assert.match(app, /path="\/avatar" element={<Navigate to="\/profile\?edit=1#dog-avatar" replace \/>}/, "legacy avatar URL must redirect into profile editing");
assert.doesNotMatch(header, /Dog Avatar Studio/, "separate studio navigation must be removed");
assert.match(achievementNotice, /\/profile\?edit=1#dog-avatar/, "reward links must open profile dog customization");
assert.match(leaderboard, /dogAvatar=\{row\.dog_avatar\}/, "leaderboard profile pictures must use each learner's dog");

console.log("Dog profile integration contract passed.");
