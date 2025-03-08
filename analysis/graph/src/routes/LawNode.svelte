<script lang="ts">
  import { type NodeProps } from '@xyflow/svelte';

  type $$Props = NodeProps & { data: { label: string } };

  export let data: { label: string };
</script>

<div class="text-center">{data.label}</div>

<style lang="postcss">
  @reference "tailwindcss/theme";

  :global(.root) {
    @apply rounded-md border border-black bg-blue-50 p-2;
  }
</style>
