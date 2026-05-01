# Deployment Guide

## Frontend: Cloudflare Pages

1. Create a new Cloudflare Pages project from this repository.
2. Set the build command to `python build_frontend.py`.
3. Set the build output directory to `web`.
4. Add a production environment variable:
   - `FRONTEND_API_BASE_URL` = your Vercel backend URL, for example `https://syntax-analyser.vercel.app`
5. Deploy the Pages project.

## Backend: Vercel

1. Import the same repository into Vercel.
2. Deploy the Python app from `app.py`.
3. Keep `requirements.txt` minimal.
4. Add a production environment variable:
   - `FRONTEND_ORIGIN` = your Cloudflare Pages URL, for example `https://syntax-analyser.pages.dev`

## What changed in the code

- The backend now acts like an API-only serverless app.
- CORS headers are controlled by `FRONTEND_ORIGIN`.
- The frontend URL is generated at build time from `FRONTEND_API_BASE_URL`.
