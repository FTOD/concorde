import type { WrapperProps } from "@docusaurus/types";
import OriginalLayout from "@theme-original/DocItem/Layout";
import type OriginalLayoutType from "@theme/DocItem/Layout";

import ContentProvenance from "../../../components/ContentProvenance";
import useScopedPage from "../../../components/useScopedPage";

type Props = WrapperProps<typeof OriginalLayoutType>;

export default function LayoutWrapper(props: Props) {
  const { page, pages } = useScopedPage();
  return (
    <>
      {page && (
        <div className="provenanceShell">
          <ContentProvenance page={page} pages={pages} />
        </div>
      )}
      <OriginalLayout {...props} />
    </>
  );
}
