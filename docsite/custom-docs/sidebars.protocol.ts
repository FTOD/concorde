import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  protocolSidebar: [
    {type: 'doc', id: 'README', label: 'Overview'},
    {type: 'doc', id: 'principles', label: 'Principles'},
    {type: 'doc', id: 'module', label: 'Module specifications'},
    {type: 'category', label: 'Spec management', collapsed: false,
      link: {type: 'doc', id: 'spec-management'}, items: [
        {type: 'doc', id: 'spec-management/spec-and-context', label: 'Spec and Context'},
      ]},
    {type: 'doc', id: 'format', label: 'Required format'},
    {type: 'category', label: 'Templates', collapsed: false, items: [
      {type: 'doc', id: 'templates/module', label: 'Module'},
      {type: 'doc', id: 'templates/scenario', label: 'Scenario fragment'},
    ]},
  ],
};

export default sidebars;
