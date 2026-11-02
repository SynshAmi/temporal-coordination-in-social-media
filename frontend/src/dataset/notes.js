// Research-note items shared by several explorer sections ([heading, text] pairs for ResearchNotes)

export const licenceNote = (source) => [
  "Licence and content",
  `The LEN authors state: “${source.licence_statement}” No licence version is given. Shown here: graph structure only, with per-graph node indices, directed edges and interaction counts; no message text, timestamps, embeddings or account identifiers.`,
];

export const nodeNotes = (sampled = false) => [
  ["Node identity", "Node numbers are per-graph indices (0 to N−1) assigned in the release. The release is anonymised: they are not account identifiers, and the same number in two events is not the same account."],
  ["Interpreting degree", `In-degree, out-degree, core number and component size describe a node's position in this ${sampled ? "observation" : "graph"}. They are descriptive and are not evidence of automation, intent or coordination.`],
  ["Layout", "Positions come from a force-directed layout (ForceAtlas2, computed in your browser from seeded starting positions). It is a visual arrangement, not physical distance, and visual clusters do not establish coordination. Self-loops are counted in the statistics but not drawn."],
];
