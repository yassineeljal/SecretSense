import type { Metadata } from "next";
import { Guide, SourceLink } from "@/components/guide";
import { CopyCommand } from "@/components/copy-command";
export const metadata: Metadata = { title: "Documentation | SecretSense" };
export default function Docs() {
  return (
    <Guide
      eyebrow="START LOCALLY"
      title="From checkout to first scan."
      intro="Python 3.11 or newer. Install the scanner from this repository; no PyPI release is claimed."
    >
      <section>
        <h2>Install and scan.</h2>
        <CopyCommand
          command={
            "git clone https://github.com/yassineeljal/SecretSense.git\ncd SecretSense\npython3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -e ./core\nsecretsense scan ./my-project"
          }
        />
        <p>
          These activation commands target macOS/Linux shells. On Windows
          PowerShell use <code>.venv\Scripts\Activate.ps1</code>. Replace{" "}
          <code>./my-project</code> with your local target. Exit codes are 0 for
          no candidates, 1 for candidates, and 2 for invalid input or incomplete
          work.
        </p>
      </section>
      <section>
        <h2>Choose a report.</h2>
        <CopyCommand
          command={
            "secretsense scan ./my-project --format json\nsecretsense scan ./my-project --format html > ../scan-report.html\nsecretsense scan ./my-project --format sarif > ../scan-report.sarif"
          }
        />
        <p>
          Keep report files outside the scanned tree. All formats mask detected
          values; CLI paths and partial values remain sensitive.
        </p>
        <SourceLink path="docs/cli.md">
          CLI, trusted model loading, and bounded history
        </SourceLink>
      </section>
      <section>
        <h2>Use it in GitHub Actions.</h2>
        <p>
          The repository supplies a reusable Linux Action with SARIF output. Pin
          its reviewed full commit SHA in another repository. In this
          repository, use the local Action after checkout:
        </p>
        <CopyCommand
          command={
            '- uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n- uses: ./\n  with:\n    path: .\n    fail-on-findings: "true"'
          }
        />
        <p>
          The Action scans locally. SARIF upload is a separate caller decision.
          Incomplete scans always fail.
        </p>
        <SourceLink path="docs/github-action.md">
          Action inputs, outputs, and integration guide
        </SourceLink>
      </section>
      <section>
        <h2>Run the browser demo.</h2>
        <p>
          Install the API extra, start one loopback worker, then build and start
          the site. The setup guide includes exact commands and limits. Public
          portfolio builds disable scan input.
        </p>
        <SourceLink path="docs/api-and-web.md">
          Local API and browser setup
        </SourceLink>
      </section>
    </Guide>
  );
}
