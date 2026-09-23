import Link from "@docusaurus/Link";
import type { Page } from "../../plugins/scoped-content/model";

function kindLabel(page: Page): string {
  return page.readingCollection === "implementation"
    ? "Implementation Spec"
    : "Module Spec";
}

export default function ContentProvenance({
  page,
  pages,
}: {
  page: Page;
  pages: Page[];
}) {
  const entry = pages.find((candidate) => candidate.primaryOf === page.owner);
  const details = pages.filter(
    (candidate) =>
      candidate.owner === page.owner &&
      candidate.readingCollection === "implementation",
  );
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">{kindLabel(page)}</span>
      <span>
        Canonical source: <code>{page.sourcePath}</code>
      </span>
      {details.length > 0 && (
        <nav aria-label="Module specification reading paths">
          {page.readingCollection === "implementation" && entry ? (
            <Link to={entry.route}>Module Specs: {entry.title}</Link>
          ) : (
            <details>
              <summary>Implementation Specs ({details.length})</summary>
              <ul>
                {details.map((detail) => (
                  <li key={detail.documentId}>
                    <Link to={detail.route}>{detail.title}</Link>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </nav>
      )}
      <details>
        <summary>Spec metadata</summary>
        {details.length > 0 && (
          <p>
            Both reading paths belong to the same complete Module specification.
          </p>
        )}
        <div>
          Document: <code>{page.documentId}</code>
        </div>
        <div>
          Owner: <code>{page.owner}</code>
        </div>
        <div>
          Selected by:{" "}
          {page.includedBy.map((m) => (
            <span key={m.moduleId}>
              <code>{m.moduleId}</code> (
              {m.reasons
                .map((r) =>
                  [r.relation, r.kind, r.id].filter(Boolean).join(" "),
                )
                .join(", ")}
              ){" "}
            </span>
          ))}
        </div>
        <div>
          Reading digest: <code>{page.contentDigest}</code>
        </div>
        <div>
          Metadata source: <code>{page.metadataPath}</code>
        </div>
        <div>
          Metadata digest: <code>{page.metadataDigest}</code>
        </div>
      </details>
    </aside>
  );
}
