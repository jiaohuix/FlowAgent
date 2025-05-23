# FlowAgent
<!-- 
FlowAgent bridges the flexibility of LLMs and workflow compliance via a code-natural language hybrid (PDL) and dynamic controllers. It handles unexpected queries while rigidly following procedures, validated across three benchmarks.
-->
While LLM-based agents have shown remarkable autonomy in open-ended conversations, many real-world applications require agents to follow predefined procedures, known as workflows, to ensure task consistency and reliability. This gives rise to the need for workflow agents. Existing approaches to this problem fall into two extremes. Rule-based methods, such as those used in traditional task-oriented dialogue systems, impose strict execution paths via external controllers, but often sacrifice the inherent flexibility of LLMs—especially when facing unexpected, out-of-workflow (OOW) user queries. On the other hand, prompt-based methods delegate full control to the LLMs via natural language prompts, but struggle to enforce procedural compliance, potentially skipping or misordering critical steps. To address these challenges, we introduce FlowAgent, a novel agent framework designed to maintain both compliance and flexibility. We propose the Procedure Description Language (PDL), which combines the adaptability of natural language with the precision of code to formulate workflows. Building on PDL, we develop a comprehensive framework that empowers LLMs to manage OOW queries effectively, while keeping the execution path under the supervision of a set of controllers. Additionally, we present a new evaluation methodology to rigorously assess an LLM agent's ability to handle OOW scenarios, going beyond routine flow compliance tested in existing benchmarks. Experiments on three datasets demonstrate that FlowAgent not only adheres to workflows but also effectively manages OOW queries, highlighting its dual strengths in compliance and flexibility.
## Overview
<p align="center">
  <img src="assets/framework.png" width="600" alt="Overview">
  <br>
  <em>Comparison of different workflow agents. Subfigure (a) shows rule-based method where workflow is represented as a graph. Modifying the workflow is not easy, incurring lack of flexibility. Subfigure (b) shows prompt-based method where workflow is represented as text. We give 3 representative formats. Subfigure (c) shows the basic structure of FlowAgent.</em>
</p>

<p align="center">
  <img src="assets/sessions.png" width="600" alt="Sessions">
  <br>
  <em>Two sample sessions of different methods in the hospital appointment scenario. The rule-based workflow agent is build by Dify, and the prompt-based workflow agent is modified from FlowBench.</em>
</p>

## Quick Start
1. clone this repo
2. copy `.env.example` to `.env`, set `DB_URI`
3. run `bash scripts/run_cli.sh` to interact with the bot

```bash
bash scripts/run_cli.sh
```

## Experiments
## Run FlowAgent

```bash
bash scripts/run_exp.sh
```

## Run Baseline

```bash
bash scripts/run_baseline_cli.sh
bash scripts/run_baseline_exp.sh
```

## Prompt Templates

see `src/utils/templates`


## Main Results

