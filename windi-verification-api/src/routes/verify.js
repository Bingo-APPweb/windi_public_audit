import express from "express";
import { verifyDocument } from "../services/verificationService.js";

const router = express.Router();

router.post("/", async (req, res) => {
  try {
    const result = await verifyDocument(req.body);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(400).json({ error: err.message });
  }
});

export default router;
