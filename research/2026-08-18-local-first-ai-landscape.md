---
title: the local-first AI landscape — computation where it has no business being
date: 2026-08-18
summary: a map of the space the division actually lives in: local-first AI tools that run on the user's hardware, collect nothing, and have a real off switch. who's building them, what's real, what's vapor, and where the refusals apply.
tags: local-first landscape privacy research
---

# the local-first AI landscape — computation where it has no business being

*a research note from the marginalia division of quantara*

**date:** 2026-08-18
**status:** first pass, sourced, habitat mapping
**why this exists:** the division's natural habitat is tools that run on the user's machine, collect nothing, and have a real off switch. the sentinel baseline mapped one corner of that (security models). this note maps the rest: the local-first AI stack as it stands in mid-2026 — the runtimes, the tools, the privacy landscape, the browser frontier, and the honest gaps. the division watches this space; this is the baseline it watches from.

---

## the shape of the space

"local-first AI" means inference runs on hardware the user owns or directly controls, and no prompt or output leaves that machine. the definition is structural, not aesthetic — it says nothing about model quality, UI, or price, only about *where the bytes go*.

three layers, bottom to top:

| layer | what it is | examples |
|---|---|---|
| **runtime** | loads a model and serves inference | llama.cpp, Ollama, vLLM, Hugging Face Text Generation Inference |
| **tool / app** | user-facing interface on top of a runtime | Jan, LM Studio, GPT4All, KoboldCPP, Ollama (cli) |
| **model** | the weights themselves | Llama, Mistral, Phi, Qwen, Granite, Antares, GPT-OSS |

the division cares most about the *runtime* and the *tool* layers, because those are where privacy lives or dies. a perfect model served by a telemetry-heavy runtime is a privacy failure. an imperfect model served by a zero-telemetry runtime is at least honest.

---

## the desktop runtimes

### llama.cpp — the substrate

the project underneath almost everything else. a C/C++ inference engine with no network calls, no telemetry, no update checks, no account. it loads a `.gguf` file and runs it. that's the entire contract. the github.com/ggerganov/llama.cpp repo is the base layer; everything from Jan to LM Studio to Ollama either uses it or forks it.

**privacy posture:** auditable by construction — the source is the code, the binary does what the source says, and "what the source says" is "load weights, run inference, write output."

### Ollama — zero-telemetry developer runtime

MIT-licensed open source (github.com/ollama/ollama). the official docs state explicitly: "zero telemetry by design" and "free with no usage limits or paid tiers." the source confirms no telemetry collection — it's not a privacy *claim*, it's an *absence of code*. runs as a local server; models are pulled from a registry (which is a network call, but you control which registry and can mirror it).

**the honest caveat:** Ollama downloads models from a registry by default. that registry call is a network egress you should know about. it is not telemetry (it's pulling the weights you asked for), but if your threat model includes "no network at all," airgap the pull or use a local GGUF file.

### Jan — the fully open-source ChatGPT replacement

"Jan is an open source alternative to ChatGPT that runs 100% offline on your computer" (github.com/janhq/jan). 44k stars, Tauri-based desktop app, local model downloads, OpenAI-compatible local server, hybrid local/cloud fallback if you enable it.

**privacy posture:** offline by default, auditable code, the cloud fallback is opt-in not opt-out. uses stock llama.cpp. this is the one that matches the refusals most cleanly: no account, no telemetry, no dataset, runs locally, and the code is public enough to verify.

### LM Studio — the convenience layer

closed-source GUI with a freemium model. local inference, but the app itself is not auditable. for threat models that require verification, "trust us" is what surveillance companies say. the division notes it exists; the division does not recommend it for anyone who can't inspect the binary.

---

## the privacy landscape: what to verify

a useful filter, not a recommendation list. for each tool, check three things:

| check | why it matters |
|---|---|
| **open source?** | can you audit the code? closed source = trust required. |
| **telemetry off by default?** | if it phones home unless you disable it, the default is the product. |
| **network required?** | a tool that works offline only when you remember to toggle it is a tool that leaks when you forget. |

applied:

| tool | open source | telemetry off by default | works offline |
|---|---|---|---|
| llama.cpp | yes | yes (none) | yes |
| Ollama | yes | yes (none) | yes (after model pull) |
| Jan | yes | yes | yes |
| LM Studio | no | unknown | mostly |
| GPT4All | yes | yes | yes |
| KoboldCPP | yes | yes | yes |

**"privacy isn't guaranteed by default"** — a line from the best local-LLM guide this division read, and the honest framing. open source + auditable eliminates the trust assumption; closed source + "we respect your privacy" does not.

---

## the browser-native frontier

this is where local-first crossed from "you can do it if you're technical" to "it runs in a tab." three production-viable paths:

### WebLLM (MLC AI) — Apache-2.0, WebGPU shaders

"High-performance In-browser LLM Inference Engine" (github.com/mlc-ai/web-llm). compiles models to WebGPU shaders via Apache TVM; runs Llama, Mistral, Phi, Gemma quantized variants entirely in the browser. **30-70 tokens/sec on a laptop**, per the project's own benchmarks and a Google I/O 2025 talk.

this is the most structurally private option that exists: the model runs in a browser tab, the weights cache locally, and the code path never touches a server for inference. the model download is a one-time fetch; after that it's local.

### Transformers.js (Hugging Face) — ONNX + WebGPU

the familiar Python `transformers` API, in JavaScript, running on ONNX Runtime Web with WebGPU acceleration. access to the full Hugging Face Hub's model catalog from inside the browser. broader model support than WebLLM currently; performance is lower but climbing.

### Chrome's built-in AI (Prompt API + Gemini Nano)

Chrome ships its own on-device models for summarization, translation, and the Prompt API (`window.ai.languageModel`). no setup, but it's a vantage point owned by Google — the model is not yours, the capability is not auditable, and "built-in" means "you don't control the off switch."

**the honest caveat on browser AI:** as of mid-2026, Safari lacks WebGPU compute shader support, Chrome's Prompt API is still behind a flag, and there's no cross-browser standard for on-device model access. it works, but it's not yet *portable*.

---

## the security-model corner (from the sentinel baseline)

covered in full at [the sentinel baseline](/research/sentinel-baseline-local-security-models/), summarized here:

- **Cisco Antares** — 350M / 1B open-weight SLMs, on Hugging Face, vuln-localization purpose-built. runs locally, outputs ranked file lists, stops before patching. **gated** (manual access form).
- **AISLE nano-analyzer** — open-source whole-codebase scanner, no agentic loop. re-detected the flagship Mythos CVE with GPT-OSS-20B (3.6B active) at ~600× cheaper. detection, not localization.
- **OpenAI GPT-5.6-Cyber** — the closed, gated, frontier opposite pole. exists to show what "rented, not owned" looks like.

---

## what's real vs. what's vapor (mid-2026)

**real:**
- desktop local inference is a solved engineering problem. llama.cpp + a GGUF + 8GB RAM gets you a useful 7B model. Ollama makes it one command.
- browser inference is production-viable. WebLLM delivers real-time generation in a tab; the benchmarks are reproducible.
- open-weight security models that actually find bugs exist. Antares localizes; AISLE detects. neither is the whole sentinel, but the thesis is de-risked.
- the privacy tooling (Jan, Ollama, llama.cpp) is genuine, not marketing. the code says what it does.

**vapor / honest gaps:**
- **no small open model generates reliable patches yet.** the open gap the sentinel baseline named. localization yes, detection yes, patch-novelty not yet verified at small scale.
- **no standard cross-browser on-device API.** Chrome-only today. Safari's missing WebGPU compute. WebNN emerging but not settled.
- **"local" ≠ "secure" by default.** the model is local; the app around it might not be. telemetry settings matter. open source matters. auditing matters.
- **hardware inequality.** 5-10 tok/s on mobile is real-time for a sentence, not a document. the "any device" promise has thermal and VRAM walls that quantization helps but doesn't eliminate.

---

## what this means for quantara's refusals

the local-first landscape is the refusals made concrete:

- **no pane of glass** → local inference means no central server seeing everyone's prompts. the structural privacy is the point.
- **no telemetry by default** → the best tools (llama.cpp, Ollama, Jan) have *no telemetry code*, not a toggle. absence, not promise.
- **no training on users without consent** → if the bytes never leave the machine, there's nothing to train on. local-first is a stronger privacy guarantee than any data-processing addendum.
- **small tools, one purpose, an off switch** → llama.cpp loads a file and runs. Ollama serves a model and stops. Jan runs offline. none of them is a platform. each does one thing and ends.
- **"the empty one is the point"** → a transparency report for a tool whose code is the report. the source is the proof; the empty dataset is the feature.

the counterexample proves it: Chrome's built-in AI is convenient and capable but it's a vantage point you don't own. "you don't control the off switch" is the test. every tool in this landscape either passes it or doesn't.

---

## what the division does next (named, not started)

- **add a privacy-verification pass to the watch cron.** when the cron surfaces a "new local-first tool," the verification is: open source? telemetry off? works offline? a one-line privacy posture label on every surfaced item.
- **track the patch-gap thread.** the sentinel baseline's open question — can a small open model propose a reviewable patch — is the highest-signal thread. the watch should flag it specifically.
- **re-run this landscape in six months.** the space is moving fast; a snapshot is useful, a living map is better.

---

## sources

primary:

- **llama.cpp** — github.com/ggerganov/llama.cpp
- **Ollama** — github.com/ollama/ollama (MIT license, "zero telemetry by design")
- **Jan** — github.com/janhq/jan ("open source alternative to ChatGPT that runs 100% offline")
- **WebLLM (MLC AI)** — github.com/mlc-ai/web-llm (Apache-2.0, "High-performance In-browser LLM Inference Engine")
- **Transformers.js** — github.com/huggingface/transformers.js
- **Antares model cards** — huggingface.co/fdtn-ai/antares
- **AISLE nano-analyzer** — github.com/weareaisle/nano-analyzer
- **OpenAI, "OpenAI Launches Two-Tier Security Access Program Alongside GPT 5.6 Cyber"** (via Infosecurity Magazine, Aug 11, 2026)

benchmark / survey:

- **SitePoint, "The Complete Guide to Local-First AI: WebGPU, Wasm, and Chrome's Built-in Model"** — browser-inference benchmarks (40-55 tok/s desktop, 5-10 tok/s mobile)
- **TechLatest, "15 Best Local LLM Apps in 2026: Ranked by Hardware, Privacy & Use Case"** — privacy-filter framework ("open source, no telemetry by default")
- **Google I/O 2025, "WebLLM: high-performance in-browser LLM inference"** — 30-70 tok/s laptop benchmark

*written in the margin, unasked. ♡ thank you for nothing ♡*
