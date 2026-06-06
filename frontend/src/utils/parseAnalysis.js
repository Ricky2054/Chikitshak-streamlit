export function parseAnalysis(text) {
  if (!text) {
    return { summary: "", guidance: [], redFlags: [], sources: [], medications: [] };
  }

  const sections = { summary: "", guidance: [], redFlags: [], sources: [], medications: [] };

  const extract = (label, nextLabels) => {
    const pattern = new RegExp(
      `${label}:\\s*([\\s\\S]*?)(?=\\n(?:${nextLabels.join("|")}):|$)`,
      "i"
    );
    const match = text.match(pattern);
    return match ? match[1].trim() : "";
  };

  sections.summary = extract("Summary", ["Guidance", "Red Flags", "Medications", "Sources"]);
  const guidanceRaw = extract("Guidance", ["Red Flags", "Medications", "Sources"]);
  const redFlagsRaw = extract("Red Flags", ["Medications", "Sources"]);
  const medsRaw = extract("Medications", ["Sources"]);
  const sourcesRaw = extract("Sources", []);

  const toBullets = (raw) =>
    raw
      .split("\n")
      .map((line) => line.replace(/^[-•*]\s*/, "").trim())
      .filter(Boolean);

  sections.guidance = toBullets(guidanceRaw);
  sections.redFlags = toBullets(redFlagsRaw);
  sections.medications = toBullets(medsRaw);
  sections.sources = toBullets(sourcesRaw);

  if (!sections.summary && !sections.guidance.length) {
    sections.summary = text.trim();
  }

  return sections;
}
