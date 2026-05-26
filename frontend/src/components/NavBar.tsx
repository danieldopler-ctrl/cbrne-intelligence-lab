import Link from "next/link";

export function NavBar() {
  return (
    <header className="border-b border-[#20323f] bg-[#0b151c]">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-wide text-white">
          CBRN-E Intelligence Lab
        </Link>
        <nav className="flex gap-6 text-sm text-[#a9bfca]">
          <Link href="/sources" className="hover:text-white">Sources & Ingest</Link>
          <Link href="/alerts" className="hover:text-white">Alerts</Link>
          <Link href="/evaluations" className="hover:text-white">Evaluations</Link>
        </nav>
      </div>
    </header>
  );
}
