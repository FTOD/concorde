/** The house style of rendered D2 diagrams. A reading's D2 block states only what is drawn, what
 * nests in what and what points at what; the publisher assigns each shape and edge one of these
 * classes from what its label names, so the look never lives in a Spec. */
export const DIAGRAM_STYLE = `classes: {
  owner: {
    style: {border-radius: 8; stroke-width: 2; font-size: 20; bold: true}
  }
  module: {
    style: {border-radius: 6; stroke-width: 2; font-size: 16; bold: true}
  }
  foreign: {
    style: {
      border-radius: 6
      stroke-dash: 4
      stroke: "#9aa3b2"
      fill: "#f3f4f6"
      font-color: "#4b5563"
      font-size: 15
    }
  }
  foreign-node: {
    style: {border-radius: 4; stroke-dash: 4; stroke: "#9aa3b2"; fill: "#f3f4f6"; font-color: "#4b5563"; font-size: 14}
  }
  realization: {
    style: {border-radius: 4; fill: "#e8edff"; stroke: "#3b5bdb"; font-size: 14}
  }
  realization-files: {
    shape: sql_table
    style: {fill: "#3b5bdb"; stroke: "#f5f7ff"; font-size: 14}
  }
  concept: {
    shape: oval
    style: {fill: "#fff8e6"; stroke: "#c9a227"; font-size: 13}
  }
  uses: {
    style: {stroke-width: 2}
  }
  relates: {
    style: {stroke-dash: 3; stroke: "#8a6d0b"; font-size: 13}
  }
}
`;
