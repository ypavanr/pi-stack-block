<script>
  import { onMount } from "svelte";
  import { api } from "./lib/api.js";

  let blocks = [];
  let loading = false;
  let errorMsg = "";
  let expandedId = null;

  let q = "";
  let tagsInput = "";

  let showCreate = false;
  let creating = false;
  let createError = "";
  let form = { question: "", answer: "", tags: "" };

  function openCreate() {
    createError = "";
    showCreate = true;
  }
  function closeCreate() {
    showCreate = false;
    form = { question: "", answer: "", tags: "" };
  }
  function formatAnswer(s) {
    if (!s) return '';
   return s.replace(/([.;?!])(?!\s*$)\s*/g, '$1\n');
  }

async function loadBlocks() {
  loading = true; errorMsg = ""; expandedId = null;
  try {
    const tags = tagsInput
      .split(",")
      .map(s => s.trim())
      .filter(Boolean)
      .join(",");

  
    let endpoint = "/get-all-blocks";
    const params = {};

    if (tags) {
      endpoint = "/blocks/by-tags";
      params.tags = tags;
    } else if (q.trim()) {
      endpoint = "/blocks/search";
      params.q = q.trim();
      params.mode = "any"; 
    }

    const res = await api.get(endpoint, { params });
    blocks = res.data;
  } catch (e) {
    errorMsg =
      (e && e.response && e.response.data && e.response.data.error) ||
      e.message ||
      "Failed to load blocks";
  } finally {
    loading = false;
  }
}

function toggle(id) {
  expandedId = expandedId === id ? null : id;
}

async function del(id) {
  if (!confirm("Delete this block?")) return;
  try {
    await api.delete(`/blocks/${id}`);
    blocks = blocks.filter(b => b.id !== id);
  } catch (e) {
    alert(
      (e && e.response && e.response.data && e.response.data.error) ||
      e.message ||
      "Delete failed"
    );
  }
}

  async function createBlock() {
    createError = "";
    const question = form.question.trim();
    const answer = form.answer.trim();
    const tagsArr = form.tags.split(",").map(s => s.trim()).filter(Boolean);

    if (!question || !answer) {
      createError = "Question and Answer are required.";
      return;
    }
    creating = true;
    try {
      await api.post("/create-block", { question, answer, tags: tagsArr });
      closeCreate();
      await loadBlocks();
    } catch (e) {
      createError = (e && e.response && e.response.data && e.response.data.error) || e.message || "Create failed";
    } finally {
      creating = false;
    }
  }

  function onKeydown(e) {
    if (showCreate && e.key === "Escape") closeCreate();
  }

  onMount(loadBlocks);
</script>

<svelte:window on:keydown={onKeydown} />

<main>
  <h1><span>STACK</span> <span class="black">BLOCK</span></h1>
</main>

<div class="toolbar">
  <div class="search">
    <input
      placeholder="Search keywords (question FTS)"
      bind:value={q}
      on:keydown={(e) => e.key === 'Enter' && loadBlocks()}
    />
    <input
      placeholder="Filter by tags (comma-separated)"
      bind:value={tagsInput}
      on:keydown={(e) => e.key === 'Enter' && loadBlocks()}
    />
    <button on:click={loadBlocks}>Search</button>
    <button on:click={() => { q=''; tagsInput=''; loadBlocks(); }}>Clear</button>
  </div>

  <button class="create-btn" type="button" on:click={openCreate}>+ New Block</button>
</div>

{#if loading}
  <p class="muted">Loading…</p>
{:else if errorMsg}
  <p class="err">{errorMsg}</p>
{:else if !blocks.length}
  <p class="muted">No results.</p>
{:else}
  <div class="grid">
    {#each blocks as b}
  <button
    class="card"
    type="button"
    on:click={() => toggle(b.id)}
    aria-expanded={expandedId === b.id}
    aria-controls={"block-" + b.id}
  >
    <h3 class="q">{b.question}</h3>

    <div class="tags">
      {#each b.tags as t}
        <button
          class="tag"
          type="button"
          on:click|stopPropagation={() => { tagsInput = t; loadBlocks(); }}
          aria-label={`Filter by tag ${t}`}
          title="Filter by this tag"
        >{t}</button>
      {/each}
    </div>

    {#if expandedId === b.id}
      <div id={"block-" + b.id} class="ans" style="white-space: pre-line;">
  {formatAnswer(b.answer)}
</div>

      <button class="danger" type="button" on:click|stopPropagation={() => del(b.id)}>
        Delete
      </button>
    {:else}
      <div class="muted">Click to view answer</div>
    {/if}
  </button>
{/each}

  </div>
{/if}

{#if showCreate}
<button
  class="backdrop"
  type="button"
  on:click={closeCreate}
  aria-label="Close dialog"
/>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="create-title" on:click|stopPropagation>
    <h2 id="create-title">Create Block</h2>
    <form on:submit|preventDefault={createBlock}>
      <label>
        Question
        <input
          type="text"
          bind:value={form.question}
          placeholder="e.g., What is ACID?"
          required
        />
      </label>

      <label>
        Answer
        <textarea
          rows="4"
          bind:value={form.answer}
          placeholder="Your answer here…"
          required
        ></textarea>
      </label>

      <label>
        Tags (comma-separated)
        <input
          type="text"
          bind:value={form.tags}
          placeholder="sql, database, backend"
        />
      </label>

      {#if createError}<p class="err" aria-live="polite">{createError}</p>{/if}

      <div class="actions">
        <button type="button" on:click={closeCreate}>Cancel</button>
        <button class="primary" type="submit" disabled={creating}>
          {creating ? "Creating…" : "Create"}
        </button>
      </div>
    </form>
  </div>
{/if}

<style>
  main { text-align: center; padding: 1em; max-width: 240px; margin: 0 auto; }
  h1 { text-transform: uppercase; font-size: 4em; font-weight: 100; }
  h1 span:first-child { color: #ff3e00; }
  h1 .black { color: black; }

  .toolbar {
    display: flex; align-items: center; gap: 1rem;
    margin: 1rem auto; max-width: 1100px;
  }
  .search { display: flex; gap: .6rem; align-items: center; flex: 1; }
  .toolbar input { flex: 1; padding: .5rem .75rem; border: 1px solid #ccc; border-radius: .5rem; }
.toolbar button {
  padding: .55rem .9rem;
  border-radius: .5rem;
  border: 1px solid #ddd;
  background: #f6f6f6;
}
.toolbar button.create-btn {           
  background: #22c55e;
  border-color: #16a34a;
  color: #fff;
  font-weight: 600;
}
.toolbar button.create-btn:hover { filter: brightness(0.95); }  .create-btn {
    margin-left: auto;
    background: #22c55e; border-color: #16a34a; color: #fff; font-weight: 600;
  }
  .create-btn:hover { filter: brightness(0.95); }

  .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
  @media (max-width: 1024px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  @media (max-width: 640px)  { .grid { grid-template-columns: 1fr; } }

  .card { background: #fff; border: 1px solid #e8e8e8; border-radius: 14px; padding: 1rem; transition: transform .12s ease, box-shadow .12s ease; cursor: pointer; }
  .card:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.08); }
  .q { font-weight: 600; margin: 0 0 .5rem; }
  .ans { margin: .75rem 0 .5rem; line-height: 1.55; }
  .tags { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .25rem; }
  .tag { font-size: .8rem; padding: .15rem .45rem; border-radius: 999px; border: 1px solid #ddd; background: #fafafa; cursor: pointer; }
  .muted { color: #777; }
  .err { color: #b00020; margin: .25rem 0; }
  .danger { margin-top: .6rem; border: 1px solid #f0c0c0; background: #ffecec; border-radius: 8px; padding: .35rem .7rem; cursor: pointer; }

  .backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,.45);
    z-index: 30;
  }
  .modal {
    position: fixed; inset: 0; display: grid; place-items: center; z-index: 40;
  }
 
  .modal .actions {
    display: flex; gap: .6rem; justify-content: flex-end; margin-top: .75rem;
  }
  .modal form {
    width: min(600px, 92vw);
    background: #fff; border-radius: 14px; border: 1px solid #e8e8e8;
    padding: 1rem 1.1rem;
    box-shadow: 0 12px 30px rgba(0,0,0,.2);
  }
  .modal h2 { margin-top: 0; margin-bottom: .5rem; }
  .modal label { display: grid; gap: .35rem; margin: .5rem 0; font-weight: 600; }
  .modal input, .modal textarea {
    padding: .5rem .7rem; border: 1px solid #ccc; border-radius: .5rem;
  }
  .modal .primary {
    background: #22c55e; border-color: #16a34a; color: #fff; font-weight: 600;
  }
  .modal .primary[disabled] { opacity: .7; cursor: not-allowed; }
  .card {
  display: block;
  width: 100%;
  text-align: left;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 14px;
  padding: 1rem;
  transition: transform .12s ease, box-shadow .12s ease;
  cursor: pointer;
}
.card:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.08); }
.card:focus-visible { outline: 2px solid #4d90fe; outline-offset: 2px; }

.tags { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .25rem; }
.tag {
  font-size: .8rem;
  padding: .15rem .45rem;
  border-radius: 999px;
  border: 1px solid #ddd;
  background: #fafafa;
  cursor: pointer;
}
.tag:focus-visible { outline: 2px solid #4d90fe; outline-offset: 2px; }
.backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 30;
  border: 0;
  padding: 0;
}
.backdrop:focus { outline: none; }

</style>
