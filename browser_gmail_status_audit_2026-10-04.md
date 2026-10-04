# Browser Gmail status verification: 2026-10-04

This follow-up uses the existing Chrome debugging port 9220 and its open Gmail tab, as explicitly requested by the user. No Gmail MCP was used for this follow-up.

The Gmail page title and Google account menu both identify the signed-in mailbox as `wenquan6328@gmail.com`. The account menu lists only that signed-in account; a separate Gmail tab is at the Google sign-in page. This is not an audit of `xuepinghan118@gmail.com`.

The visible Gmail search used `in:anywhere after:2026/08/09` with decision, amendment, revision, and submission-confirmation subjects. It returned 27 conversations, including Spam. Message text was read from Gmail's rendered message bodies, not through an email API. Gmail's displayed dates below are in Asia/Shanghai and have minute precision.

| Manuscript | Browser message date | Message ID read in the page | Verified state |
| --- | --- | --- | --- |
| Indoor ageing-friendly resilience / Humanities and Social Sciences Communications | 2026-09-11 16:22 | `1a08f8f71829545d` | Accepted for publication |
| Elderly day-care thermal comfort / Energy & Buildings | 2026-09-13 00:15 | `1a09667669e9d1a9` | Accepted, ENB-D-26-04086R3 |
| Refrigeration energy efficiency at 65 facilities / Scientific Reports | 2026-09-16 22:31 | `1a0aaa1176e8ec22` | Accepted, 2a8d0dcd-74c6-4848-86ff-62ad8eb84d62 |
| Peer-normalised refrigeration inspection queue / Energy Reports | 2026-09-07 10:14 | `1a079a58b6347f95` | Rejected, EGYR-D-26-01996R1; unauthorized authorship changes |
| Frailty reversibility / npj Aging | 2026-09-11 01:15 | `1a08c513d7caf0f4` | Rejected, 536d3f2f-d37c-4d89-bd0e-2035b36f03ae |
| Work-role participation / BMC Medicine | 2026-08-12 19:25 | `19ff5b835714faed` | Amendment required; clarify placement of Fig. 1-4 |
| Point-cloud component segmentation / Journal of Big Data | 2026-09-25 04:12; 2026-09-27 14:58 | `1a0d50c005222070`; `1a0e1a88f2a0c74a` | Minor revision followed by explicit manuscript-submitted receipt |
| Historic-community retrofit resident support / Frontiers in Environmental Science | 2026-09-18 17:53 | `1a0b3ef8be92a2b3` | Cannot be accepted for publication |

The Energy Reports conversation contains an Inbox message and a Spam duplicate. Gmail displayed the expanded Spam duplicate, with its built-in Chinese translation; the identifier, rejection, and authorship-policy reason match the recorded decision.

The browser evidence agrees with the statuses already published in source commit `bfa28d5` and public dashboard commit `aec9f9d`. No further status change is justified by this follow-up. Three accepted manuscripts remain recorded in the source overrides and excluded from the active dashboard under its existing rules. The active dashboard has 60 entries: 35 awaiting submission, 2 requiring revision, 18 in internal processing, and 5 in external review.

The earlier audit is retained in `gmail_status_audit_2026-10-04.md`, with exact email timestamps and manuscript-repository evidence. This document distinguishes the user-requested browser verification from that earlier MCP-based audit.
