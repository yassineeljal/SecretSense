import Link from "next/link";
export default function Home() {
  const portfolio = process.env.NEXT_PUBLIC_SECRETSENSE_MODE === "portfolio";
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="dot" /> SECRETS BELONG OUTSIDE YOUR CODE
          </p>
          <h1>
            Catch the secret.
            <br />
            <span>Keep the control.</span>
          </h1>
          <p className="lede">
            Find potential credentials before they become someone else’s
            discovery. Scan locally, understand the finding, and know what to do
            next.
          </p>
          <div className="actions">
            <Link
              className="button primary"
              href={portfolio ? "/docs" : "/scan"}
            >
              {portfolio ? "Run locally" : "Try the scanner"}{" "}
              <span aria-hidden="true">↗</span>
            </Link>
            <a className="text-link" href="#local-cli">
              Use the CLI <span aria-hidden="true">↓</span>
            </a>
          </div>
          <p className="micro">
            Open source · Rules + entropy · No credential verification
          </p>
        </div>
        <div
          className="demo-window"
          aria-label="Illustrative redacted scan result"
        >
          <div className="window-bar">
            <span>
              <i />
              <i />
              <i />
            </span>
            <span>secretsense / preview</span>
            <span>01</span>
          </div>
          <div className="demo-code">
            <p>
              <span>01</span> <b>const</b> config = &#123;
            </p>
            <p className="highlight">
              <span>02</span> &nbsp; apiToken: <em>&quot;[REDACTED]&quot;</em>
            </p>
            <p>
              <span>03</span> &#125;;
            </p>
            <div className="scan-line" />
          </div>
          <div className="demo-finding">
            <div className="flex justify-between gap-4">
              <span className="eyebrow">POTENTIAL EXPOSURE</span>
              <span className="risk high">High</span>
            </div>
            <h3>One finding. A clear next step.</h3>
            <p>
              Review the token locally. If exposed, revoke it, replace it, and
              inspect access logs.
            </p>
            <div className="demo-foot">
              <span>✓ Value redacted</span>
              <span>Illustrative preview</span>
            </div>
          </div>
        </div>
      </section>
      <section className="feature-strip" aria-label="Scanner capabilities">
        <div>
          <strong>15</strong>
          <span>Service-specific patterns</span>
        </div>
        <div>
          <strong>In memory</strong>
          <span>
            {portfolio ? "Local demo processing" : "Demo inputs are not saved"}
          </span>
        </div>
        <div>
          <strong>Your machine</strong>
          <span>
            {portfolio
              ? "Install the local scanner"
              : "Loopback API processing"}
          </span>
        </div>
      </section>
      <section className="section">
        <div className="section-heading">
          <p className="eyebrow">A SMALL CHECK. A BETTER HABIT.</p>
          <h2>From a signal to a next step.</h2>
        </div>
        <div className="three-grid">
          <article className="step">
            <span className="step-number">01 / DETECT</span>
            <h3>Look for the telltale signs.</h3>
            <p>
              Service patterns and entropy checks identify potential credentials
              in UTF-8 source text.
            </p>
          </article>
          <article className="step">
            <span className="step-number">02 / UNDERSTAND</span>
            <h3>See what needs attention.</h3>
            <p>
              Review locations, severity, and explanations. A match is a
              candidate, never proof of validity.
            </p>
          </article>
          <article className="step">
            <span className="step-number">03 / RESPOND</span>
            <h3>Take the right next step.</h3>
            <p>
              Service-specific guidance helps you rotate credentials, review
              access, and clean up source.
            </p>
          </article>
        </div>
      </section>
      <section className="cli-panel" id="local-cli">
        <div>
          <p className="eyebrow">PREFER YOUR TERMINAL?</p>
          <h2>Keep it in your workflow.</h2>
          <p>
            Install from this checkout. Scan files, directories, or bounded Git
            history.
          </p>
        </div>
        <div className="commands">
          <code>python -m pip install -e ./core</code>
          <code>secretsense scan ./my-project</code>
          <span>The CLI also exports JSON, HTML, and SARIF reports.</span>
        </div>
      </section>
    </>
  );
}
