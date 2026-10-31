import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import PageOverview from "./pages/PageOverview";
import PageExplorer from "./pages/PageExplorer";
import PageMethods from "./pages/PageMethods";
import { AlertCircle, Download, ShieldCheck } from "lucide-react";

export default function App() {
  // Sync active tab with URL hash (#overview, #explorer, #methods)
  const getTabFromHash = () => {
    const hash = window.location.hash.replace("#", "").toLowerCase();
    if (["overview", "explorer", "methods"].includes(hash)) {
      return hash;
    }
    return "overview";
  };

  const [activeTab, setActiveTabState] = useState(getTabFromHash);
  const [researchData, setResearchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const setActiveTab = (tab) => {
    setActiveTabState(tab);
    window.location.hash = tab;
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handleHashChange = () => {
      setActiveTabState(getTabFromHash());
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    fetch("/data/research_data.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status} while loading research data`);
        return res.json();
      })
      .then((data) => {
        setResearchData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load research data:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#faf8f5] flex items-center justify-center p-6 text-[#15263a] font-mono text-xs">
        <div className="text-center space-y-3">
          <div className="inline-block w-6 h-6 border-2 border-[#15263a] border-t-transparent rounded-full animate-spin"></div>
          <div>Loading research results...</div>
        </div>
      </div>
    );
  }

  if (error || !researchData) {
    return (
      <div className="min-h-screen bg-[#faf8f5] flex items-center justify-center p-6 text-xs font-mono">
        <div className="bg-white border border-[#8f2626] p-6 max-w-md space-y-3">
          <div className="flex items-center gap-2 text-[#8f2626] font-bold">
            <AlertCircle size={16} />
            <span>Results Could Not Be Loaded</span>
          </div>
          <p className="text-[#3c3a37] text-xs">
            {error || "The results data could not be read."}
          </p>
          <div className="text-[11px] text-[#757065] pt-2 border-t border-[#e5e0d4]">
            Please reload the page. If the problem persists, the paper PDF is available from the repository.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#faf8f5] text-[#181818]">
      {/* Top Academic Masthead */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} meta={researchData.metadata} />

      {/* Main Content Area (Spacious Editorial Canvas) */}
      <main className="flex-1 site-container pt-12 pb-4 md:pt-16 lg:pt-20">
        {activeTab === "overview" && (
          <PageOverview data={researchData} setActiveTab={setActiveTab} />
        )}
        {activeTab === "explorer" && (
          <PageExplorer data={researchData} />
        )}
        {activeTab === "methods" && (
          <PageMethods data={researchData} />
        )}
      </main>

      {/* Minimal Academic Footer Focused on Citations & Working Downloads */}
      <footer className="mt-24 lg:mt-32 border-t border-[#dcd7ca] bg-[#f4efe6] font-sans text-[#4a4740]">
        <div className="site-container pt-14 pb-12 lg:pt-16 lg:pb-14">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-x-12 gap-y-12 lg:gap-x-16">
            {/* Column 1: Research Identity */}
            <div className="md:col-span-2 lg:col-span-4 space-y-4">
              <div className="font-serif text-2xl text-[#15263a] leading-tight">
                Temporal Coordination in Social Media
              </div>
              <p className="text-sm leading-relaxed text-[#4a4740] max-w-[46ch]">
                What the LEN-Small benchmark labels can be predicted from: incremental information beyond graph counts, and how much survives in a single fixed-size sample of edges.
              </p>
              <div className="text-xs font-mono text-[#5e5a52] flex items-center gap-2">
                <ShieldCheck size={14} className="text-[#23527c] shrink-0" />
                <span>{researchData.paper.verification.n_pass}/{researchData.paper.verification.n_checks} independent checks pass &bull; Event-level 5-fold CV</span>
              </div>
            </div>

            {/* Column 2: Relevant Citations & External Links */}
            <div className="lg:col-span-4 space-y-5">
              <div className="font-mono font-semibold text-[#15263a] uppercase tracking-wider text-xs pb-3 border-b border-[#d8d3c5]">
                Primary Sources
              </div>
              <ul className="space-y-4 text-sm text-[#4a4740] leading-relaxed">
                <li>
                  Gopalakrishnan, Hossain, Elmas and Sarıyüce. <em>Large Engagement Networks for Classifying Coordinated Campaigns and Organic Twitter Trends</em>. ICWSM 2025.
                </li>
                <li>
                  Gopalakrishnan, Hossain, Elmas and Sarıyüce. <em>Density-Aware Walks for Coordinated Campaign Detection</em>. ECML PKDD 2025.
                </li>
                <li>
                  <em>LEN: Large Engagement Networks</em>, dataset repository.{" "}
                  <a href="https://erdemub.github.io/large-engagement-network/" target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#23527c]">erdemub.github.io/large-engagement-network</a>
                </li>
              </ul>
            </div>

            {/* Column 3: Working Downloadable Artifacts */}
            <div className="lg:col-span-4 space-y-5">
              <div className="font-mono font-semibold text-[#15263a] uppercase tracking-wider text-xs pb-3 border-b border-[#d8d3c5]">
                Downloads
              </div>
              <ul className="divide-y divide-[#e2dcd0]">
                {[
                  { href: "/LEN_Small_Predictive_Information_Beyond_Scale.pdf", file: "LEN_Small_Predictive_Information_Beyond_Scale.pdf", label: "Research Paper — PDF", meta: "IEEE conference paper · PDF" },
                  { href: "/data/research_data.json", file: "research_data.json", label: "Results Data", meta: "JSON · every value shown on this site" },
                ].map((d) => (
                  <li key={d.href}>
                    <a
                      href={d.href}
                      download={d.file}
                      className="group flex items-start gap-3 py-3 first:pt-0 text-[#15263a] hover:text-[#23527c] transition-colors"
                    >
                      <Download size={15} className="text-[#8f2626] shrink-0 mt-1" />
                      <span className="min-w-0">
                        <span className="block text-sm font-medium underline decoration-[#b5ad9e] underline-offset-4 group-hover:decoration-[#23527c]">
                          {d.label}
                        </span>
                        <span className="block text-xs font-mono text-[#757065] mt-0.5">{d.meta}</span>
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Provenance & Copyright Strip, visually quieter and fully separated */}
        <div className="border-t border-[#d8d3c5] bg-[#ede8dc]">
          <div className="site-container py-5 flex flex-col md:flex-row md:items-center justify-between gap-2 text-[11px] font-mono text-[#6b6862]">
            <div>All values generated from the analysis pipeline &bull; LEN-Small archive ({researchData.paper.dataset.n_events} events)</div>
            <div>Suryansh Singh &bull; Devansh Kewlani &bull; Manipal Institute of Technology, Bengaluru</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
