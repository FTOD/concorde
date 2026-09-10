import {useEffect,useMemo,useRef,useState} from 'react';
import cytoscape from 'cytoscape';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import {usePluginData} from '@docusaurus/useGlobalData';
import type {Target,Edge,Page} from '../../plugins/scoped-content/model';
export default function ScopedGraph(){
  const data=usePluginData('concorde-content') as unknown as {architectureGraph:{nodes:Target[];edges:Edge[]};pages:Page[]};
  const [query,setQuery]=useState('');const [kind,setKind]=useState('all');const [relation,setRelation]=useState('all');const [selected,setSelected]=useState<string>();
  const container=useRef<HTMLDivElement>(null);
  const nodes=useMemo(()=>data.architectureGraph.nodes.filter(n=>(kind==='all'||n.kind===kind)&&(`${n.id} ${n.title}`).toLowerCase().includes(query.toLowerCase())),[data,query,kind]);
  const edges=useMemo(()=>{const ids=new Set(nodes.map(n=>n.id));return data.architectureGraph.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(relation==='all'||e.kind===relation));},[data,nodes,relation]);
  useEffect(()=>{
    if(!container.current)return;
    const cy=cytoscape({container:container.current,elements:[...nodes.map(n=>({data:{id:n.id,label:n.title,kind:n.kind}})),...edges.map((e,i)=>({data:{id:'edge'+i,source:e.source,target:e.target,label:e.contract??e.kind.replaceAll('_',' ')}}))],
      layout:{name:'cose',animate:false,padding:35},style:[
        {selector:'node',style:{label:'data(label)','background-color':'#277fc1','text-valign':'bottom','font-size':12,'text-margin-y':7}},
        {selector:'node[kind="module"]',style:{'background-color':'#27875e',shape:'round-rectangle'}},
        {selector:'edge',style:{label:'data(label)',width:1.4,'target-arrow-shape':'triangle','curve-style':'bezier','font-size':9,'line-color':'#9ba4b3','target-arrow-color':'#9ba4b3','text-background-color':'#fff','text-background-opacity':0.8}},
        {selector:':selected',style:{'border-width':3,'border-color':'#202b40'}}]});
    cy.on('tap','node',e=>setSelected(e.target.id()));return()=>cy.destroy();
  },[nodes,edges]);
  const target=data.architectureGraph.nodes.find(n=>n.id===selected);
  const mainPage=target&&data.pages.find(p=>p.memberships.some(m=>m.targetId===target.id&&m.primary));
  return <Layout title="Architecture relationships" description="Module composition, dependencies and bound implementation files">
    <main className="container margin-vert--lg"><h1>Architecture relationships</h1>
      <p>Modules describe their purpose, scenarios, entities and internal architecture, and bind their own implementation files. Select a node to inspect its Spec and relationships.</p>
      <p>This graph derives from the registered Specs. For an interactive view of their bound files, run <code>python -m concorde ua-graph</code> and open the exported graph in the Understand Anything viewer. The command updates an existing graph at a supported UA location, or creates <code>.ua/knowledge-graph.json</code>.</p>
      <div style={{display:'flex',gap:16,flexWrap:'wrap'}}>
        <label>Find <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Entity name or ID"/></label>
        <label>Kind <select value={kind} onChange={e=>setKind(e.target.value)}>{['all','module'].map(k=><option key={k}>{k}</option>)}</select></label>
        <label>Relationship <select value={relation} onChange={e=>setRelation(e.target.value)}>{['all','composes','uses','requires'].map(k=><option key={k}>{k}</option>)}</select></label>
      </div>
      <div ref={container} role="img" aria-label="Interactive architecture graph" style={{height:540,border:'1px solid #ccd3df',borderRadius:12,marginTop:20}}/>
      {target&&<aside className="margin-vert--md"><h2>{mainPage?<Link to={mainPage.route}>{target.title}</Link>:target.title}</h2><p><code>{target.id}</code> · {target.kind}</p><ul>{data.pages.filter(p=>p.memberships.some(m=>m.targetId===target.id)).map(p=>{const membership=p.memberships.find(m=>m.targetId===target.id)!;return <li key={p.route}><Link to={p.route}>{p.title}</Link>{membership.primary?' · Main Spec':''}</li>;})}</ul>{target.files.length>0&&<details><summary>Files ({target.files.length})</summary><ul>{target.files.map(path=><li key={path}><code>{path}</code></li>)}</ul></details>}</aside>}
      <table className="margin-vert--md"><thead><tr><th>Source</th><th>Relationship</th><th>Target</th></tr></thead><tbody>{edges.map((e,i)=><tr key={i}><td><button onClick={()=>setSelected(e.source)}>{e.source}</button></td><td>{e.contract??e.kind.replaceAll('_',' ')}</td><td><button onClick={()=>setSelected(e.target)}>{e.target}</button></td></tr>)}</tbody></table>
    </main></Layout>;
}
