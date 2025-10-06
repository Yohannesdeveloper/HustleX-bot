/*
 * Netlify Function: submission-created
 * Triggered automatically whenever a Netlify Form submission is created.
 * It forwards job-posting form fields to a Telegram channel.
 *
 * Environment variables required (set them in the Netlify dashboard → Site settings → Environment Variables):
 *   BOT_TOKEN   – Telegram Bot token, e.g. 123456:ABCDEF...
 *   CHANNEL_ID  – Target chat ID or @channel_username (recommended: numeric channel ID that starts with -100)
 *   WEBSITE_URL – Optional, base URL to display in the footer of the post (defaults to the Netlify site URL)
 */

const https = require("https");

// Minimal HTML escaper to keep Telegram safe
function escapeHtml(str = "") {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildTelegramMessage(data, siteUrl) {
  const esc = escapeHtml;
  const descRaw = (data.description || "").trim();
  const description = descRaw.length > 1500 ? `${descRaw.slice(0, 1500)}…` : descRaw;

  return (
    `<b>📢 New Job Posted!</b><br><br>` +
    `<b>Job Title:</b> ${esc(data.job_title)}<br>` +
    `<b>Job Type:</b> ${esc(data.job_type)}<br>` +
    `<b>Location:</b> ${esc(data.work_location)}<br>` +
    `<b>Salary:</b> ${esc(data.salary)}<br>` +
    `<b>Deadline:</b> ${esc(data.deadline)}<br>` +
    `<b>Description:</b> ${esc(description)}<br>` +
    `<b>Client Type:</b> ${esc(data.client_type)}<br>` +
    `<b>Company Name:</b> ${esc(data.company_name)}<br>` +
    `<b>Verified:</b> ${esc(data.verified)}<br>` +
    `<b>Previous Jobs:</b> ${esc(data.previous_jobs)}<br><br>` +
    `From: ${esc(siteUrl)}`
  );
}

function sendMessage({ botToken, chatId, html, buttonUrl }) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      chat_id: chatId,
      text: html,
      parse_mode: "HTML",
      disable_web_page_preview: true,
      reply_markup: {
        inline_keyboard: [[{ text: "View Details", url: buttonUrl }]],
      },
    });

    const options = {
      hostname: "api.telegram.org",
      path: `/bot${botToken}/sendMessage`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(postData),
      },
    };

    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const json = JSON.parse(data);
          if (json.ok) return resolve(json);
          return reject(new Error(json.description || "Telegram error"));
        } catch (e) {
          return reject(new Error("Invalid Telegram response"));
        }
      });
    });

    req.on("error", (err) => reject(err));
    req.write(postData);
    req.end();
  });
}

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 200, body: "Function expects a POST" };
  }

  const BOT_TOKEN = process.env.BOT_TOKEN;
  const CHANNEL_ID = process.env.CHANNEL_ID;
  const SITE_URL = process.env.WEBSITE_URL || event.headers["x-netlify-scheme"] + "://" + event.headers.host;

  if (!BOT_TOKEN || !CHANNEL_ID) {
    return {
      statusCode: 500,
      body: "BOT_TOKEN or CHANNEL_ID env vars not set",
    };
  }

  let payload;
  try {
    payload = JSON.parse(event.body);
  } catch (e) {
    return { statusCode: 400, body: "Invalid JSON body" };
  }

  const formData = payload.data || {};

  // Build Telegram message & button URL (fallback to site root)
  const detailsUrl = (formData.job_link || "").trim() || SITE_URL;
  const messageHTML = buildTelegramMessage(formData, SITE_URL);

  try {
    await sendMessage({
      botToken: BOT_TOKEN,
      chatId: CHANNEL_ID,
      html: messageHTML,
      buttonUrl: detailsUrl,
    });

    return {
      statusCode: 200,
      body: JSON.stringify({ ok: true }),
    };
  } catch (err) {
    console.error("Telegram send error:", err);
    return {
      statusCode: 500,
      body: JSON.stringify({ ok: false, error: err.message }),
    };
  }
};
