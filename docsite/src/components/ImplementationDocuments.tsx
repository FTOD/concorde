import Link from "@docusaurus/Link";
import type { Page } from "../../plugins/scoped-content/model";

/** The folded list, at the bottom of a Module's entry, of the Module's implementation documents:
 * no sidebar lists them, so this and links in the documents are how a reader reaches them. */
export default function ImplementationDocuments({
  entry,
  pages,
}: {
  entry: Page;
  pages: Page[];
}) {
  const details = pages.filter(
    (candidate) =>
      candidate.owner === entry.owner &&
      candidate.readingCollection === "implementation",
  );
  if (!details.length) return null;
  return (
    <nav
      className="implementationDocuments"
      aria-label="Module specification reading paths"
    >
      <details>
        <summary>{`Implementation documents (${details.length})`}</summary>
        <ul>
          {details.map((detail) => (
            <li key={detail.documentId}>
              <Link to={detail.route}>{detail.title}</Link>
            </li>
          ))}
        </ul>
      </details>
    </nav>
  );
}
