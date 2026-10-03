# SecretSense local site

Next.js 16.3.8, React 19.3, TypeScript, and Tailwind CSS. Run alongside the
checkout's loopback FastAPI service. See [setup, privacy, limits, and tests](../docs/api-and-web.md).

```sh
npm ci
npm run build
npm run start
```

Visit `http://127.0.0.1:3000`. `npm run dev` starts the development server.
Read repository instructions and installed `node_modules/next/dist/docs/` before
starting or changing this application. No external assets or analytics are used.

```sh
npm run lint
npm run format:check
npm run typecheck
npx playwright install chromium
npm test
npm audit --omit=dev
```

The browser suite starts both production servers; keep ports 3000/8000 free.
Set `SECRETSENSE_PYTHON` if the API interpreter is not `../.venv/bin/python`.
Never enable traces, video, or input screenshots for real scan content.

ESLint is pinned to 9.39.5 because the installed Next.js React lint plugin fails
with ESLint 10's removed context APIs. Revisit this development-only compatibility
pin when the plugin supports ESLint 10. npm currently marks ESLint 9 deprecated;
`npm audit --omit=dev` found no known vulnerabilities when last recorded. Plain `npm audit` currently flags `braces` (GHSA-vfj7-8cjw-p6xm) through `eslint-config-next`, a lint-only dependency that is not shipped.

Sprint 7 adds six informational pages and interactive benchmark exploration from
versioned aggregate JSON in `ml/results/`. The bundler root includes the repository
so those build-time imports work; source datasets and model artifacts are not used.

For a documentation-only hosted build, run `npm run build:portfolio`, followed by
`npm run test:portfolio`. This removes scan input and loopback API access. The
Vercel configuration selects that mode; no deployment has occurred. See the
[hosting and release guide](../docs/release.md) for required project settings.
Rebuild with `npm run build` before running the local scan tests or demo again.
