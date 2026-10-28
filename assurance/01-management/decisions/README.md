# Decision register

Questions that wait on the project lead live in [`register.yaml`](register.yaml), one entry per
question. The decision inbox page is generated from it by [`build_inbox.py`](build_inbox.py), and
[`check_decisions.py`](check_decisions.py) checks it in CI.

The register is where a question is asked and answered. It is not the decision record: once a
decision is applied, it is recorded where the project already keeps that kind of decision
(WP-M-01 §6 for strategic decisions, otherwise the work product that owns the item), and the
register entry points there.

## Lifecycle

![A question's path through the register: queued (recorded, not asked yet) moves to open when Claude asks it in a batch of ten; from open, it becomes answered when the lead picks an option, or assumed when there is no answer by proceed_after, which is allowed for easy questions only; answered and assumed both become applied once the change is made; any state can become withdrawn when the question no longer applies. A box at the bottom repeats the rule that a hard question is never assumed and never applied without an answer from the lead](figures/fig-dr-1-lifecycle.svg)

*How an entry moves between the states in the table below; copied from LionDriver, where `fig_lifecycle.py` draws it from the same table.*

| Status | Meaning | Who moves it |
|---|---|---|
| `queued` | Recorded but not asked yet. Listed collapsed on the page; needs no `asked` date and may have no gate. `after` names questions to settle first | Claude |
| `open` | Asked; no answer yet | Claude, when asking |
| `answered` | The project lead picked an option (on the inbox page or in chat) | Claude, when copying the answer in |
| `assumed` | No answer by `proceed_after`; Claude went ahead with the recommended option. Allowed only for `reversibility: easy`. The lead can still change it | Claude |
| `applied` | The change is made; `applied.ref` names the commit or PR, `applied.record` where the decision is recorded | Claude |
| `withdrawn` | The question no longer applies; `note` says why | Claude |

A `hard` question is never assumed and never applied without an answer from the lead. A `revisit`
question waits for an answer too, but can be reopened at the gate named in `gate`.

`decider: claude` marks a reversible technical choice: Claude goes with the recommended option when the work
reaches it (as `assumed`, so the lead can change it) unless the lead objects. Everything else is the lead's.

Ask in batches of ten. An open question carries `batch: N`. The page shows the earliest batch that still has an open
question; its **Next batch** button reveals the following one, so keep the next batch or two written ahead. When the
lead has worked through them, write the next ten from the queue, those that unblock the most first (earliest gate,
nothing left in `after`), rewritten to the open-card standard. Rewrite its wording to the standard of the open cards
when it moves.


## The inbox page

Built from this file by [`build_inbox.py`](build_inbox.py) and published at <https://claude.ai/artifact/4kzbTRfzKd2czLetiewL5g>
(private to the lead). Republish to the same link after every change to this file.

Answers and requests for more explanation are saved in the page's own store, in the collections `answers` and
`explain`, keyed by register `id`. At the start of a session Claude reads both, copies answers into this file
(`via: inbox`), writes any requested explanation into `explanation`, applies what can be applied, rebuilds the page
and republishes it.

```sh
python3 assurance/01-management/decisions/check_decisions.py
python3 -m unittest discover -s assurance/01-management/decisions -p 'test_*.py'
python3 assurance/01-management/decisions/build_inbox.py --out <scratch>/inbox.html
```

The register format, checker and page builder are ported from LionDriver
(`assurance/01-management/decisions/`, 2026-10-26); keep them in step when either side changes.
