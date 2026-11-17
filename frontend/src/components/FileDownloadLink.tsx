import type { AnchorHTMLAttributes, ReactNode } from "react";

type FileDownloadLinkProps = Readonly<{
  href: string;
  children: ReactNode;
  className?: string;
  title?: string;
} & Pick<AnchorHTMLAttributes<HTMLAnchorElement>, "aria-label">>;

export function FileDownloadLink({ href, children, className, title, ...props }: FileDownloadLinkProps) {
  return (
    <a href={href} className={className} title={title} {...props}>
      {children}
    </a>
  );
}
