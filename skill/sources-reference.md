# Retrieval Sources Reference / 检索来源参考

Use this file in **Module 2** to:
1. Detect the query domain
2. Activate only the matching source packs
3. Look up venue lists and scoring rules

---

## Domain Router / 领域路由（必读）

After Module 1 query rewrite, **detect 1–2 primary domains**, then load the corresponding source packs below.

| Domain ID | Trigger keywords (CN / EN examples) | Activate packs |
|-----------|-------------------------------------|----------------|
| `ai_cs` | 大模型, LLM, CV, NLP, 强化学习, transformer, deep learning, computer vision, IR, data mining | **A** + **B** (+ **A-CN** when CN/国产/中文大模型) |
| `math_physics` | 数学, 物理, 粒子物理, nonlinear, quantitative biology | **A**(arXiv) + **C** + **E**(CERN/OSTI if energy/aero) |
| `chemistry` | 化学, 分子, CAS, 化工, chemistry, reagent | **D** + **A**(arXiv q-bio/cond-mat if needed) |
| `materials` | 材料, 纳米, materials science, NIMS | **D** + **E**(OSTI) + **A** |
| `biomed` | 医学, 生物, PubMed, clinical, genome, drug | **F** + **A**(q-bio) + **H**(SciELO/DOAJ) |
| `education` | 教育, pedagogy, curriculum, edtech | **F**(ERIC) + **H** + **I** |
| `humanities_ss` | 哲学, 历史, 政治, 社会, 法学, 新闻, 人文社科 | **I** + **H** + **J**(newspapers if media history) |
| `economics` | 经济, 金融, 管理, marketing, SWOT, econ | **I**(EconLit/SSRN-class) + **K**(EBSCO-class) |
| `engineering_energy` | 能源, 航空航天, 工程, NASA, DOE | **E** + **A** + **H** |
| `patent_ip` | 专利, patent, IP | **L** only (+ domain pack if tech context) |
| `thesis` | 学位论文, thesis, dissertation, 硕博 | **M** + domain pack |
| `general_oa` | 开放获取, OA, open access, 找不到领域 | **H** + **A** + **N** |
| `cross_domain` | 跨学科 / unclear | **A** + **H** + **N** → then refine |

### Routing rules / 路由规则

1. Always run **Pack A** for STEM queries that may have preprints (AI/CS/math/physics/bio).
2. Always keep **English search terms** for international packs, even in `/query_chinese` mode.
3. Cap active packs at **3** unless the user asks for exhaustive coverage.
4. If domain confidence is low → use `general_oa` + ask one clarifying question.
5. Do **not** activate shadow libraries / pirate ebook sites for skill retrieval.
6. **CN LLM labs (A-CN)**: if query mentions 国产/中文大模型/Qwen/DeepSeek/GLM/InternLM/混元/豆包/文心/星火 etc., activate **A-CN Tier-1 matching orgs (2–4)**; if query is a broad CN-LLM survey, also scan **A-CN Discovery**.
7. Named-model force map: see [A-CN force triggers](#a-cn-force-triggers--强制触发).

### Priority scholarly APIs (2.14 routing)

When Pack **A** / **F** is active, prefer these hubs (web UI and/or API; compose article-mcp if configured):

| Source | Use | How |
|--------|-----|-----|
| **Semantic Scholar** | AI/CS citation + metadata | https://www.semanticscholar.org/ · optional `S2_API_KEY` |
| **OpenAlex** | Broad scholarly graph / open metadata | https://openalex.org/ · polite pool |
| **Crossref** | DOI resolve → BibTeX enrich | https://api.crossref.org/ |
| **PubMed / NCBI** | Biomed (`biomed` domain → Pack F) | https://pubmed.ncbi.nlm.nih.gov/ |
| **OpenReview** | ICLR & drafts | https://openreview.net/ |
| **DBLP** | CS venue metadata | https://dblp.org/ |

Do **not** treat source count as a KPI; activate ≤3 packs unless user asks exhaustive.

---

## Pack A — AI / Computer Science Core（计算机 · AI 主库）

Default pack for Paper_Rec. Highest priority for ML/AI/CV/NLP/systems queries.

| Source | URL | Search tip |
|--------|-----|------------|
| arXiv | https://arxiv.org/search/ | Filter `cs.LG` `cs.CV` `cs.CL` `cs.AI` `cs.IR` `stat.ML` |
| Hugging Face Papers | https://huggingface.co/papers | Daily trending ML papers |
| Papers With Code | https://paperswithcode.com/ | SOTA + code links |
| GitHub | https://github.com/search | Implementations, stars, topics |
| Semantic Scholar | https://www.semanticscholar.org/ | Citation graph · API-friendly metadata |
| DBLP | https://dblp.org/ | CS bibliography / venue lookup (also https://dblp.uni-trier.de/) |
| OpenReview | https://openreview.net/ | ICLR & peer-review drafts |
| Connected Papers | https://www.connectedpapers.com/ | Graph neighborhood from a seed paper |
| AMiner | https://www.aminer.cn/ | CN-friendly scholar/paper graph (alt https://mrt.aminer.cn/) |
| Google Scholar | https://scholar.google.com/ | Broad citation search; prefer browser (anti-bot) |
| ACL Anthology | https://aclanthology.org/ | NLP proceedings |
| CVF Open Access | https://openaccess.thecvf.com/ | CVPR / ICCV / ECCV |

### CCF-A venues (AI/CS)

| Abbrev | Field |
|--------|-------|
| NeurIPS, ICML, ICLR | ML |
| CVPR, ICCV | Vision |
| ACL, AAAI, IJCAI | NLP / AI |
| WWW, SIGKDD, SIGIR | Web / DM / IR |

### CCF-B (selective)

EMNLP, NAACL, ECCV, BMVC, COLING, WSDM, CIKM

### Conference / journal hubs（开放全文）

- NeurIPS: https://papers.nips.cc/ · https://proceedings.neurips.cc/
- ICML: https://proceedings.mlr.press/
- ICLR: https://openreview.net/group?id=ICLR.cc
- JMLR: https://jmlr.csail.mit.edu/papers/ · https://www.jmlr.org/

### Venue planning meta（非正文检索；投稿/档期时启用）

| Source | URL | Use |
|--------|-----|-----|
| CCF AI 评估列表 | https://www.ccf.org.cn/Academic_Evaluation/AI/ | CCF 分区参考 |
| CCF Deadlines | https://ccfddl.github.io/ | 截稿日历 |
| AI Deadlines | https://aideadlin.es/?sub=ML,CV,NLP | ML/CV/NLP 截稿 |
| 会伴 myhuiban | https://www.myhuiban.com/?lang=zh_cn | 国内会议日历 |

---

## Pack A-CN — Chinese LLM Labs（国产大模型 · 论文发现补充）

Source catalog distilled from [awesome-LLMs-In-China](https://free-gpt.github.io/awesome-LLMs-In-China/).  
**Purpose**: catch latest CN foundation-model tech reports / arXiv / GitHub releases that global indexes may lag on.

### A-CN Discovery（发现层）

| Source | URL | When to use |
|--------|-----|-------------|
| awesome-LLMs-In-China (site) | https://free-gpt.github.io/awesome-LLMs-In-China/ | Broad 国产/中文大模型 survey; discover new teams |
| awesome-LLMs-In-China (repo) | https://github.com/wgwang/awesome-LLMs-In-China | Track updates / Issues |
| awesome-open-foundation-models | https://github.com/wgwang/awesome-open-foundation-models | Open foundation model index |
| awesome-LLM-benchmarks | https://github.com/wgwang/awesome-LLM-benchmarks | Benchmarks → reverse-find papers |
| ModelScope 魔搭 | https://www.modelscope.cn/ | CN model cards often link tech reports |
| BAAI Model Hub | https://model.baai.ac.cn/ | Aquila / FlagAI ecosystem docs |

**Default**: enable Discovery only for queries about 国产大模型 / 中文 LLM 综述 / CN foundation models — not every `ai_cs` query.

### A-CN Tier-1 Labs（默认高优先）

For matching keywords, search **GitHub org + HF org + official tech report/blog**; always prefer arXiv/PDF primary link when found.

| Team | Models / aliases | Primary channels |
|------|------------------|------------------|
| DeepSeek 深度求索 | DeepSeek, R1, Coder, V | https://github.com/deepseek-ai · https://huggingface.co/deepseek-ai |
| Alibaba Qwen / 通义 / 达摩 | Qwen, Tongyi, Qwen-VL/Audio | https://github.com/QwenLM · https://huggingface.co/Qwen · https://tongyi.aliyun.com/ |
| Zhipu / THUDM 智谱 | ChatGLM, GLM, 清言 | https://github.com/THUDM · https://huggingface.co/THUDM · https://chatglm.cn/ |
| Shanghai AI Lab 书生 | InternLM, InternVL | https://github.com/InternLM · https://intern-ai.org.cn/ |
| BAAI 智源 | Aquila, Emu, FlagAI, 悟道 | https://github.com/FlagAI-Open · https://huggingface.co/BAAI · https://model.baai.ac.cn/ |
| OpenBMB / 面壁 | CPM, MiniCPM | https://github.com/OpenBMB · https://huggingface.co/openbmb · https://modelbest.cn/ |
| 01.AI 零一万物 | Yi | https://github.com/01-ai/Yi · https://huggingface.co/01-ai |
| Moonshot 月之暗面 | Kimi, Moonshot | https://www.moonshot.cn/ · official blog / tech reports |
| Baichuan 百川 | Baichuan | https://github.com/baichuan-inc · https://huggingface.co/baichuan-inc |
| Tencent Hunyuan 混元 | Hunyuan | https://hunyuan.tencent.com/ · Tencent AI Lab releases |
| ByteDance / 豆包 / Seed | Doubao, Seed, 云雀 | https://www.doubao.com/ · ByteDance / Seed research posts |
| IDEA CCNL | 姜子牙, Fengshenbang, Ziya | https://fengshenbang-lm.com/ · https://huggingface.co/IDEA-CCNL |

### A-CN Tier-2 Labs（按需）

| Team | Models | Channels | Activate when |
|------|--------|----------|---------------|
| iFlytek 讯飞 | 星火 Spark | https://xinghuo.xfyun.cn/ | 星火 / 讯飞 / speech+LLM |
| Huawei Noah / 盘古 / 鹏城 | PanGu | https://www.huaweicloud.com/product/pangu.html · openi.pcl.ac.cn | 盘古 / 华为 / 工业大模型 |
| SenseTime 商汤 | 商量, SenseNova | https://chat.sensetime.com/ · SenseTime research | 商汤 / 多模态工业 |
| Baidu ERNIE 文心 | 文心一言, ERNIE | https://yiyan.baidu.com/ · Baidu Research | 文心 / ERNIE / 百度 |
| Fudan OpenLMLab / DISC | MOSS, FinLLM | https://github.com/OpenLMLab | MOSS / 复旦 LLM |
| HKUST LMFlow | Robin, LMFlow | GitHub LMFlow / related papers | LMFlow / 训练框架 |
| XVERSE 元象 | XVERSE | https://github.com/xverse-ai | XVERSE |
| Kunlun Skywork 天工 | Skywork | HF/GitHub Skywork | Skywork / 天工 |
| vivo BlueLM | BlueLM | HF/GitHub BlueLM | BlueLM |
| Inspur 源 | 源 2.0 | Inspur open releases | 浪潮 / 源大模型 |

### A-CN Academic labs（子领域）

| Lab | Focus | Note |
|-----|-------|------|
| THUDM (Tsinghua) | GLM lineage | Overlaps Zhipu; use arXiv + GitHub |
| PKU groups | ChatLaw, CodeShell, Chat-UniVi | law / code / multimodal |
| ZJU NLP / OpenKG | KnowLM, 智海系列 | knowledge / legal / edu |
| SJTU BAI / AI Institute | 白玉兰, K2, GeoLLaMA | science LLM |
| HIT | 本草, 活字 | medical / Chinese LLM |
| CASIA | 紫东·太初 | full-modality |
| HUST / SYSU | Monkey, Firefly | multimodal SFT series |

Vertical medical/legal/finance LLMs: prefer parent domain packs (`biomed` / `humanities_ss` / `economics`) **plus** the named lab channel above.

### A-CN force triggers / 强制触发

| Query contains | Force-open channels |
|----------------|---------------------|
| DeepSeek, R1, deepseek | DeepSeek GitHub/HF + arXiv |
| Qwen, 通义, Tongyi | QwenLM + HF Qwen (**prefer Qwen3.7 > 3.6 > 3.5 > 3 > 2.5**; include official blog/docs if no TR yet) |
| GLM, ChatGLM, 智谱, 清言 | THUDM + Zhipu |
| InternLM, 书生, InternVL | InternLM / Shanghai AI Lab |
| Aquila, 悟道, BAAI, FlagAI | BAAI hub + FlagAI |
| MiniCPM, CPM, 面壁, OpenBMB | OpenBMB |
| Yi- , 零一 | 01-ai/Yi |
| Kimi, Moonshot, 月之暗面 | Moonshot official |
| Baichuan, 百川 | baichuan-inc |
| 混元, Hunyuan | Tencent Hunyuan |
| 豆包, Seed, 云雀 | ByteDance / Doubao |
| 姜子牙, Fengshenbang, Ziya | IDEA-CCNL |
| 国产大模型, 中文大模型综述 | A-CN Discovery + Tier-1 sample (4+) |

**Rules**: pick **2–4** Tier-1 orgs max per query (unless survey); always verify blog claims with arXiv/PDF; GitHub search may 429 — fall back to org page + HF model card + web search `site:github.com/org`.

---

## Pack B — AI Industry & Trend（产业 · 趋势补充）

Use when Pack A hits <30 or user wants latest industrial work.

### Global labs

| Source | URL |
|--------|-----|
| Google Research | https://research.google/ |
| Meta AI | https://ai.meta.com/research/ |
| Microsoft Research | https://www.microsoft.com/en-us/research/ |
| OpenAI Research | https://openai.com/research |
| DeepMind | https://deepmind.google/research/ |
| Anthropic | https://www.anthropic.com/research |
| NVIDIA Research | https://research.nvidia.com/ |

### CN industry portals（与 A-CN 互补；偏产品/发布，论文需回链）

| Source | URL |
|--------|-----|
| 阿里达摩院 / 通义 | https://tongyi.aliyun.com/ · DAMO research posts |
| 腾讯 AI Lab / 混元 | https://hunyuan.tencent.com/ |
| 字节跳动 / 豆包 | https://www.doubao.com/ |
| 华为诺亚 / 盘古 | https://www.huaweicloud.com/product/pangu.html |
| 百度文心 | https://yiyan.baidu.com/ |
| 讯飞星火 | https://xinghuo.xfyun.cn/ |
| 商汤 | https://www.sensetime.com/ |

**CN media** (trend only → always verify with primary paper): 机器之心 · 量子位 · 阿里达摩院 · 腾讯AI Lab · 字节跳动技术 · 华为诺亚方舟

**Influencer examples**: CV → Kaiming He; RL → Levine / Abbeel; expand 2–3 leaders per subfield.

---

## Pack C — Math / Physics / Preprint STEM（数理 · 预印本）

| Source | URL | Focus |
|--------|-----|-------|
| arXiv | https://arxiv.org/ | `math.*` `physics.*` `hep-*` `nlin.*` `q-bio.*` |
| CERN Document Server | https://cds.cern.ch/ | Particle physics (browser may work if API/script 403) |
| Science.gov | https://www.science.gov/ | US federal STEM aggregation |

---

## Pack D — Chemistry / Materials（化学 · 材料）

| Source | URL | Focus | Notes |
|--------|-----|-------|-------|
| ChemBlink | https://www.chemblink.com/ | Chemical product / CAS lookup | **Not a paper DB** — use for substance metadata |
| Chemistry Central / Springer Chem | https://www.chemistrycentral.com/ | Chem OA (may redirect Springer) | Prefer DOAJ + publisher OA |
| SciELO | https://www.scielo.org/ | Regional OA journals | Good for LatAm chem/life sci |
| DOAJ | https://doaj.org/ | OA journal/article search | Filter Chemistry / Materials |
| OSTI | https://www.osti.gov/ | DOE reports, materials, energy | Full-text tech reports |
| NIMS (JP) | https://www.nims.go.jp/eng/ | Materials research | Site may timeout; retry or use Google site: |

**Do not** treat ChemBlink as a literature engine; pair it with DOAJ/OSTI/SciELO for papers.

---

## Pack E — Engineering / Energy / Aerospace（工程 · 能源 · 航天）

| Source | URL | Focus |
|--------|-----|-------|
| NASA NTRS | https://ntrs.nasa.gov/ | Aerospace reports & conference papers |
| OSTI / DOE | https://www.osti.gov/ | Energy, materials, engineering reports |
| Science.gov | https://www.science.gov/ | Multi-agency STEM |
| NSTL | https://www.nstl.gov.cn/ | CN sci-tech literature hub |

---

## Pack F — Biomed / Life Sciences / Education（生医 · 教育）

| Source | URL | Focus | Access |
|--------|-----|-------|--------|
| ERIC | https://eric.ed.gov/ | Education literature | Free abstracts; some full text |
| Local PubMed portal | https://www.yuntsg.com/ | PubMed-style biomedical search | Registration / trial |
| SciELO | https://www.scielo.org/ | Life/health OA | Free |
| DOAJ | https://doaj.org/ | OA medical journals | Free |
| Bioline | https://www.bioline.org.br/ | Developing-country OA journals | Free |
| HighWire (Stanford) | https://highwire.stanford.edu/ | Biomed publisher portal | Often unstable / 502 |

Prefer ERIC for education; prefer PubMed-class + DOAJ/SciELO for biomed.

---

## Pack G — reserved (AI labs already in Pack B)

*(Merged into Pack B — kept ID for router compatibility.)*

---

## Pack H — Open Access Aggregators（开放获取聚合）

Activate for any domain when needing free full text or OA coverage.

| Source | URL | Strength |
|--------|-----|----------|
| DOAJ | https://doaj.org/ | Quality-controlled OA journals |
| OALib | https://www.oalib.com/ | Broad OA article search (CN-friendly) |
| Socolar | https://www.socolar.com/ | OA discovery + full-text links |
| SciELO | https://www.scielo.org/ | Regional OA |
| Open J-Gate | http://www.openj-gate.com/ | OA journal portal (quality uneven) |
| Cambridge Repository | https://www.repository.cam.ac.uk/ | Institutional OA |
| NAP | https://www.nationalacademies.org/publications/all | Free academy reports/books |

---

## Pack I — Humanities / Social Sciences（人文社科）

| Source | URL | Focus | Access |
|--------|-----|-------|--------|
| NCPSSD | https://www.ncpssd.org/ | 国家哲学社会科学文献中心 | Free / open portal |
| CSSCI | http://cssci.nju.edu.cn/ | Chinese social sciences citation | Limited / institution |
| CSSN | https://www.cssn.cn/ | 中国社会科学网（动态/资讯） | Free (not a paper DB) |
| CNKI | https://www.cnki.net/ | 中文期刊/硕博/会议 | Paywall / campus |
| Wanfang | https://www.wanfangdata.com.cn/ | 中文综合学术库 | Paywall / campus |
| RDFYBK | http://www.rdfybk.com/ | 人大复印报刊资料 | Subscription |
| Xinhua Wenzhai DB | https://www.xinhuawz.com/ | 新华文摘 | Subscription |
| NTU E-Journal | https://ejournal.press.ntu.edu.tw/ | 台大学术期刊 | Open / campus |
| JSTOR | https://www.jstor.org/ | Humanities & social sciences | Subscription |
| SSRN-class | https://www.ssrn.com/ | Working papers (econ/law/ss) | Often 403 via script; browser OK |

---

## Pack J — Media / Newspaper Archives（报刊史料）

Only when query is about journalism history, media studies, or primary news sources — **not** for method papers.

| Source | URL |
|--------|-----|
| 人民日报图文库 | https://data.people.com.cn/rmrb/ |
| 光明日报库 | http://epaper.gmw.cn/gmrbdb/ |
| 大公报(1902–1949) | https://tk.cepiec.com.cn/tknewsc/tknewskm |
| 中国近代报刊库 | https://tk.cepiec.com.cn/SP/ |

---

## Pack K — Business / Economics Databases（经管）

| Source | URL | Notes |
|--------|-----|-------|
| EconLit (AEA) | https://www.aeaweb.org/econlit/ | Index; full search usually via campus |
| EBSCO | https://www.ebscohost.com/ | Marketing page; real search needs institution |
| ScholarVox | https://www.scholarvox.com/ | Business ebooks; institution |
| SSRN | https://www.ssrn.com/ | Preprints in econ/finance/law |

---

## Pack L — Patents（专利）

| Source | URL |
|--------|-----|
| SooPAT | https://www.soopat.com/Home/Index |

Use alone or alongside `ai_cs` / `engineering_energy` when the query is IP-focused.

---

## Pack M — Theses / Dissertations（学位论文）

| Source | URL | Region |
|--------|-----|--------|
| theses.fr | https://theses.fr/ | France |
| DART-Europe | https://www.dart-europe.org/basic-search.php | EU theses portal (may block bots; browser OK) |
| CALIS OPAC | https://opac2.calis.edu.cn/ | CN union catalog |
| UCDR S / 全国图书馆参考咨询联盟 | http://www.ucdrs.superlib.net/ | Document delivery |
| UMI / ProQuest-class | https://wwwlib.umi.com/ | Intl theses (access limited) |
| CNKI / Wanfang degree DBs | cnki / wanfang | CN theses (paywall) |

---

## Pack N — CN National Sci-Tech & Libraries（国内科技文献枢纽）

| Source | URL | Role |
|--------|-----|------|
| NSTL | https://www.nstl.gov.cn/ | National sci-tech literature |
| CALIS | https://opac2.calis.edu.cn/ | Higher-ed union catalog |
| Tsinghua Library portal | https://lib.tsinghua.edu.cn/ | Gateway (not a paper DB itself) |
| paper.edu.cn | https://www.paper.edu.cn/ | CN sci-tech paper online |
| Nature (journal hub) | https://www.nature.com/ | Flagship STM; mostly paywalled |

---

## Explicitly Excluded / 明确排除（不要作为 skill 检索源）

| Category | Examples | Reason |
|----------|----------|--------|
| Shadow libraries | Library Genesis, Z-Library, BookSC/BookZZ, **Sci-Hub** (`sci-hub.*`) | Copyright risk; unstable |
| Scholar / PDF mirrors | `scholar.scqylaw.com`, `gfsoso.99lb.net`, `ac.scmor.com` | Unofficial; often broken / piracy-adjacent |
| Predatory OA catalogs | SCIRP journal listing as sole source | Quality uneven |
| Writing-only hubs | home-for-researchers as sole “search” | Not a paper corpus |
| Doc pirate / 文库破解 | hi138, ebuymed, bingdian-style | Not scholarly; unreliable |
| Search bookmark hubs | 虫部落 chongbuluo | Meta-directory, not a corpus |
| Broken / archive-only | CiteSeerX live index, many 404 portals | Not searchable anymore |
| Product-only chem shops | ChemBlink as sole source | Metadata ≠ papers |

> Pack A supplements (Connected Papers / AMiner / Scholar / JMLR / deadline hubs) curated from [Awesome-Resources/Research](https://github.com/QinHsiu/Awesome-Resources/blob/main/Research/README.md) after a 2026-07 reachability probe; pirate & mirror sites excluded.

---

## Domain → Pack Quick Map / 速查表

```
ai_cs              → A, B  (+ A-CN if CN LLM keywords)
math_physics       → A, C
chemistry          → D, H
materials          → D, E, H
biomed             → F, H, A(q-bio)
education          → F(ERIC), H, I
humanities_ss      → I, H
economics          → K, I, H
engineering_energy → E, N, H
patent_ip          → L (+ parent domain pack)
thesis             → M (+ parent domain pack)
general_oa         → H, A, N
cross_domain       → A, H, N
cn_llm_survey      → A, A-CN(Discovery+Tier-1), B
```

---

## Scoring Reference / 打分参考

### Venue tier (Importance)

| Tier | Examples | Boost |
|------|----------|-------|
| Tier-1 (AI/CS) | NeurIPS, ICML, ICLR, CVPR, ICCV, ACL, AAAI | +3 |
| Tier-1 (field) | Field-top journals/conferences for non-CS domains | +3 |
| Tier-2 | EMNLP, ECCV, NAACL, strong OA journals | +2 |
| Tier-3 | arXiv preprint, workshop, tech report | +0–1 |
| Industry flagship | Google / Meta / OpenAI flagship | +2 |
| National hub hit | NSTL / NCPSSD / ERIC verified record | +1 |

### Recency default

- Default: prefer last **12 months** for ranking; last **24 months** still eligible.
- If query has **最新 / latest / recent**: apply **latest-intent hard rules** in \SKILL.md\ §2.3 — newer same-family versions must outrank older citation magnets.
- Model-family order example (Qwen): .7 > 3.6 > 3.5 > 3 > 2.5 > 2\. Product release notes count when no arXiv TR exists.
- Keep seminal older works only as labeled baselines, not as「最新」answers.

### Deduplication keys
1. arXiv ID  
2. DOI  
3. Normalized title  
4. Same PDF URL  
5. Same model family + version (keep newest)

When latest-intent is on, keep the **newest version** even if an older duplicate has a richer venue.

---

## Module-2 checklist (domain-aware)

```
- [ ] Detect Domain ID(s) from rewritten query
- [ ] If CN LLM keywords → announce A-CN labs (2–4) or Discovery
- [ ] Announce: Domain = {id} → Packs = {list}
- [ ] Search Pack sources with Specific + Keyword queries
- [ ] Add English terms for international packs
- [ ] Score & keep Top 50
- [ ] Prefer Pack A/H/A-CN primary (arXiv/PDF) over media blogs
```
