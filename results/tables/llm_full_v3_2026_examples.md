# 20 random reviews of run `full_v3_2026` (seed 0)

Review text is public content from OpenReview. `[ignored]` units are in no critique.

## Example 1 — review `f6qmTFyRyh` (ICLR 2026)

28 units, 10 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 1.  The idea of converting multi-agent trajectories into a natural language dialogue is elegant and powerful. It effectively tackles the representation mismatch problem by leveraging the LLM's inherent ability to handle diverse inputs through tokenization. The dialogue format naturally encapsulates the CTDE paradigm, preserving inter-agent context during training while allowing for decentralized execution.

**Critique 2** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. The paper does an excellent job of identifying and systematically addressing three critical bottlenecks in multi-task offline MARL. Representation Mismatch is  solved via verbalization of observations and actions; CTDE Incompatibility is Solved via the dialogue-style trajectory representation. Reward Scarcity & Credit Assignment is Solved by fine-tuning a pre-trained LLM (which can perform implicit credit assignment via temporal attention) and entirely discarding reward signals during SFT. This is a bold and effective design choice.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> 3.  The experimental section is thorough and convincing. DLM's performance is rigorously evaluated against a wide range of strong baselines (both value-based and imitation-based) across the full spectrum of SMAC difficulty levels. 4.  A notable advantage of DLM is its lower total computational cost compared to task-specific value-based methods, despite its two-stage training. This scalability is a significant practical benefit.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1.  While the paper argues that the pre-trained LLM provides a strong prior for decision-making, the experiments do not fully isolate its contribution. An ablation study comparing DLM initialized with a pre-trained LLM versus a randomly initialized Transformer of the same size would help quantify the value of the linguistic prior versus the architectural benefits of the Transformer itself.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 2.  The current work uses the relatively small LLaMA-3.2-1B model. It is unclear how the approach would scale to larger LLMs in terms of performance and computational requirements. Furthermore, while SMAC is a standard benchmark, the actions and observations are still within a constrained, grid-like world. Testing on environments with richer, more natural language-based dynamics (e.g., text-based games or more complex simulators) would further validate the "language model for decision" premise.

**Critique 6** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 3. The handcrafted executability reward for GRPO, while simple and effective, is quite sparse. It primarily penalizes invalid actions but does not actively guide the policy toward optimal behavior. The performance gains likely stem from avoiding catastrophic failures. Exploring denser, task-oriented heuristic rewards (even if still lightweight) could potentially lead to further performance improvements.

**Critique 7** — aspect `reproducibility`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 4.  For reproducibility, it is crucial that the constructed ChatSMAC dataset—the dialogue-formatted version of the offline data—is made publicly available. The paper should explicitly state its availability.

**Critique 8** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 1.  How does the model's performance and training stability change if the dialogue history is truncated more aggressively? Is there a point where reducing context length significantly harms performance, particularly in long-horizon tasks?

**Critique 9** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 2.  The GRPO stage uses a KL penalty w.r.t. the SFT model as a reference. Did you experiment with using the original pre-trained LLM as the reference model instead, and if so, what were the results?

**Critique 10** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 3.  Have you observed any failure modes or specific task types where the dialogue formulation or the LLM-based approach consistently underperforms compared to traditional value-based MARL methods?

## Example 2 — review `rNTnWI1T60` (ICLR 2026)

10 units, 7 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 1. Conceptual novelty: The paper reframes multi-step LLM workflows as typed latent-variable models, bridging probabilistic programming with LLM adaptation.

**Critique 2** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. Principled optimization: The proposed TACSTaR algorithm generalizes STaR under type constraints and offers theoretical guarantees for unbiased learning as compliance improves.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> 3. Strong empirical validation: Experiments demonstrate consistent and large gains across reasoning, structured generation, and classification tasks.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. Incomplete ablation of theoretical components: The contributions of type compliance, unnormalized optimization, and amortized inference are intertwined. A controlled study isolating each factor’s impact (e.g., removing Theorem-justified bias correction) would strengthen causal attribution.

**Critique 5** — aspect `reproducibility`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2. Accessibility and implementation clarity: Although the system is well-explained, the probabilistic program abstraction may be difficult for non-probabilistic ML practitioners to reproduce. Public release of code or example workflows would greatly improve reproducibility.

**Critique 6** — aspect `soundness`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 1. The proposed framework relies heavily on the assumption that type compliance can be accurately estimated during training. How sensitive is the method to imperfect or noisy type parsers in practice?

**Critique 7** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> 2. Figure 1 is difficult to interpret and could be organized more clearly.

## Example 3 — review `0eYfGSnVxa` (ICLR 2026)

10 units, 6 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. This paper is well organized and flows naturally; the need for addressing batch effects is clearly motivated.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 2. Combining batch-aware local affinities with adaptive sampling and low rank approximation is a scalable and well-reasoned solution.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> The authors provide proofs for coverage guarantees and approximation error bounds of the sparse affinity matrix. 3. Evaluations span multiple real-world Cell Painting datasets and synthetic scalability tests; BALANS achieves consistently strong performance and outperforms baselines in runtime. Runtime scales near-linearly with sample size and demonstrates significant speedup over existing methods.

**Critique 4** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> 1. Core ideas like adaptive kernels and landmark-based sampling are not entirely new for biological data or affinity matrix computation. Prior work using adaptive bandwidths and landmark-based scalable affinity construction, such as PHATE (by Kevin Moon et al.), is not cited.

**Critique 5** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> 2. Figure 4 is presented but lacks sufficient interpretation or biological insight; more discussion of qualitative improvements would strengthen the narrative.

**Critique 6** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 3. While quantitative metrics are discussed, more analysis on why BALANS performs better in certain settings (or fails in others) would be valuable.

`[ignored]` This paper addresses an important and practical problem, batch correction, with a method that is theoretically grounded and empirically strong, but lacks originality in some components and could better discuss qualitative/quantitative insights.

## Example 4 — review `DH6e2NG3m0` (ICLR 2026)

13 units, 8 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> Generally clear and readable; figures and tables are informative.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. lack of experiments on large-scale datasets (e.g., ImageNet-1k) and transformer-based backbones (e.g. ViT)

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 2. comprasion is not comprehensive. this paper only compares with 1 baselines proposed from 2024

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 3. Theorem 1 assumes that $\ell$ satisfies the triangle inequality. For standard losses (including any metric), this inequality is not guaranteed. With $\ell$ as cross-entropy, it’s even worse (no triangle inequality at all). what loss is used as $\ell$ in this paper?

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 4. Eqs. (A.22, A.23) assume that there exists a hypothesis perfectly handling unknowns, which seems to be strong and should be justified. Even the assumption can (unreasonably) hold in practice, Eq. (6) in Theorem 1 addinitionally assumes that the same $h$  (or at least some common $h$) simultaneously achieves the minima for both $P$ and $Q$, which is not clearly stated and justified in this paper.

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 5. the claim in Lines 671-672 is heuristic and depends on the unknown $h$, which is not reasonable in practice.

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 6. lack of ablation study on hyperparameters

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> 7. Compared with full density estimation in Fang et al.(2021) that is thorectically justified, the use of uniform distribution is a simplified version in practice. The authors should give thorectical guarantees for the effectiveness of this operation.

`[ignored]` see Weaknesses.

## Example 5 — review `TdCqMVvZZX` (ICLR 2026)

6 units, 4 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The manuscript provides a comprehensive theoretical analysis and numerical results, which are convincing.

**Critique 2** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The proposed method is a natural application of Bayesian optimization with Gaussian process to VQE gradient estimation, which offers limited novelty.

**Critique 3** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The motivation of employing the Bayesian PSR is not clearly clarified. It would be more convincing to discuss the challenges the proposed method tries to address.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The manuscript lacks a formal statement or theorem guaranteeing the existence of an optimal sequence for both the shift parameter and shot allocation that ensures the fastest convergence.

`[ignored]` Please see the Weakness section

## Example 6 — review `sxn8Frc4Fl` (ICLR 2026)

21 units, 11 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - Evaluation methodology is thoroughly reported and appears to follow best practices (e.g. multi-seed evaluation on high-variance benchmarks, ablation across prompt variants) which increases confidence in the robustness of the results.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - Evaluation on both in-distribution and out-of-distribution benchmarks is good.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - The authors include a thorough analysis of learning dynamics.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - Multiple ablations are presented, including on entropy weighting factors and training on different Qwen-based model variants

**Critique 5** — aspect `clarity`, severity `minor`, polarity `positive`, target `figure_table`, actionable `False`

> - Figures and Tables are well made

**Critique 6** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Motivation is clear

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The method is only tested on the Qwen model family.

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The claims in section 3.1 seem to lack quantitative validation. (It is the result of one training run per category on Qwen2.5-Math-7B)

**Critique 9** — aspect `soundness`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> - **Q1:** Training stability - (a) Reinforcement learning on smaller models (1.5B/7B) is often brittle and sensitive to hyperparameters. Could the authors comment on the training stability of SRFT compared to standard RL (e.g., GRPO)? - (b) Introducing additional loss components can sometimes destabilize optimization. How does SRFT’s stability compare to pure SFT training in practice?

**Critique 10** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> - **Q2:** It is mentioned that math-verify is used for dataset filtering. Is it also used for the answer matching in the evaluation? If not, could the authors clarify which evaluation framework or procedure is used?

**Critique 11** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> - **Q3:** Generalization across models - (a) Does SRFT also improve performance when starting from an RL tuned model (like Qwen2.5-Math-7B-Instruct)? - (b) Were other model architectures tested (e.g. Gemma, LLaMa) to asses the whether SRFT benefits generalize beyond the Qwen family? - **Q4:** How does the computational cost of SRFT compare to the standard SFT->RL pipeline?

## Example 7 — review `h9tHZg6ETP` (ICLR 2026)

48 units, 8 critiques, 9 ignored, 1 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper asks a fundamental question in the field of self-supervised NVS.

**Critique 2** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> The proposed "transferability" is a powerful and original reframing of the problem.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper is well-written and well-motivated.

**Critique 4** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> The design of the proposed solutions is elegant and principled, with its effectiveness validated by extensive experiments.

**Critique 5** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> Through the lens of transferability, the paper provides valuable insights to the community of self-supervised NVS.

**Critique 6** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> The Challenge of Evaluating a True NVS Model My main concern is how to fairly and comprehensively evaluate NVS performance under the new, important definition of "true NVS model". While I agree that standard autoencoding metrics like those in Table 4 are biased, I am not convinced that the proposed True Pose Similarity (TPS) metric (Eq. 9), used in Tables 1-3, provides a complete picture. My reasons are as follows: Assessing Perceptual Quality in the Transfer Setting:** The TPS metric evaluates the *geometric consistency* of a transferred camera trajectory but does not directly measure the *perceptual quality* of the synthesized images. The paper itself compellingly argues that autoencoding reconstruction (seq-to-seq rendering on the same scene) is "not equivalent to true NVS" (lines 641-642) and is merely a measure of interpolation ability. This creates a critical gap in the evaluation: we can see from the TPS scores in Table 1 & 2 that XFactor is geometrically consistent, but we have no quantitative perceptual measure of the actual view synthesis quality, which should be a key point for NVS methods. This leaves the assessment of the model's core capability incomplete. Fragility of the Oracle-based Metric:** The TPS metric's reliance on a post-hoc oracle (VGGT) makes it potentially fragile. As the paper notes (lines 199-202), the metric could be "hacked". More practically, it can fail in challenging extrapolation scenarios. For example, consider transferring a forward-motion trajectory from a driving scene (A) to a scene featuring an ego-centric rotation of an object (B). A model might produce meaningless, blurry artifacts for $\text{Render}(\mathcal{S}^B, \mathcal{Z}_T^A)$, as it is a difficult extrapolation synthesis task (line 474-477). In such a case, an oracle like VGGT would likely fail to extract any meaningful pose from these artifacts, leading to a poor TPS score. This low score, however, would be an artifact of the evaluation tool's failure, not necessarily a failure of the model's transferability logic. Inherent Noise in Oracle Tools:** It is well-documented that structure-from-motion oracles like COLMAP, and the feed-forward methods like VGGT, are not perfectly reliable and can produce noisy or incorrect poses. This issue has been analyzed in prior work such as RayZer [1] (arxiv version, Figure 4) and Less3Depend [2] (arxiv version, Appendix F). This unreliability introduces noise into the evaluation, making it difficult to disentangle the model's errors from the oracle's errors. Given these points, I wonder if a well-defined perceptual measurement, independent of TPS, is necessary to complete the evaluation. For example, leveraging the **Pose-Preserving Augmentation** framework (Eq. 11) at **test time**. By applying two different augmentations to the same source sequence, the model could render a target frame from the second augmented sequence using the pose from the first. The resulting image could then be directly compared to the ground-truth target using standard perceptual metrics (PSNR, LPIPS, etc.). This would provide a direct, quantitative measure of rendering quality under the context of true transferability, which might complement the TPS metric. I believe a discussion of these evaluation limitations in the main paper or appendix would be highly beneficial. On this point, I am open to hearing the authors' clarification and am highly willing to raise my rating if this concern is addressed.

**Critique 7** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> Potentially Related Work The paper astutely identifies the ill-posed nature of the autoencoding objective for NVS. This issue has also been noted by [3], which also addresses this problem, but proposes an alternative solution that involves leveraging explicit 3D representations for fine-tuning. Including a discussion that contrasts XFactor's geometry-free, transferability-based approach with this alternative 3D-aware solution would further strengthen the paper's contribution and contextualize it within the latest research landscape.

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. The reported performance of the RayZer baseline in Table 4 appears to be a significant degradation when compared to the results presented in the original RayZer paper (Figure 1). I recognize and appreciate that the authors had to re-implement this baseline due to the lack of public code, and commend them for seeking confirmation from the original authors that their implementation is "faithful" (lines 312-314). However, the substantial performance gap is confusing. Are there key differences in the training dataset, evaluation protocol, or hyperparameter settings compared to those used in the original RayZer publication?

`[ignored]` I appreciate the paper's main idea and find its core contribution to be insightful and significant. ⏐ ### 1. ⏐ **1.1. ⏐ **1.2. ⏐ **1.3. ⏐ ### 2. ⏐ [1] RayZer: A Self-supervised Large View Synthesis Model (ICCV'25) ⏐ [2] The Less You Depend, The More You Learn: Synthesizing Novel Views from Sparse, Unposed Images without Any 3D Knowledge (arxiv) ⏐ [3] Recollection from Pensieve: Novel View Synthesis via Learning from Uncalibrated Videos (arxiv)

`[post-rebuttal, set aside]` While the work is very strong, I have some concerns, primarily regarding the evaluation methodology for what the paper defines as a "true NVS model".

## Example 8 — review `6z8JQDlafB` (ICLR 2026)

24 units, 11 critiques, 0 ignored, 2 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 1. To the best of my knowledge I have not come across a similar dataset so I strongly believe in the novelity of the dataset and its scale, assembling 31,877 curated, cross-cultural dream interpretation pairs is a useful resource that fills a gap outside Western-centric datasets.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 2. The paper quantitatively measures overlap/uniqueness (e.g., 595 symbols shared by all three cultures <18%) and provides category analyses, which is interesting.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 3. The bilingual (English/Arabic) component is a plus, especially since many such resources remain English-centric.

**Critique 4** — aspect `reproducibility`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. One main concern I had was large parts of the Arabic and Chinese data come from classical/online dream dictionaries (Ibn Sirin, Zhougong, etc.) and scraped webpages; it’s not clear whether authors obtained permission or whether any licensing / copyright issues apply. The paper should state the licenses and whether data release is allowed. 4. Can you clarify the licensing status of all the Arabic and Chinese sources? From my own checks, I could not locate clear open licenses for several of the sources cited in the paper.

**Critique 5** — aspect `reproducibility`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 2. The paper repeatedly mentions evaluation of 17 LLMs, but on inspecting the listed models the count appears to be different (commercial models + open source) only. This discrepancy raises questions of clarity and reproducibility: which exact models/variants were used? Are the missing three simply duplicates or omitted? This needs correction.

**Critique 6** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 3. The paper highlights the empirical observation that LoRA fine-tuning benefits larger models while full-parameter fine-tuning benefits smaller ones. While this finding is consistent with the data presented, the claim itself is not novel, it has already been documented in earlier comparative studies such as: 1. Sun, Xianghui, et al. "A comparative study between full-parameter and lora-based fine-tuning on chinese instruction data for instruction following large language model." arXiv preprint arXiv:2304.08109 (2023). 2. Shuttleworth, Reece, et al. "Lora vs full fine-tuning: An illusion of equivalence." arXiv preprint arXiv:2410.21228 (2024). Even though this is not a central claim compared to the dataset contribution, the authors could better position the paper as primarily dataset-centric, emphasizing the cultural and linguistic resource itself while treating the fine-tuning findings as supporting analysis rather than a novelty claim.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4. Evaluation judge for QA: free-form QA correctness and sentiment are judged by GPT5-mini (automated judge). This is convenient but can introduce bias, a small human evaluation subset (with inter-annotator agreement) is required for credibility.

**Critique 8** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 1. Were all models run with the same prompt templates and temperature settings?

**Critique 9** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> 2. Do you plan to host a public leaderboard or benchmark portal (e.g., on Hugging Face or Papers with Code) so future models can be evaluated on this dataset?

**Critique 10** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 3. Beyond confirming previous trends, does your LoRA vs full-parameter analysis reveal any new behavior specific to this domain (e.g., cross-cultural symbolic tasks, low-resource fine-tuning)?

**Critique 11** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 4. Does LLM performance increase with prompt or context optimization stratergies?

`[post-rebuttal, set aside]` My current rating is mainly due to remaining questions about the licensing and provenance of the data sources. ⏐ That said, I find the dataset itself valuable and timely, and with clearer documentation of licensing as well as broader and more LLM evaluations, I would be more favorable toward an acceptance decision.

## Example 9 — review `1xBTP2Lsat` (ICLR 2026)

28 units, 7 critiques, 8 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The idea of reframing latent representation learning for time series as a control problem is novel.

**Critique 2** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> By explicitly modeling a feedback control signal in the latent dynamics, NFC can stabilize predictions even under high levels of missing inputs, which is a major challenge for existing methods.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 2. Authors provide a formal stability guarantee (I admit, I assume the theorem is correct)

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> 3. The experiments on both classification and forecasting tasks demonstrate that NFC consistently outperforms several state-of-the-art ODE-based models, such as ODE-RNN, NCDE, and Latent ODE.

**Critique 5** — aspect `reproducibility`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. Several key components of the paper are under-specified, making it hard to clearly understand the working of the model (i) What exactly is the input to the VAE? The authors mention masked history. Does it include the historical timepoints or only historical observations and labels? (ii) The paper mentions predicting controls for the next $M$ time steps, but does not specify how $M$ is chosen, whether it varies across datasets, or why a multi-step horizon is used instead of a single-step control. (iii) Because the control horizon $M$ is not defined and the procedure for computing multi-step controls is unclear, it is ambiguous how the latent states $h_t$ are computed at each step. Is the latent ODE integrated step-by-step with updated controls or over a fixed horizon with precomputed controls? (iv) The paper does not describe the VAE architecture (encoder/decoder) or how it summarizes historical observations into a latent context. (v) Hyperparameters and training details missing: Latent dimensions, VAE latent size, and ODE solver settings are not reported. Training hyperparameters (learning rate, batch size, optimizer, number of epochs, loss weights) are missing. Without these details, results are not reproducible.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 2. Algorithm 1 does not help in clearly understanding the model.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 3. NFC outperforms ODE-based models, but comparisons with non-ODE state-of-the-art methods (eg, [1] for classification, [2,3] for forecasting) are needed to validate its practical utility. While good to see the comparison with Contiformer, it is useful to see more recent baselines.

`[ignored]` [1] Luo, Yicheng, et al. "Knowledge-empowered dynamic graph network for irregularly sampled medical time series." Advances in Neural Information Processing Systems 37 (2024): 67172-67199. ⏐ [2] Zhang, Weijia, et al. "Irregular multivariate time series forecasting: A transformable patching graph neural networks approach." Forty-first International Conference on Machine Learning. ⏐ 2024. ⏐ [3]  Yalavarthi, Vijaya Krishna, et al. "Grafiti: Graphs for forecasting irregularly sampled time series." Proceedings of the AAAI Conference on Artificial Intelligence. ⏐ Vol. ⏐ 38. No. 15. ⏐ 2024. ⏐ See weakness

## Example 10 — review `bXQ3lrgknP` (ICLR 2026)

17 units, 6 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The arguments in the paper are well-grounded, and the writing is logically rigorous and easy to follow.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> 2. The proposed dataset offers a richer variety of HDR scenes, substantiated by partial visualizations and extensive quantitative comparisons. When combined with the strongly generalized domain adaptation method, it further enhances the performance in the field of HDR fusion.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> The paper does not discuss the limitations of the proposed method. Is it effective in all scenarios? Please specify any potential constraints and provide examples of failure cases, which would help readers understand the method's boundaries.

**Critique 4** — aspect `reproducibility`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. The authors emphasize the efficiency of their method. Could you provide the additional computational cost (for both training and inference) introduced by the domain adaptor? Specifically, during inference, if the method necessarily requires additional test-time-training from the adaptor for every new scenarios (e.g., day, night, dusk), the claimed efficiency might be compromised. Clarifying this practical overhead is crucial.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 2. The LDR data in the Unreal Engine 5 synthetic dataset is generated via data augmentation, but the process (e.g., adding noise) is not detailed. For instance, the LDR examples in Figure 3 show no noise variation across exposures. This lack of realistic degradation might be a key reason for the poor generalization when trained solely on the proposed dataset. Enhancing the data synthesis pipeline with a more realistic degradation model could significantly boost the dataset's generalization capability and contribution.

**Critique 6** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 3. Abundant HDR data from professional film-grade equipment can be acquired on the internet. What is the specific advantage of the dataset proposed in this work compared to these readily available sources? Please elaborate on its unique value.

## Example 11 — review `abhWLVahTw` (ICLR 2026)

48 units, 10 critiques, 10 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - **Clear Problem Motivation:** The work targets the highly relevant issue of object hallucination in vision-language decision-making, specifically addressing scenarios where VLMs are used out-of-the-box without task-specific retraining.

**Critique 2** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> - **Methodological Innovation:** SceneDiver’s two-stage, coarse-to-fine approach for generating a focus plan—comprising global scene graph planning followed by local fine-grained focusing—offers a structured strategy to mitigate distractor interference. This is visually clarified in Figure 1, which presents an end-to-end pipeline spanning instruction input to image modification. - **Strong Empirical Support:** The paper provides comprehensive experiments (Tables 1 & 2) across multiple VLMs and tasks, showing consistent performance gains over baselines.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> Ablation analysis (Section 4.2, Table 2) convincingly dissects the contribution of each system component. - **Thorough Visualizations:** The qualitative trajectories in Figures 3 and 4 and additional examples in the appendix (Figures 6–13) provide interpretability into the method’s effect on attention and decision steps. - **Practical Robustness:** The paper demonstrates that the approach remains beneficial—even with untrained or partially trained scene graph generation—suggesting real-world applicability.

**Critique 4** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - **Reproducibility:** The methods and experimental setups are described in detail, including a stated intention to release code. 1. **Incomplete Positioning against Closest Prior Work:** Several recent and highly relevant works addressing hallucination in VLMs (see 'Potentially Missing Related Work') are not cited or discussed. This is a significant oversight given their strong alignment in motivation and technical foundation. Examples include works on visual inference chains, multi-view reasoning, and systematic hallucination benchmarking. This omission directly affects the paper’s contextualization and could impact the novelty claim. 1. **Clarification on Focus Score Calibration:** How is the $\sigma$ parameter (Section 3.4.1) chosen for the attention map, and how sensitive are the results to its value? Is there an adaptive mechanism or heuristic for this, especially in cluttered or off-center tasks?

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 2. **Math and Clarity Issues in Focus Map Construction (Section 3.4):** The mathematical exposition around score map construction and image editing suffers from a lack of clarity and rigor: - The definition of the coefficient $c(d)$ in Section 3.4.1 uses a Gaussian decay, but it is unclear how $\sigma$ is chosen, how sensitivity to hyperparameters is controlled, or how “distance to the image center” generalizes to complex scenes with off-center targets. - The blending equations for image emphasis/de-emphasis ($I' = I \odot (\beta + (1-\beta) s)$ and $I'' = (1-a) \odot I' + a \odot \mathcal{B}_{\sigma_b}(I)$) are correct in isolation, but the implementation details—such as the handling of per-object overlaps and thresholds—are not fully described. It is unclear how the method ensures that background suppression does not accidentally eliminate critical context in complex, occluded scenes. Furthermore, the method implicitly assumes $s$ is well-calibrated, yet there is no explicit calibration or adaptive thresholding, which can reduce robustness in cluttered or unfamiliar visual settings. 2. **Handling of Overlapping/Adjacent Candidates:** When multiple candidate objects overlap or are spatially adjacent, how is the focus map $A$ constructed to avoid unintended attention diffusion or masking of critical context?

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 3. **Missing and/or Weak Baselines:** While ablation studies are included, some direct baselines from recent literature on hallucination reduction (such as multi-view and multi-hop reasoning or inference-chain frameworks) are missing. The lack of direct comparison to these approaches in Table 2 or the main results is a methodological gap that makes it difficult to situate SceneDiver’s relative merits and shortcomings. 4. **Baselines Against Recent Hallucination-Mitigation Methods:** Are there technical reasons for not including Visual Inference Chain, Multi-View Reasoning, or related methods as direct baselines? If so, please clarify. If not, would the authors be able to add these for a fairer comparison?

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4. **Over-reliance on Scene Graph Quality:** Despite some sensitivity analysis, the method fundamentally depends on the quality of object and relationship detection in the scene graph. While the results (discussed around Figure 5) show some robustness, there is insufficient quantitative exploration of failure modes—e.g., what happens if critical task-relevant objects are misdetected or missed in the initial coarse stage. The qualitative figures (e.g., Figure 4) focus on clean success cases rather than highlighting or dissecting difficult failures. 3. **Failure Cases in Scene Graph Detection:** Can the authors provide additional quantitative analysis of how failures in scene graph extraction (missed objects/relations) propagate through the pipeline? What is the worst-case impact on downstream decision accuracy?

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 5. **Lack of Theoretical Guarantees or Deeper Analysis:** The paper motivates its pipeline with conceptual intuition but does not provide theoretical guarantees or analysis (e.g., convergence, error propagation, or attention calibration bounds). For example, in Section 3.3, the three focusing strategies are described, but no formalism is provided regarding their completeness or worst-case behavior. The stepwise approach may fail to recover in situations of cascading errors, which is not examined.

**Critique 9** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 6. **Some Ambiguity in Experimental Protocols:** While the experimental setup is well detailed, it is not always clear how statistical significance is established in performance comparisons (Table 2)—variance is reported, but there’s no mention of hypothesis testing or statistical thresholds used to claim “significant enhancement.” Additionally, the supplementary visualizations (Figures 6–13) add interpretability but do not systematically evaluate failure cases. 7. **Potential Issues with Generalizability:** The method is tested on robotic manipulation and room navigation but may not generalize to visual domains with different object spatial relationships or more abstract task definitions (e.g., medical imaging or non-spatial language grounding). This limitation is briefly discussed but not empirically explored. 5. **Statistical Significance:** What specific statistical tests or thresholds are used to determine whether the improvements in Table 2 are significant?

**Critique 10** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 8. **Limited Discussion of Limitations in Main Text:** Most of the limitations and future work are condensed at the end, without being integrated into the problem discussion or experimental interpretation.

`[ignored]` Potentially Missing Related Work ⏐ 1. Zheng, H., Xu, T., Sun, H. (2024): *Thinking Before Looking: Improving Multimodal LLM Reasoning via Mitigating Visual Hallucination* — Proposes a Visual Inference Chain framework highly aligned in spirit with the focus on mitigating hallucinations in complex visual scenes. ⏐ Should be cited and compared in Section 2 (Related Work, Object Hallucination) and included as a baseline/alternative strategy in comparisons (Tables 1 or 2). ⏐ 2. Gu, Z., Chen, J., Liu, F. (2025): *MedVH: Toward Systematic Evaluation of Hallucination for Large Vision Language Models in the Medical Context* — Establishes systematic benchmarks for hallucination evaluation; relevant for broader claims and should be referenced in Section 4 (Experiments) when discussing generalizability and benchmarking. ⏐ 3. Anonymous (2025): *See, Think, Hallucinate: Interpreting Reasoning and Hallucinations Beyond the First Hop in Vision-Language Models* — Investigates hallucinations beyond first-step reasoning, providing deep insights into multi-step or cascading errors similar to those in this work. ⏐ Should be discussed in Sections 2 and 4, and ideally referenced alongside SceneDiver's multi-stage planning in Section 3. ⏐ 4. Anonymous (2025): *Look, Compare, Decide: Alleviating Hallucination in Large Vision-Language Models via Multi-View Multi-Path Reasoning* — Introduces a training-free framework for hallucination reduction using multi-view, multi-path reasoning. ⏐ Highly relevant as a direct baseline or discussed alternative; should be cited in Section 2 and quantitatively compared in Section 4/Table 2. ⏐ 5. Anonymous (2025): *VIDHALLUC: Evaluating Temporal Hallucinations in Multimodal Large Language Models for Video Understanding* — Develops benchmarks for evaluating hallucinations in temporal/multimodal tasks. ⏐ Should be referenced when situating SceneDiver’s applicability and generalization to temporally-evolving scenes.

## Example 12 — review `qIKFCePQTW` (ICLR 2026)

17 units, 7 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The proposed method is derived using only a few posterior samples and the squared likelihood score can be estimated with state-of-the -art methods such as Decoupled Annealing Posterior Sampling.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> - The algorithm is compared to various baselines in several challenging tasks and consistently outperforms the alternatives.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> -  The model selection results for the real M87* data and the posterior samples with the lowest and highest evidence highlights that the method can be used in real data settings, using numerous potential priors.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The proposed algorithm is well motivated and easy to derive from pretrained denoisers. However there are no theoretical guarantees or no intuitions on the data distribution for which the logevidence estimator is good.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The algorithm uses DAPS whose annealing process reduces the dependency between samples at consecutive time steps,and allows to obtain marginal posterior samples for any noise level starting from samples from any other noise level. However, the reasearch on posterior sampling using pretrained score-based models has been very active for the past few years and alternatives could be considered. As there is no theoretical guarantee on the proposed estimate, exploring other samplers would support the choice made by the authors.

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The proposed estimate of the posterior covariance is based on a Gaussian approximation of the data distribution using training data. Although it provides a very easy to compute estimate, the assumption that the data distribution is close to a Gaussian is strong in settings where this distribution is likely to be multimodal. The covariance estimate proposed by Lemma 1 used a Gaussian assumption. Would you have insights on how to propose an estimate in a more general setting ? Or to provide guarantees that the proposed estimates is good even in non Gaussian settings.

**Critique 7** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> The literature providing theoretical guarantees for score-based diffusion models is very rich for unconditional and conditional sampling. Could this theory be used to provide guarantees on the proposed logevidence estimator ? Did you try score-based alternatives to DAPS to obtain the samples to support that this choice outperforms other posterior sampling algorithms based on pretrained diffusions ? Could you include computational time to your experiments to understand the trade-off between number of samples from the diffusion and computational complexity ?

## Example 13 — review `kodFE0eZ2T` (ICLR 2026)

18 units, 4 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Good design. I'm impressed by the separated CFG design. This cleverly bypasses the difficulty of limb-length differences.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - Good generalization performance.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Some crude components/approximations: The approximation for the $\Pi$GDM is somewhat crude. (i) It requires a strong assumption. The assumption in Theorem 1 requires the 6 DoF representation to be already close to a Stiefel matrix. However, this may not be true for a large part of the diffusion process. (ii) Theorem 1 is somewhat misleading. The proof only shows that the mean and the covariance of the distribution will correspond to the derived expressions. This does not imply that the resulting distribution will be close enough to a Gaussian one. It can be a widely different distribution, which still has the same mean and covariance.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> - Better generalization, but worse in the best-case scenario? In Figure 3, InPose is worse than existing methods when the scale is one. The paper says that this is "expected," but why is this? I cannot find a valid reason for the proposed formation being worse with the default scale. A more thorough discussion is needed here.

`[ignored]` Please see the above weaknesses.

## Example 14 — review `25vB9XtR9w` (ICLR 2026)

15 units, 5 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> I like that this approach learns a neural implicit dynamics model with the help of existing explicit physics laws as guidance. The final learning outcome can be correlated back to the explicit models while not constrained by them. The way the explicit physics laws are used is in a spirit similar to expectation maximization.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> The experimental result shows superior performance of the proposed model.

**Critique 3** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> I'm not sure how realistic the problem and experiment setup is. The deformation of the objects is very significant and uncommon in the real world. The dropping motion is doable but also limiting and not very common in real-world experience. I wonder what the practical application of this task are, given that it takes more than 1 hour to reason about one video of one object.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> There is a lack of ablation study of the methodology. Only comparisons shown are without either of the two loss functions. This is a very coarse comparison. I think more detailed experiments are helpful especially given that there are very specific designs of the loss functions (e.g., global vs anchor-level supervision, rank-based loss formulation, procedure of the Multi-Hypothesis Physics Verifier, etc).

**Critique 5** — aspect `soundness`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> Why is the color-space supervision not used? Does it hurt the result? What is the rationale behind the depth loss based on the rank correlation instead of metric-based losses?

## Example 15 — review `FptpyAmExR` (ICLR 2026)

21 units, 5 critiques, 4 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> The proposed method achieves SOTA performance on public benchmarks, KITTI and NYUv2

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The authors validate the effectiveness of the proposed modules and the robustness over sparsity.

**Critique 3** — aspect `reproducibility`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The authors also provide detailed information regarding the method, like model structure, proof, parameters, etc.

**Critique 4** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The idea of using use Gaussian Belief Propagation for inference is interesting, with strong motivation from previous methods.

**Critique 5** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The strategy, MRF for depth estimation, has been explored before [1][2]. The authors should provide some discussions. - What are the advantages of the MRF for depth completion (GMCN & GBP) in comparison with previous propagation-based methods? - The authors claim that " allowing the model to adaptively capture complex, long-range spatial dependencies guided by image content". Maybe it would be better if some cases are provided. - As shown in Tab. 9 of the Supplementary, the proposed method has higher running time than BP-Net, while there performance is very close. Therefore, what advantages does the method have in comparison with BP-Net (apart from fewer parameters) - Discussion about the Serial & Parallel Propagation Scheme should be provided, like the efficacy. How the strategy improves the performance/computational cost? - In which scenarios, the proposed method performs better? and what issues it can solve? Please give more examples and analysis. Since the performance is close to the latest methods, the authors should give more evidences for the effectiveness of the proposed method.

`[ignored]` [1] Chen et al., Fast MRF Optimization with Application to Depth Reconstruction. ⏐ [2] Liu et al., Deep Convolutional Neural Fields for Depth Estimation from a Single Image ⏐ See the weakness. ⏐ Please give feedbacks for each point.

## Example 16 — review `vnkd94VCbm` (ICLR 2026)

28 units, 9 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. Flexible noise modeling with proper scoring rules yields calibrated predictive distributions instead of mere point estimates.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 2. Closed-form reverse transitions allow efficient sampling and easy integration with standard diffusion samplers.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 3. Modular parameterizations (diag Gaussian, mixtures, multivariate/low-rank) trade off accuracy vs. compute without redesigning the pipeline.

**Critique 4** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 4. Broad empirical scope (tabular, autoregressive flow/weather, depth) shows consistent CRPS/calibration gains over diffusion baselines.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. The paper's core premise—learning the full noise distribution $ p_{\theta}^{\epsilon}(\cdot|x_t) $ via proper scoring rules—was concurrently proposed by Bortoli et al. (2025). This work's primary contribution is thus the specific instantiation with (mixture) Gaussian heads. This is further narrowed by the fact that the simplest case (univariate Gaussian) is, as the authors note, conceptually equivalent to prior work on variance learning.

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 2. The reported improvements are inconsistent and, in some cases, negligible. On UCI benchmarks, CRPS gains vary widely, from substantial (e.g., Naval: $ -32 % $) to nonexistent (e.g., Wine: $ 0 % $). The method can also underperform the baseline in RMSE on some datasets (e.g., Yacht). Likewise, on depth estimation, the CRPS gains are marginal (e.g., $ \approx -0.45 % $ on KITTI, $ \approx -2.5\% $ on DIODE) and even show a slight regression on ETH3D ($ \approx +0.7\% $). This mixed evidence weakens the claim of general applicability. 2.  How do the authors explain the highly variable, and in some cases negligible or negative, empirical gains (e.g., 0% CRPS on Wine, RMSE regression on Yacht, marginal/negative CRPS on KITTI/ETH3D)? Can rigorous ablations be provided to demonstrate that these gains are not mere artifacts of added parameters, especially for the depth estimation tasks?

**Critique 7** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 3.  The method's calibration claims are undermined by the reliance on a post-hoc hyperparameter, $ \tau $. The authors concede the model is "over-conservative" and that achieving near-nominal coverage—as well as the largest CRPS/ES gains—requires a small $ \tau \approx 0.05 $. This is a significant, unprincipled deviation from the underlying DDIM framework, and no method for selecting this critical parameter is proposed. 1.  Given the method is demonstrably "over-conservative" at $\tau=1$, how can the reliance on an unprincipled, post-hoc $\tau \approx 0.05$ to correct calibration be justified? Can the authors provide a principled selection rule for $\tau$ and re-evaluate all key metrics using it, rather than presenting ad-hoc results?

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4. The empirical evaluation lacks the rigor expected for a high-impact venue. The authors admit to only "minor hyperparameter tuning" for comparators and an inability to conduct an "extensive statistical evaluation" of their own hyperparameters due to cost. Furthermore, computational comparisons are dismissed as "rough estimates". Without a rigorous and fair benchmark, the reported performance margins are difficult to interpret confidently. 3.  Given the admission of "minor hyperparameter tuning" and "not optimized" timing, how can the claims of superiority be validated? Can the authors strengthen the paper by providing comparisons against properly tuned, strong UQ baselines (e.g., variance-learning DDPMs, MDNs) under a fair, matched-compute framework?

**Critique 9** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 4.  How can the framework be considered "principled" when it currently lacks practical guidance for model selection and the claims of epistemic uncertainty separation are purely qualitative? Can the authors substantiate these claims by providing a quantitative heuristic for head selection and either a formal analysis or a quantitative benchmark for the UQ decomposition?

`[ignored]` See the weakness section and the following:

## Example 17 — review `U0L1H7yhsF` (ICLR 2026)

15 units, 7 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The paper addresses an important and common challenge in deep-search agent tasks.

**Critique 2** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 2. The writing is clear and easy to follow.

**Critique 3** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 3. The use of an auxiliary refiner agent to summarize and compress task information is interesting and potentially generalizable.

**Critique 4** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. The main innovations claimed by this paper: sub-goal–based dense rewards and failure-guided hints are primarily data-driven enhancements rather than methodological advances. Both rely on stronger external LLM APIs for sub-goal generation and hint generation through specifically designed prompts. This makes the approach highly engineered and dataset-specific rather than an automated, generalizable "strategy". The contribution is therefore weakened, as the benefit largely stems from using denser supervision from stronger models. In contrast, many prior works have proposed principled, model-independent methods for reward densification, from general reward shaping in RL to process reward models in LLM training. Thus, relying on the LLM API to provide a sub-goal reward applicable only to customized datasets seems highly intensive and lacks innovation, and should certainly not be considered the main contribution of the paper.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 2. Since the sub-goal decomposition, sub-goal reward, and trajectory hints are all derived from external APIs, the method distills additional knowledge into the training data. Comparing this enhanced dataset against baselines trained on unaugmented data is unfair and does not demonstrate algorithmic superiority, only data quality differences.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 3. In Section 3.2.1, the use of the term *rejection sampling* is inaccurate, as the described process is a deterministic data filtering procedure rather than probabilistic rejection sampling in the Monte Carlo sense. I suggest the authors revise this terminology to avoid misunderstanding.

**Critique 7** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 4. The paper provided an anonymous code link, but the repository is empty (at least at the time of review).

`[ignored]` See the weakness

## Example 18 — review `cfR4X4qmKk` (ICLR 2026)

20 units, 8 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 1. **Important problem**: Addresses a genuine issue in low-rank approximation where distribution shifts can cause cumulative errors across layers. The observation that anisotropic input distributions can cause small singular values to align with high-energy input components (leading to disproportionate output distortion) is well-articulated and provides strong motivation for the proposed approach.

**Critique 2** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. **Theoretical motivation**: Provides theoretical analysis linking distribution alignment to error propagation, which adds depth to the empirical work. The decomposition of whitening drift into initial residual and compression-induced shift (Equation 12) offers valuable insights into the source of performance degradation.

**Critique 3** — aspect `clarity`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 3. **Clear presentation of the core idea**: The motivation and high-level approach are communicated effectively. The progression from problem identification to solution design is logical and well-structured.

**Critique 4** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. **Some kind of Limited novelty in core technique:** The use of whitening transformations to decorrelate features is a well-established technique in machine learning. While the dynamic, layer-wise application is novel, the core mathematical framework (ZCA whitening via Cholesky decomposition) is standard. The main contribution appears to be the engineering insight of recomputing whitening based on compressed activations rather than a fundamentally new algorithmic approach.

**Critique 5** — aspect `reproducibility`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2. **Computational overhead not thoroughly analyzed:** While Appendix A acknowledges additional computational cost from per-layer whitening operations, the paper lacks quantitative analysis of this overhead. Critical missing information includes: (a) wall-clock time comparison during compression, (b) memory overhead during the compression process, (c) impact on inference latency after compression, and (d) scalability analysis showing how overhead grows with model size. For practitioners, these practical considerations are as important as perplexity improvements.

**Critique 6** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> - Can you provide tighter bounds that incorporate the regularization parameter ε? - How do the Lipschitz constants ρₗ behave in practice for transformer layers?

**Critique 7** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> 2. **Scalability:** Your largest model is 13B parameters. Do you expect the method to scale to 70B+ models?

**Critique 8** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 3. **Dynamic compression:** In Section 4.4, you combine your method with dynamic ratio allocation. How does layer-wise variation in compression ratio affect the whitening computation? Should the whitening strategy be different for layers with different compression ratios?

`[ignored]` 1. [**Theoretical guarantees:**]

## Example 19 — review `xYCZqxBvwB` (ICLR 2026)

15 units, 5 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - **Interpretable diagnostics:** The hierarchical objects and attributes composition isolates minimal causes of failure rather than conflating factor.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> - **Scalable exploration:** Pruning and prioritizer accurately reduce evaluations and speed discovery. For instance, retained layer‑3 nodes drop to 4.2% for SD1.5 and enables failure discovery faster. - **Actionable link to data and reliable evaluation:** Data‑attribution connects many failures to low training frequency and the automated evaluator aligns well with humans.

**Critique 3** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - This paper doesn’t address timely topics that recent state-of-the-art diffusion models advanced at capturing user text prompts, particularly for objects and their properties. It not only adheres to models at the forefront, such as SD-v3.5 and flux, but its analysis relies on LAION-2B, released around three years ago. Considering the paper’s contribution, it doesn’t technically contribute to the domain of generative models.

**Critique 4** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - While this paper could be considered a benchmark, its focus on data point generation highlights how to make them. As a benchmark, it should justify the angles generative models are assessed and why they are meaningful. However, most of the paper’s content focuses on data point generation and efficiency of the procedure. I believe this approach would be beneficial if it could generalize across video generation or other types of text-based generative models. However, in its current form, it only considers text-to-image cases and doesn’t appear generalized to other types of models.

**Critique 5** — aspect `significance`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> As mentioned earlier, I was wondering if this approach could be applied to video generation tasks. I believe that the current video generation tasks still require relevant benchmarks to evaluate models based on their quality and ability to reflect user text prompts. I would greatly appreciate it if this approach could be extended to video generation.

## Example 20 — review `SgJOvgUKUo` (ICLR 2026)

20 units, 16 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The paper presents a conceptually novel extension of adversarial learning to policy transfer.

**Critique 2** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> The idea of using adversarial agents not for equilibrium learning but for transfer is well-motivated and new within the MARL context.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The formulation of a bi-level adversarial objective, combined with policy distillation, is technically sound and well-justified.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> - The experiments are solid. APT consistently outperforms fine-tuning, MAICL, and ATT across both cooperative and competitive benchmarks.

**Critique 5** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - The paper includes thorough ablation studies, examining fixed vs. adaptive guidance, the number of adversaries, dataset size, and shared vs. separate opponent models.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The writing is clear, well-structured, and easy to follow.

**Critique 7** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The novelty is incremental. The framework combines known ideas—adversarial training, policy distillation, and transfer learning—into a coherent and well-executed system.

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The analysis justifies the adaptive adversarial weight locally (via score disagreement) but lacks global convergence or stability guarantees. There is also no discussion on local-global consistency, which is a key consideration in cooperative MARL.

**Critique 9** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The paper does not include a rigorous proof of convergence for the APT algorithm. The bi-level optimization between the adversary and the learner is described conceptually and algorithmically, but there is no theoretical analysis regarding convergence to equilibrium, stability of adversarial updates, or consistency of the transfer process.

**Critique 10** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> - The evaluated tasks (MPE, Overcooked, Atari) are relatively small and low-dimensional.

**Critique 11** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> Including experiments on more challenging MARL benchmarks (e.g., SMACv2) would better demonstrate scalability and robustness.

**Critique 12** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> - LLMs are used only to generate partner or opponent behaviors in certain evaluations, and there is no ablation study to assess their contribution to overall performance.

**Critique 13** — aspect `related_work`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 1. How does APT differ from previous combinations of adversarial training and transfer learning in MARL and single-agent RL?

**Critique 14** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 2. Can the authors provide any theoretical insights or guarantees regarding convergence or stability of the bi-level optimization?

**Critique 15** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> 3. What is the impact of LLM-based agents on the reported results, and can this be isolated through ablation?

**Critique 16** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 4. Does the adaptive adversarial weighting mechanism maintain consistency between local and global objectives in cooperative settings?

