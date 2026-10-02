import Link from "next/link";

export const repository = "https://github.com/yassineeljal/SecretSense";
export const guideLinks = [
  ["/how-it-works", "How it works"],
  ["/benchmarks", "Benchmarks"],
  ["/docs", "Documentation"],
  ["/model", "Model card"],
  ["/security", "Security & privacy"],
  ["/about", "About"],
];
export function Guide({
  eyebrow,
  title,
  intro,
  children,
}: {
  eyebrow: string;
  title: string;
  intro: string;
  children: React.ReactNode;
}) {
  return (
    <section className="section guide">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="lede">{intro}</p>
      <nav className="guide-nav" aria-label="Explore the project">
        {guideLinks.map(([href, label]) => (
          <Link key={href} href={href}>
            {label}
          </Link>
        ))}
      </nav>
      <div className="guide-content">{children}</div>
    </section>
  );
}
export function SourceLink({
  path,
  children,
}: {
  path: string;
  children: React.ReactNode;
}) {
  return (
    <a className="text-link" href={`${repository}/blob/main/${path}`}>
      {children}
    </a>
  );
}
