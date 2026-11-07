import React from "react";
import { FileText } from "lucide-react";

const TABS = [
  { id: "overview", label: "Paper" },
  { id: "results", label: "Results" },
  { id: "methods", label: "Methods" },
  { id: "dataset", label: "Dataset" },
];

export default function Navbar({ activeTab, setActiveTab, meta }) {
  return (
    <header className="masthead-border bg-[#faf8f5] sticky top-0 z-30">
      <div className="site-container py-3 sm:py-0 sm:h-16 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4">
        <button type="button" onClick={() => setActiveTab("overview")} className="text-left min-w-0 max-w-full group">
          <span className="block font-serif text-[19px] sm:text-[21px] leading-[1.3] text-[#15263a] group-hover:text-[#23527c] truncate">
            {meta.paper_title}
          </span>
          <span className="hidden sm:block text-[14px] leading-[1.3] text-[#757065]">
            {meta.project_identity}
          </span>
        </button>

        <div className="flex items-center gap-2 sm:gap-4 shrink-0 -ml-2 sm:ml-0">
          <nav aria-label="Sections" className="no-scrollbar flex items-center gap-1 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id)}
                aria-current={activeTab === t.id ? "page" : undefined}
                className={`h-9 px-2 sm:px-3 text-[16px] rounded-[4px] whitespace-nowrap ${
                  activeTab === t.id
                    ? "text-[#15263a] bg-[#ece6d8] font-medium"
                    : "text-[#5e5a52] hover:text-[#15263a] hover:bg-[#f4efe6]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <a
            href={`/${meta.paper_pdf}`}
            className="hidden md:inline-flex items-center gap-2 h-9 px-4 rounded-[4px] bg-[#15263a] text-white text-[16px] font-medium hover:bg-[#233b54]"
          >
            <FileText size={16} strokeWidth={1.5} />
            PDF
          </a>
        </div>
      </div>
    </header>
  );
}
