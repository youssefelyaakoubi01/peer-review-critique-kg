# 20 random reviews of run `dev_v2` (seed 0)

Review text is public content from OpenReview. `[ignored]` units are in no critique.

## Example 1 — review `5WWa3sZKqR` (ICLR 2024)

36 units, 0 critiques, 36 ignored, 0 set aside as post-rebuttal.

**Segmentation failed for this review.**

`[ignored]` Originality: The author proposed a new learning framework by combining the auto-encoder and sparse-promoting loss functions for equation discovery tasks. ⏐ Quality: The result for the proposed method is comprehensive and includes various ODE cases. ⏐ Clarity: The figure and equation are well formulated in general. ⏐ The writing is self-contained to understand ⏐ Significance:  The proposed methods integrates sparse equation discovery methods deep generative modeling. ⏐ The problem setting is confusing and the baseline models are not adequate. ⏐ Details see the questions part. ⏐ 1. Problem setting about the stochastic system. ⏐ As the author mentioned, they used an alternative definition of the stochastic dynamics, e.g random ODE. ⏐ However, the reviewer is confused by the benefit of such definition compared to the deterministic setting. ⏐ In result part 4.1, both the mean and the STD of the underlying system are shown. ⏐ However, the STD form doesn't corresponds to any dynamics and the mean is close the the true mean of the system. ⏐ In such circumstances, it seems only the mean estimation is important and the std cannot be leveraged to judge the performance of the proposed model. ⏐ For part 4.2, the STD result is also confusing. ⏐ It is compared with the diffusion terms but it is totally different from the true diffusion term. ⏐ Therefore, the reviewer wants to ask why we need to include the STD and how it can help the proposed model. ⏐ 2. The result needs to compare with more SOTA models and include more comprehensive metrics. ⏐ There are several model combining learning based method and SINDy-like algorithm for the equation discovery tasks [1][2]. ⏐ Also, by checking the Figure 2, we could find that the discovery form is different under different $\sigma$. ⏐ For a equation discovery problem, it is important to get a consistent and correct form. ⏐ Therefore the reviewer suggests adding more metrics on evaluating if the proposed model can get the correct form, e.g, precision and recall metrics. ⏐ [1] Bayesian Spline Learning for Equation Discovery of Nonlinear Dynamics with Quantified Uncertainty. ⏐ [2] Physics-informed learning of governing equations from scarce data ⏐ 3. The high dimensional 10d lorenz 96 is not compared with any baselines. ⏐ Moreover, the analytical form is not listed in the main manuscript. ⏐ Figure 4's caption says check equation 9 but that's for lorenz 63. ⏐ Lorenz 96 should like equation 12 but with the concrete forcing terms. ⏐ Equation 12 indicates that all the coefficients except the forcing terms should be close to 1 or -1. ⏐ However, the discovered coefficients for $x_i$ is not close to these values. ⏐ Again, the reviewer doesn't understand what is the gain of reporting the STD form of the equation here. ⏐ 4. The methodology part is confusing. ⏐ Figures 2 says $\theta$ has 3 terms but page 8 says $\theta$ has 2 terms. ⏐ Moreover, in the lower part of Figure 2, $z$ is firstly sampled from $p_{\theta}(z)$ then was fed into decoder $H$. ⏐ However, the definition of $\theta$ has already included $H$, making the $H$ applied to $z$ 2 times. ⏐ The term "inference model" is commonly used for test time, but the author use it to indicate training procedure. ⏐ There are all the confusing parts need to be clarified.

## Example 2 — review `qj1hwDHLwV` (ICLR 2024)

7 units, 6 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The authors provide a clear motivation of the problem and is easy to read and follow.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The authors also supplement the claims with some proofs and empirical results.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> One part which is not very clear is around the choice of the accuracy predictor and not very clear how the experiments look like with respect to other design choices around different compression strategies which would make it better to understand the generalizability of the solution. Because of this choice it limits the applicability of the results as they are compared against only one compression constraint.

Author response — `clarification` (units 4–6):

> Two architectures were considered for the accuracy prediction task - multi layer perceptron (MLP) and gradient boosted decision trees (GBDT), with hyperparameters such as depth of MLP and number of decision trees selected using cross validation. GBDT outperformed MLP in our experiments, which is also consistent with the findings of [1] where multiple performance prediction architectures for DNNs are considered. [1] White et al, “How Powerful are Performance Predictors in Neural Architecture Search?”, NeurIPS’21

Author response — `clarification` (units 8–11):

> The choice of compression methods selected in our experiments is based on a practical constraint - the availability of stable implementations that can compress a wide array of DNN architectures. We found the open source library “neural network intelligence (NNI)” to align the closest with our requirements and used the compression methods implemented there for our experiments. Some methods such as movement pruning had to be discarded as their fine tuning diverged for several architectures leading to unreliable data. In summary, our experiments so far suggest that the proposed meta compression a […]

Author response — `clarification` (units 13–15):

> While we evaluate and provide results for two key constraints in our analysis - compression constraint and accuracy constraint, additional constraints can also be easily incorporated into the proposed framework. For instance, a constraint on FLOPs/MACs can be implemented by limiting the search space to compression methods that reduce FLOPs(eg. Channel pruning), and predicting the performance of several pretrained models after compression using channel pruning methods to a level that satisfies the constraint.

**Critique 4** — aspect `significance`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> It is not clear how the research generalized with more recent modeling techniques specifically around transformers, which would help to strengthen the paper and understand the generalizability of the provided approach.

Author response — `concession` (units 16–19):

> “_It is not clear how the research generalized with more recent modeling techniques specifically around transformers, which would help to strengthen the paper and understand the generalizability of the provided approach._” We fully agree that using more recent models and compression methods would be beneficial. However, many of these (including transformers) require significant computing resources and are tailored for specific architectures, making the evaluation very challenging. We will consider such an evaluation as future work.

**Critique 5** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 1. How would the result and analysis hold against newer architectures specifically around transformers?

Author response — `concession` (units 16–19):

> “_It is not clear how the research generalized with more recent modeling techniques specifically around transformers, which would help to strengthen the paper and understand the generalizability of the provided approach._” We fully agree that using more recent models and compression methods would be beneficial. However, many of these (including transformers) require significant computing resources and are tailored for specific architectures, making the evaluation very challenging. We will consider such an evaluation as future work.

**Critique 6** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> 2. Do you see limitations of the approach with respect to datasets or architectural choice?

Author response: none.

## Example 3 — review `WdVrtK2jWM` (ICLR 2024)

21 units, 5 critiques, 12 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The main originality seems to be theoretical proofs rather than network structures. However, the proofs heavily depend on NTK techniques.

Author response — `clarification` (units 5–12):

> 1. As pointed out by the reviewer, one novel contribution comes from the newly designed input and output of neural networks to reduce the input dimension to $d$. In addition to the empirical improvement, this design also brings theoretical improvement. This is because our approach can directly take the label vector for the back-propagation of neural networks, such that we can derive a tighter confidence bound for the estimation based on the generalization bound of online gradient descent. In contrast, [48] only takes the reward of the selected arm (class) for the back-propagation and adopts th […]

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The experiments were conducted only five times, which could potentially impact the reliability of the results. I would appreciate seeing outcomes derived from a greater number of runs.

Author response — `new_experiment` (units 15–16):

> We've extended our experiments to 10 runs (Table 1 and Table 2). The new results are consistent with the previous results and conclusion.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The theoretical results are only for the setting where the Tsybakov noise $\alpha = 0$, making it less comparable to existing literature, except when compared to [48] indirectly as $\alpha \rightarrow \infty$.

Author response — `new_experiment` (units 19–34):

> We've added the new theoretical results (Section F in the latest manuscript) adapting to the varying $\alpha$. Since the Mammen-Tsybakov noise $\alpha$ assumption and related work [48] only study the binary classification, we present the following results in the binary classification. The results for our proposed algorithm: \begin{aligned} \mathbf{R}\_{stream}(T) \leq \widetilde{\mathcal{O}}( (S^2 )^{\frac{\alpha+1}{\alpha+2}} T^{\frac{1}{\alpha + 2}}),  \\\\ \mathbf{N}(T) \leq \widetilde{\mathcal{O}}( (S^2 )^{\frac{\alpha}{\alpha+2}} T^{\frac{2}{\alpha + 2}}). \end{aligned} For comparison, th […]

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> - May I ask the reason behind limiting the experiments to five iterations? Was it influenced by computational constraints or other considerations?

Author response: none.

**Critique 5** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> - What's the main difficulty of analyzing settings other than $\alpha = 0$? What do the authors expect different levels of $\alpha$ to influence the theoretical results intuitively?

Author response — `new_experiment` (units 19–34):

> We've added the new theoretical results (Section F in the latest manuscript) adapting to the varying $\alpha$. Since the Mammen-Tsybakov noise $\alpha$ assumption and related work [48] only study the binary classification, we present the following results in the binary classification. The results for our proposed algorithm: \begin{aligned} \mathbf{R}\_{stream}(T) \leq \widetilde{\mathcal{O}}( (S^2 )^{\frac{\alpha+1}{\alpha+2}} T^{\frac{1}{\alpha + 2}}),  \\\\ \mathbf{N}(T) \leq \widetilde{\mathcal{O}}( (S^2 )^{\frac{\alpha}{\alpha+2}} T^{\frac{2}{\alpha + 2}}). \end{aligned} For comparison, th […]

`[ignored]` # Origionality ⏐ - The idea of exploration-exploitation networks is not so novel but related works are covered in detail. ⏐ It originates in [10] and is then adopted by [11], which is one of the works this paper is compared to. ⏐ - The idea of reducing the dimension to $d$ is novel considering the literature starting from [10]. ⏐ # Quality ⏐ - The theoretical proofs seem to be concrete. ⏐ - The experiments are extensive and detailed. ⏐ They validate the performance and computation efficiency claimed. ⏐ # Clarity ⏐ - The paper is in general well-written and smooth to follow, with the exception of some proofs in the supplementary material. ⏐ # Significance ⏐ - The proposed algorithms are of interest as the input is more coherent and the performance is great.

## Example 4 — review `Upm4GL7iRr` (ICLR 2024)

15 units, 6 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The paper is in general well organized and easy to follow.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 2. The proposed method is straightforward and shown to be effective on the test data.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. The main issue of the proposed method lies in the experimental evaluation. Only one learned-based method is adopted for comparison in the main paper on a rather simple dataset. More methods including some traditional methods should be also evaluated for better comparison. The experiment on the real dataset should be also provided to show the robustness of the proposed method.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> 2. From Fig. 6 in the supplementary, we can see that the performance of the proposed method on the I/I scenario is much worse than the SOTA method. More analysis of the drop of performance should be given. Moreover, the performance of different methods with different rotation angles should be provided for better comparison.

**Critique 5** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 3. How about the performance of other methods with a rough alignment of the initial shape? If a rough alignment is enough for the existing methods, why should we learn SO(3)-invariant correspondence in an end-to-end manner?

**Critique 6** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 4. The whole method is mainly built upon the existing SO(3)-equivariant representation. The main contribution lies in introducing this representation to the specific task. I didn't get too much novel insight in terms of network design.

`[ignored]` Please refer to the Weaknees part.

## Example 5 — review `seAPIHqQa8` (ICLR 2024)

27 units, 7 critiques, 12 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> The main contributions of the paper are the empirical results: outperforming [ZiCo][] by 0.7% with the same search time (0.4 GPU days).

Author response — `new_experiment` (units 60–71):

> Yes, the moving average is used to make the training more stable. Here, we provide an ablation study of the element importance measure. | Measure Method | Top-1 | | Index | 72.3 | | Taylor importance without moving average | 72.5 | | Taylor importance with moving average | 73.1 | "Index" means assigning an importance value to each element according to its index in the sequence statically. For example, we assign 0 to the first element, 1.0 to the last. As shown in the above Table, the Taylor importance and the moving average improve the performance. As Taylor importance computes importance by m […]

Author response — `clarification` (units 115–124):

> There are two reasons. 1. The comparison is unfair, as Zico uses a stronger training script, such as distillation and mix-up. Therefore, the real improvement should be larger. 2.  Our main target is not to provide SOTA ImageNet performance but to provide a general and flexible architecture search method. Our method is almost compatible with most network architectures and training processes. Therefore, we only change the depth and width of our baselines and do not use any tricks to improve performance. For our method, improving various tasks stably with limited search costs and limited hyperpar […]

Author response — `clarification` (units 194–204):

> We think there are two aspects of why it still works when we do not use taylor importance. 1. We agree with you that the method in this situation is similar to Nested Dropout, which is also a way to find a set of weights, better than random initialization, for the model. Index importance is also widely used in NAS methods, such as [1]. Their experiments also support this opinion. 2. There are mainly two aspects of why pruning/NAS methods improve the performance, including finding better initialization for the model and finding a better structure for the model[2,3]. As index importance is also  […]

Author response — `new_experiment` (units 238–261):

> We are conducting experiments to compare our method with ZiCo in the same training setting. But it will take some time to finish the experiments. We will comment on this question after we finish the experiments, again. Thanks for your feedback, again. It makes our paper better. If you have further questions, please let us know. We expect to describe our method more clearly to address your question, especially w2, q6, and q7, as they are important to our method. Looking forward to your reply. > Q8: Unfortunately, I can't conclude that the method would have ... We apologize for not finishing thi […]

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> This result appears to be well tested and therefore the paper achieves this goal.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> Similar results also support the method empirically on COCO and language model finetuning.

Author response: none.

**Critique 4** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> The authors describe the key difference between this work and similar architecture search methods is that it provides a differentiable and direct way to approach architecture search. In other words, other works allow a differentiable selection of which elements to include but do not allow easy optimization of how many elements to include. Architecture search is a significant area of research and this paper submits a new method for consideration.

Author response: none.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> In Section 3.2 the authors mention that this method bears some resemblance to pruning works, "Our DMS follows a pipeline similar to training-based model pruning." This implies that the model should be compared to pruning based methods in experiments. However, the comparisons appear to be made to NAS methods, such as [JointPruning][]. A comparison to state of the art sparse methods, such as [RIGL][] would make the experiments more robust.

Author response — `clarification` (units 7–26):

> Thanks for your suggestion. We compared our method with SOTA structure pruning methods in our original paper, detailed in Appendix A.4. Our method also outperforms SOTA structure pruning methods. There are two types of pruning methods: unstructural pruning and structural pruning. Unstructural pruning methods, such as RIGL, prune the model by setting the weights to zero. Structural pruning methods, such as our method, prune the model by removing the whole dimensions of the weight tensor. The two types of pruning methods have different pruning granularity. Unstructural pruning needs special hard […]

Author response — `new_experiment` (units 74–99):

> Here, we compare the pipeline of our method with standard pruning methods as follows. | Method | Pruning | Ours | | Stage 1 | Pretrain | No Need | | Stage 2 | Prune | Search | | Stage 3 | Fintune | Retrain | We guess that you may think the fintune stage of pruning methods is more efficient than the Retrain stage (train from scratch) of our method. However, most structural pruning methods directly use the same training setting as pretraining in fintuning stage [1,2]. Because this setting achieves the best performance. Therefore, our method is more efficient by omitting the most resource-consumi […]

Author response — `new_experiment` (units 206–236):

> We provide a more detailed table below. In this table, we prune the supernets to models with 1G flops. "N" indicates we do not pretrain the supernet, and "Y" indicates we pretrain the supernet. | Supernet   | Pretrain Stage | Search Stage               | Retrain Stage            | $cost_{pretrain}$ | $cost_{search}$ | $Cost_{retrain}$ | $cost_{total}$ | Top-1    | | ResNet-50  | N              | initialize randomly        | initialize randomly      | 0                 | 41              | 100              | 141            | 72.6     | | ResNet-50  | Y              | initialize with pretrained | […]

**Critique 6** — aspect `soundness`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> The function they have constructed for optimization is smooth but saturates outside of the active regions illustrated in Figure 2. This may cause vanishing gradient information. Any experiment to investigate whether this happens during training, or why it doesn't happen would be valuable.

Author response — `new_experiment` (units 30–40):

> Through our deduction and observation, we think gradient vanishing does not happen in our method. We show our deduction as follows. Figure 2 illustrates the gradient of $a$ with respect to element mask $m_i$. Here, we denote it as $\frac{\partial m_i}{\partial a}$. It's indeed that $\frac{\partial m_i}{\partial a}$ may equal to 0 when $m_i$ is close to 0 or 1. But the gradient of $a$ with respect to the $task\_loss$ is $\sum_{i=0}^{N}{\frac{\partial task \_loss}{\partial m_i}\frac{\partial m_i}{\partial a}}$. As shown in Figure 2, $\frac{\partial m_i}{\partial a}$ will not be 0 for all $i \in  […]

Author response — `new_experiment` (units 143–193):

> > W2: Figure 2 ...$\lambda_{resource}$ ## 1. $g_a$ decides whether the gradient vanishing problem exists, rather than $\frac{\partial m_i}{\partial a}$. Here, we think it's important to distinguish two situations, where some gradients are close to zero. 1. The **total gradient** of a learnable weight is close to zero. It means the weight is not updated, and causes the gradient vanishing problem. 2. The **partial gradient** of a learnable weight is close to zero. The weight may receive gradients from other parts, making its total gradient not close to zero. Therefore, it does **not** cause the  […]

**Critique 7** — aspect `clarity`, severity `major`, polarity `negative`, target `section`, actionable `True`

> The relationship between resource constraint and the top-k parameters is in the appendix but it's extremely important to the overall algorithm. The top-k operator as described leads the reader to assume $k$ would be fixed but in practice it's not constrained and $k$ can be any value. Really it's just a binary mask that has a soft constraint to sum to a low enough value to meet the resource constraints.

Author response — `clarification` (units 41–45):

> We apologize for the inconvenience. As many papers have used the resource constraint[1,2], we move the section about the resource constraint to the appendix when the paper is too long. Thanks for your advice. We will consider moving the section to the main paper. [1] Li, Yanyu, et al. "Pruning-as-Search: Efficient Neural Architecture Search via Channel Pruning and Structural Reparameterization."

Author response — `clarification` (units 50–55):

> We are sorry for the confusion. We agree that the 'k' is usually fixed. The reason we use the term "top-k" is because we just follow prior work. For example, [1] uses "soft top-k" in their method with an unfixed 'k'. We will consider more carefully when using the term "top-k" in the future. [1] Gao, Shangqian, et al. "Disentangled differentiable network pruning." European Conference on Computer Vision.

Author response — `clarification` (units 101–113):

> > Q7 "I don't understand what Table 4 means because the rows and columns refer to search and retraining, but one can't have both a pretrained model and a model that is retrained?" We apologize for the confusion. We update the table as follows: | Supernet | $Iinit_{search}$ | $Init_{retrain}$ | $cost_{pretrain}$ | $cost_{search}$ | $cost_{total}$ | Top-1 | | ResNet-50 | Random | Random | 0 | 41 | 41 | 72.6 | | ResNet-50 | Pretrained | Random | 410 | 41 | 451 | 72.5 | | ResNet-50 | Random | Searched | 0 | 41 | 41 | 73.1 | | ResNet-50 | Pretrained | Searched | 410 | 41 | 451 | 73.8 | This table s […]

`[ignored]` [zico]: https://arxiv.org/abs/2301.11300 ⏐ [rigl]: https://arxiv.org/abs/1911.11134 ⏐ [jointpruning]: https://ieeexplore.ieee.org/document/9516010 ⏐ How sensitive is the method to the element importance measure $c$? ⏐ It's computed as a moving average with a specific hyperparameter. ⏐ It seems like the gradient estimate of $a$ depends on this being stable. ⏐ In Section 3.2 you say "Compared with training-based pruning, our method eliminates the need for time-consuming pretraining since we think searching from scratch is more efficient thatn from a pretrained model...". ⏐ How does that save resources? ⏐ Typically pretrained models are available for free, but training one yourself from scratch is extremely expensive? ⏐ I don't understand what Table 4 means because the rows and colums refer to search and retraining but one can't have both a pretrained model and a model that is retrained? ⏐ The gains over prior architecture search methods seem to be relatively minor, such as 0.7% accuracy on ImageNet. ⏐ What would be your argument against this?

## Example 6 — review `uBxEe1Ujuc` (ICLR 2024)

34 units, 11 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1.	The ides of incorporating spike ODE (discrete solution) with graph ODE (continuous framework) as a unified PDE framework is novel to me.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> 2.	Extensive and thorough experiments have been conducted for model evaluation.

**Critique 3** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1.	The motivation provided in the paper is somewhat unclear. Essentially, GraphCON[1] is described as a "physically inspired" approach that formulates the stacking of GNN layers as discretized ODE governed by graph-coupled oscillators. In G-PDE, SNN act as the role of encoder within GraphCON[1] framework. However, in introduction section, we can only tell that the drawbacks of SNN arises from dealing with time-series problem. The justification why SNN should replace general GNN encoder, and their connection are both lacking.

**Critique 4** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2.	The author claims that G-PDE is intentionally designed to leverage the advantages of both spike ODE and graph ODE. However, it should be noted that the fundamental structure of G-PDE is an incremental improvement upon GraphCON[1], where the static encoder is substituted by SNN.

**Critique 5** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 3.	The paper is not easy to follow due to several reasons: (1) notation abuse; (2) lack of model details. For details and relevant questions, please refer to the Questions sections.

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4.	Based on the experimental evaluations, the improvements brought by G-PDE-2nd-order appear to be minimal across datasets such as Cora, PubMed and MNIST. Furthermore, G-PDE-1st-order even underperforms variants of GraphCON[1] in almost all scenarios. Given that G-PDE can be seen as a variant of GraphCON[1] with a sophisticated SNN encoder, there are doubts regarding the effectiveness of introducing SNNs.

**Critique 7** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 1.	Notations abuses - a.	What’s the definition of Greek letter ‘k’ right after Eq. (8) - b.	What’s the definition of ‘k’ in Eq. (10) - c.	The definition of r(s) in Eq. (15) is identical to \hat{\alpha}(N) before Eq. (10), why should we define two identical variables?

**Critique 8** — aspect `clarity`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 2.	Model details - a.	Section 4.1 only introduces the first-order G-PDE constructed by first-order SNN and first-order graph ODE. However, the variant G-PDE-1st-order in the experimental section is a combination of first-order SNN and second-order graph ODE, which is missing in the main context. Where’s the corresponding model details for this variant?

**Critique 9** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> - b.	Prop. 4.1 appears to be a straightforward formulation based on simple double integration, rather than a substantial proposition. In addition, to be more rigorous, the prerequisite of double integration exchangeability can be also included in the claim. - c.	To enhance readability, it would be helpful to provide the detailed derivation from Eq. (4) to Eq. (9)? In addition, how does the author derive the second line from the first line in Eq. (10)?

**Critique 10** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> - d.	In G-PDE-2nd-order, does SNN replace the F_{\theta} in Eq. (7)? If so, its connection towards model inputs (X^{n -1}) is entirely missing in your derivation from Eq. (9) to (15). Can you clarify how SNN calculate the spike representations using X^{n -1}?

**Critique 11** — aspect `soundness`, severity `blocking`, polarity `negative`, target `section`, actionable `True`

> - e.	Prop. 4.3 is not convincing. Per your proof in appendix, the left-hand side of equation in second line (the integration of second-order graph ODE) is incorrect due to the absence of lower & upper bound of first-order derivative (first term). Consequently, the equations in third line (e(\cdot) & h(\cdot)) are also incorrect, which makes the second-order G-PDE framework unconvincing.

`[ignored]` [1] Rusch, T. Konstantin, et al. "Graph-coupled oscillator networks." ICML 2022. ⏐ I have some concerns regarding the presentations of this papers:

## Example 7 — review `1k43kwisPy` (ICLR 2024)

18 units, 9 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> Interpretability is an important subject for improving the safety of frontier AI systems, so this work belongs in a socially important research niche.

Author response: none.

**Critique 2** — aspect `novelty`, severity `minor`, polarity `negative`, target `general`, actionable `False`

> The main contribution of showing greater interpretability with sparse features derived from the learned LLM layers is useful, although similar sparse representations have already been shown to be useful from an interpretability point of view for neural networks.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `section`, actionable `True`

> The paper claims in the abstract and conclusion that the results show *greater* monosemanticity than other methods but I do not see such comparisons in the paper (it should be in section 5.1). Either I missed something or one of the main claims is not supported.

Author response — `clarification` (units 1–2):

> Our claim that we have greater monosemanticity rests on our comparisons in section 3 to the neuron basis, random directions, and directions found by PCA and ICA. On the originality of the approach, while we agree that none of the individual elements is novel on its own, the pipeline of using a sparse autoencoder to decompose activations in a large model (section 2), which are then passed to an automatic interpretation protocol (section 3), and then analysed in terms of the circuits that build up later features (section 5) represents a meaningful step in our ability to peer into the inner worki […]

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> The authors used linear encoders (followed by a ReLU) while it is well known that this is suboptimal (the optimal encoder needs to be much more nonlinear). A useful contribution would have been to evaluate and compare different types of encoding mechanisms for obtain a sparse representation. A simple variant is to introduce hidden layers (and depth) in the encoder. There are also optimization-based encoders that work very well and are well-known for sparse coding.

Author response — `clarification` (units 3–4):

> While we didn’t show these results, preliminary experiments using multilayer encoders did not show improvements in the reconstruction/sparsity curves and manual examination of the features found showed that they tended to be less interpretable, so we abandoned this line of work at an early stage. While there are optimization-based encoders, the iterative way that the coefficients are calculated means that they take significantly longer to train, we wanted an approach that is scalable to lots of data (which we found to be key to training these models) and larger models.

**Critique 5** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `False`

> Most of the pieces in this paper (the sparse autoencoder and the interpretability score) are pre-existing, and so is the idea and demonstration that sparse features yield greater interpretability. This makes the overall level of originality and significance of the paper pretty low.

Author response: none.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> In the first paragraph of sec. 5.1, the authors talk about 'real-word features'. Please clarify what that means. If it is a "human-understable concept", one crucial problem is that such a concept (except for single-token cases studied in the paper) can be represented in many ways as a sequence of words, making any practical extension of the proposed idea (in sec 5.1) not obvious at all (or maybe not even feasible).

Author response — `clarification` (units 5–6):

> We appreciate the point about ‘real-world features’ lacking clarity, and we’ve edited the text to amend this. We think your characterization that we’re “only looking at the most interpretable features” applies only to Section 5 of the paper, and not to “the whole study”.

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> In section 5.3, it would be good to add evaluations using not just the top hidden layer (which has a very special semantics because it lives in the space of token embeddings) but also lower hidden layers

Author response — `clarification` (units 12–14):

> > In section 5.3, it would be good to add evaluations using not just the top hidden layer (which has a very special semantics because it lives in the space of token embeddings) but also lower hidden layers The section 5.3 figure (previously Figure 5, now numbered Figure 6) does show results for the lower hidden layers. Namely, the diagram is generated recursively, where we start by with a layer 5 feature and identify its most causally-relevant layer 4 features, and then for each of those layer 4 features independently find the previous causally-relevant layer 3 features, etc.

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> In section 6 about limitations, I would venture that two reasons for the poor reconstruction could be that (a) the proposed linear encoder does not have enough expressive power or (b) there exists no sparse linear basis to explain the LLM layers or (c) there is no compact natural language description for the sparse features.

Author response — `concession` (units 19–25):

> You raise two important possibilities - that this technique simply isn’t good enough to capture all of the relevant features, and that even if it were, the number of features would be impractical. The first we agree is super important - we haven’t demonstrated that we can understand a full layer by this technique - though we think that we show sufficient improvement that we should be hopeful for progress in this area, whether by improved training techniques or alternative methods of feature identification. We see the second as less of an issue. We think that looking over such a large number of […]

**Critique 9** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> Finally, the whole study is only looking at the *most interpretable* features in the lot, but in order to obtain any kind of safety guarantee, one will need to make sense of *all* the information in the LLM layers. We seem very far from that, which makes me doubt that the whole approach will ever be providing sufficient safety reassurances one day.

Author response — `concession` (units 7–9):

> In particular, in Section 3 we compute the interpretability scores on randomly chosen features, and find our average score is much higher than that of our comparison methods. Additionally, in Section 4 our selection method for features is their impact on the IOI task, not any a-priori interpretability. You’re correct to say that a true safety guarantee would only be obtained by a complete enumeration of features, though we do reconstruct the vast majority of the variance.

Author response — `concession` (units 26–29):

> Whether a regulator could have sufficient confidence in these techniques is difficult to judge - certainly such confidence would rely on advances to the technique combined with improvements in evaluations. We think that for goals like unlearning of dangerous knowledge, where you can perhaps directly remove its ability to process certain patterns, we could indeed have sufficient confidence that these capabilities are not present. We think that a bigger difficulty is to map from features to higher level behaviours - lots of dangerous behaviour won’t neatly map to single or small numbers of featu […]

`[ignored]` Please try to address the questions I raised in the previous section.

## Example 8 — review `i7mhZEhOCg` (ICLR 2024)

15 units, 7 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The paper is written well and easy to follow.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The way of using theorem to design proxy makes sense.

Author response: none.

**Critique 3** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> My main concerns are

Author response — `clarification` (units 4–10):

> However, we would like to offer some clarifications that might shed light on our approach: - Assumption 2: The “ball” is a typo, we will change it to “set” in our revised manuscript. - Assumption 3: We would like to clarify our differentiability assumption by using a rigorous definition of "differentiable almost everywhere." This means that, apart from a negligible set with zero measure, the loss function associated with candidate architectures maintains differentiability. The entire theoretical framework would still hold. In fact, the assumption is commonly implicitly assumed in the field of  […]

Author response — `clarification` (units 33–41):

> 1. **Assumption of Local Convexity**: We understand your concern that local convexity typically requires extensive training rather than being a characteristic of the initial stages or a short warm-up period. We want to clarify that, - In practice, to initialize all candidate networks, we can choose large learning rates instead of “good” learning rates. For example, in experiments in Section 4.2 and 4.3 of our revised paper, we used 0.2 and 1.0 learning rates respectively to facilitate the warm-up process. - Recent theoretical results have demonstrated that gradient descent converges at a **lin […]

**Critique 4** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> - Too strong/wrong assumptions. The foundations of their theorems, e.g., A3-A4, are rarely held for DNNs. For examples, there exists a lot operators in the search space that results in non-differentiability. Meanwhile, the Hessian matrix being positive-definitive implies the objective function as convex at least while is non-convex for Deep learning. In addition for A2, the authors used $\ell_1$-norm to bound point in a ball, which is wrong since the domain is not a ball at all under $\ell_1$ norm.

Author response: none.

**Critique 5** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Wording is a bit big. The paper is titled as information theory, yet I did not find a specific area that actually leverages it significantly, except the usage of Fisher information matrix, while is commonly used as an alternative to Hessian matrix in other literatures.

Author response — `clarification` (units 11–18):

> 2. **Title and Information Theory Application**: We appreciate your critique regarding the title's reference to information theory. The development of SiGeo was based on a significant amount of knowledge and existing work from Information theory in statistics. For example, the use of Fisher information matrix, the loss landscape, and the Fisher-Rao norm. 3. **Theoretical Necessity and Proxy Design**: Thank you for your thought-provoking feedback regarding the necessity of the theorem in our proxy design. - Indeed, the development of a new proxy might not necessarily require a theoretical frame […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Theorem is not necessary for the proxy designs. I would expect that the theorem could indeed provide some novel insights to design some unique and innovative proxy. However, the present proxy seems quite standard for me that researchers should be able to design it out without deriving theorem under strong assumptions beforehand.

Author response — `clarification` (units 19–24):

> Our approach aims to bridge this gap, offering a more flexible theoretical framework that can adapt to a broader range of architectures such as RecSys domain. - The theoretical framework has been instrumental in guiding our search for a new proxy. Initially, our project nearly discarded the Fisher-Rao norm, as it seemed to offer no substantial improvement over ZiCo. However, further theoretical exploration suggested that the Fisher-Rao norm could be effective, provided the weight is close to the local minimum of the loss function. It motivates us to reassess the Fisher-Rao norm, particularly i […]

Author response — `concession` (units 42–50):

> 2. **Theoretical Contributions**: Regarding your views on our theorems, we understand that they may not appear novel or significant as main theorems in a theoretical optimization paper. However, - It might not be a fair comparison between theoretical optimization and NAS. The theorems in NAS serve as a tool to search for better proxies; in contrast, theorems in theoretical optimization fields provide new proof techniques, optimization insights, or better rate of convergence. - Our intention was to employ these theorems in identifying the new proxies as well as the specific conditions necessary […]

**Critique 7** — aspect `significance`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> Due to the above main reasons, I could not accept the paper at the moment, though the routine of using theorem to design algorithm is what I agree on.

Author response: none.

`[ignored]` See the weakness.

## Example 9 — review `4LKj9yFaeb` (ICLR 2024)

10 units, 8 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The problem setup is commendable, addressing the important issue of super-resolution across different platforms and dynamic runtime environments.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - A variety of experiments support the claims made in the paper.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `figure_table`, actionable `False`

> - Figure 3 shows the superiority of the trade-off curve compared to conventional knowledge distillation models.

Author response: none.

**Critique 4** — aspect `clarity`, severity `minor`, polarity `positive`, target `figure_table`, actionable `False`

> - Figure 4 demonstrates operation on various architectures such as Snapdragon 845, Intel i5, and RTX 1080 Ti.

Author response: none.

**Critique 5** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `figure_table`, actionable `False`

> - Table 1 compares the results on different datasets.

Author response: none.

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> - In Figure 4 and Table 1, the performance of AdaSR is still inferior to that of MobiSR and the large SR model.

Author response — `disagreement` (units 1–2):

> **1.** The purpose of our paper is not to beat state-of-the-art, but to achieve comparative performance while being able to dynamically compress a single model according to a device’s need. We will clarify this in the paper.

**Critique 7** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The training process of AdaSR appears to be complex, making it more challenging to extend to other platforms compared to designing a bespoke SR model for the target platform.

Author response: none.

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - Why regularization for mapping layer is enough to keep the inference performance when removing the mapping layer? In my experience SR model is very sensitive to that kind of operation. Is there a related analysis or experiment?

Author response — `clarification` (units 7–13):

> **3.** Thank you for pointing this out. Correct, we also found the SR model is sensitive to changes in removal of this layer. We found that using regularization to make the mapping layer to have very small weights somewhat mitigates this issue. We still observe a drop in performance compared to having the mapping layer. However, having no regularization or too large regularization thresholds can result in a much more significant drop in performance. The threshold we used has been tuned to make the performance drop to what we feel are within acceptable limits. We will add these details in the p […]

## Example 10 — review `l7mCEb6HJx` (ICLR 2024)

19 units, 5 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> (1) The solution of applying distribution alignment for active learning is valid.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> (2) Multiple datasets including balanced and imbalanced datasets are evaluated to show the advantages of the proposed method.

Author response: none.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> (1)	It seems that the paper pose a relatively strong assumption that the data follows Gaussian mixture model (GMM) and derive the statistics from GMM. However, the author fails to show that GMM is a good model to approximate the data distribution in active learning. Actually, because of the nature of active learning, there are frequently samples from new classes that does not follow the estimated GMM model. In that case, the estimation based on GMM will not be accurate.

Author response — `new_experiment` (units 4–13):

> As the reviewer correctly points out, in early learning cycles of AL, the labeled set ($X_L$) does not generally align well with the true distribution of the entire dataset. We agree that a single GMM would not give a good estimate here. However, note that in our approach we utilize two different GMMs $\psi_L$ and $\psi_{UL}$ for $X_L$ and $X_{UL}$; we fit new GMMs $\psi_L$, $\psi_{UL}$ at every AL cycles to reflect changes in $X_L$ and $X_{UL}$ such that new $\psi_L$ can encompass samples from new classes. This is how our method can handle samples from outliers and new classes. Related to thi […]

Author response — `clarification` (units 32–39):

> Compared to other clustering algorithms such as K-means clustering, agglomerative clustering, and DBSCAN, GMM has the advantage of considering the desired number of modes along with the variance; it allows GMM to capture complex patterns in data with non-linear or non-spherical cluster shapes. Additionally, GMM is effective when clusters have overlapping boundaries due to its ability to allow for soft assignment, which takes into account ambiguity or uncertainty. Due to these advantages, GMM has been proven to be effective for the approximation of general real-world data (e.g., ImageNet, Citys […]

Author response — `clarification` (units 41–49):

> 1) Proposed likelihood informativeness ($I_{Like}$ in equation 4) can be calculated without any modification of our algorithm, even when the number of categories in $X_L$ and $X_{UL}$ differs (i.e., the number of modes in two GMMs is different). This is because we compare the likelihood score computed from each GMM. In a realistic imbalanced data setting, the likelihood difference between two GMMs ($\psi_L$, $\psi_{UL}$) is large around minor/unseen classes (i.e., large likelihood from $\psi_{UL}$ & low likelihood from $\psi_L$). Thus, the proposed informativeness score $I_{Like}$ prioritizes  […]

Author response — `clarification` (units 88–103):

> ### **`Generality/applicability of our work`** We respectfully reiterate that **our algorithm is applicable to general AL settings**, and the **use of GMM does not limit the applicability** of our work. We also do not assume any special cases. To support these, we have provided comprehensive responses, conducted extensive experiments under the same/fair setting as other AL baselines in the manuscript, and showed general superiority in various datasets and AL scenarios **(balanced, imbalanced, long-tail, new classes)**, including the ones that the reviewer requested. ### **`Open-set annotation` […]

**Critique 4** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> (2)	The novelty of the paper is limited as the distribution alignment has been widely studied in the previous work: (i)	Zhang et al “Distribution Alignment: A Unified Framework for Long-tail Visual Recognition”. CVPR 2021 (ii)	“Agreement-Discrepancy-Selection: Active Learning with Progressive Distribution Alignment”, AAAI 2021 The reference (ii) also mentioned distribution alignment with adversarial learning but under a more general setting without GMM assumption. Thus, it seems this paper is talking about an existing method under some special conditions.

Author response — `new_experiment` (units 4–13):

> As the reviewer correctly points out, in early learning cycles of AL, the labeled set ($X_L$) does not generally align well with the true distribution of the entire dataset. We agree that a single GMM would not give a good estimate here. However, note that in our approach we utilize two different GMMs $\psi_L$ and $\psi_{UL}$ for $X_L$ and $X_{UL}$; we fit new GMMs $\psi_L$, $\psi_{UL}$ at every AL cycles to reflect changes in $X_L$ and $X_{UL}$ such that new $\psi_L$ can encompass samples from new classes. This is how our method can handle samples from outliers and new classes. Related to thi […]

Author response — `clarification` (units 32–39):

> Compared to other clustering algorithms such as K-means clustering, agglomerative clustering, and DBSCAN, GMM has the advantage of considering the desired number of modes along with the variance; it allows GMM to capture complex patterns in data with non-linear or non-spherical cluster shapes. Additionally, GMM is effective when clusters have overlapping boundaries due to its ability to allow for soft assignment, which takes into account ambiguity or uncertainty. Due to these advantages, GMM has been proven to be effective for the approximation of general real-world data (e.g., ImageNet, Citys […]

Author response — `clarification` (units 41–49):

> 1) Proposed likelihood informativeness ($I_{Like}$ in equation 4) can be calculated without any modification of our algorithm, even when the number of categories in $X_L$ and $X_{UL}$ differs (i.e., the number of modes in two GMMs is different). This is because we compare the likelihood score computed from each GMM. In a realistic imbalanced data setting, the likelihood difference between two GMMs ($\psi_L$, $\psi_{UL}$) is large around minor/unseen classes (i.e., large likelihood from $\psi_{UL}$ & low likelihood from $\psi_L$). Thus, the proposed informativeness score $I_{Like}$ prioritizes  […]

Author response — `disagreement` (units 50–63):

> **High-level differences with distributional alignment (DA) methods:** With regards to Distributional Alignment (DA) methods including references (i) and (ii), note that **our contribution is not on DA itself but more on capturing distributional information via GMM, for both DA and informativeness metric design.** As illustrated in Fig. 5 of the main paper, the discriminator of traditional DA methods tend to overfit to $X_L$, thereby generating overconfident and unreliable predictions (i.e., low entropy). In contrast, we propose to feed GMM statistics to the discriminator to improve efficiency […]

Author response — `new_experiment` (units 64–74):

> - **Table 3**: Accuracy(%) on CIFAR10 | # of labeled samples | 1K    | 2K    | 3K    | 4K    | 5K    | 6K    | 7K    | 8K    | 9K    | 10K   | | Random               | 51.76 | 63.50  | 72.17 | 76.94 | 80.56 | 82.32 | 84.17 | 85.00    | 86.11 | 87.27 | | ADS                  | 56.92 | 70.18 | 77.75 | 81.78 | 83.46 | 85.83 | 87.76 | 88.74 | 89.55 | 90.30  | | DAAL                 | **58.98** | **74.15** | **79.21** | **83.42** | **85.63** | **86.75** | **88.09** | **89.39** | **90.01** | **90.87** | - **Table 4**: Accuracy(%) on CIFAR100 | # of labeled samples | 2K    | 4K    | 6K    | 8K    | 1 […]

Author response — `clarification` (units 78–82):

> The novelty of our work lies in the **incorporation of GMM into training and selection methods that aim to minimize the discrepancy between $X_L$ and $X_{UL}$,** thereby mitigating the risk of overfitting to small $X_L$. Particularly, our approach involves the **estimation of latent distributions of $X_L$ and $X_{UL}$ using GMM**, a novel feature not observed in existing AL works. GMM is an useful tool for active learning since it can estimate the original data distribution even with the absence of certain categories in $X_L$, by leveraging the rich data in $X_{UL}$. Our proposed GMM-aided met […]

Author response — `clarification` (units 88–103):

> ### **`Generality/applicability of our work`** We respectfully reiterate that **our algorithm is applicable to general AL settings**, and the **use of GMM does not limit the applicability** of our work. We also do not assume any special cases. To support these, we have provided comprehensive responses, conducted extensive experiments under the same/fair setting as other AL baselines in the manuscript, and showed general superiority in various datasets and AL scenarios **(balanced, imbalanced, long-tail, new classes)**, including the ones that the reviewer requested. ### **`Open-set annotation` […]

Author response — `clarification` (units 104–111):

> We would like to highlight that **the key philosophy of our work does not lie in distributional alignment (DA)**. DA (in Section 3.4) is just one of our components, and our contribution spans from GMM modeling (in Section 3.2) to regularization (in Section 3.3) and informativeness metrics (in Section 3.5), encompassing the entire AL scheme. **The core of this work is the use of GMM to better capture the dataset distribution and build a unified framework** for "distribution-aware AL" that facilitates effective regularization, effective DA-based learning, and effective informativeness-based samp […]

**Critique 5** — aspect `novelty`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> As metioned in the weakness, the fundament problem of this paper is that it is merely a special case of a solved general problem, which makes the novelty of the paper very limited. Without detailed discussion of the difference from the existing work as listed, the novelty of the paper does not stay on a safe ground. Moreover, the author needs to show why the GMM model is a good approximation of the data distribution in active learning as there can be many outliers and unknown classes. How about if the data is a long-tail distribution. The assumption of the paper is a bit too strong. Last but not least, the paper did not any new insights of this field. The results are merely a small extension and special cases of existing approaches.

Author response — `new_experiment` (units 4–13):

> As the reviewer correctly points out, in early learning cycles of AL, the labeled set ($X_L$) does not generally align well with the true distribution of the entire dataset. We agree that a single GMM would not give a good estimate here. However, note that in our approach we utilize two different GMMs $\psi_L$ and $\psi_{UL}$ for $X_L$ and $X_{UL}$; we fit new GMMs $\psi_L$, $\psi_{UL}$ at every AL cycles to reflect changes in $X_L$ and $X_{UL}$ such that new $\psi_L$ can encompass samples from new classes. This is how our method can handle samples from outliers and new classes. Related to thi […]

Author response — `clarification` (units 32–39):

> Compared to other clustering algorithms such as K-means clustering, agglomerative clustering, and DBSCAN, GMM has the advantage of considering the desired number of modes along with the variance; it allows GMM to capture complex patterns in data with non-linear or non-spherical cluster shapes. Additionally, GMM is effective when clusters have overlapping boundaries due to its ability to allow for soft assignment, which takes into account ambiguity or uncertainty. Due to these advantages, GMM has been proven to be effective for the approximation of general real-world data (e.g., ImageNet, Citys […]

Author response — `clarification` (units 41–49):

> 1) Proposed likelihood informativeness ($I_{Like}$ in equation 4) can be calculated without any modification of our algorithm, even when the number of categories in $X_L$ and $X_{UL}$ differs (i.e., the number of modes in two GMMs is different). This is because we compare the likelihood score computed from each GMM. In a realistic imbalanced data setting, the likelihood difference between two GMMs ($\psi_L$, $\psi_{UL}$) is large around minor/unseen classes (i.e., large likelihood from $\psi_{UL}$ & low likelihood from $\psi_L$). Thus, the proposed informativeness score $I_{Like}$ prioritizes  […]

Author response — `disagreement` (units 50–63):

> **High-level differences with distributional alignment (DA) methods:** With regards to Distributional Alignment (DA) methods including references (i) and (ii), note that **our contribution is not on DA itself but more on capturing distributional information via GMM, for both DA and informativeness metric design.** As illustrated in Fig. 5 of the main paper, the discriminator of traditional DA methods tend to overfit to $X_L$, thereby generating overconfident and unreliable predictions (i.e., low entropy). In contrast, we propose to feed GMM statistics to the discriminator to improve efficiency […]

Author response — `new_experiment` (units 64–74):

> - **Table 3**: Accuracy(%) on CIFAR10 | # of labeled samples | 1K    | 2K    | 3K    | 4K    | 5K    | 6K    | 7K    | 8K    | 9K    | 10K   | | Random               | 51.76 | 63.50  | 72.17 | 76.94 | 80.56 | 82.32 | 84.17 | 85.00    | 86.11 | 87.27 | | ADS                  | 56.92 | 70.18 | 77.75 | 81.78 | 83.46 | 85.83 | 87.76 | 88.74 | 89.55 | 90.30  | | DAAL                 | **58.98** | **74.15** | **79.21** | **83.42** | **85.63** | **86.75** | **88.09** | **89.39** | **90.01** | **90.87** | - **Table 4**: Accuracy(%) on CIFAR100 | # of labeled samples | 2K    | 4K    | 6K    | 8K    | 1 […]

Author response — `clarification` (units 78–82):

> The novelty of our work lies in the **incorporation of GMM into training and selection methods that aim to minimize the discrepancy between $X_L$ and $X_{UL}$,** thereby mitigating the risk of overfitting to small $X_L$. Particularly, our approach involves the **estimation of latent distributions of $X_L$ and $X_{UL}$ using GMM**, a novel feature not observed in existing AL works. GMM is an useful tool for active learning since it can estimate the original data distribution even with the absence of certain categories in $X_L$, by leveraging the rich data in $X_{UL}$. Our proposed GMM-aided met […]

Author response — `clarification` (units 88–103):

> ### **`Generality/applicability of our work`** We respectfully reiterate that **our algorithm is applicable to general AL settings**, and the **use of GMM does not limit the applicability** of our work. We also do not assume any special cases. To support these, we have provided comprehensive responses, conducted extensive experiments under the same/fair setting as other AL baselines in the manuscript, and showed general superiority in various datasets and AL scenarios **(balanced, imbalanced, long-tail, new classes)**, including the ones that the reviewer requested. ### **`Open-set annotation` […]

Author response — `clarification` (units 104–111):

> We would like to highlight that **the key philosophy of our work does not lie in distributional alignment (DA)**. DA (in Section 3.4) is just one of our components, and our contribution spans from GMM modeling (in Section 3.2) to regularization (in Section 3.3) and informativeness metrics (in Section 3.5), encompassing the entire AL scheme. **The core of this work is the use of GMM to better capture the dataset distribution and build a unified framework** for "distribution-aware AL" that facilitates effective regularization, effective DA-based learning, and effective informativeness-based samp […]

## Example 11 — review `JBVfks1AIY` (ICLR 2024)

18 units, 6 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> Given its efficiency, secure aggregation is a natural candidate for privacy preserving federated learning.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> Therefore, exploring ways to integrate this primitive to VFL is an interesting research direction.

**Critique 3** — aspect `novelty`, severity `blocking`, polarity `negative`, target `section`, actionable `True`

> The paper has the following weaknesses: 1- Lack of novelty: the contribution presents a combination of VFL and Secure Aggregation. Even if I think that this is a nice idea, I do not see sufficient novelty on the contribution. Combining Secure Aggregation a FL setting without other added value is quite common in literature of privacy preserving techniques. Substantial parts of Section 3, 4 and 5 of the main text are devoted to explain already existent ideas present in the (already classic) Secure Aggregation technique of (Bonawitz, 2017). This kind of content is more appropriate to preliminary sections or appendices rather than main contribution sections.

**Critique 4** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2- Significance: the presented protocol shows good accuracy and communication cost, but it is unclear how much privacy is offered. Since the Secure Aggregation layer only protects an intermediate output, it is not clear how much information is disclosed. 3- Soundness:

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 3a- Insufficient security claims: the security analysis of a novel technique requires a more elaborate treatment, even in in the absence of no actively malicious adversaries (see for example [1] on how to prove security properties of multiparty protocols). Such analysis is present in (Bonawitz, 2017), but not in Section 5 + Appendix 2 of this contribution.

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 3b- Poor evaluation: it is not clear if the comparison with other privacy preserving techniques is fair. A fair comparison should also show how much privacy is offered by each technique. Some techniques might be more expensive, but they could also provide more privacy.

`[ignored]` [1] https://eprint.iacr.org/2016/046 ⏐ Please address the significance (point 2) and evaluation (3b) points described above.

## Example 12 — review `bcHll1OPPx` (ICLR 2024)

16 units, 4 critiques, 5 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The proposed paradigm is interesting and might bring new insight to the ML community.

**Critique 2** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> A significant weakness of this paper is that its theoretical analyses are limited. Specifically, the theoretical results are highly dependent on the strong assumption (i.e., Gaussian distribution), which is insufficient for a model. It is better to see a result related to the underlying model parameters or training process.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> Another concern is the consistent attack manner for the adversarial robustness. In tab.5, are the models trained by ERM/DuRM attacked by their corresponding training loss? If true, what will happen if we use ERM+PGD/FGSM for DuRM? Besides, parameter-free AutoAttack should be further considered.

**Critique 4** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> Moreover, one of the effective paradigms is AUC optimization [1,2,3], which is distribution-insensitive concerning long-tailed recognition. In light of this, how is the performance of DuRM compared with AUC? Then, can we apply a similar dummy trick to such a pairwise paradigm?

`[ignored]` Ref: ⏐ [1] AUC Maximization in the Era of Big Data and AI: A Survey. ⏐ [2] When AUC meets DRO: Optimizing Partial AUC for Deep Learning with Non-Convex Convergence Guarantee. ⏐ [3] Learning with Multiclass AUC: Theory and Algorithms. ⏐ Please see the Weaknesses above.

## Example 13 — review `tQFPrczjvM` (ICLR 2024)

18 units, 7 critiques, 5 ignored, 1 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> + Very intriguing to see emergent perceptual grouping from ANNs trained on unsupervised image reconstruction objectives.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> Super interesting perspective that latent neuronal noise could lead to learning good gestalt priors. + The approach is very straightforward and easy to understand. I think this simplicity is a big strength of the proposed work.

Author response: none.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> + Good Gestalt datasets are also a nice addition to the contributions from this work, I hope this benchmark can serve as a good way to measure perceptual grouping abilities of models in the community.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> + I like the additional analyses performed on understanding how latent noise parameters affects emergent grouping.

Author response: none.

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The focus of the paper feels a bit narrow in terms of the architecture / learning objective. Is there something special about VAEs trained with ELBO + LNS that makes them develop emergent grouping, or does LNS generalize across architectural choices and learning rules (say, diffusion-based or adversarial generative models)? Adding a discussion on this would add more value to the submission

Author response — `clarification` (units 10–16):

> Thank you for the suggestion. We agree this would add value to the paper, and have added a section in Appendix A.1.5 that is referred to in Section 2 of the main text. The section reads: “In this work, we have focused primarily on the Variational Autoencoder (VAE) in lieu of other generative models, such as Diffusion models (Sohl-Dickstein et al., 2015; Rombach et al., 2022) or Adversarial Generative (Goodfellow et al., 2014; Creswell et al., 2018) models. There are two primary reasons behind this choice: 1) The VAE formulation allows us to neatly follow the argumentation in Zietlow et al. (20 […]

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - I feel that GG's difficulty could be significantly improved by adding more distractors and/or noise to the background of images. Although the current emergence of grouping looks interesting, I would be even more surprised if the model is learning to discount background noise in its presence, i.e., currently the dataset makes figure-ground organization too simple by providing a largely low-frequency background and I believe GG can be solved merely by using simple rules on low-level feature detectors.

Author response — `new_experiment` (units 19–22):

> In a much earlier version of the work, we had simpler versions of some of the GG datasets, which indeed were somewhat too easy. To remedy this, we made the tasks more difficult (e.g., we increased the frequency of the Illusory Occlusion’s background stripes), and added more GG datasets that combine different challenges (e.g., long-range integration of contours in Kanizsa, and inference of objects of the same color in Proximity). The difficulty in our datasets does not come from the individual images themselves per se, but rather from the qualitatively substantial generalization gap between the […]

Author response — `clarification` (units 39–55):

> These results are now reported in the main text in Table 1. While quantitative results for the Genesis model look impressive, a further investigation in Appendix C1 reveals that the decent quantitative performance is driven by good pixel-level predictions in nearly all cases, and not actual Gestalt grouping phenomena (Figure 10). Indeed, the model appears to primarily follow pixel-level information present in the input. To verify that this result was not caused by a mistake in our implementation (such as a trivial failure in convergence), we followed the official implementation of Genesis and  […]

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> This makes the paper weaker due to the absence of relevant baselines other than the VAE-based ones currently reported in this version of the paper.

Author response — `new_experiment` (units 25–38):

> Thank you for this suggestion, with which we agree. We now report results for two additional SOTA/near-SOTA models: Genesis and Genesis-v2 (Engelcke et al., 2020; 2022). | Model     | Kanizsa           | Closure           | Continuity        | Proximity         | Gradient Occ.     | Illusory Occ.     | | AE        | 0.859 ± 0.008     | 0.766 ± 0.008     | 0.552 ± 0.008     | **0.996\*** ± 0.001 | 0.926 ± 0.009     | **0.994\*** ± 0.002 | | VAE       | **0.871** ± 0.005 | **0.795** ± 0.009 | 0.593 ± 0.012     | 0.943 ± 0.010     | 0.918 ± 0.002     | 0.974 ± 0.003     | | AE Rec.   | 0.246 ± 0. […]

Author response — `clarification` (units 60–62):

> To show that low-level statistics do not indeed drive the emergence of perceptual grouping, we now report two additional SOTA/near-SOTA baseline models that achieve good reconstruction error, and yet fail at the desired perceptual grouping tests even when they get pixel value properties correct (e.g., exact position of elements). >Adding stronger baselines such as the ones the authors have mentioned in related work will help improve my score further. Thank you again for the suggestion - we have addressed this above.

`[ignored]` - The authors have covered a variety of unsupervised object discovery approaches such as Slot Attention, Complex-valued autoencoders in related work but have not performed a direct comparison to these baselines in their reported experiments. ⏐ - Can the authors please comment on whether they experimented with harder versions of GG? ⏐ Here are a few potential options: (1) Change the size of the square/circle between train and test splits for Kanisza Squares, Closure, Continuity, (2) Use different rotations (without overlap between train and test splits) of the Kanisza squares / Closure squares, (3) Use different colors / textures as backgrounds in all tasks. ⏐ Any modification of the dataset in the spirit of the modifications suggested here will further strengthen the message that simple low-level statistics don't drive the emergence of perceptual grouping. ⏐ - Adding stronger baselines such as the ones the authors have mentioned in related work will help improve my score further.

`[post-rebuttal, set aside]` Overall, the strengths of this work marginally outweigh the weaknesses mentioned above, I would be inclined to further improving my score provided the authors convincingly rebut my concerns about this work.

## Example 14 — review `lOsstp42e8` (ICLR 2024)

7 units, 7 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper propose a generative statistical model such that recursive marginalization of athe model is in tight equivalence with the calculations performed by inference in a vanilla transformer.

Author response: none.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> This idea can provide a foundation for the design of new inductive bias into transformers, which is inductive transformers.

Author response: none.

**Critique 3** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> It's very hard to understand the equivalence between the proposed generative model and the vanilla transformer.

Author response — `concession` (units 10–11):

> --> We completed a lot of edits to hopefully make the paper more accessible   We agree that it would have been nice to be able to include (a) a high-level figure for the production and statistical model without all of the factor graph details, (b) a comparison table with more space to explain the comparison of each layer type (c ) the factored probability distribution for vanilla and for inductive transformers. (The factored probability distributions for the vanilla and for inductive transformers are actually identical to one another, so it would be the same equation twice.)  In the archival v […]

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. It's difficult to understand the equivalence between the generative model and vanilla transformer, is there more formal way to prove the equivalence?

Author response — `new_experiment` (units 14–19):

> --> One potential way we thought of to show this in more formal detail is with the code. In our code, we show the pytorch calculations for our layers and we bring in the Harvard code for the "annotated transformer" which is an implementation of the vanilla transformer. This makes the the comparison very apples-to-apples and the equivalence becomes readily apparent. --> Another way is to see that the factorization of the probability distribution is identical. --> Between the higher level representation of the probability notation and the lowest level which is the code, we have not identified an […]

**Critique 5** — aspect `clarity`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 2. Can you provide more explanations on the "concept" meaning in both the generative model and vanilla transformer.

Author response — `clarification` (units 21–21):

> --> In response to your comment, we added this explanation: "We define a ``concept'' as a sub-network that can generate many different but synonymous token sequences (e.g. ``tiny canine'')."

**Critique 6** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 3. What's the time complexity of the propose generative model's training/inference process?

Author response — `clarification` (units 23–24):

> --> In response to your comment, we added this explanation: "The inductive transfomer is a more focused version of the vanilla transformer, and will therefore generalize similarly. The time and space complexity is identical."

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 4. Is it possible to apply the proposed generative model on large scale dataset?

Author response — `concession` (units 26–36):

> -->  Two thoughts here: (1) We agree that a key next step will be to scale this up! That said, we see it as future work. We intend this first paper to be analogous to theoretical physicists proposing a new mathematical model with simulations that show that the math works. Future work then typically involves a larger team of experimentalists. We have now joined with an experimental team to do just that, but we would humbly submit that this paper represents a publishable contribution in terms of new ideas, novel mathematical derivations, and code that implements the model and runs. (2) Scaling l […]

## Example 15 — review `O71GilBPCN` (ICLR 2024)

24 units, 11 critiques, 3 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper makes a notable attempt to tackle the shortcomings of bisimulation metrics in sparse reward settings by integrating a transformer-based dynamics model.

Author response — `clarification` (units 151–161):

> Other issues** (1) MICo or SimSR don't call themselves "bisimulation" We appreciate the reviewer's perspective on the term 'bisimulation' and understand that it may be perceived as having strict limitations, potentially leading to disagreements. Our intention is to highlight that the motivation of our work is from bisimulation-like objectives (or bisimulation-like measurements), rather than the specific stricted "bisimulation metric". We will modify these terms in the camera-ready version to ensure clarity and precision. (2) $\kappa$ is mentioned in Equation 3 but defined after Equation 5 We f […]

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The adoption of block-wise masking as a strategy for sampling stochastic dynamics is an interesting approach.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> Empirically, the method appears to offer improvements over existing techniques, as demonstrated in the results section which features performance gains across Atari, DMC, and DMC with distraction.

Author response: none.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> The paper aims to address two challenges of bisimulation metrics: the reliance on Gaussian distribution for modeling and the issue of uninformative rewards. However, the justification for how the proposed ReBis method successfully overcomes these challenges remains unconvincing.

Author response — `clarification` (units 95–99):

> About  Deterministic Assumption** We concur with the reviewer's suggestion that our assumption should also include deterministic policy instead of only considering deterministic transition. Our experiments on Atari games, with the use of Rainbow, to some extent, reflects the experiments under this assumption, as illustrated in [1]. We sincerely thank the reviewer for their assistance in enhancing the quality of our paper. We have revised  relevant descriptions in our manuscript to ensure the accuracy and consistency of our derivations.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> The paper's method of using block-wise masking observation to simulate the sampling of stochastic dynamics is not fully explained. Various other techniques, such as random cropping as in DrQ, employing Dropout layers, or introducing noise to weights or latent features, could potentially serve a similar purpose. A detailed comparison of these methods within the experimental section would be beneficial for substantiating the need for block-wise masking.

Author response — `clarification` (units 47–53):

> Explanation of "multi-modals".** "Multi-modals" here refers to the presence of multiple modes in the behavior or decision-making patterns of an agent. **5. Description of the blue color in Tables 1 and 2.** The blue color in these tables is specifically used to highlight tasks that operate under sparse reward conditions. These tasks include Ball in Cup, Catch, Cartpole Swingup Sparse, Finger Turn Easy/Hard, and Pendulum Swingup. In the newly uploaded manuscript, we added the corresponding explanation.

Author response — `disagreement` (units 55–65):

> Explanation of Block-wise Masking.** We would like to clarify that the use of block-wise masking is not to simulate the sampling of stochastic dynamics as the reviewer assumed. As we have  discussed in Section 4, we consider the environment nearly deterministic, we employee the transformer as a deterministic dynamics model. Besides, block-wise masking in our approach does not  serve as the sampling of stochastic dynamics, it in fact is used to get rid of spatio-temporal redundance of the observations, coupled with bisimulation-based objective. Intuitively, we don't think random cropping, drop- […]

Author response — `new_experiment` (units 103–115):

> Alternation of Block-wise Masking** We argue once again that the primary purpose of block-wise masking is NOT to introduce randomness for exploration or to enhance sample and computational efficiency. Instead, its main role is to address the inherent spatial (and temporal) redundancy in pixel space. As noted in MAE[4], a useful approach in computer vision is 'masking a very high portion of random patches,' which effectively reduces redundancy and poses a challenging self-supervised task requiring a comprehensive understanding beyond mere low-level image statistics. This concept is echoed in re […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> Regarding the challenge of sparse rewards, the explanation of how ReBis overcome this issue is not adequately addressed. The paper should provide a clearer rationale for why its methods would be more effective in such environments.

Author response — `new_experiment` (units 67–75):

> The explanation of how ReBis overcome the challenge of sparse rewards.** ReBis overcomes the challenge of sparse rewards by employing an asymmetrical architecture in its dynamics model. As mentioned in our paper, particularly in Theorem 4, we acknowledge that bisimulation tends to collapse in sparse reward environments. However, it's important to note that agents can still interact with these environments, which means the agent can still learn control relevant informations from the interactions. This understanding forms the primary motivation behind our work with ReBis. In the framework of ReB […]

Author response — `clarification` (units 140–149):

> Concern on Theorem 5** We apologize for the overclaim in our last reply of the sentence "ReBis overcomes the challenge of sparse rewards by ...". We meant to say ReBis can alleviate the representation collapse issues in sparse reward environments. In our context, the term 'asymmetric' refers not only to the network architecture, such as in siamese networks, but also encompasses the asymmetry in inputs. This is implemented by applying block-wise masking to one branch with the online encoder, while the other branch with the momentum encoder remains unmasked. We underscore that block-wise masking […]

**Critique 7** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> The paper’s claim to novelty largely rests on the application of a transformer dynamics model, but this alone does not present a compelling case for novelty. The absence of a thorough comparative analysis, especially in the ablation studies, against non-transformer or non-sequential architectures, diminishes the strength of the argument for the proposed method’s innovation. Furthermore, the paper borrows heavily from prior work for various aspects, such as the masked observation approach, the metric used, and the theoretical framework, which detracts from the original contribution.

Author response — `clarification` (units 77–84):

> Concern about the novelty of our paper.** While our model utilizes structural components that are commonly recognized in the field, the true claim of our research lies in our unique application of these elements. We've conducted an in-depth examination of bisimulation within the context of reinforcement learning, with a specific focus on its limitation in complex environments with sparse rewards. Our main contribution is the development of a straightforward yet highly effective approach, designed specifically to address the limitations we identified in traditional bisimulation methods. We have […]

**Critique 8** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> The theoretical foundation of the paper also shows weaknesses.

Author response — `clarification` (units 6–21):

> **1. Explanation of Definition 1.** It is important to note that the term 'bisimulation-based' does not necessarily imply the inclusion of the Wasserstein distance. The bisimulation-based methods, such as MICo or SimSR, also do not incorporate the Wasserstein distance. Instead, they employ independent coupling as an alternative to mitigate the computational cost associated with the Wasserstein distance. Besides, back to the early developments in bisimulation, as illustrated in [1, 2], they originally presented both Wasserstein-based and Total-Variation-based objectives. Therefore, ‘bisimulatio […]

Author response — `clarification` (units 151–161):

> Other issues** (1) MICo or SimSR don't call themselves "bisimulation" We appreciate the reviewer's perspective on the term 'bisimulation' and understand that it may be perceived as having strict limitations, potentially leading to disagreements. Our intention is to highlight that the motivation of our work is from bisimulation-like objectives (or bisimulation-like measurements), rather than the specific stricted "bisimulation metric". We will modify these terms in the camera-ready version to ensure clarity and precision. (2) $\kappa$ is mentioned in Equation 3 but defined after Equation 5 We f […]

**Critique 9** — aspect `related_work`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. The Definition 1 provided is mislabeled as "bisimulation-based" since it lacks the Wasserstein distance. It defines metric like MICo or SimSR but misses an expectation operator in front of $\bar{d}$.

Author response — `clarification` (units 6–21):

> **1. Explanation of Definition 1.** It is important to note that the term 'bisimulation-based' does not necessarily imply the inclusion of the Wasserstein distance. The bisimulation-based methods, such as MICo or SimSR, also do not incorporate the Wasserstein distance. Instead, they employ independent coupling as an alternative to mitigate the computational cost associated with the Wasserstein distance. Besides, back to the early developments in bisimulation, as illustrated in [1, 2], they originally presented both Wasserstein-based and Total-Variation-based objectives. Therefore, ‘bisimulatio […]

**Critique 10** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. Theorem 2 and 3 for bisimulation metric, originated from (Kemertas & Aumentado-Armstrong, 2021), cannot be directly applied to the metric defined in the paper because their proofs rely on the Wasserstein distance, which is absent from the paper's metric.

Author response — `clarification` (units 6–21):

> **1. Explanation of Definition 1.** It is important to note that the term 'bisimulation-based' does not necessarily imply the inclusion of the Wasserstein distance. The bisimulation-based methods, such as MICo or SimSR, also do not incorporate the Wasserstein distance. Instead, they employ independent coupling as an alternative to mitigate the computational cost associated with the Wasserstein distance. Besides, back to the early developments in bisimulation, as illustrated in [1, 2], they originally presented both Wasserstein-based and Total-Variation-based objectives. Therefore, ‘bisimulatio […]

Author response — `clarification` (units 22–30):

> Explanation of Theorem 2 and 3.** We're grateful for the chance to elucidate our theoretical framework and how it aligns with our definitions. In our paper, we operate under the assumption that the dynamics in real-world environments are nearly deterministic. Therefore, our focus is primarily on deterministic settings. Specifically, we assume that for any latent state  $s\in\mathcal{S}$, $a \in \mathcal{A}$, there exists a unique $\kappa(s,a)\in\mathcal{S}$ such that $P_{s}^a(\kappa(s,a))=1$. With this assumption in place, we show that the equivalence between the bisimulation measurement $d(\k […]

**Critique 11** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> The authors need to develop new proofs that are pertinent to their specific metric definition. 1. Theorem 4 does not seem intuitive if the metric includes an expectation operator. (Castro et al., 2021) mentioned it is Łukaszyk–Karmowski distance with non-zero distance. The transition from Equation (15) to Equation (16) in the proof is unclear and requires further clarification.

Author response — `clarification` (units 6–21):

> **1. Explanation of Definition 1.** It is important to note that the term 'bisimulation-based' does not necessarily imply the inclusion of the Wasserstein distance. The bisimulation-based methods, such as MICo or SimSR, also do not incorporate the Wasserstein distance. Instead, they employ independent coupling as an alternative to mitigate the computational cost associated with the Wasserstein distance. Besides, back to the early developments in bisimulation, as illustrated in [1, 2], they originally presented both Wasserstein-based and Total-Variation-based objectives. Therefore, ‘bisimulatio […]

Author response — `clarification` (units 33–40):

> We apologize for the typo error that we made. The right-hand-side of Equation 16 in our previous manuscript should be $\max_{x,y}|R_x^\pi-R_y^\pi|$ instead of $|r_{s_i}^{\pi} - r_{s_j}^{\pi}|$. We have fixed this error in new manuscript. We also provide a more detailed derivation in the appendix now. Regarding Theorem 4, our intention was to address the challenges posed by sparse reward environments when using bisimulation. MICo distance is a special case, inherently possesses a non-zero distance. However, as we described in the beginning of Section 3, we "primarily focus on a cosine distance- […]

`[ignored]` 1. Could the authors clarify the term "multi-modals" within the paper? ⏐ 1. In Tables 1 and 2, the blue color is not described. ⏐ What does it represent in the context of these tables?

## Example 16 — review `2XoYZRGe3f` (ICLR 2024)

15 units, 12 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> (1) Significance of the problem: The study addresses a critical issue in real-world applications.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> (2) Extensive experimental validation: The authors back their proposal with an extensive set of experiments.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> (3) Theoretical foundation: The inclusion of theoretical analysis strengthens the credibility of the proposed method.

**Critique 4** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> (1) Unavailable code link: Considering the importance of practical implementation, it would greatly benefit the readers if the authors could provide access to the code repository.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> (2) Lack of experiment details: A more comprehensive discussion of the experiments, including a breakdown of evaluation metrics and insights into why ACPO demonstrates strong generalizability, would enhance the clarity of the findings.

**Critique 6** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> (3) Ambiguous conclusion statement: The authors claim that since the algorithm processes decomposition characteristics, it is well-suited for expansion for multi-agent systems. Clarification is needed regarding the complexity of the proposed method in relation to multi-agent systems. It would be helpful to know if the proposed method incurs high sampling or computational complexity and to understand the implications for multi-agent systems.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> (4) Confusing experiment results: The safety performance of ACPO is not good enough.

**Critique 8** — aspect `clarity`, severity `minor`, polarity `neutral`, target `section`, actionable `True`

> (1) Practical implementation: Could you elaborate on how the penalty coefficient sigma in Theorem 2 is selected?

**Critique 9** — aspect `related_work`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> (2) Comparison with related methods: It would be beneficial if the authors discussed similar methods that tackle the conversion of hard safety constraints into soft constraints.

**Critique 10** — aspect `clarity`, severity `minor`, polarity `neutral`, target `section`, actionable `True`

> (3) Definition clarification: What does “security RL” refer to in the conclusion?

**Critique 11** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> (4) Adaptability and comparisons: Can you elaborate on the adaptability of the proposed method to off-policy methods and whether any comparisons were made with relevant off-policy baselines?

**Critique 12** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> (5) Safety performance discussion: Could you provide further insights into the safety performance depicted in Figures 2 and 3, especially in instances where the ACPO method struggles to converge to the target cost threshold in tasks like Safety-Swimmer, CarGoal, and PointGoal?

`[ignored]` (See my question 5)

## Example 17 — review `CH5YCwswGn` (ICLR 2024)

15 units, 7 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. This paper is well written and well organized.

Author response: none.

**Critique 2** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. Distinct from other autoregressive equivariant generative models, the proposed approach employs higher-degree E(3) equivariant features. This enhances the flexibility in representing probability distributions. 3. In terms of performance, the proposed method is on par with existing diffusion models. However, it boasts a significant advantage in computational efficiency, as current diffusion models rely on fully-connected graphs that may pose scalability challenges.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. The manuscript employs a coarse discretization of the radial component for predicting the relative positions of subsequent atoms, a limitation acknowledged in the conclusion section. It would be intriguing to explore the effects of employing a finer discretization. Specifically, would such a refinement significantly compromise the computational efficiency of the method? Furthermore, could this potentially improve the distribution of bond lengths?

Author response — `new_experiment` (units 4–10):

> > would such a refinement significantly compromise the computational efficiency of the method? We answer exactly this question below! The following is the approximate training speed of the model for a batch size of $16$ graphs, as measured on a single NVIDIA RTX A5000 GPU: | Number of Radii| $32$ | $64$ | $128$ | $256$ | |  Approximate Training Speed (steps/second)     |   $16.5$   | $13.8$ | $10.1$ | $6.6$ | So while there definitely is a tradeoff, it does not seem to be a major bottleneck. We are currently exploring the effect of the radial discretization on the bond length metrics.

**Critique 4** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 2. n Equation (1), would it be more precise to describe this as a conditional distribution of $f$ given $S$? does the embedder at $f_{n+1}$ use both $h^{\text{position}}$ and $h^{\text{focus}}$?

Author response — `clarification` (units 11–14):

> > In Equation (1), would it be more precise to describe this as a conditional distribution of $f$ given $S$? Hmm, it is just a matter of notation, whether to represent it as $p(f | S)$ or $p(f; S)$. In any case, the fragment $S$ is given at training time, but is sampled from the model's predictions at inference time. So, both options are okay.

Author response — `clarification` (units 15–18):

> > does the embedder at $f_{n + 1}$ use both $h^\text{position}$ and $h^\text{focus}$? For predicting the focus and the target atom type, $h^\text{focus}$ is used. For predicting the positions, $h^\text{position}_f$ is used. The two embedders never interact with each other directly.

**Critique 5** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 3. Typo: In the final equation on page 4, the term should correctly be denoted as $p^{\text{position}}$.

Author response — `clarification` (units 19–21):

> > Typo: In the final equation on page 4, the term should correctly be denoted as $p^\text{position}$. We believe this formulation is correct: we are parametrizing the logits $f^\text{position}$ of the distribution $p^\text{position}$. The logits are then exponentiated to get the distribution, as described in Section 3.3.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 4. On the first line of page 6, the mechanism for predicting the STOP condition remains unspecified. Could you elaborate on this aspect?

Author response — `new_experiment` (units 22–25):

> > On the first line of page 6, the mechanism for predicting the STOP condition remains unspecified. Could you elaborate on this aspect? Great find! We have added this to Section 3.3 under Equation 5.

**Critique 7** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 5. Typo: The first equation in Section 2 misses a translation $T$.

Author response — `clarification` (units 26–28):

> > Typo: The first equation in Section 2 misses a translation $T$. The features we look at here are invariant under translation. We have clarified this in the text below.

`[ignored]` Please refer to the previous section

## Example 18 — review `cvsbsLFcXs` (ICLR 2024)

13 units, 7 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> ++ The paper attempts to address an important problem of cell type identification.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> ++ The experimental results seem to be promising and useful in practice.

Author response: none.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> -- Essential technical details of the digital twin (i.e. the neural network used to predict the neuron responses) are missing. From the text, it is not clear how the digital twin is obtained and how it will affect the optimisation of MDS.

Author response — `clarification` (units 6–8):

> - a. The models are convolutional neural networks in the well-established core-readout architecture (Klindt et al., NeurIPS 2017; Lurz et al., ICLR 2021) trained from scratch (no pre-training) on neural responses to images/videos. The detailed parameters vary from dataset to dataset and have been optimized by the authors of previous papers to maximize the predictive power of the models on the respective datasets (mouse retina: Höfling et al. bioRxiv 2022; macaque V4: Willeke et al, bioRxiv 2023; marmoset retina: work soon to be submitted). We will include an appendix that describes the technic […]

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> -- It is stated in the paper "We optimized the stimulus by gradient-ascent, using the SGD optimizer with a learning rate of 100". What are the learnable parameters during this optmization? It is unusual to use such a large value of learning rate.

Author response — `clarification` (units 9–11):

> - b. The learnable parameters are the pixel values of the maximally discriminable images/video segments, while the network weights are treated as fixed and not being optimized. The high learning rate is typical for pre-image search problems like activity maximization and has been selected as the best one from within the range we explored (10^-3 to 10^3). We will add this information to the paper.

**Critique 5** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> -- The statement is ambiguous "After each step we renormalize the video snippet to a L2 norm of 30 and clamp ... into ranges of [-0.913, 6.269] and [-0.654, 6.269]". What does it mean by "a L2 norm of 30"? What are the ranges from?

Author response — `clarification` (units 12–18):

> - c. The normalization is done because neural responses usually increase with the contrast of the input, but the monitor that displayed the digital twin’s training videos has a finite dynamic range. If we had not constrained the overall energy of the stimuli, the optimized MDS would show an unrealistically high contrast that cannot be displayed by the monitor. This procedure is typical in activity maximization settings (e.g. Walker et al., Nature Neuroscience 2019; Hoefling et al., bioRxiv 2022; Willeke et al, bioRxiv 2023). Even with constraining the L2 norm, single pixels can still exceed th […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. Where does the digital twin (i.e. the neural network) come from? Is it a pre-trained neural network?

Author response — `clarification` (units 19–20):

> 1. The digital twin models were trained from scratch on neural responses by authors of previous papers. See answer to a.

**Critique 7** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 2. How are the results/performance sensitive to the hyper-parameters and initializations?

Author response — `new_experiment` (units 21–32):

> 2. The three hyperparameters of the method are learning rate, number of initial clusters, and temperature (Eq. 1). The learning rate affects primarily the runtime of the optimization procedure, not the resulting optimal stimuli. We verified that the results are robust with respect to different initializations and number of initial clusters (mouse retina: adjusted rand index ARI=0.87 (page 7) and compare Figure 2A to Appendix Figure 7; marmoset retina: ARI=0.49 (p. 8) and compare Figure 4A to Appendix Figure 8; macaque V4: ARI=0.53 (p. 8) and compare Figure 5 to Appendix Figure 9). The temperat […]

Author response — `clarification` (units 37–49):

> |  51.2       |  0.68      | We found a broad, flat objective optimum (bold-face numbers) for temperature values between 0.8 and 12.8 with a consistent number of five to seven resulting clusters. Generally, all clustering algorithms will slightly over- or under-cluster, and to determine a precise number of cell types, functional clusters need to be verified by comparing to morphological, genetical, or transcriptomics data. Analysis in our paper are based on temperature 1.6 with the highest objective value resulting in seven clusters that we successfully matched to an existing hierarchy of cell […]

Author response — `clarification` (units 50–51):

> We will add results of this analysis as a figure and a discussion to the Appendix of the final version of the paper. Thank you very much for asking this interesting question, which will make our paper stronger.

## Example 19 — review `E85rsbg9Jy` (ICLR 2024)

8 units, 7 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> (1) The Chain-of-Verification concept is straightforward and can be practically implemented without necessitating adjustments to LLM's parameters.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> (2) The empirical evaluations conducted on a varity of tasks, including list-based questions (Wikidata), closed-book MultiSpanQA, and longform text generation, demonstrate the effectiveness of the proposed method in mitigating LLMs' hallucinations.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> (3) This paper is well-written and presents its ideas in a clear and comprehensible manner.

Author response: none.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> (1) The introduction of the proposed method does incur additional inference overhead. It would enhance the paper's rigor to compare these added computational costs with those associated with alternative methods that also target the reduction of LLM hallucinations.

Author response — `clarification` (units 4–5):

> Please check the common response. We also provide further comparative analysis in section 8 in our appendix.

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> (2) The utilization of few-shot learning for enabling LLMs to perform planning, verification, and generation (3-shot as detailed in the Appendix) raises a potential concern that the results might be influenced by variations in the few-shot examples used.

Author response — `clarification` (units 7–9):

> We have now added the few-shot prompts used in our supplementary material for reproducibility. We agree that changing the few-shot prompts can lead to a variance in the final output. In our comparative analysis, we use the same prompts to generate the baseline response for all our baseline approaches.

**Critique 6** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> (1) What criteria were employed for the selection of few-shot examples, and what is the potential influence of employing different examples on the results?

Author response — `clarification` (units 12–18):

> 1. Our few-shot prompts for the list-based QA benchmarks were randomly chosen from the train set. We however keep these prompts constant across our variants. 2. For the biographies dataset, we choose some of the most viewed people's pages on Wikipedia and craft our prompts based on their biographies. We find few-shot examples that allow us to show the model our desired verification responses. We have added the few-shot prompts used to the supplementary material.

**Critique 7** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> (2) Could you provide an estimate of the additional computational overhead that the proposed method would introduce?

Author response — `clarification` (units 19–20):

> 2. We perform an analysis of the inference overhead. Please see the common response and Section 8 in our appendix.

## Example 20 — review `LYYpPYojvw` (ICLR 2024)

43 units, 11 critiques, 12 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The proposed framework, MpM, corroborates and extends the line of work on multilingual transfer through frozen language models, showing it to be more effective than previous models on the chosen tasks according to the evaluation measures adopted by the authors.

Author response: none.

**Critique 2** — aspect `clarity`, severity `minor`, polarity `positive`, target `figure_table`, actionable `False`

> 2. The plot in Figure 2 is interesting, showing how most of the Wukong text data might be poorly aligned with the corresponding images.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 3. Human evaluation on Chinese Drawbench shows how the proposed model is often preferred to the baselines.

Author response: none.

**Critique 4** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> 4. It is interesting to see how much English data helps during fine-tuning in the ablation study, perhaps because it bridges the gap between the style and language axes. 1. The paper claims to “generalize to other languages in a zero-shot manner.” This is not true, and very misleading. In fact, the chat model had to be fine-tuned on target language data, otherwise it would generate text in English. Calling the behavior “quasi-zero-shot” is also (i) different from the literature, and especially (ii) misleading: the model cannot generate text in the target language without supervision.

Author response — `clarification` (units 5–9):

> In MLLM literature, to the best of our knowledge, there has been no report on the phenomenon where a model exclusively pre-trained on English multimodal data, can provide accurate responses in English for instructions in other languages. In this context, the foundational MLLM capability has been successfully generalized from English to the target language, requiring merely a switch in language to fully realize this capability. On the one hand, this demonstrates a remarkable strength: the model's ability to comprehend and respond to Chinese multimodal instructions without being exposed to any C […]

**Critique 5** — aspect `significance`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> Such claims, while valid for the text-to-image model, should be removed. 2. The paper claims to propose “an effective training paradigm for training large multimodal models in low-resource languages.” However, none of the languages tested were low-resource. There is a significant difference in the representations of the LM model between high- and low-resource languages, as well as in the quality of translations that an MT system can provide for those languages. None of these things are true for Chinese. Any claims about performance and applicability to low-resource languages need to be removed as they are never verified.

Author response — `concession` (units 12–15):

> - The claim about low-resource language. In this paper, we refer to the low-resource language under a multimodal scenario. Please refer to the general response for a more detailed discussion. We have revised our paper to avoid misunderstanding with the term ‘low-resource’ language.

**Critique 6** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 3. The paper also claims to be multilingual. Yet, most of the experiments are done in a bilingual setup (English+Chinese) or in a few, high-resource European languages. These languages share the same script, similar topology. Claims about multilinguality should be supported by a better selection of languages that increase diversity in scripts, topology, and resource availability.

Author response — `new_experiment` (units 16–19):

> - Language Diversity. Thanks for your advice! We have expanded our evaluation on a larger range of languages based on the IGLUE benchmark, which covers more diverse languages and obtains good performance, such as Russian in Cyrillic script with a 47.68 score on xGQA. We leave a wider range of language models in future work.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4. My other major concerns are related to the experimental setup. - (4a) The model is evaluated on unusual benchmarks for multilingual multimodal modeling. These datasets are obtained through machine translation of the corresponding English dataset. The authors claim to fix minor errors (only for Chinese, and not even for all the other 6 European languages), yet do not provide any indication of the quality of the resulting test data.

Author response — `clarification` (units 21–36):

> - **Quality of test data** For the Chinese test data, we manually check the data quality. This operation has been adopted in previously well-recognized benchmarks such as IGLUE to ensure the test data quality. For other languages, note that directly using machine translation to translate the test benchmark without manual checking is also widely adopted in the literature [1][2][3]. Nonetheless, we agree that evaluation on manually validated benchmarks can better support the findings. During the response period, we additionally evaluate the performance of these languages on manually validated be […]

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - (4b) The evaluation scores are based on GPT-4, which might not understand languages beyond English well. This is an hypothesis that might or might not hold true, but the fact that such concern exists, I believe it is enough to undermine the evaluation setup used by the authors.

Author response: none.

**Critique 9** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - (4c) There exists multilingual multimodal benchmarks. For instance, IGLUE [1] tests for 4 multimodal tasks in 20 languages, with data *manually* collected by native speakers. MaRVL [2] and XM3600 [3] even include images sourced from the countries where a language is spoken. These benchmarks are adopted in the literature and completely missing (even as part of the related work) in this paper.

Author response — `new_experiment` (units 38–40):

> Thanks for your valuable advice. We perform an additional evaluation on the IGLUE. Please refer to the general response for the results.

**Critique 10** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 5. There is a lack of discussion of relevant related work. Models like {m,x}UNITER [2], CCLM [4] and TD-MML [5] are missing. The latter in particular shows how machine translation data can be very helpful during pretraining if filtering out poor translations, which provides a contrasting point to the one made by the authors in this paper. A discussion of these findings and how they differ is important to guide the community.

Author response — `promise_to_fix` (units 59–61):

> Thanks for your suggestions. We will incorporate the missing related work and benchmark in the final version. **Q5: Inconsistency with the previous conclusion**

**Critique 11** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> You say that you perform manual inspection, can you elaborate more on your findings and their relation to CLIP scores?

Author response — `clarification` (units 69–78):

> **Q6: Findings of manual check about the CLIP score** We use Chinese-CLIP [2] to compute the CLIP score in Chinese image-text pairs. Chinese CLIP models have been used in several Chinese text-to-image models for data filtering and text encoding [3][4][5]. We manually check the caption in the Wukong dataset. We observe that the overall quality of text content in Wukong is unsatisfactory. Here are some findings about low CLIP scores: - Broken Images: Some image URLs are broken or redirected to the same default image for downloading. - Unrelated captions: Some content of captions are totally unre […]

Author response — `promise_to_fix` (units 79–81):

> Thanks for your reminder. Due to space limitations, we leave the detailed introduction of baseline models in the Appendix. We will incorporate more crucial information about the baselines in the body during revision.

`[ignored]` [1] Bugliarello et al. IGLUE: A Benchmark for Transfer Learning across Modalities, Tasks, and Languages. ⏐ ICML’22. ⏐ [2] Liu et al. Visually Grounded Reasoning across Languages and Cultures. ⏐ EMNLP’21. ⏐ [3] Thapliyal et al. A Massively Multilingual Multimodal Evaluation Dataset. ⏐ EMNLP’22. ⏐ [4] Zeng et al. Cross-View Language Modeling: Towards Unified Cross-Lingual Cross-Modal Pre-training. ⏐ ACL’23. ⏐ [5] Qiu et al. Multilingual Multimodal Learning with Machine Translated Text. ⏐ EMNLP’22. ⏐ 1. The low CLIP scores in Wukong might be related to misunderstanding of Chinese captions from CLIP. ⏐ 2.  It would be useful for the reader to have more information about the baselines, so that one can easily understand what changes among models when comparing their results.

