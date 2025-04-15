<script lang="ts">
  import { focusElement } from '$lib';
  import { tick } from 'svelte';
  import Markdown from 'svelte-exmarkdown';
  import { highlightPlugin } from './highlight-plugin';
  import 'highlight.js/styles/github-dark.css';
  import PreWithCopyButton from './PreWithCopyButton.svelte';
  import { browser } from '$app/environment';

  const copyButtonPlugin = {
    renderer: { pre: PreWithCopyButton },
  };

  type Message = {
    id: string;
    content: string;
    isOwn: boolean;
    timestamp: Date;
  };

  let apiKey = '';
  let apiFormIsShown = true;
  let apiKeyInput: HTMLInputElement | undefined;

  let messages: Message[] = [];
  let input = '';
  let messagesContainer: HTMLDivElement;
  let inputElement: HTMLInputElement;

  let quickReplies: string[] = [];

  function handleKeySubmit() {
    if (browser) {
      localStorage.setItem('api-key', apiKey);
    }

    apiFormIsShown = false;
  }

  // Initialize WebSocket connection
  const socket = new WebSocket('/importer/ws');

  // Connection opened
  socket.addEventListener('open', function (event) {
    console.log('Connected to server');
  });

  // Listen for messages
  socket.addEventListener('message', function (event) {
    // Parse the event data
    const data = JSON.parse(event.data) as { id: string; content: string; quick_replies: string[] };

    // If the message ID equals the ID of the previous message, append it to the previous message
    if (messages.length && messages[messages.length - 1].id === data.id) {
      messages[messages.length - 1].content += `${data.content}`; // IMPROVE: also look at earlier messages, since the user may post a message in between?
      messages = [...messages];
    } else {
      messages = [
        ...messages,
        {
          id: data.id,
          content: data.content,
          isOwn: false,
          timestamp: new Date(),
        },
      ]; // Note: instead of messages.push(...) to trigger Svelte reactivity, also below
    }

    // If the message contains quick replies, show them
    quickReplies = data.quick_replies || [];

    tick().then(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });
  });

  // Submit handler
  function handleSubmit() {
    if (input && socket.readyState === WebSocket.OPEN) {
      socket.send(input);

      messages = [
        ...messages,
        {
          id: '',
          content: input,
          isOwn: true,
          timestamp: new Date(),
        },
      ];
      input = '';
      quickReplies = [];

      tick().then(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      });
    }

    inputElement.focus();
  }
</script>

<svelte:head>
  <title>Machine law importer</title>
</svelte:head>

<main class="fixed left-0 top-0 flex h-full w-full flex-col px-6 py-4">
  <h1 class="mb-2 text-2xl">⚡️ Machine law importer</h1>

  {#if apiFormIsShown}
    <form
      on:submit|preventDefault={handleKeySubmit}
      class="mb-5 rounded-md border border-gray-300 bg-gray-50 p-4"
    >
      <label class="mb-2 inline-block font-medium" for="api-key">Claude / Anthropic API key</label>

      <div class="mb-1 flex">
        <input
          bind:value={apiKey}
          bind:this={apiKeyInput}
          placeholder="sk-…"
          id="api-key"
          type="text"
          class="mr-2 block w-full rounded-md border border-gray-300 bg-white px-2.5 py-2 focus:border-blue-500 focus:ring-blue-500"
          autocomplete="off"
        />

        <button
          type="submit"
          class="cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-4 py-2 text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
        >
          Gebruiken
        </button>
      </div>

      <small class="text-sm text-gray-600"
        >Verplicht, wordt niet opgeslagen, alleen in de browser. <a
          class="text-blue-700 underline hover:no-underline"
          href="https://console.anthropic.com/"
          target="_blank"
          rel="nofollow">Meer informatie</a
        ></small
      >
    </form>
  {:else}
    <div
      class="mb-5 flex items-center rounded-md border border-emerald-700/25 bg-emerald-50 px-3 py-2"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mr-1.5 h-5 w-5 text-emerald-600"
        viewBox="0 0 24 24"
        ><g
          fill="none"
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          ><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0" /><path d="m9 12l2 2l4-4" /></g
        ></svg
      >
      Claude / Anthropic API ingesteld

      <button
        on:click={async () => {
          apiFormIsShown = true;
          await tick();
          apiKeyInput?.focus();
        }}
        type="button"
        class="ml-3 cursor-pointer rounded-md border border-blue-600 bg-blue-600 px-2 py-1 text-sm text-white transition duration-200 hover:border-blue-700 hover:bg-blue-700"
      >
        Aanpassen
      </button>
    </div>
  {/if}

  <div class="grid flex-grow grid-cols-3 gap-4">
    <div
      bind:this={messagesContainer}
      class="col-span-2 mb-2 flex flex-col overflow-y-auto scroll-smooth rounded-md bg-gray-100 p-4"
    >
      {#each messages as message}
        {#if message.isOwn}
          <div class="message own">{message.content}</div>
        {:else}
          <div class="message">
            <Markdown md={message.content} plugins={[highlightPlugin, copyButtonPlugin]} />
          </div>
        {/if}
      {/each}

      <div class="self-start">
        {#each quickReplies as quickReply}
          <button
            on:click={() => {
              input = quickReply;
              handleSubmit();
            }}
            class="mr-1.5 inline-flex cursor-pointer items-center rounded-full border border-blue-600 bg-white px-4 py-1 text-blue-600 hover:bg-blue-600 hover:text-white"
            type="button"
          >
            {#if quickReply === 'Ja'}
              <svg xmlns="http://www.w3.org/2000/svg" class="mr-1 h-4 w-4" viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="m5 12l5 5L20 7"
                /></svg
              >
            {:else if quickReply === 'Nee'}
              <svg xmlns="http://www.w3.org/2000/svg" class="mr-1 h-4 w-4" viewBox="0 0 24 24"
                ><path
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M18 6L6 18M6 6l12 12"
                /></svg
              >
            {/if}
            {quickReply}</button
          >
        {/each}
      </div>
    </div>

    <div>
      <ol class="relative ml-4 border-s border-gray-200 text-gray-500">
        <li class="mb-10 ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 ring-4 ring-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 text-emerald-600"
              viewBox="0 0 24 24"
              ><path
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="m5 12l5 5L20 7"
              /></svg
            >
          </span>
          <h3 class="font-medium leading-tight">Wetnaam</h3>
          <p class="text-sm">Identificatie van de wet</p>
        </li>
        <li class="mb-10 ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 ring-4 ring-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 text-gray-500"
              viewBox="0 0 24 24"
              ><path
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="m9 15l6-6m-4-3l.463-.536a5 5 0 0 1 7.071 7.072L18 13m-5 5l-.397.534a5.07 5.07 0 0 1-7.127 0a4.97 4.97 0 0 1 0-7.071L6 11"
              /></svg
            >
          </span>
          <h3 class="font-medium leading-tight">Wet URL</h3>
          <p class="text-sm">Plek waar de wet online staat</p>
        </li>
        <li class="mb-10 ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 ring-4 ring-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 text-gray-500"
              viewBox="0 0 24 24"
              ><g
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                ><path
                  d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
                /><path
                  d="M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2m0 9h.01M9 17h.01M12 16l1 1l3-3"
                /></g
              ></svg
            >
          </span>
          <h3 class="font-medium leading-tight">Controle</h3>
          <p class="text-sm">Controle of de output voldoet</p>
        </li>
        <li class="ms-6">
          <span
            class="absolute -start-4 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 ring-4 ring-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 text-gray-500"
              viewBox="0 0 24 24"
              ><g
                fill="none"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                ><path
                  d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
                /><path
                  d="M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v0a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2m0 9l2 2l4-4"
                /></g
              ></svg
            >
          </span>
          <h3 class="font-medium leading-tight">Output</h3>
          <p class="text-sm">Model van de wet in YAML-formaat</p>
        </li>
      </ol>
    </div>
  </div>

  <form class="mt-auto flex" on:submit|preventDefault={handleSubmit}>
    <input
      bind:this={inputElement}
      bind:value={input}
      use:focusElement
      class="mr-2 block w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-gray-800 focus:border-blue-500 focus:ring-blue-500"
      type="text"
      placeholder="Type a message…"
    />

    <button
      class="inline-block rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
      type="submit"
      aria-label="Send message"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24"
        ><path
          fill="none"
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4.698 4.034L21 12L4.698 19.966a.5.5 0 0 1-.546-.124a.56.56 0 0 1-.12-.568L6.5 12L4.032 4.726a.56.56 0 0 1 .12-.568a.5.5 0 0 1 .546-.124M6.5 12H21"
        /></svg
      >
    </button>
  </form>
</main>

<style lang="postcss">
  @reference "tailwindcss/theme";

  .message {
    @apply mb-3 max-w-[75%] self-start whitespace-pre-line rounded-md bg-white px-3 py-2;

    &.own {
      @apply self-end bg-green-100;
    }
  }

  :global(.message a) {
    @apply text-blue-600 underline hover:text-blue-800 hover:no-underline;
  }

  :global(pre code.hljs) {
    @apply !bg-transparent !p-0;
  }
</style>
