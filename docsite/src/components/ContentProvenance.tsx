import Link from "@docusaurus/Link";
import type { Page } from "../../plugins/scoped-content/model";

function kindLabel(page: Page): string {
  return page.readingCollection === "implementation"
    ? "Implementation document"
    : "Module document";
}

export default function ContentProvenance({
  page,
  pages,
}: {
  page: Page;
  pages: Page[];
}) {
  const entry = pages.find((candidate) => candidate.primaryOf === page.owner);
  const hasDetails = pages.some(
    (candidate) =>
      candidate.owner === page.owner &&
      candidate.readingCollection === "implementation",
  );
  return (
    <aside className="provenance" aria-label="Content provenance">
      <span className="provenance__kind">{kindLabel(page)}</span>
      {/* No sidebar lists an implementation document, so its page names the Module it belongs to. */}
      {page.readingCollection === "implementation" && entry && (
        <nav aria-label="Owning Module">
          Of the Module <Link to={entry.route}>{entry.title}</Link>
        </nav>
      )}
      <span>
        Canonical source: <code>{page.sourcePath}</code>
      </span>
      <details>
        <summary>Spec metadata</summary>
        {hasDetails && (
          <p>
            The Module's entry and its implementation documents together make
            its complete specification.
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
