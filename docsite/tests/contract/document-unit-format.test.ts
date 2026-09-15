import {describe,it,expect} from 'vitest';
import {parseJson,readingMeanings,metadata,relationshipLabels,requireReading} from '../../plugins/scoped-content/reading-format';
import {validateContractExample} from '../../plugins/scoped-content/contract-schema';

const reading='# Example\n\n## Purpose\n\nProvide one result.\n\n## Usage\n\nSubmit one request.\n\n## Design\n\n'+
 '<a id="entity.example.a"></a><a id="entity.example.b"></a>\n\nA produces the record B after admission.\n\n'+
 '## Relationships\n\nThis view shows result production.\n\n```mermaid\nflowchart LR\n    producer["A"]\n    b["B"]\n    producer -->|produces| b\n```\n';
const declaration={schema_version:1,document:{id:'document.example',owner:'module.example'},
 entities:[{id:'entity.example.a',title:'A',kind:'program',meaning:'#entity.example.a'},
 {id:'entity.example.b',title:'B',kind:'record',meaning:'#entity.example.b'}],dependencies:[],bindings:[]};

describe('Protocol-defined reading and document metadata',()=>{
 it('reads grouped anchors without copying semantic strings into metadata',()=>{
  const meanings=requireReading(reading,'example/module.md',true);
  expect(meanings.get('entity.example.a')).toBe(meanings.get('entity.example.b'));
  expect(metadata(JSON.stringify(declaration),'example/module.md.json','module.example',meanings)).toEqual(declaration);
  expect([...relationshipLabels(reading,'example/module.md')]).toEqual(['A','B']);
 });
 it('rejects reserved Mermaid node identifiers before the browser renderer fails',()=>{
  expect(()=>relationshipLabels(reading.replaceAll('producer','graph'),'example/module.md')).toThrow(/Reserved Mermaid/);
 });
 it('rejects missing, borrowed and malformed identity/meaning fields',()=>{
  for(const id of [null,true,42,'Invalid ID'])expect(()=>metadata(JSON.stringify({...declaration,
   document:{...declaration.document,id}}),'example.md.json','module.example',readingMeanings(reading,'example.md'))).toThrow();
  const value={...declaration,entities:[{...declaration.entities[0],meaning:'other.md#entity.example.a'}]};
  expect(()=>metadata(JSON.stringify(value),'example.md.json','module.example',readingMeanings(reading,'example.md'))).toThrow();
 });
 it('rejects duplicate nested keys and overflowing JSON numbers',()=>{
  expect(()=>parseJson('{"document":{"id":"a","id":"b"}}','metadata')).toThrow(/Duplicate JSON key/);
  expect(()=>parseJson('{"example":1e999}','metadata')).toThrow(/Non-finite/);
 });
 it('leaves fenced examples opaque to identity and metadata parsing',()=>{
  const example='\n````markdown\n<a id="entity.example.a"></a>\n```concorde-entities\n[]\n```\n````\n';
  expect(()=>requireReading(reading+example,'example/module.md',true)).not.toThrow();
 });
});

describe('offline canonical contract examples',()=>{
 it('supports local definitions, combinators, bounds, required properties and exact values',()=>{
  const schema={$defs:{quantity:{type:'integer',minimum:1,maximum:3}},type:'object',
   properties:{quantity:{$ref:'#/$defs/quantity'},tag:{oneOf:[{const:'a'},{const:'b'}]}},
   required:['quantity','tag'],additionalProperties:false};
  expect(()=>validateContractExample(schema,{quantity:2,tag:'b'},'example')).not.toThrow();
  for(const example of [{quantity:0,tag:'b'},{quantity:2,tag:'c'},{quantity:2},{quantity:2,tag:'a',extra:true}])
   expect(()=>validateContractExample(schema,example,'example')).toThrow();
 });
 it('distinguishes boolean values from numeric values and measures string code points',()=>{
  expect(()=>validateContractExample({type:'integer'},true,'example')).toThrow();
  expect(()=>validateContractExample({type:'string',maxLength:1},'🌱','example')).not.toThrow();
  expect(()=>validateContractExample({type:'array',uniqueItems:true},[{a:1,b:2},{b:2,a:1}],'example')).toThrow();
 });
 it.each([
  {$ref:'https://example.test/schema'},{$ref:'#/properties/other'},
  {type:'object',unevaluatedProperties:false},{type:'unsupported'},
  {minLength:-1},{minimum:2,maximum:1},{oneOf:[]},{format:'remote-url'},
 ])('rejects unsupported or malformed schemas without fetching (%j)',schema=>{
  expect(()=>validateContractExample(schema,{},'example')).toThrow();
 });
});
