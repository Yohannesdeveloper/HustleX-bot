# HustleX – Netlify → Telegram Job Posting

This repository now contains a **Netlify Function** that automatically forwards Netlify Form submissions to your Telegram channel.

## How it works

1. Your public site hosts a form (e.g. `post_job.html`) with **Netlify Forms** enabled.
2. When a visitor submits the form, Netlify stores the submission and fires a **submission-created** event.
3. Netlify invokes `netlify/functions/submission-created.js` (added in this commit).
4. The function builds an HTML message and sends it to your Telegram channel via the Bot API.

## Required Environment Variables (Netlify Dashboard)

| Key         | Example                    | Description                                   |
|-------------|----------------------------|-----------------------------------------------|
| `BOT_TOKEN` | `123456:ABCDEF...`         | Telegram Bot token (bot must be **admin** in the target channel). |
| `CHANNEL_ID`| `-1001234567890`           | Numeric channel ID or `@channelusername`. Numeric is recommended. |
| `WEBSITE_URL` | `https://hustlexeth.netlify.app/` | (Optional) Base URL shown in the footer of the message. |

Add them under **Site settings → Build & deploy → Environment**.

## Form Mark-up requirements

Include `netlify` attribute and a matching `name`:

```html
<form name="post-job" method="POST" data-netlify="true">
  <input type="text" name="job_title" required>
  <!-- other fields matching the ones used in the function -->
  <button type="submit">Post Job</button>
</form>
```

The function expects the following field *names* (same as the previous Flask form):

```
job_title, job_type, work_location, salary, deadline, description,
client_type, company_name, verified, previous_jobs, job_link
```

## Local testing

Install Netlify CLI globally (`npm i -g netlify-cli`) then run:

```bash
netlify dev
```

Submit a sample JSON to the function:

```bash
curl -X POST http://localhost:8888/.netlify/functions/submission-created \
     -H "Content-Type: application/json" \
     -d '{"data":{"job_title":"Test","job_type":"Remote"}}'
```

You should see the message posted in Telegram.
