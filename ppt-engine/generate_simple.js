#!/usr/bin/env node
/**
 * Simple PPTX Generator for Dragon Server
 * Usage: node generate_simple.js input.json output.pptx
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node generate_simple.js input.json output.pptx");
  process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1];

try {
  const input = JSON.parse(fs.readFileSync(inputFile, "utf-8"));
  const pres = new pptxgen();

  // WINDI branding
  pres.author = "WINDI Publishing House";
  pres.company = "WINDI";
  pres.subject = input.title || "WINDI Document";
  pres.title = input.title || "WINDI Presentation";

  // NOIR theme colors
  const GOLD = "C9A227";
  const BG = "0A0A0F";
  const TEXT = "E8E8EC";

  // Title slide
  const titleSlide = pres.addSlide();
  titleSlide.background = { color: BG };
  titleSlide.addText(input.title || "WINDI Document", {
    x: 0.5, y: 2, w: 9, h: 1,
    fontSize: 36, fontFace: "Arial", color: GOLD, bold: true, align: "center"
  });
  titleSlide.addText(input.serial || new Date().toISOString().slice(0, 10), {
    x: 0.5, y: 3.2, w: 9, h: 0.5,
    fontSize: 14, fontFace: "Arial", color: TEXT, align: "center"
  });
  titleSlide.addText("KI verarbeitet. Der Mensch entscheidet. WINDI garantiert.", {
    x: 0.5, y: 5, w: 9, h: 0.3,
    fontSize: 10, fontFace: "Arial", color: TEXT, italic: true, align: "center"
  });

  // Content slides
  const slides = input.slides || [];
  slides.forEach((slideData, idx) => {
    const slide = pres.addSlide();
    slide.background = { color: BG };

    // Title
    slide.addText(slideData.title || `Slide ${idx + 1}`, {
      x: 0.5, y: 0.3, w: 9, h: 0.6,
      fontSize: 24, fontFace: "Arial", color: GOLD, bold: true
    });

    // Content
    slide.addText(slideData.content || "", {
      x: 0.5, y: 1.1, w: 9, h: 4,
      fontSize: 14, fontFace: "Arial", color: TEXT, valign: "top"
    });

    // Footer
    slide.addText(`${input.serial || "WINDI"} | Slide ${idx + 2}`, {
      x: 0.5, y: 5.2, w: 9, h: 0.3,
      fontSize: 8, fontFace: "Arial", color: "666666", align: "right"
    });
  });

  // Save
  pres.writeFile({ fileName: outputFile })
    .then(() => {
      console.log("OK");
      process.exit(0);
    })
    .catch(err => {
      console.error("Write error:", err.message);
      process.exit(1);
    });

} catch (err) {
  console.error("Error:", err.message);
  process.exit(1);
}
