const { Telegraf } = require("telegraf");
const axios = require("axios");
const QRCode = require("qrcode");

const bot = new Telegraf("8530795944:AAHkWXBFRZBtrObRCcSxrft1USdx2HgU6lw");

bot.start(async (ctx) => {
  const telegram_id = ctx.from.id;
  const referrer = ctx.startPayload || null;

  const res = await axios.post("http://localhost:3000/register", {
    telegram_id: telegram_id,
    referrer: referrer
  });

  const public_id = res.data.public_id;
  const joinUrl = "http://localhost:3000/join?r=" + public_id;
  const qr = await QRCode.toBuffer(joinUrl);

  await ctx.reply("הנה ה‑QR האישי שלך:");
  await ctx.replyWithPhoto({ source: qr });
});

bot.launch().then(() => console.log("Bot is running"));
