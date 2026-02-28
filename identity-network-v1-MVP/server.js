const express = require("express");
const { v4: uuid } = require("uuid");

const app = express();
app.use(express.json());

let users = [];
let referrals = [];

app.post("/register", (req, res) => {
  const { telegram_id, referrer } = req.body;

  const public_id = uuid();
  users.push({ telegram_id, public_id, created_at: Date.now() });

  if (referrer) {
    referrals.push({ referrer, new_user: public_id, timestamp: Date.now() });
  }

  res.json({ public_id });
});

app.get("/join", (req, res) => {
  const { r } = req.query;
  res.send(`הוזמנת על ידי: ${r}`);
});

app.listen(3000, () => console.log("Server running on http://localhost:3000"));
