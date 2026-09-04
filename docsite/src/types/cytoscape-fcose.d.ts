/**
 * `cytoscape-fcose` ships no type declarations of its own and there is no first-party `@types`
 * package for it; this is the minimal ambient shape the fcose layout extension needs: a Cytoscape
 * extension registration function, exactly like `cytoscape.Ext`.
 */
declare module 'cytoscape-fcose' {
  import type cytoscape from 'cytoscape';

  const register: cytoscape.Ext;
  export default register;
}
