# Retrieval Sources Reference / 检索来源参考

Use this file when Module 2 needs venue lists, source URLs, or domain-specific supplements.

---

## Primary Sources / 主要来源

### arXiv
- URL: https://arxiv.org/search/
- Tips: Filter by category (cs.CL, cs.CV, cs.LG, etc.); sort by submission date for recency

### Hugging Face Papers
- URL: https://huggingface.co/papers
- Tips: Daily trending; good for community-validated recent work

### GitHub
- URL: https://github.com/search
- Tips: Search README + topic tags; sort by stars updated recently for active implementations

### Papers With Code
- URL: https://paperswithcode.com/
- Tips: Use for SOTA tables, benchmark comparisons, linked code repos

---

## CCF Top Venues / CCF 推荐会议

Search official proceedings or DBLP / Semantic Scholar for these when user needs top-tier work.

### CCF-A (Computer Science / AI)

| Abbrev | Full name | Field |
|--------|-----------|-------|
| ACL | Annual Meeting of the ACL | NLP |
| CVPR | IEEE/CVF Conference on CVPR | Vision |
| ICCV | IEEE/CVF International Conference on ICCV | Vision |
| ICML | International Conference on ML | ML |
| IJCAI | International Joint Conference on AI | AI |
| NeurIPS | Neural Information Processing Systems | ML/AI |
| AAAI | AAAI Conference on AI | AI |
| WWW | The Web Conference | Web/IR |
| SIGKDD | ACM SIGKDD | Data mining |
| SIGIR | ACM SIGIR | Information retrieval |

### CCF-B (selective, use when domain-specific)

| Abbrev | Full name | Field |
|--------|-----------|-------|
| EMNLP | Empirical Methods in NLP | NLP |
| NAACL | NAACL-HLT | NLP |
| ECCV | European Conference on CV | Vision |
| BMVC | British Machine Vision Conference | Vision |
| COLING | Intl Conference on Computational Linguistics | NLP |
| WSDM | Web Search and Data Mining | IR |
| CIKM | Conference on Information and Knowledge Management | IR |

### Conference open-access hubs
- NeurIPS: https://papers.nips.cc/
- ICML: https://proceedings.mlr.press/
- ICLR: https://openreview.net/group?id=ICLR.cc
- CVPR/ICCV: https://openaccess.thecvf.com/
- ACL Anthology: https://aclanthology.org/

---

## Supplementary Sources / 补充来源

### Industry research labs
| Lab | URL |
|-----|-----|
| Google Research | https://research.google/ |
| Meta AI (FAIR) | https://ai.meta.com/research/ |
| Microsoft Research | https://www.microsoft.com/en-us/research/ |
| OpenAI Research | https://openai.com/research |
| DeepMind | https://deepmind.google/research/ |
| Anthropic Research | https://www.anthropic.com/research |
| NVIDIA Research | https://research.nvidia.com/ |

### Domain influencers (examples — expand per user domain)
| Domain | Researcher | Notes |
|--------|------------|-------|
| CV | Kaiming He | ResNet, MoCo, MAE lineage |
| CV | Jitendra Malik | Recognition, segmentation |
| NLP | Yoshua Bengio, Yann LeCun | Foundational (cross-domain) |
| RL | Sergey Levine, Pieter Abbeel | Robotics + RL |

When user specifies a subfield, identify 2–3 active leaders and search their recent publications.

### Chinese tech research channels
- 机器之心 (Jiqi Zhixin WeChat / website)
- 量子位 (QbitAI)
- Company official WeChat accounts: 阿里达摩院, 腾讯AI Lab, 字节跳动技术, 华为诺亚方舟实验室

Use these for **fast-moving trends**; always trace back to primary paper/source.

---

## Scoring Reference / 打分参考

### Venue tier mapping (Importance sub-score)

| Tier | Examples | Base boost |
|------|----------|------------|
| Tier-1 | NeurIPS, ICML, ICLR, CVPR, ICCV, ACL, AAAI | +3 |
| Tier-2 | EMNLP, ECCV, NAACL, BMVC, WSDM | +2 |
| Tier-3 | arXiv preprint, workshop, tech report | +0–1 |
| Industry flagship | Google/Meta/OpenAI flagship releases | +2 |

### Recency default
- No user preference → prioritize last **2 years**, still include seminal older work if highly cited/referenced in top results

### Deduplication keys
1. arXiv ID
2. DOI
3. Normalized title (lowercase, strip punctuation)
4. Same PDF URL

Keep the version with highest venue status and most complete metadata.
