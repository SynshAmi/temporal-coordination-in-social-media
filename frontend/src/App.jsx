import React, { useState, useEffect, lazy, Suspense } from "react";
import Navbar from "./components/Navbar";
import PageOverview from "./pages/PageOverview";
import PageResults from "./pages/PageResults";
import PageMethods from "./pages/PageMethods";
import { Download } from "lucide-react";
import Authors from "./components/Authors";

const REPO_URL = "https://github.com/SynshAmi/temporal-coordination-in-social-media";

// The dataset explorer (and its graph libraries) loads only when visited
const PageDataset = lazy(() => import("./pages/PageDataset"));

// Routes: #overview, #results, #methods, #dataset[/...]. #explorer was the earlier name of #results.
function tabFromHash() {
  const hash = window.location.hash.replace("#", "").toLowerCase();
  if (hash === "explorer") return "results";
  if (["overview", "results", "methods"].includes(hash)) return hash;
  if (hash === "dataset" || hash.startsWith("dataset/")) return "dataset";
  return "overview";
}

export default function App() {
  const [activeTab, setActiveTabState] = useState(tabFromHash);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const setActiveTab = (tab) => {
    setActiveTabState(tab);
    window.location.hash = tab;
    window.scrollTo({ top: 0 });
  };

  useEffect(() => {
    const onHash = () => setActiveTabState(tabFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    fetch("/data/research_data.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status} while loading the results`);
        return res.json();
      })
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (data) document.title = data.metadata.paper_title;
  }, [data]);

  if (error) {
    return (
      <div className="min-h-screen bg-[#faf8f5] flex items-center justify-center p-6">
        <div className="border border-[#8f2626] bg-white p-6 max-w-md space-y-2 text-[16px] text-[#3c3a37]">
          <p className="font-medium text-[#8f2626]">The results could not be loaded</p>
          <p>{error}</p>
          <p className="text-[#757065]">Reload the page. The paper PDF is also available from the repository.</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-[#faf8f5] flex items-center justify-center text-[16px] text-[#5e5a52]" role="status">
        Loading the results
      </div>
    );
  }

  const M = data.metadata;

  return (
    <div className="min-h-screen flex flex-col bg-[#faf8f5] text-[#181818]">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} meta={M} />

      <main key={activeTab} className="page-enter flex-1 site-container pt-8 pb-4 md:pt-10 lg:pt-12">
        {activeTab === "overview" && <PageOverview data={data} setActiveTab={setActiveTab} />}
        {activeTab === "results" && <PageResults data={data} />}
        {activeTab === "methods" && <PageMethods data={data} />}
        {activeTab === "dataset" && (
          <Suspense fallback={<div className="text-[16px] text-[#5e5a52]">Loading the dataset explorer</div>}>
            <PageDataset />
          </Suspense>
        )}
      </main>

      <footer className="mt-16 lg:mt-20 border-t border-[#dcd7ca] bg-[#f4efe6] text-[#4a4740]">
        <div className="site-container py-12 lg:py-14 grid grid-cols-1 md:grid-cols-12 gap-x-12 gap-y-10">
          <div className="md:col-span-5 space-y-4">
            <div className="font-serif text-[28px] text-[#15263a] leading-tight">{M.paper_title}</div>
            <Authors linked />
          </div>

          <div className="md:col-span-4 space-y-2">
            <div className="font-serif italic text-[18px] text-[#15263a]">Data source</div>
            <p className="text-[17px] leading-relaxed">
              Gopalakrishnan, Hossain, Elmas and Sarıyüce, Large Engagement Networks for Classifying Coordinated Campaigns and Organic Twitter Trends,
              ICWSM 2025. The archive was obtained from the{" "}
              <a href="https://erdemub.github.io/large-engagement-network/" target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#23527c]">LEN project website</a>.
            </p>
          </div>

          <div className="md:col-span-3 space-y-2">
            <div className="font-serif italic text-[18px] text-[#15263a]">Downloads</div>
            <ul className="space-y-3">
              {[
                { href: `/${M.paper_pdf}`, file: M.paper_pdf, label: "Research paper (PDF)", meta: `${M.paper_pages} pages · full manuscript`, primary: true },
                { href: "/data/research_data.json", file: "research_data.json", label: "Results data (JSON)", meta: "The values shown on this site" },
              ].map((d) => (
                <li key={d.href}>
                  <a href={d.href} download={d.file} className="group flex items-start gap-3 text-[#15263a] hover:text-[#23527c]">
                    <Download size={16} strokeWidth={1.5} className="text-[#5e5a52] shrink-0 mt-1" />
                    <span>
                      <span className={`block underline decoration-[#b5ad9e] underline-offset-4 ${d.primary ? "text-[18px] font-medium" : "text-[17px]"}`}>{d.label}</span>
                      <span className="block text-[16px] text-[#6b6862] mt-0.5">{d.meta}</span>
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="border-t border-[#d8d3c5] bg-[#ede8dc]">
          <div className="site-container py-4 flex flex-col md:flex-row md:items-center justify-between gap-2 text-[16px] text-[#5e5a52]">
            <div>
              Code, supporting data and reproduction instructions are in the{" "}
              <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#23527c]">project repository</a>.
            </div>
            <div>Code under the MIT licence; paper and figures © the authors.</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
