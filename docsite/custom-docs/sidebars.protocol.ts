import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  protocolSidebar: [
    {type: 'doc', id: 'README', label: 'Overview'},
    {type: 'doc', id: 'principles', label: 'Principles'},
    {type: 'category', label: 'The model', collapsed: false, items: [
      {type: 'doc', id: 'model', label: 'Node types'},
      {type: 'doc', id: 'relations', label: 'Relations'},
      {type: 'doc', id: 'context', label: 'Context'},
      {type: 'doc', id: 'boundaries', label: 'Boundaries'},
    ]},
    {type: 'doc', id: 'module', label: 'Module specifications'},
    {type: 'doc', id: 'format', label: 'Required format'},
    {type: 'doc', id: 'checks', label: 'Checks'},
    {type: 'doc', id: 'views', label: 'Views'},
    {type: 'doc', id: 'migration', label: 'Migration to Protocol 11'},
    {type: 'category', label: 'Templates', collapsed: false, items: [
      {type: 'doc', id: 'templates/module', label: 'Module'},
      {type: 'doc', id: 'templates/scenario', label: 'Scenario fragment'},
    ]},
  ],
};

export default sidebars;
