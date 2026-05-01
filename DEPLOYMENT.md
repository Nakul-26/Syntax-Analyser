# Deployment Guide

## Frontend: Cloudflare Pages

1. Create a new Cloudflare Pages project from this repository.
2. Set the build output to the `web` folder if you use a direct upload or a static build step.
3. Make sure `web/index.html` points to your backend URL:
   - Replace `https://YOUR-VERCEL-APP.vercel.app` with the real Vercel deployment URL.
4. Deploy the Pages project.

## Backend: Vercel

1. Import the same repository into Vercel.
2. Deploy the Python app from `app.py`.
3. Keep `requirements.txt` minimal.
4. After deployment, copy the Vercel URL into `window.API_BASE_URL` in `web/index.html`.

## What changed in the code

- The backend now acts like an API-only serverless app.
- CORS headers are enabled so Cloudflare Pages can call the Vercel API.
- The frontend now sends requests to a configurable backend URL instead of a same-origin `/analyze` endpoint.

