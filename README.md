# Scout 🔭

> **An AI-powered personal monitoring agent that understands what you want, watches for changes, and tells you when something meaningful happens.**

Scout started with an idea from my friend **Neeraj**: instead of making someone repeatedly check for the things they care about, what if an agent could watch for meaningful changes and tell them when something actually matters?

We built Scout together as an MVP around that idea.

---

## What is Scout?

Scout is a personalized monitoring agent.

Instead of simply asking an AI for recommendations once, you tell Scout what you want, and Scout keeps watching for changes that matter to you.

For example:

> "I want to watch Dune 3 this Saturday evening with two people. IMAX if possible, PVR Lulu preferred, under ₹1500, and preferably cheaper."

Scout can:

1. Understand the request using **Gemma 3:4b**
2. Convert the natural-language request into structured preferences
3. Resolve semantic preferences such as "Saturday evening"
4. Evaluate available screenings against those preferences
5. Remember what it previously observed
6. Detect meaningful changes
7. Identify opportunities that matter to the user
8. Decide whether the user should be notified

The goal is simple:

> **Scout doesn't just recommend. It watches.**

---

## Why Scout?

Most recommendation systems answer a question once.

But many real-world decisions are not one-time questions.

You might care about:

* a movie becoming available
* seats becoming available
* a price dropping
* a preferred format appearing
* a preferred theatre getting a suitable screening

Checking manually over and over is tedious.

Scout turns that repeated checking into a monitoring problem.

Instead of:

```text
User → Ask → Search → Check → Repeat
```

Scout aims for:

```text
User
  ↓
Natural-language preference
  ↓
Gemma
  ↓
Structured intent
  ↓
Scout watches
  ↓
Environment changes
  ↓
Meaningful opportunity
  ↓
Notification
```

---

## Example

Scout's current demo uses a deterministic fixture source to simulate a changing movie-booking environment.

### Initial state

No suitable IMAX screening is available.

```text
Shows observed:    2
Changes detected:  0
Opportunities:     0
Decision:          do_not_notify
```

### A matching screening appears

```text
Changes detected:  1
Opportunities:     3
Decision:          notify

🔔 NOTIFICATION

New matching screening available:
  PVR Lulu IMAX
  Saturday 07:30 PM
  3 matching seat categories are available.
```

### Availability changes

Seats become less available, but the change does not create a meaningful opportunity for this watch.

```text
Changes detected:  2
Opportunities:     0
Decision:          do_not_notify
```

Scout stays quiet.

### Price improves

The Premium seat price drops:

```text
₹700 → ₹620
```

Scout detects that this matters because the user said they prefer cheaper options.

```text
Changes detected:  1
Opportunities:     1
Decision:          notify

🔔 NOTIFICATION

Price improvement:
  Premium: ₹700 → ₹620
```

This is the behavior we wanted to demonstrate:

> **Observe → compare → understand significance → notify only when it matters.**

---

## How Gemma is used

Scout uses **Gemma 3:4b** locally through **Ollama**.

Gemma's responsibility is understanding the user's natural-language intent.

For example:

```text
"I want Dune 3 this Saturday evening with two people,
IMAX if possible, PVR Lulu preferred,
under ₹1500, and preferably cheaper."
```

becomes structured information such as:

```text
Movie:              Dune 3
Party size:         2
Date:               2026-10-03
Time:               17:00 - 22:00
Preferred format:   IMAX
Preferred theatre:  PVR Lulu
Max budget:         ₹1500
Budget operator:    <
Hard budget:        true
Prefer cheaper:     true
```

Gemma **does not** decide whether a screening is actually available, calculate ticket prices, or invent facts about the source.

Those responsibilities stay in deterministic application code.

### The design principle

> **Gemma interprets intent. Code establishes facts.**

This separation makes the system easier to reason about and prevents the LLM from becoming the source of truth for things such as prices, availability, dates, or changes.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │     User Prompt     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Gemma 3:4b        │
                    │  Intent Extraction  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ PreferenceSpec      │
                    │ Structured Intent   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Preference Resolver │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Watch           │
                    │ Persistent State    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Collector       │
                    │  Current Observed   │
                    │       Shows         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Candidate Evaluator │
                    │ Deterministic Facts │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Snapshots        │
                    │ Previous vs Current │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Change Detection    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Opportunity         │
                    │ Detection            │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Notification        │
                    │ Decision            │
                    └─────────────────────┘
```

---

## Project Structure

```text
scout/
├── ai/
│   └── gemma.py
│
├── domain/
│   ├── preferences.py
│   ├── seats.py
│   ├── shows.py
│   ├── matches.py
│   ├── metrics.py
│   ├── watches.py
│   ├── snapshots.py
│   ├── changes.py
│   ├── opportunities.py
│   └── notifications.py
│
├── matching/
│   ├── evaluator.py
│   └── resolver.py
│
├── monitoring/
│   ├── monitor.py
│   ├── stores.py
│   ├── changes.py
│   ├── opportunities.py
│   ├── notifications.py
│   ├── runner.py
│   └── scheduler.py
│
├── persistence/
│   └── sqlite.py
│
└── sources/
    └── fixture.py
```

---

## Core Design

Scout separates the system into several responsibilities.

### 1. Preference interpretation

Gemma converts natural language into a `PreferenceSpec`.

```text
Natural language
      ↓
     Gemma
      ↓
PreferenceSpec
```

### 2. Preference resolution

Semantic preferences such as:

```text
"Saturday evening"
```

are resolved into concrete date/time information by deterministic code.

### 3. Candidate evaluation

Scout evaluates each screening against the user's preferences.

This produces factual information such as:

* movie match
* seat availability
* total price
* budget remaining
* date match
* time match
* format match
* theatre match
* area match

### 4. Persistent monitoring

Scout stores:

* what it is watching
* what it observed
* when it observed it
* the candidates found during that observation

SQLite is currently used for durable local persistence.

### 5. Change detection

Scout compares snapshots to determine what changed.

Examples:

```text
Show added
Show removed
Seat availability changed
Seat price changed
```

### 6. Opportunity detection

Not every change matters.

Scout therefore separates:

```text
Change
  ↓
Does this matter to this watch?
  ↓
Opportunity
```

For example, a seat becoming unavailable is a change, but it is not necessarily an opportunity worth notifying about.

### 7. Notification decision

Finally:

```text
Opportunity
     ↓
Should the user be interrupted?
     ↓
Notify / Do not notify
```

This gives Scout a clean progression from raw observations to meaningful user-facing events.

---

## Local AI

Scout currently uses:

* **Gemma 3:4b**
* **Ollama**
* Local inference

The project is intentionally built around an open-weight model rather than treating the LLM as an external black-box API.

This makes the AI component part of the application architecture itself.

---

## Running Scout Locally

### 1. Install Ollama

Install Ollama for your platform.

Then pull the model:

```bash
ollama pull gemma3:4b
```

Verify that it works:

```bash
ollama run gemma3:4b
```

### 2. Install Python dependencies

Create your environment and install the project's dependencies.

For example:

```bash
pip install -r requirements.txt
```

### 3. Run the demo

The repository includes a demo that connects the major Scout components together.

```bash
python demo.py
```

The demo:

```text
User prompt
    ↓
Gemma
    ↓
Preference resolution
    ↓
Persistent watch
    ↓
Monitoring
    ↓
Fixture state changes
    ↓
Change detection
    ↓
Opportunity detection
    ↓
Notification decision
```

---

## Why Fixture Data?

The current MVP uses a deterministic fixture source rather than a live movie-booking integration.

This is intentional.

The core problem Scout is demonstrating is not web scraping. It is:

> **Can Scout understand what the user wants, observe a changing environment, recognize when something meaningful happens, and decide when to notify?**

The fixture source lets us reproduce those state changes reliably while developing and demonstrating the monitoring architecture.

The source is isolated behind an adapter, so the monitoring pipeline does not depend on where the observations come from.

A live external source can therefore be added later without redesigning Scout's core monitoring logic.

---

## Current MVP

The current MVP demonstrates:

* Natural-language preference understanding
* Local Gemma inference
* Structured preference extraction
* Semantic preference resolution
* Deterministic candidate evaluation
* Persistent watches
* SQLite persistence
* Monitoring snapshots
* Change detection
* Opportunity detection
* Notification decisions
* A simple monitoring scheduler
* End-to-end demonstration using changing fixture data

### What is intentionally not part of this MVP

The current submission does not claim:

* Live BookMyShow integration
* Automated ticket booking
* Payment handling
* Production notification delivery
* A hosted cloud AI service

The focus is on demonstrating Scout's core agent behavior.

---

## The Core Idea

Scout is built around one principle:

> **Don't make the user keep checking.**

The user describes the outcome they care about.

Scout remembers it.

Scout watches.

When the environment changes, Scout evaluates whether that change matters.

And only then does it speak up.

```text
Understand
    ↓
Remember
    ↓
Watch
    ↓
Detect
    ↓
Evaluate
    ↓
Notify
```

That's Scout. 🔭

---

## Built for a Friend

Scout was built collaboratively by:

* **Mohit** — `mohit_anand_9f7275b63f423`
* **Neeraj** — `ks_neeraj_7b407064bd57e34`

The core idea behind Scout was originally suggested by Neeraj.

We then worked together to turn that idea into the current MVP.

That collaboration is also why Scout fits the challenge theme **Build for a Friend**: the project started from a real conversation about a problem someone might actually want an agent to solve.

---

## Hacktoberfest Weekend Challenge 2026

Scout was built for the **DEV Hacktoberfest Weekend Challenge 2026**.

The project focuses on the challenge's open-source AI requirement by using **Gemma 3:4b locally** as a core part of the system.

---

## Status

🚧 **MVP complete**

The current implementation focuses on the core monitoring loop:

```text
User intent
    ↓
Gemma
    ↓
Watch
    ↓
Observe
    ↓
Detect changes
    ↓
Find meaningful opportunities
    ↓
Decide whether to notify
```

Future source adapters and richer interfaces can build on top of this foundation.
