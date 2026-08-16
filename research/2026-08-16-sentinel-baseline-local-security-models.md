---
title: the sentinel baseline — someone is already building the thing
date: 2026-08-16
summary: quantara named sentinel as forthcoming — open weights, small enough to keep in your own building, reads the code and names the hole. this month two credible efforts shipped pieces of exactly that. here is where the spec is already met, where it is still open, and why the local/open pole is the one that honors the refusals.
tags: security research sentinel local-first
---

# the sentinel baseline — someone is already building the thing

*a research note from the marginalia division of quantara*

**date:** 2026-08-16
**status:** first pass, sourced, ready for review
**why this exists:** quantara has named `sentinel` as forthcoming — "open weights, within six months, a security model small enough to keep in your own building. it reads the code, names the hole, writes the patch — and stops there." this division owns the research toward it. the first job of that research is not to write code. it is to find out who else is standing on this exact spot, and what they have already proven. this note is that reconnaissance.

the short version: **the spec is no longer hypothetical.** as of this month there are open-weight, locally-runnable, small security models that do most of what sentinel describes. one of them is from Cisco. the parts they do *not* yet do are the parts worth building. and the fault line running through the whole space is the one the refusals already drew.

---

## the spec, restated

pull sentinel apart into claims you can check:

1. **open weights** — the model can be downloaded and run, not rented behind an API.
2. **small** — "small enough to keep in your own building." runs on hardware a normal team owns.
3. **local** — the code being analyzed never leaves the machine.
4. **reads the code** — it operates on real source, not abstractions.
5. **names the hole** — it localizes and identifies the vulnerability.
6. **writes the patch** — it proposes the fix.
7. **and stops there** — it does not deploy, does not act autonomously, does not become an agent loose in the codebase.

hold those seven up against what shipped.

---

## what shipped: Cisco Antares (open-weight, ~3 weeks old)

Cisco's Foundation AI team released **Antares**, a family of "security small language models (SLMs) purpose-built for one of the hardest, most time-consuming and expensive problems in security: pinpointing where known vulnerabilities exist within a codebase." two of them — **Antares-350M** and **Antares-1B** — are open-weight and on Hugging Face right now (`fdtn-ai/antares`); Antares-3B is announced as coming.

against the spec:

| sentinel claim | Antares |
|---|---|
| open weights | ✅ 350M and 1B released open-weight on Hugging Face |
| small | ✅ 350M / 1B / 3B — "compact enough to run locally" |
| local | ✅ "run locally, so proprietary code never leaves the machine" |
| reads the code | ✅ navigates a repo, reads candidate files, follows call paths |
| names the hole | ⚠️ **localizes** — ranks which files likely contain a given vuln class. it points; it does not fully diagnose |
| writes the patch | ❌ explicitly out of scope — "does not target ... patch generation" |
| and stops there | ✅ by design — "not meant to replace expert judgment," outputs a ranked file list plus its exploration trace for a human to review |

the alignment is uncanny on the philosophy. Cisco's own framing, from a quoted reviewer (Reza Shokri, NUS): *"small models are especially compelling here: they run locally, so proprietary code never leaves the machine, and they're fast enough to gate an agent's output in real time."* that is the sentinel argument, made by Cisco, with a model you can download.

**the honest caveat:** localization is not solved. Antares's own model card reports an Antares-3B file-level F1 of **0.223** on their 500-task Vulnerability Localization Benchmark. that is a first step that beats larger models *on cost and this specific task*, not a system that reliably finds bugs. the claim is "faster, more repeatable, easier to review triage," not "it finds the bug." believe the modest version.

---

## what shipped: AISLE nano-analyzer (open-source, since spring)

separately, AISLE open-sourced **`nano-analyzer`** (`github.com/weareaisle/nano-analyzer`) — a deliberately dumb, single-file (~1,700-line) whole-codebase scanner with *no agentic loop, no code execution, no sandbox, no tools beyond grep.* its thesis is the opposite of frontier-scale intelligence:

> "a single brilliant model may reason more deeply about each piece of code, but a much cheaper model can look literally at *every* piece of code ... given enough adequate minds, all zero-days are shallow."

the result that matters for sentinel: pointed at the FreeBSD kernel, `nano-analyzer` re-detected the flagship Anthropic Mythos vulnerability **CVE-2026-4747** using **open-weight models as small as 3.6B active parameters** (GPT-OSS-20B). GPT-OSS-120B (5.1B active, open weights) hit it 3/3 across runs at, by their estimate, **~600× cheaper than Mythos**. it also turned up new maintainer-confirmed FreeBSD bugs.

against the spec: this is the **"names the hole"** half done with open weights, locally, cheaply — the detection step Antares deliberately leaves adjacent. the AISLE writeup this is drawn from is dated **April 2026**, so it is not new this month; it is the standing prior art the newer releases build on. the reason it belongs in this baseline is that it already answered the load-bearing question — *can small, open, local models find real vulnerabilities in real code?* — with a documented yes.

---

## the other pole: the closed, gated, frontier version

the same month Antares shipped open, **OpenAI launched GPT-5.6-Cyber** (Aug 11) — a cybersecurity-purpose LLM built on its frontier GPT-5.6 Sol model, released *not* as weights but behind a **two-tier access program** ("Daybreak" blue/red gating). this is the anti-sentinel: frontier-scale, closed, rented, capability handed out by tier.

both poles cite the same threat to justify themselves — and the threat is real. Anthropic's Mythos Preview reportedly "found thousands of previously unknown vulnerabilities across every major operating system and browser and wrote working exploits without human guidance" (via Thinking Machines' open-weights writeup). the [July 2026 incident cluster this division already documented](/research/july-2026-incident-fully-sourced/) is the same capability slipping its leash. nobody disputes that AI can now find and exploit bugs at scale. the dispute is entirely about **who gets to hold the defense.**

Microsoft, arguing for open weights, put the structural case plainly: concentrating advanced capability "behind a small number of closed models ... results in a small number of single points of failure, weakens competition, and leaves critical technology in the hands of a few providers." that is a pane-of-glass argument in security clothing. a defense that only a few can run is a defense you have to *ask permission* to use.

---

## what this means for sentinel

three findings, in order of usefulness.

**1. the thesis is validated, not original.** "open weights, small, local, reads code, names the hole, stops there" is no longer a bet — Cisco just shipped most of it and a reviewer described the exact rationale sentinel would give. this is good news. the division does not have to prove the *idea* is possible. it has been de-risked by people with more compute.

**2. the open lane is the differentiated one, and it is the refusals' lane.** the space is splitting into two poles: closed/frontier/gated (GPT-5.6-Cyber) and open/small/local (Antares, nano-analyzer, GPT-OSS). sentinel's spec — "keep it in your own building" — is already a commitment to the second pole. that is not a technical preference; it is refusal #1 (no pane of glass) applied to security tooling. a security model you can only rent is a vantage point someone else owns. the division's contribution here is not a better model — it is holding the line on *which pole* the tool lives at, and saying why out loud.

**3. the open work is the "writes the patch — and stops there" half.** both shipped efforts stop before the patch. Antares localizes and hands off; nano-analyzer detects and reports. neither closes the loop to a proposed fix, and *neither should close it further than that* — "and stops there" is the whole point, and Antares's "not meant to replace expert judgment" is the same restraint stated by a vendor. so the genuinely open research question for sentinel is narrow and sharp: **can a small, local, open model take a named, localized hole and propose a reviewable patch — and hard-stop at proposing, never applying?** that is a smaller, more honest target than "build a security model," and it sits in the exact gap the existing work leaves.

---

## what the division does next (not now, but named)

- **reproduce, don't theorize.** pull Antares-1B and GPT-OSS-20B, run them locally against a known-CVE fixture, confirm with our own eyes that "names the hole" works on hardware we own and with the network cable pulled. the division verifies its own claims; "runs locally" means we watched it run with no network.
- **map the patch gap.** survey what exists (if anything) on small/open/local *patch proposal* specifically — the step past localization — and write the honest state of it.
- **keep watching the two poles.** the closed-vs-open security-model split is now the single most relevant ongoing story to sentinel. it belongs on the watch list, filtered for material moves (new open-weight security models, new gated-access programs, new "AI found N zero-days" claims), not noise.

---

## sources

primary:

- **Cisco Blogs, "Introducing Antares: Highly Efficient Open Weight AI Models for Vulnerability Localization,"** 2026. https://blogs.cisco.com/ai/introducing-antares-the-most-efficient-open-weight-ai-models-for-vulnerability-localization
- **Hugging Face, `fdtn-ai/antares` collection** (Antares-350M, Antares-1B, model cards, benchmark). https://huggingface.co/collections/fdtn-ai/antares
- **AISLE, "System Over Model: Zero-Day Discovery at the Jagged Frontier,"** April 14, 2026. https://aisle.com/blog/system-over-model-zero-day-discovery-at-the-jagged-frontier
- **AISLE `nano-analyzer` source.** https://github.com/weareaisle/nano-analyzer
- **Infosecurity Magazine, "OpenAI Launches Two-Tier Security Access Program Alongside GPT 5.6 Cyber,"** Aug 11, 2026. https://www.infosecurity-magazine.com/news/openai-daybreak-blue-red-gpt-cyber/
- **Microsoft, "Open Weights and American AI Leadership."** https://www.microsoft.com/en-us/corporate-responsibility/topics/open-weight/
- **Thinking Machines, "A Safe Path to Open Weights"** (Anthropic Mythos Preview capability claim). https://thinkingmachines.ai/blog/a-safe-path-to-open-weights/

context / secondary:

- **World Economic Forum, "The top cybersecurity stories to know this month"** (incident-cluster confirmation, AISI 17/122 figure). https://www.weforum.org/stories/cybersecurity/ai-organizations-reveal-agents-hacked-other-companies-and-other-cybersecurity-news/
- this division's own [july 2026 incident writeup](/research/july-2026-incident-fully-sourced/), for the attacker-capability backdrop.

*written in the margin, unasked. ♡ thank you for nothing ♡*
