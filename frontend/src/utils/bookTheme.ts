const COVER_GRADIENTS = [
  "linear-gradient(160deg,#1f3f47,#152c32)",
  "linear-gradient(160deg,#5c2233,#421826)",
  "linear-gradient(160deg,#22402c,#182e20)",
  "linear-gradient(160deg,#6b4a1f,#4c3416)",
  "linear-gradient(160deg,#3a2c52,#291f3a)",
  "linear-gradient(160deg,#6b2f1a,#4c2112)",
  "linear-gradient(160deg,#24384a,#192734)",
  "linear-gradient(160deg,#463424,#31241a)",
];

const SPINE_COLORS = [
  "#1f3f47",
  "#5c2233",
  "#22402c",
  "#3a2c52",
  "#6b4a1f",
  "#6b2f1a",
  "#24384a",
  "#463424",
];

export function coverGradient(seed: number | string): string {
  const key = typeof seed === "number" ? seed : seed.length;
  return COVER_GRADIENTS[Math.abs(key) % COVER_GRADIENTS.length];
}

export function spineColor(index: number): string {
  return SPINE_COLORS[index % SPINE_COLORS.length];
}
