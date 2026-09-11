import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const expectedMedia: Record<string, string> = {
  "public/media/stonkhedge-crystal.png": "ee49acb3b320ee13bc28346c2f148baa52227e3101a00947a1e28de8e989931f",
  "public/media/stonkhedge-park.jpg": "6f134a3b538fe47717c2ac8796542a36f3559c55fee9936cb54995e6ffae846b",
  "public/media/stonkhedge-progress.mp4": "a70dad41a25b358b0ed82fb5c2aa29bc2334ea27675423a6c862ca0e276daf7b",
  "public/media/stonkhedge-testnet-hero.jpg": "ff17694013b6ac46409a1d9b5763849fa5b55498a5f8cb968129222399ab1d0f",
  "public/media/park/bench-left.png": "01fdbd296d1157b50587c764c64851527cf20a8c67e157dc13bdeaaed6b7d2d2",
  "public/media/park/bench-right.png": "b0bd1d37e5f71778cbf60293eb27d04e1dc74f5915f1b61c39ba18d38a9266fb",
  "public/media/park/cloud-left.png": "a254f09250ed2311c6c6ab94fbfcf1760b3bc3dce1676b4552af41419677d18a",
  "public/media/park/cloud-right.png": "afc5143c7dad6a76a4b5e43cadb6d85f915f86e1176f211627cfd1458347ff7f",
  "public/media/park/flowers-left.png": "12c7dadb514544fd7fd57d27cce0860909e4d79cf756591a6ee4f0f0e113511d",
  "public/media/park/flowers-right.png": "6a76ae5860e88896d154f90f54490668e83d957f5ea6d498ae161095fe0e859e",
  "public/media/park/grass.png": "c91196913eca774c1a9930d6d42bb3f28a8796e785ba50ec658643e93a0bfcf9",
  "public/media/park/lamp.png": "382e04fa5641aaf12fcaadfd953ac23023dd3b8a0ba2444206cdea011fc9aca3",
  "public/media/park/platform.png": "8622fff08a1d39a05e518e7c6de57de5b501a5ac23bf5df20bfe097a49ec267b",
  "public/media/park/sky.png": "be935626ad06e3d83a39b05163047065be03359395db4a8c1dc1a53c48d57c1c",
  "public/media/park/skyline.png": "8151e695670170f4f5206174174a3f47eea58ff97cfde5598ed7aadaaffb88a3",
  "public/media/park/tree-canopy.png": "58c88dad77f540ac4c52e05a611837de497b0e1fd1f21918f671f1bf399b7c89",
  "public/media/park/tree-center.png": "e16514975752becc0c09cef27b10a5503b72fb5c586bb09af9d0175ae85f62ed",
  "public/media/park/tree-left.png": "fe4ebdc1650f703fb4827f87429ea96d720352e8cd7535a65881891a9c661f70",
  "public/media/park/tree-small.png": "5512517f0c274d70248abf959c59de48c138e8a95e188b6028205aca7bf9809a",
  "public/media/park/walkway.png": "7c7d7779b2ba88e966f145b968eba3de33d1e72a0e7eb11d85ffd546aaa7e8a9",
};

describe("brand media provenance", () => {
  it("keeps every published media file byte-identical to its recorded source", () => {
    Object.entries(expectedMedia).forEach(([path, expectedHash]) => {
      const hash = createHash("sha256").update(readFileSync(resolve(process.cwd(), path))).digest("hex");
      expect(hash, path).toBe(expectedHash);
    });
  });
});
