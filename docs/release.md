# Hosting and release preparation

Sprint 7 prepares a portfolio deployment and a package release workflow. It does
not establish deployment, PyPI project ownership, or publication. The scanner
remains installable from this checkout. Public scanning remains out of scope until
the API's authentication, shared limits, TLS/ingress, logging, and isolation are
implemented and reviewed.

## Website modes

Run the existing `npm run build` / `npm run start` in `web/` for the local demo.
Only a locally running API on `127.0.0.1:8000` accepts input.

For a documentation-only portfolio, from `web/`:

```sh
npm ci
npm run build:portfolio
npm run test:portfolio
npm run start
```

The build sets `NEXT_PUBLIC_SECRETSENSE_MODE=portfolio`. `/scan` renders local setup
instructions without a form or upload, the home CTA points to documentation, and
the CSP excludes the loopback API. This is a build-time choice: rebuild to change
modes. Set the same environment variable on the host at build and runtime. Never
host a local-mode build as a public scanning service.

The [Vercel configuration](../web/vercel.json) selects Next.js, `npm ci`, and the
portfolio build command. Import the repository with root directory `web`, Node 24,
and **Include source files outside of the Root Directory in the Build Step**
enabled: the benchmark server page imports only the two versioned aggregate JSON
reports from `ml/results/`. This setting follows the
[Vercel monorepo documentation](https://vercel.com/docs/monorepos/monorepo-faq).
No API deployment, proxy, provider credentials, or public API origin is configured.
Use preview hosting first, confirm all informational routes and disabled input,
and record the actual URL, host logging/retention, and privacy contact before launch.
The root metadata currently requests no indexing; deliberate indexing is a later
launch choice. No deployment CLI was run for this preparation.

## Release workflow

[Release preparation](../.github/workflows/release.yml) is manual-only. Dispatch
with `target=build` (the default) to lint/test the core, build a wheel and sdist,
validate README/metadata with Twine, audit dependencies, install the wheel in a
fresh environment outside the checkout, and retain distribution artifacts for
seven days. It does not publish or create tags/releases in build mode. The wheel
contains the core and MIT license, not the API, site, datasets, or model artifacts.

To enable publication later:

1. Verify ownership/availability of the `secretsense` project separately on
   TestPyPI and PyPI; rename package metadata and docs if it is unavailable.
2. Configure GitHub environments `testpypi` and `pypi` with required reviewers and
   deployment restrictions for reviewed version tags. Register their corresponding
   trusted publishers for owner `yassineeljal`, repository `SecretSense`, workflow
   `release.yml`, and the exact environment name.
3. Set repository variable `PUBLISHING_ENABLED=true` only after that setup.
4. Update the package version, changelog, and handoff, verify a successful push CI
   run for that exact commit, then create the matching `v<version>` tag. Run build
   mode first and review/install its artifacts. Tags are not created automatically.
5. Dispatch the workflow at that tag with `target=testpypi`, inspect its result,
   then use `target=pypi` for the intended final release. Publication rebuilds and
   checks artifacts before the protected publish job; inspect that run's artifacts.
6. Verify the published distribution from the intended registry in a fresh
   environment, then add the verified release link and installation command.

The publish job only downloads built artifacts and uploads them with OIDC. It does
not check out or build source. Publication requires an exact version tag, an
explicit enabling variable, and successful push CI for that commit. These controls
follow the [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
No long-lived registry token is needed. Configuration is not proof of a successful
release. Both target projects and environment protections remain unconfigured
until verified by their owner.

## Launch status

- Informational pages, interactive recorded evidence, local demo, and portfolio
  mode: implemented and verified by [remote CI](https://github.com/yassineeljal/SecretSense/actions/runs/36950882794).
- [Build-only release rehearsal](https://github.com/yassineeljal/SecretSense/actions/runs/36950893726):
  passed at `5a9024d`, with wheel/sdist artifacts retained for seven days and the
  publication job skipped. See [progress](progress.md) for full validation.
- Host account/project, URL, privacy contact/logging review: not supplied.
- PyPI/TestPyPI ownership, trusted publishers, protected release environments,
  version tags, and publication: not established.
- Author biography and LinkedIn: not supplied; the about page uses only the Git
  remote's repository identity.
- Independent evaluation, score calibration, and optional Ollama: future work.

The README preview uses only an illustrative redacted home panel and aggregate
benchmark pages. It contains no submitted source or credentials.
