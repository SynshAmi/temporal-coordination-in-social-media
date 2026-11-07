import React from "react";

// Authors in paper order, with their roles. Kept in one place so every page shows the same byline.
const AUTHORS = [
  { name: "Suryansh Singh", role: "Co-first author", email: "suryansh.mitblr2024@learner.manipal.edu" },
  { name: "Devansh Kewlani", role: "Co-first author", email: "devansh1.mitblr2024@learner.manipal.edu" },
  { name: "Yashaswini K A", role: "Second author", email: "yashaswini.ka@manipal.edu" },
];
const AFFILIATION = "Manipal Institute of Technology, Bengaluru, India";

const Name = ({ a, linked }) =>
  linked ? (
    <a href={`mailto:${a.email}`} className="hover:text-[#23527c] underline decoration-[#cfc8b8] underline-offset-4">{a.name}</a>
  ) : (
    <span>{a.name}</span>
  );

/**
 * Byline in paper order, each name with its role in small italics beneath.
 * `linked` turns the names into mailto links (used in the footer).
 */
export default function Authors({ linked = false, className = "" }) {
  return (
    <div className={className}>
      <ul className="flex flex-wrap gap-x-8 gap-y-3">
        {AUTHORS.map((a) => (
          <li key={a.name}>
            <div className="font-serif text-[21px] leading-snug text-[#15263a]"><Name a={a} linked={linked} /></div>
            <div className="text-[17px] italic text-[#5e5a52]">{a.role}</div>
          </li>
        ))}
      </ul>
      <div className="mt-2 text-[17.5px] text-[#3c3a37]">{AFFILIATION}</div>
    </div>
  );
}
