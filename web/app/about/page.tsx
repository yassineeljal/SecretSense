import type { Metadata } from "next";
import { Guide, SourceLink, repository } from "@/components/guide";
export const metadata: Metadata = { title: "About | SecretSense" };
export default function About() {
  return (
    <Guide
      eyebrow="ABOUT THE PROJECT"
      title="Make the evidence visible."
      intro="SecretSense is an open-source local secret-scanning project, built around inspectable findings and reproducible experiments."
    >
      <section>
        <h2>What is delivered.</h2>
        <p>
          A Python CLI, local API, browser demo, redacted reports, remediation
          playbooks, bounded Git-history scanning, a reusable Action, and
          optional forest annotations. The informational site explains the
          measurements and limitations behind those choices.
        </p>
      </section>
      <section>
        <h2>What is still ahead.</h2>
        <p>
          Independent data review, fresh unseen-repository evaluation,
          calibration, public scanning infrastructure, and PyPI publication
          remain planned. No deployment or package release is implied by this
          site. Optional Ollama assistance is a later experiment.
        </p>
      </section>
      <section>
        <h2>Built in the open.</h2>
        <p>
          The repository is hosted under the GitHub account{" "}
          <code>yassineeljal</code> and uses the MIT license. Contributions and
          technical discussion are welcome in the repository.
        </p>
        <a className="text-link" href={repository}>
          Explore the source on GitHub →
        </a>
      </section>
      <p className="source-links">
        <SourceLink path="CONTRIBUTING.md">Contribute</SourceLink>
        <SourceLink path="docs/roadmap.md">Roadmap</SourceLink>
        <SourceLink path="LICENSE">MIT license</SourceLink>
      </p>
    </Guide>
  );
}
