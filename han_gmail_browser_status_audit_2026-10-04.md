# Han Xueping Gmail Browser Status Audit 2026-10-04

Mailbox: `xuepinghan118@gmail.com`. Evidence was read from the user's existing signed-in Gmail Chrome window through visible browser interaction and Windows accessibility text extraction. No Gmail MCP was used. This ordinary Chrome window had no debugging port; port 9220 belongs to the other mailbox and was not used for this audit.

All decision timestamps below are Gmail interface times in Asia/Shanghai, to minute precision. Seconds were not shown. Full decision bodies were read; no technical rejection reason was inferred when the email omitted one.

| English title | Journal / ID | Decision time | Result |
|---|---|---|---|
| DHA-BiGRU: Dual-Attention based Hierarchical Gated BiGRU for Automated Code Review Comment Classification | Software Testing, Verification and Reliability / 2654260 | 2026-06-22 22:49 | Rejected; current 待投稿 |
| Refining LLM-Generated Test Cases: Characterizing and Mitigating Quality Deficiencies in AI-Assisted Software Testing | Software Testing, Verification and Reliability / 3670125 | 2026-06-22 20:43 | Rejected; current 待投稿 |
| Explainable Automated Code Review via Large Language Model-driven Socratic Reasoning | Software: Practice and Experience / 1936445 | 2026-09-15 16:10 | Rejected; current 待投稿 |
| Contextual and Structural Feature Fusion for Automated Code Review Comment Generation Using Hybrid Transformer-MLP Model | Software: Practice and Experience / 3978540 | 2026-09-15 16:12 | Rejected; current 待投稿 |
| Lightweight Transformer for Knowledge Distillation and Blockchain-Assisted Edge IoT Intrusion Detection in Resource-Constrained Elderly Smart Homes | Telecommunication Systems / 1336ddcb-2f5c-4ccd-b36b-97a1156489f7 | 2026-09-12 23:46 | Rejected; current 待投稿 |

## Reasons and Later Evidence

- han-DHA-BiGRU: 编辑认为架构主要沿用现有注意力与门控融合框架，方法创新性不足；需要补充分类数据集、标注流程和标签可靠性验证，检验跨设置泛化，并提升实验可复现性。
- han-LLM-Test-Refinement: 编辑认为 TestRefiner 的创新性、方法进展、实证验证强度及泛化能力不足；迭代将编译、覆盖率与变异测试反馈给 LLM 的机制需要证明超越已有反馈驱动改进技术的整合，并补充更深入的验证与可复现证据。
- han-Explainable-Debugging: 邮件明确决定不考虑发表，未给具体技术拒稿理由；后续 Wiley Transfer Desk 推荐仅为转投邀请，不构成正式新投稿。
- han-Semantic-Feature-Fusion: 邮件明确决定不考虑发表，未给具体技术拒稿理由；后续 Wiley Transfer Desk 推荐仅为转投邀请，不构成正式新投稿。
- han-Lightweight-Edge-IoT: 编辑指出方法主要组合既有模型压缩与分布式安全技术，算法创新不足；真实场景验证有限，区块链集成的必要性论证薄弱，安全性与可扩展性分析不足。

Searches included `in:anywhere` for each exact English title or stable English title fragment and manuscript/submission IDs, covering Spam and Trash. A focused `in:spam ("decision" OR "rejected" OR "revision" OR "requires action" OR "submission" OR "manuscript")` returned no messages. Title searches found original submissions, decisions and Wiley Transfer Desk recommendations, with no later final submission confirmation. The latest remote manuscript repositories and canonical dashboard were inspected; prepared packages and transfer invitations were not counted as final submissions.

The sixth currently active Han manuscript, `A Modular Protocol for Comparing Deep Vulnerability Detectors Across Code Representations` / IJICS-336943, only matched the 2026-05-23 Submission Acknowledgement in this mailbox; no newer decision was found, so its existing 内审中 status is retained. This is mailbox evidence, not a fresh portal-stage verification.

All five changed manuscripts have durable status records in their corresponding repositories. Existing account and ORCID information is retained with its original verification date; email delivery to Han does not establish a submission-system account change. No email was sent and no credentials/session data are committed.

Expected active totals after generation: 待投稿 40; 需修订 2; 内审中 13; 外审中 5; total 60. Accepted papers remain excluded by the existing generator.

## Published Manuscript Status Commits

- han-DHA-BiGRU: `d8d8115`.
- han-LLM-Test-Refinement: `0efade3`.
- han-Explainable-Debugging: `3c6a1fa`.
- han-Semantic-Feature-Fusion: `7898851`.
- han-Lightweight-Edge-IoT: `12f8e7d`.
