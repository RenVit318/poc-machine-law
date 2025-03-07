<script lang="ts">
  import { writable } from 'svelte/store';
  import yaml from 'yaml';
  import { base } from '$app/paths';
  import {
    MarkerType,
    SvelteFlow,
    Controls,
    Background,
    BackgroundVariant,
    MiniMap,
    type Node,
    type Edge,
  } from '@xyflow/svelte';

  // Import the styles for Svelte Flow to work
  import '@xyflow/svelte/dist/style.css';

  type Law = {
    uuid: string;
    name: string;
    service: string;
    properties: {
      sources?: { name: string }[];
      input?: { name: string; service_reference?: { service: string; field: string } }[];
      output?: { name: string }[];
    };
  };

  // Define the paths to the YAML files
  let filePaths: string[] = [
    'algemene_ouderdomswet/SVB-2024-01-01.yaml',
    'algemene_ouderdomswet/leeftijdsbepaling/SVB-2024-01-01.yaml',
    'awb/beroep/JenV-2024-01-01.yaml',
    'awb/bezwaar/JenV-2024-01-01.yaml',
    'handelsregisterwet/KVK-2024-01-01.yaml',
    'kieswet/KIESRAAD-2024-01-01.yaml',
    'participatiewet/bijstand/SZW-2023-01-01.yaml',
    'participatiewet/bijstand/gemeenten/GEMEENTE_AMSTERDAM-2023-01-01.yaml',
    'penitentiaire_beginselenwet/DJI-2022-01-01.yaml',
    'vreemdelingenwet/IND-2024-01-01.yaml',
    'wet_brp/RvIG-2020-01-01.yaml',
    'wet_forensische_zorg/DJI-2022-01-01.yaml',
    'wet_inkomstenbelasting/BELASTINGDIENST-2001-01-01.yaml',
    'wet_inkomstenbelasting/UWV-2020-01-01.yaml',
    'wet_op_de_huurtoeslag/TOESLAGEN-2025-01-01.yaml',
    'wet_op_het_centraal_bureau_voor_de_statistiek/CBS-2024-01-01.yaml',
    'wet_structuur_uitvoeringsorganisatie_werk_en_inkomen/UWV-2024-01-01.yaml',
    'wet_studiefinanciering/DUO-2024-01-01.yaml',
    'wetboek_van_strafrecht/JUSTID-2023-01-01.yaml',
    'zorgtoeslagwet/TOESLAGEN-2024-01-01.yaml',
    'zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml',
    'zvw/RVZ-2024-01-01.yaml',
  ];

  const nodes = writable<Node[]>([]);
  const edges = writable<Edge[]>([]);

  (async () => {
    try {
      // Fetch the available laws from the backend
      const response = await fetch('/laws/list');
      filePaths = await response.json();

      let i = 0;

      const ns: Node[] = [];
      const es: Edge[] = [];

      // Initialize a map of service names to their UUIDs
      const serviceToUUIDsMap = new Map<string, string[]>();

      const laws: Law[] = await Promise.all(
        filePaths.map(async (filePath) => {
          // Read the file content
          const fileContent = await fetch(`${base}/law/${filePath}`).then((response) => response.text());

          // Parse the YAML content
          const law = yaml.parse(fileContent) as Law;

          // Populate the map with the service names and their corresponding UUIDs
          const current = serviceToUUIDsMap.get(law.service);
          if (current) {
            serviceToUUIDsMap.set(law.service, [...current, law.uuid]);
          } else {
            serviceToUUIDsMap.set(law.service, [law.uuid]);
          }

          return law;
        }),
      );

      // Sort the laws (topological sort)
      laws.sort((a, b) => {
        return (
          (
            a.properties.input?.filter((input) =>
              serviceToUUIDsMap.has(input.service_reference?.service as string),
            ) || []
          ).length -
          (
            b.properties.input?.filter((input) =>
              serviceToUUIDsMap.has(input.service_reference?.service as string),
            ) || []
          ).length
        );
      });

      for (const data of laws) {
        const lawID = data.uuid;

        // Add parent nodes
        ns.push({
          id: lawID,
          type: 'default',
          data: { label: data.name }, // Algorithm name
          position: { x: i++ * 400, y: 0 },
          width: 340,
          height:
            Math.max(
              ((data.properties.sources?.length || 0) + (data.properties.input?.length || 0)) * 50 +
                70,
              (data.properties.output?.length || 0) * 50,
            ) + 120,
          class: 'root',
        });

        // Sources
        const sourcesID = `${data.uuid}-sources`;

        ns.push({
          id: sourcesID,
          type: 'default',
          data: { label: 'Sources' },
          position: { x: 10, y: 60 },
          width: 150,
          height: (data.properties.sources?.length || 0) * 50 + 50,
          parentId: lawID,
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        let j = 0;

        for (const source of data.properties.sources || []) {
          ns.push({
            id: `${data.uuid}-source-${source.name}`,
            type: 'input',
            data: { label: source.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            parentId: sourcesID,
            extent: 'parent',
            expandParent: true,
          });
        }

        // Input
        const inputsID = `${data.uuid}-input`;

        ns.push({
          id: inputsID,
          type: 'default',
          data: { label: 'Input' },
          position: { x: 10, y: j * 50 + 130 },
          width: 150,
          height: (data.properties.input?.length || 0) * 50 + 50,
          parentId: lawID,
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        j = 0;

        for (const input of data.properties.input || []) {
          const inputID = `${data.uuid}-input-${input.name};`;

          ns.push({
            id: inputID,
            type: 'input',
            data: { label: input.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            parentId: inputsID,
            extent: 'parent',
            expandParent: true,
          });

          // If the input has a service reference, show it with an edge
          const ref = input.service_reference;
          if (ref) {
            for (const uuid of serviceToUUIDsMap.get(ref.service) || []) {
              const target = `${uuid}-output-${ref.field}`;
              es.push({
                id: `${inputID}-${target}`,
                source: inputID,
                target: target,
                data: { refersToService: ref.service },
                type: 'bezier',
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                },
                zIndex: 1,
              });
            }
          }
        }

        // Output
        const outputsID = `${data.uuid}-output`;

        ns.push({
          id: outputsID,
          type: 'default',
          data: { label: 'Output' },
          position: { x: 180, y: 60 },
          width: 150,
          height: (data.properties.output?.length || 0) * 50 + 50,
          parentId: lawID,
          extent: 'parent',
          expandParent: true,
          class: 'property-group',
        });

        j = 0;

        for (const output of data.properties.output || []) {
          ns.push({
            id: `${data.uuid}-output-${output.name}`,
            type: 'output',
            data: { label: output.name },
            position: { x: 10, y: (j++ + 1) * 50 },
            width: 130,
            parentId: outputsID,
            extent: 'parent',
            expandParent: true,
          });
        }
      }

      // Add the nodes to the graph
      $nodes = ns;

      // Add the edges to the graph
      $edges = es;
    } catch (error) {
      console.error('Error reading file', error);
    }
  })();
</script>

<svelte:head>
  <title>Dependency graph — Digilab</title>
</svelte:head>

<!--
👇 By default, the Svelte Flow container has a height of 100%.
This means that the parent container needs a height to render the flow.
-->
<div class="h-screen">
  <SvelteFlow
    {nodes}
    {edges}
    fitView
    nodesConnectable={false}
    proOptions={{
      hideAttribution: true,
    }}
    minZoom={0.1}
  >
    <Controls showLock={false} />
    <Background variant={BackgroundVariant.Dots} />
    <MiniMap zoomable pannable />
  </SvelteFlow>
</div>

<style lang="postcss">
  @reference "tailwindcss/theme";

  :global(.root) {
    @apply bg-blue-50;
  }

  :global(.property-group) {
    @apply bg-blue-100;
  }

  :global(.svelte-flow) {
    --xy-edge-stroke: #0284c7; /* var(--color-blue-600); */
    --xy-edge-stroke-selected: #0284c7; /* var(--color-blue-600); */
  }

  :global(.svelte-flow__arrowhead polyline) {
    @apply fill-blue-600 stroke-blue-600;
  }

  :global(.svelte-flow__edge.selected) {
    --xy-edge-stroke-width-default: 2.5;
  }
</style>
