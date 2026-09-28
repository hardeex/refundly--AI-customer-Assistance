const DOCS_URL = process.env.NEXT_PUBLIC_BACKEND_DOCS_URL ?? "http://localhost:8000/docs";

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white px-6 py-3 text-center text-xs text-slate-500">
      <a href={DOCS_URL} target="_blank" rel="noopener noreferrer" className="hover:text-slate-800">
        API documentation (Swagger UI)
      </a>
    </footer>
  );
}
