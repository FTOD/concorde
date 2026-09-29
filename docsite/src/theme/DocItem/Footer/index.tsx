import type { WrapperProps } from "@docusaurus/types";
import OriginalFooter from "@theme-original/DocItem/Footer";
import type OriginalFooterType from "@theme/DocItem/Footer";

import ImplementationDocuments from "../../../components/ImplementationDocuments";
import useScopedPage from "../../../components/useScopedPage";

type Props = WrapperProps<typeof OriginalFooterType>;

export default function FooterWrapper(props: Props) {
  const { page, pages } = useScopedPage();
  return (
    <>
      {page?.primaryOf && (
        <ImplementationDocuments entry={page} pages={pages} />
      )}
      <OriginalFooter {...props} />
    </>
  );
}
