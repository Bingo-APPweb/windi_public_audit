import express from "express";
import morgan from "morgan";
import verifyRoute from "./routes/verify.js";

const app = express();

app.use(express.json());
app.use(morgan("combined"));

app.get("/health", (req, res) => {
  res.json({ status: "WINDI Verification API running" });
});

app.use("/verify", verifyRoute);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`WINDI Verification API listening on port ${PORT}`);
});
