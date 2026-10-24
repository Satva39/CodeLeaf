import { readFileSync } from "node:fs";
import { parse } from "@babel/parser";
import { resolve } from "node:path";
for (const file of [
  "src/pages/LessonPage.jsx",
  "src/components/lessons/LessonLiveExample.jsx",
]) {
  const source = readFileSync(resolve(process.cwd(), file), "utf8");
  parse(source, { sourceType: "module", plugins: ["jsx", "importMeta", "optionalChaining", "nullishCoalescingOperator"] });
  console.log(`JSX parse passed: ${file}`);
}
