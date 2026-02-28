const express = require("express");
const path = require("path");
const { v4: uuid } = require("uuid");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

let users = [];
let referrals = [];

app.post("/register", (req, res) => {
  const telegram_id = req.body.telegram_id;
  const referrer = req.body.referrer;

  const public_id = uuid();
  users.push({ telegram_id: telegram_id, public_id: public_id, created_at: Date.now() });

  if (referrer) {
    referrals.push({ referrer: referrer, new_user: public_id, timestamp: Date.now() });
  }

  res.json({ public_id: public_id });
});

app.get("/api/profile/:id", (req, res) => {
  const id = req.params.id;
  const profile = users.find(u => u.public_id === id);
  if (!profile) return res.status(404).json({ error: "Not found" });
  res.json(profile);
});

app.get("/join", (req, res) => {
  const r = req.query.r;
  res.redirect("/profile.html?id=" + r);
});

app.listen(3000, () => console.log("Server running on http://localhost:3000"));
