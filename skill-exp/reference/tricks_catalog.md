# Internal tricks catalog (symptom → verifiable actions)

Self-contained inside `skill-exp`. Used **after** analysis names a symptom.
Pick **2–3** actions per priority symptom → `plans/P*.md` with `source:`.

Curated from public training-trick digests (bundled here; **no external path at runtime**).
Do **not** invent metrics; each action has a mini-verify probe.

| Symptom id | Typical signals |
|------------|-----------------|
| `data_first` | new task; unknown distribution; pipeline unproven |
| `overfitting` | train ≫ val; val drops late |
| `long_tail` | rare classes dominate errors; imbalance |
| `hard_subset` | one style/domain cluster high error |
| `underfit` | train & val both low |
| `label_noise` | disagreeing labels; high loss on easy samples |
| `train_unstable` | NaN / spikes / dead ReLU |
| `oom` | CUDA OOM |
| `eval_boost` | train ok; need test-time gain (optional) |

**Banned**: labeling the test set for training; blind trick-stacking without baseline.

---

## `data_first`

1. **data_clean · inspect** — visualize labels + class/size distribution.  
   Mini-verify: dist table + N-sample audit clean.  
   Source: `tricks:data_first#know_data`
2. **train_recipe · overfit_tiny** — tiny subset, fixed seed, no random aug.  
   Mini-verify: train error → ~0 (pipeline learnable).  
   Source: `tricks:data_first#overfit_tiny`
3. **data_clean · unit_test_loader** — batch=1, single-process numeric check.  
   Mini-verify: matches hand / reference values.  
   Source: `tricks:data_first#test_loader`

## `overfitting`

1. **train_recipe · regularize** — dropout / weight-decay / early-stop on val.  
   Mini-verify: train–val gap shrinks; best val ↑ or holds.  
   Source: `tricks:overfitting#reg`
2. **data_clean · increase** — Flip/Cutout/Mixup (vision) or synonym/back-translation (text), style-aware.  
   Mini-verify: probe ↑; global drop ≤ ε.  
   Source: `tricks:overfitting#aug`
3. **train_recipe · swa** — stochastic weight averaging near end.  
   Mini-verify: val more stable or ↑ at same budget.  
   Source: `tricks:overfitting#swa`

## `long_tail`

1. **data_clean · increase** — oversample / hard-neg mine rare buckets.  
   Mini-verify: rare recall ↑; head Δ ≤ ε.  
   Source: `tricks:long_tail#resample`
2. **train_recipe · loss** — focal / weighted CE / class-balanced.  
   Mini-verify: macro or rare-class F1 ↑.  
   Source: `tricks:long_tail#loss`
3. **train_recipe · multi_loss** — weighted mix (e.g. focal+Dice); watch scale balance.  
   Mini-verify: components descend without one dominating; probe ↑.  
   Source: `tricks:long_tail#multi_loss`

## `hard_subset`

1. **data_clean · increase** — add/synthesize samples for failing subset.  
   Mini-verify: subset ↑; global not ↓ > ε.  
   Source: `tricks:hard_subset#focus_data`
2. **train_recipe · diff_lr** — smaller LR on backbone, larger on head; freeze early layers if data-small.  
   Mini-verify: stabler converge; subset ↑.  
   Source: `tricks:hard_subset#diff_lr`
3. **train_recipe · domain_pt** — domain MLM / similarity continued pretrain (NLP) then finetune.  
   Mini-verify: subset probe ↑.  
   Source: `tricks:hard_subset#domain_pt`

## `underfit`

1. **train_recipe · capacity_first** — prove tiny-set overfit before chasing depth.  
   Mini-verify: see `data_first#overfit_tiny`.  
   Source: `tricks:underfit#capacity_first`
2. **train_recipe · lr_sched** — warmup; val plateau ×0.5 or cosine; scale LR with batch.  
   Mini-verify: train loss ↓ and val ↑.  
   Source: `tricks:underfit#lr_sched`
3. **train_recipe · pretrain** — load pretrained; avoid tiny final LR (often floor ~1e-5).  
   Mini-verify: beats from-scratch on probe.  
   Source: `tricks:underfit#pretrain`

## `label_noise`

1. **data_clean · remove** — drop high-entropy / low-agreement samples.  
   Mini-verify: cleaner subset ≥ noisy full on probe.  
   Source: `tricks:label_noise#noise_drop`
2. **label_clean · consensus** — multi-model CV; change label only if agree & conf≥τ.  
   Mini-verify: flip log; probe ↑.  
   Source: `tricks:label_noise#relabel_cv`
3. **train_recipe · label_smooth** — if residual noise remains.  
   Mini-verify: calibration/gen improves without mushy labels.  
   Source: `tricks:label_noise#label_smooth`

## `train_unstable`

1. **train_recipe · seed_repro** — fix seed; disable random aug while debugging.  
   Mini-verify: two short runs ≈ same loss.  
   Source: `tricks:train_unstable#seed`
2. **train_recipe · bn_nan** — BN update on in train; locate NaN (forward vs backward).  
   Mini-verify: train↓ and eval not “fake converged”.  
   Source: `tricks:train_unstable#bn_nan`
3. **train_recipe · dead_relu** — LeakyReLU/ELU; clean outliers before relying on grad clip.  
   Mini-verify: train error moves again; no explode.  
   Source: `tricks:train_unstable#dead_relu`

## `oom`

1. **train_recipe · fp16_accum** — amp fp16; grad accumulation; DDP no_sync when accumulating.  
   Mini-verify: 1 epoch completes; metric ≈ fp32.  
   Source: `tricks:oom#fp16`
2. **data_clean · modify** — shorter max length / smaller image side.  
   Mini-verify: fits GPU; metric Δ logged.  
   Source: `tricks:oom#resize`

## `eval_boost` (optional; after train plan)

1. **eval_recipe · tta** — multi-view test-time aug fusion.  
   Mini-verify: same ckpt metric ↑; latency logged.  
   Source: `tricks:eval_boost#tta`
2. **eval_recipe · ensemble** — fuse few models if latency allows.  
   Mini-verify: ensemble > best single; cost logged.  
   Source: `tricks:eval_boost#ensemble`

---

## Agent rules

1. **Analyze first** — clusters / curves / label stats → symptom(s).
2. Take **2–3** actions → `content/exp/<id>/plans/P*.md` with `source:`.
3. Prefer `data_clean` / `label_clean` before `train_recipe`; `eval_boost` last.
4. Rank via PTV; mini-verify before full `/exp_training`.
