# 20 random reviews of run `full_v3` (seed 0)

Review text is public content from OpenReview. `[ignored]` units are in no critique.

## Example 1 — review `3Mzo55emlc` (ICLR 2024)

16 units, 7 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The problem studied is interesting.

Author response: none.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> It is important to learn whether we can make adaptive gradient methods learning rate-free.

Author response: none.

**Critique 3** — aspect `novelty`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> The contribution of the paper is unclear. In the first sentence in the abstract, the authors claim that they "address the challenge of estimating the learning rate for adaptive gradient methods." The issue is important, but after reading the paper, I do not follow how they addressed the issue.

Author response — `clarification` (units 3–7):

> W1) In our paper, we present two algorithms to estimate the learning rate of adaptive gradient methods. In Alg. 1, line 6 represents the update rule of an optimizer, with the learning rate $\eta_k$ estimated in line 5. Similarly, in Alg. 2, line 11 represents the update rule of an optimizer, with the learning rate $\eta_k$ estimated in line 10.

**Critique 4** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> Then, the authors claim they "interpret adaptive gradient methods as steepest descent applied on parameter-scaled networks ." Authors need to explain why their new interpretation is important to the ICLR community.

Author response — `clarification` (units 9–10):

> W2) Our proposed interpretation of adaptive gradient methods enables the transformation of learning-rate-free optimizers developed for steepest descent [1], [2] into adaptive gradient learning-rate-free optimizers. &nbsp;

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> Also, the authors claim they "propose learning rate-free adaptive gradient methods". It appears that algorithm 2 is the method they propose. However, in algorithm 2, there are a lot of hyper-parameters, including $\eta_k$, $\gamma_k$, and even $\alpha_k$. It is not clear to me why Algorithm 2 is "learning rate-free". The explanation about the notations in Algorithm 2 should be clearer.

Author response — `clarification` (units 11–23):

> W3) Training a deep neural network with an adaptive gradient optimizer involves various design choices: 1. Selecting a gradient rescaling strategy, such as AdaGrad, Adam, or AMSGrad. 2. Choosing a base learning rate within the range of $0.0003$ to $0.01$ or broader. 3. Selecting a learning rate annealing schedule, such as constant, step decay, or cosine annealing. In this context, Alg. 1 relieves the second and third design choices, while Alg. 2 addresses the second design choice. These algorithms are termed learning-rate-free methods as they alleviate the manual tuning of the base learning ra […]

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> In section 5.2, authors should report the metrics for their reinforcement learning experiment. It is hard to understand the value of the proposed PS-SPS and PS-DA-SGD from Table 3. Also, the authors mention that they removed all the batch normalization layers in the CIFAR-100 experiment. What are the benefits of such removal?

Author response — `clarification` (units 32–37):

> W4) In our experiments evaluating reinforcement learning, we utilized the average of the reward output of the OpenAI Gym environment as the performance metric. The values in parentheses represent the training success rate. It is important to note that SPS and PS-SPS were omitted from these experiments due to their reliance on the loss value at optimum, denoted as $f^*$, which is challenging to estimate before training within the context of reinforcement learning models. We have removed all batch normalization layers from VGG networks, while ResNet networks remain unchanged. This modification a […]

**Critique 7** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> Authors should also clearly write their assumptions and conclusions into a formal theorem in Section 4.2.

Author response — `new_experiment` (units 39–45):

> W5) A formal theorem of Sec. 4.2 is as follows. AMGRrad scaling rule: $\alpha_k=(\max_{i\le k}v_i)^{1/4}$, where $v_{i+1}=\beta v_i + (1 - \beta) g^2_i$, $0<\beta<1$. For a convex G-Lipschitz function $f$ and AMSGrad scaling rule, Alg. 1 converges to the minimum of $f$. For a convex G-Lipschitz function $f$, AMSGrad scaling rule, and a decreasing sequence $\gamma_k$ satisfying $\sum^\infty_{k=1}\gamma_k=\infty$ and $\sum^\infty_{k=1}\gamma_k^2<\infty$, Alg. 2 converges to the minimum of $f$.

`[ignored]` Please see the weakness section.

## Example 2 — review `c5UVTlEFgV` (ICLR 2024)

13 units, 6 critiques, 3 ignored, 1 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper has a clean presentation, and it's easy to follow the authors' ideas.

Author response: none.

**Critique 2** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> The specific approach here is to replace the human side with an LM trained on human queries. This trained LM then interacts with ChatGPT to bootstrap more data.

Author response — `disagreement` (units 2–6):

> We are very sorry for the misunderstanding. Our motivation focuses on how we can **simulate** human questioning better and how the human questioning pattern **benefits** the response quality after witnessing the success of Vicuna, absolutely not on how to bootstrap data from ChatGPT more easily. In fact, ChatGPT can be replaced by any other stronger response models. We used it just because of the high-quality answers. The reason why we conducted the scaling experiments is also to explore whether the benefits of human questioning pattern to response model can be scalable.

Author response — `clarification` (units 30–36):

> **Rationale of PlatoLM** In our paper, the intuitive reason is that **the human-like questioning pattern** can elicit the high-quality responses better in real-time dialogs. In the human-to-machine interaction, humans dominate the conversation. Hence, a **more human-like questioning pattern** will bring a **richer topic structure**, such as topic drifting and shifting, leading to higher topic diversity. This was all quantified in revised Sec.5.4. Compared to static stimulation, the questions posed by Socratic are more human-like, and the topic diversity is higher. （in Sec 5.2 Table 4）. Compare […]

**Critique 3** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> While the approach can produce interesting artifacts such as the dialogue dataset, I don't think the research goal -- making bootstrapping data from ChatGPT easier -- is a scientific problem.

Author response — `disagreement` (units 2–6):

> We are very sorry for the misunderstanding. Our motivation focuses on how we can **simulate** human questioning better and how the human questioning pattern **benefits** the response quality after witnessing the success of Vicuna, absolutely not on how to bootstrap data from ChatGPT more easily. In fact, ChatGPT can be replaced by any other stronger response models. We used it just because of the high-quality answers. The reason why we conducted the scaling experiments is also to explore whether the benefits of human questioning pattern to response model can be scalable.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> For instance, in Table 2 with the same number of examples, PlatoLM-7b doesn't outperform Vicuna-7B with 10k examples for MT-bench.

Author response — `clarification` (units 9–16):

> It may be caused by the confusing layout of our tables, please review the revised Tables 1 and 2 again. **If we use randomly sampled 10K conversations** Compared to the static simulation (Baize、UltraLM), our model outperforms it in alpaca-eval、vicuna-bench、mt-bench. Compared to Vicuna, Our model outperforms it in alpaca-eval, vicuna-bench, and mt-bench's pair-wise evaluations. In fact, we just **lag behind Vicuna in the single evaluation** judged by machine and we have explained it in 4.2.2 Automatic Evaluation. Specifically, the author of the MT-Bench paper gave us the example: if one model i […]

Author response — `new_experiment` (units 17–21):

> In the beginning, we envisaged Vicuna as our ceiling. After conducting **the scaling experiments** based on LLaMA1-LLaMA1（in Sec.5.3）, we find that the teaching ability of our paradigm can be **scalable** with the data volumes. Using a 100K sample (according to **Reviewer FWRq and Z8HQ**) can beat the Vicuna-10K in MT-Bench's **single evaluation**（5.85 v.s. .5.9598±0.0339）. **If we use 50k samples based on LLaMA1-LLaMA2 (in Table2)** Under the same backbone LLaMA2, PlatoLM beats Vicuna-7b-v1.5 and LLaMA-2-7b-chat in MT-Bench and Alpaca-Eval.

Author response — `new_experiment` (units 23–28):

> After conducting the pairing experiments in Appendix E according to **Reviewer Z8HQ**, we find **the different pairing backbone of Socratic and PlatoLM** will be more adaptive to our paradigm（see table below）. With only 28.5K samples, Plato-7B surpassed Vicuna-13B-v1.5 and LLaMA-2-13B-chat in MT-Bench. | Q/A     | LLaMA-1       | LLaMA-2       | Mistral       | | LLaMA-1 | 5.7506±0.0314 | 6.0920±0.0515 | 6.4187±0.0470 | | LLaMA-2 | 5.8775±0.0205 | 5.9900±0.0163 | 6.6838±0.0464 | | Mistral | 5.9094±0.0261 | 6.1744±0.0199 | 6.3250±0.0406 |

**Critique 5** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> I can imagine the technique useful when the number of total human queries is small, where fine-tuning on human queries helps the query model learn the style. The pretrained base has a lot of knowledge; thus the fine-tuned query model can produce much more diverse query content. But small human data setting is not explored.

Author response — `promise_to_fix` (units 37–42):

> **For the small human data setting** The newly-added scaling experiments (with 100k examples) demonstrated that the performance of the response model does not saturate in MT-bench (especially in the second turn) as the data volume increases to **100K**. Using fewer training examples might negatively affect the user simulator as it starts from a *base* model; the *base* might be originally poor in questioning, and it needs some data for training, so we used **20K samples** to fine-tune the simulator. Although we also used ShareGPT-gpt4-6K to train the simulator and found it works well when infe […]

**Critique 6** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> For vicuna-7b, authors should clarify the exact version, i.e., is it v1.3 or v1.1, or something else.

Author response — `clarification` (units 43–45):

> ## Version of vicuna-7b The baseline version is V1.5, see https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard. Vicuna gets a score of 6.17 and is linked to  https://huggingface.co/lmsys/vicuna-7b-v1.5 . we have added the version and the training type in the revised version.

`[ignored]` - **Problem Motivation:** The goal of the current work is to make it easier and cheaper to produce synthetic dialogues for fine-tuning language models for chat applications. ⏐ - **Performance**: After reading the paper, it's unclear to me whether there are real gains from first training a human query simulator and then using its simulated data. ⏐ - **Understanding**: After reading the analysis section (Sec 5), it's still unclear to me that if there's a benefit from using Socratic simulated data, what would be an intuitive reason for that?

`[post-rebuttal, set aside]` I read the author response and have updated my score.

## Example 3 — review `Mnvu79n7Dn` (ICLR 2024)

6 units, 6 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The proposal to adapt various benchmarks when they no longer become useful or representative of the task being solved makes sense and should indeed be investigated

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The authors make several observations that are useful for the larger community e.g. how best to handle FSOD datasets

**Critique 3** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> The contribution seems pretty limited for a paper submission, especially since neither Detic nor FedLoss are a contribution of this paper and the InvFedLoss is a very small modification.

**Critique 4** — aspect `reproducibility`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> Proposing that a VLM be used for FSOD may sometimes not be possible because of the large compute cost involved.

**Critique 5** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> This doesn't seem to be mentioned anywhere in the paper (both fine-tuning and inference) so it would be nice to get the authors' thoughts on a like-for-like comparison in terms of FLOPs.

**Critique 6** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> Has there been any analysis on the text prompt for these tasks and how modifications of it affect the result.

## Example 4 — review `vaSd6KrFJz` (ICLR 2024)

20 units, 10 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> - The paper introduces two novel algorithms for online learning in POMGs, marking the first study of Imperfect Information Extensive-Form Games using linear function approximation.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> This linear approximation approach is notably more practical.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The paper clearly presents the problem setting, making it accessible to readers unfamiliar with the topic.

Author response: none.

**Critique 4** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The algorithms are clearly explained, and the intuition behind them is also provided.

Author response: none.

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - For LSOMD, the parameter setting ($\eta$) necessitates prior knowledge of $\alpha$. A discussion on determining or estimating $\alpha$ is required. An adaptive algorithm would be a preferable solution. - Is it possible to provide an adaptive algorithm that achieves a similar regret bound without knowing $\alpha$ or $\lambda$ in advance?

Author response — `promise_to_fix` (units 5–13):

> The dependence on $\rho$ (here $\rho$ is a more general and more adaptive parameter than its previous counterpart $\alpha$; please see Assumption 3.2 in the revision of our paper for details) of the learning rate $\eta$ and exploration parameter $\gamma$ in our LSOMD algorithm comes from the fact that it is required to control the variance of the loss estimate so that the loss estimate is not prohibitively negative when using the negative entropy as the potential function of online mirror descent (OMD). We conjecture that the dependence on $\rho$ of $\eta$ and $\gamma$ (and also the regret gua […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - Similarly, the parameter setting ($\eta$) of LSFTRL requires prior knowledge of $\lambda$. Besides lack of discussion on $\lambda$, it is not clear whether we should use the first or the second parameter initialization in practice. I think when $\lambda\geq X/H$, the second initialization should be adopted, but how to determine whether $\lambda\geq X/H$ and what regret we can get if $\lambda< X/H$?

Author response — `promise_to_fix` (units 5–13):

> The dependence on $\rho$ (here $\rho$ is a more general and more adaptive parameter than its previous counterpart $\alpha$; please see Assumption 3.2 in the revision of our paper for details) of the learning rate $\eta$ and exploration parameter $\gamma$ in our LSOMD algorithm comes from the fact that it is required to control the variance of the loss estimate so that the loss estimate is not prohibitively negative when using the negative entropy as the potential function of online mirror descent (OMD). We conjecture that the dependence on $\rho$ of $\eta$ and $\gamma$ (and also the regret gua […]

**Critique 7** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Discussion on lower bounds is needed, even if some necessary conditions on some of the factors in the regret bounds are helpful.

Author response — `new_experiment` (units 16–17):

> We now provide a regret lower bound of order $\Omega(\sqrt{d\min(d,H)T})$. Please see Section 4.3 for the formal statements and the discussions on the tightness of our regret upper bounds in the revised version of our paper (highlighted in green).

**Critique 8** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> - No experiment is provided in the main paper. - Could you conduct empirical experiments to demonstrate the algorithms' effectiveness? Even numerical tests using toy examples would be insightful.

Author response — `promise_to_fix` (units 20–22):

> We do think conducting empirical evaluations to further validate the performance of our proposed algorithms is valuable and is an important next step. However, we also would like to note that in this work we aim to make the first step to advance the theoretical understandings of learning partially observable Markov games (POMGs) in the function approximation setting. Thus we did not include empirical evaluations in our paper following previous works [6,7] and we leave conducting empirical evaluations of our proposed algorithms as one of our future studies.

**Critique 9** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> - Are the regret bounds provided by LSOMD and LSFTRL optimal? I guess that $\sqrt{HdT}$ is unavoidable in the bound, but this requires a more rigorous proof.

Author response: none.

**Critique 10** — aspect `soundness`, severity `minor`, polarity `neutral`, target `section`, actionable `True`

> - In Assumption 2.1, the paper assumes $\left\|{\bf\theta}\right\|_2\leq \sqrt{d}$ and $\sup_{s_h,a_h,b_h}\left\|\Phi(s_h,a_h,b_h)\right\|_2\leq 1$. Can this pair of inequalities be substituted with $\bar{r}_h(s_h,a_h,b_h)\leq \sqrt{d}$?

Author response — `disagreement` (units 26–26):

> In general, the regularity conditions imposed over $\mathbf{\phi}(\cdot,\cdot,\cdot)$ and $\mathbf{\theta}_h$ can not be substituted with the regularity condition imposed over $|\bar{r}_h(s_h,a_h,b_h)|$, as they are required to control the variance of the loss estimate (please see this in the proof of Lemma D.4 in Appendix D.2.2 of our paper).

`[ignored]` Please refer to the weaknesses part.

## Example 5 — review `uJTHUad87c` (ICLR 2025)

21 units, 10 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `figure_table`, actionable `False`

> 1. The motivation behind the proposed approach is both technically sound and clearly explained, supported by two informative figures illustrating the varying levels of similarity among different tokens and the accumulation of error across these tokens. These visual aids effectively convey the rationale for the proposed method.

Author response: none.

**Critique 2** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. The methodology for selecting scores and making decisions for each layer is novel, offering valuable insights into the acceleration of transformer models. This innovative approach not only enhances the efficiency of the models but also contributes to a deeper understanding of feature caching strategies within the context of transformers.

Author response: none.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. There appears to be a lack of a complete algorithmic description within the manuscript. Specifically, a detailed explanation is needed for the token selection process at each layer and each timestep, as well as the procedure for redistributing the cached tokens back into the overall framework. This omission could lead to misunderstandings regarding the efficacy and functionality of the proposed method.

Author response — `new_experiment` (units 6–22):

> **A1:**  Thank you for your suggestion. We agree that the algorithmic analysis of ToCa can be further improved. To address this, we have expanded the algorithm illustration in Figure 3 into a more detailed flow diagram, now presented as **Appendix Figure 12**. Below, we provide the detailed step-by-step process of our ToCa method: **Step1: Cache Initialization in the first step.**  In the first step of each cache cycle (referred to as the "fresh step", e.g., step t in this example), the denoising model performs full computation for all layers and stores the output features of all layer types i […]

**Critique 4** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 2. The manuscript does not adequately illustrate the computation costs associated with the proposed approach, making it challenging to comprehend the additional expenses involved. A clearer breakdown of these costs would enhance the reader's understanding of the method's efficiency.

Author response — `new_experiment` (units 25–67):

> **A2:** Thank you for your suggestion. In the updated PDF, we have added a detailed breakdown in the **Appendix A.4 COMPUTATION COMPLEXITY ANALYSIS** section. In summary, the computation costs of self-attention score (s1), cross-attention score (s2), caching frequency score & spatial bonus **only account for 0.28%, 0.35%, 0.18% of the whole computation costs, respectively**. In the following Response Part 2, we introduce the computation complexity for attention and MLP layers, as well as the computation costs for token selection in detail. **Attention layer.** In the Attention layer, tokens ar […]

**Critique 5** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> 3. Including a token diagram for specific layers during both early and late timesteps, across various layer types, may provide additional clarity. Such visual representations could effectively illustrate how tokens are managed and utilized within the different stages of the computation, facilitating a better grasp of the overall caching strategy.

Author response — `new_experiment` (units 71–80):

> **A3:** Thank you for your insightful suggestion. Adding a token diagram is indeed a more intuitive way to convey the caching strategy compared to text and equations alone. In the updated **Appendix Figure 14**, we provide a detailed illustration of the computation allocation across different layer types, depths, and timesteps using DiT as an example. As described in our paper, due to the cost-effectiveness of computation allocation, no additional computation is assigned to the self-attention layers during cache steps. Thus, as shown in the diagram, computation is only allocated during the fre […]

**Critique 6** — aspect `related_work`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. The introductory paragraph of the methods section should be rephrased to clarify the concept of the "naive scheme" for feature caching. This naive scheme is actually no different from existing approaches, such as DeepCache, FORA, and delta-DiT, which should not be "we propose".

Author response — `clarification` (units 83–90):

> **A4:**  Thank you for pointing this out. We agree that the original phrasing in the draft was imprecise. In the updated PDF version, we have revised this section to replace the previous statement:*"Following previous caching methods for U-Net-like diffusion denoisers, we introduce the naive scheme for feature caching."* with:*"We follow the naive scheme for feature caching adopted by most previous caching methods such as DeepCache [1], FORA [2], and $\Delta$-DiT [3] for diffusion denoisers."* We have also added the appropriate citations to ensure proper acknowledgment of prior works. [1] Ma e […]

**Critique 7** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> 2. It should be noted that Figure 3(b) does not depict any low-ratio caching scenarios.

Author response — `clarification` (units 91–97):

> **A5:** Thank you for your observation. We noticed similar feedback from other reviewers. When viewing the submitted PDF using browsers such as Edge or Chrome, this issue does not appear. However, we identified that certain mobile browsers fail to display the gradient colors in vector graphics correctly. Specifically, the arrow in **Figure 3(b)** is designed to have a yellow lower end transitioning to a blue upper end. To address this issue, we have updated the figure in the revised version by adjusting the gradient settings of the vector graphic and embedding the problematic arrow as a standa […]

**Critique 8** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 3. There is a discrepancy regarding the application of the scores s1, s2, and s3 across the layers. Specifically, s1 is applicable only to self-attention layers, while s2 pertains solely to cross-attention layers.

Author response — `clarification` (units 101–112):

> **A6:** Thank you for raising this important point. You are correct that in practice, $s_1$ is calculated solely through self-attention layers, $s_2$ is only calculated through cross-attention layers, and $s_3$ is updated across all layers. This design raises the question of how these scores are utilized in layers such as MLP layers, where $s_1$, $s_2$, and $s_3$ are not directly computed. To clarify, in our implementation, the calculation materials for $s_1$ and $s_2$, which are based on the self-attention or cross-attention features, are cached along with the corresponding attention maps dur […]

**Critique 9** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> However, the current definition combines these scores, which raises questions about how this aggregation functions across the different types of layers.

Author response: none.

**Critique 10** — aspect `reproducibility`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 4. Clarification is needed regarding the additional time cost associated with computing the selection scores. Given that the scoring relies on rank computation, there remains a need to calculate and distribute the cached tokens among the uncached tokens. This process is somewhat ambiguous, particularly concerning how the acceleration time is achieved. Presenting the actual extra costs incurred for selecting scores alongside the resulting speedup from the caching process would provide valuable insights.

Author response — `clarification` (units 117–118):

> **A7:** We have made a detailed computation breakdown in **A2**. Dear Reviewer 3XM7,

## Example 6 — review `5lGc5VCtYd` (ICLR 2025)

36 units, 12 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> This paper has the potential to be an important contribution to the field, for two main reasons: - Great benchmark proposed with a comprehensive range of tasks and difficulty levels, and good metrics for evaluating performance - Excellent coverage of experiments. Testing comprehensively many aspects relevant to this problem, like different types of generalisation, different architectural changes, different existing models, effects of scale, existing methods for improving numeric understanding, prompting, etc. I would be very interested in these results, if the weaknesses below could be addressed.

Author response — `clarification` (units 64–64):

> [1] Hu et al. Case-Based or Rule-Based: How Do Transformers Do the Math?, 2024.

**Critique 2** — aspect `reproducibility`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> Unfortunately, the presentation is lacking and it's very hard to interpret the results because of missing details on how models are trained. - There is no information at all in the paper about how the models are trained for the experiments in section 3.1 and 3.2. How much examples do you train on? How long? Optimizers, hyperparameters, repeats, etc.? How do you define in and out-of-domain? It's very difficult to interpret the results of this experiment without knowing more.

Author response — `clarification` (units 3–12):

> 1. **Training details** We train our models using an autoregressive Transformer architecture based on Llama-3.1 (unless stated otherwise). Sections 3.1 and 3.2 cover training from scratch with all hyperparameters, except model size, aligned with the original Llama setup. The AdamW optimizer is used with a learning rate of 5e-5, weight decay of 0.01, and batch sizes of 256, 64, and 32 for 0.1B, 0.9B, and 3B models, respectively, following default settings in the Transformers library. Each model is trained on a consolidated dataset, comprising $10^7$ samples for each length (where feasible). Mod […]

**Critique 3** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The paper needs substantial rewrites, and will probably benefit from corrections by someone whose first language is English or by using an LLM to revise and point out mistakes. - There is a long discussion of things like the relevance of integers and how fractions arise (section 2.1 and 2.2), but this seems unnecessary and the space could be used instead to represent the results better. For example, Figure 2 presenting the main results in the text is very small and almost impossible to read without zooming in 200%. The colors used are also hard to distinguish. I would suggest shortening section 2.2 and almost entirely removing 2.1 and use the space to represent the results better. Especially because this is the great part of this paper, you have so many results but you do not discuss the details of the experiments and present the results in a way that are hard to follow.

Author response — `clarification` (units 14–24):

> 2. **In-domain and Out-of-domain** The terms "in-domain" and "out-of-domain" refer to the **length** of numbers. As described in Section 3.1, the model is trained on numbers of lengths 1 to 8 (20) and tested on numbers of lengths 1 to 20 (100). Thus, lengths 1 to 8 (20) are considered in-domain, while lengths 9 (21) to 20 (100) are out-of-domain. 3. **Section 2.1 and 2.2** The primary goal of our work is to propose a comprehensive benchmark to formalize NUPA. We believe it’s important to provide clear reasoning behind the choice of representations and tasks. To enhance clarity, we have signifi […]

Author response — `new_experiment` (units 25–28):

> 4. **Figure 2** Figure 2 has been updated for better readability. Additionally, to further enhance clarity, we have provided an interactive performance report as an anonymous *HTML* page [here](https://huggingface.co/spaces/NUPA-Anonymous/Performance). This allows readers to **interact with** the figure by selecting models, tasks, and metrics for a more detailed exploration.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Some results are interpreted in ways that are not substantiated by the evidence found. For example, line 298 to 309; I disagree that this result means the model does not understand the concept of digit. The fact that it becomes harder to return the right digit for longer numbers actually hints at something else going on that might be more related to the model's inherent difficulties with retrieving something from a position in longer sequences, which has nothing to do with it's understanding of the concept digit. I also disagree that this points to case-based reasoning, because again it might be due to some aspects of its architecture. Additionally, the fact that models of different sizes show the same performance on a task does not necessarily indicate the performance depends on the training approach over size, it might also depend on architecture.

Author response — `clarification` (units 29–41):

> 5. **Interpretation about the results** We recognize that some explanations in our initial submission may have led to misunderstandings due to less precise wording. - For instance, when we state that "*the model does not understand the concept of digit*," we mean that the model cannot consistently solve digit-related tasks. Here, "concept" refers to a "set of digit-centered abilities" as defined in Section 2.2. We clarify that our paper acknowledges models can comprehend task instructions: "*models can at least comprehend the task instruction.*" This statement has been rephrased for clarity in […]

**Critique 5** — aspect `related_work`, severity `major`, polarity `negative`, target `section`, actionable `True`

> - There is no section on related work, and the authors say in the beginning of section 2 that they will show limitations of prior benchmarks while discussing the coverage of their own, but this does not happen. This makes it difficult for the reader to place this contribution w.r.t. existing literature.

Author response — `new_experiment` (units 43–46):

> Thank you for your suggestion. In the updated submission, we have added a related work section that now includes relevant datasets and benchmarks. To summarize, our work differs from previous benchmarks by treating NUPA as an independent task, distinct from math, language, or commonsense abilities. Additionally, we provide a comprehensive and detailed analysis of diverse numerical representations and tasks, which sets our approach apart.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> - Would be great to already get some more concrete information in the abstract (what probability of error? which 3 factors influence it?). Or at least in the intro some more concrete info.

Author response — `clarification` (units 47–59):

> 7. **For these minor points:** - The abstract has been revised and the vague terms have been removed. - More explanations have been added in the caption of figures. Specifically, the X-axis is the seen samples, Dn is the number length (digit). - The citation about the calculation hallucination has been added. - The discussion on innateness has been removed. - The citation of gpt-4o has been added. The original occurrence of "chatgpt" has been removed due to the space limitation. - Regarding few-shot learning: In practical applications of number processing, such as financial reporting or solvin […]

**Critique 7** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> - Figure 4 and 5: it's unclear what's on the X-axis (though one can assume it's training steps), and also unclear what D6 to D10 refers to. It's also unclear what is in-domain and what is OOD without reading the text.

Author response — `clarification` (units 47–59):

> 7. **For these minor points:** - The abstract has been revised and the vague terms have been removed. - More explanations have been added in the caption of figures. Specifically, the X-axis is the seen samples, Dn is the number length (digit). - The citation about the calculation hallucination has been added. - The discussion on innateness has been removed. - The citation of gpt-4o has been added. The original occurrence of "chatgpt" has been removed due to the space limitation. - Regarding few-shot learning: In practical applications of number processing, such as financial reporting or solvin […]

**Critique 8** — aspect `related_work`, severity `minor`, polarity `negative`, target `reference`, actionable `True`

> - *"These types of errors are a major cause of hallucinations when dealing with math, reasoning, and data analysis tasks, as the model presents seemingly correct problem solving approaches but ultimately produces incorrect results"* -> this statement requires a citation

Author response — `clarification` (units 47–59):

> 7. **For these minor points:** - The abstract has been revised and the vague terms have been removed. - More explanations have been added in the caption of figures. Specifically, the X-axis is the seen samples, Dn is the number length (digit). - The citation about the calculation hallucination has been added. - The discussion on innateness has been removed. - The citation of gpt-4o has been added. The original occurrence of "chatgpt" has been removed due to the space limitation. - Regarding few-shot learning: In practical applications of number processing, such as financial reporting or solvin […]

**Critique 9** — aspect `significance`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> - line 117 to 119; a discussion on the innateness of integer understanding seems somewhat out of scope for this work and not too relevant to the contribution.

Author response — `clarification` (units 47–59):

> 7. **For these minor points:** - The abstract has been revised and the vague terms have been removed. - More explanations have been added in the caption of figures. Specifically, the X-axis is the seen samples, Dn is the number length (digit). - The citation about the calculation hallucination has been added. - The discussion on innateness has been removed. - The citation of gpt-4o has been added. The original occurrence of "chatgpt" has been removed due to the space limitation. - Regarding few-shot learning: In practical applications of number processing, such as financial reporting or solvin […]

**Critique 10** — aspect `related_work`, severity `minor`, polarity `negative`, target `reference`, actionable `True`

> - Cite / reference openai chatgpt when using it line 135

Author response — `clarification` (units 47–59):

> 7. **For these minor points:** - The abstract has been revised and the vague terms have been removed. - More explanations have been added in the caption of figures. Specifically, the X-axis is the seen samples, Dn is the number length (digit). - The citation about the calculation hallucination has been added. - The discussion on innateness has been removed. - The citation of gpt-4o has been added. The original occurrence of "chatgpt" has been removed due to the space limitation. - Regarding few-shot learning: In practical applications of number processing, such as financial reporting or solvin […]

**Critique 11** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> - One approach that seems missing is few-shot examples, which might significantly boost performance for all models. Not just because they might learn from the examples, but because they get primed on the output format required.

Author response — `clarification` (units 47–59):

> 7. **For these minor points:** - The abstract has been revised and the vague terms have been removed. - More explanations have been added in the caption of figures. Specifically, the X-axis is the seen samples, Dn is the number length (digit). - The citation about the calculation hallucination has been added. - The discussion on innateness has been removed. - The citation of gpt-4o has been added. The original occurrence of "chatgpt" has been removed due to the space limitation. - Regarding few-shot learning: In practical applications of number processing, such as financial reporting or solvin […]

Author response — `new_experiment` (units 78–97):

> Best regards, Authors Thank you for your detailed and invaluable feedback. Your sightful suggestions have significantly improved the quality of our paper. We agree with your suggestions about "concept", "case-based learning" and "few-shot learning". 1. The use of term "concept" was indeed misleading. What we actually intended to highlight was that "the model fails to solve a series of tasks related to digits". we believe that the current revision will eliminate any misunderstandings. 2. For case-based learning, the reference [1] actually use more experimental evidence to support the case-based […]

**Critique 12** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> Main questions is can you give details on how the experiments that use training of fine-tuning are done, and what in-domain and out-of-domain refers to (what examples do you hold out for this)?

Author response: none.

`[ignored]` **Main weaknesses** ⏐ **Minor points**

## Example 7 — review `IlRNAIQK7Q` (ICLR 2024)

36 units, 9 critiques, 11 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Clear explanation of both the algorithm and the key intuitions

Author response: none.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The basic idea is definitely worth pursuing—using a guide for rolling out possible scenarios in order to ensure some coverage of the space of near-optimal policies is clearly something that might benefit current RL methods in LLMs.

Author response: none.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The study of reward optimization tradeoff is interesting and very welcome. It’s pretty clear that our metrics only work under “normal conditions” where complete gibberish isn’t being measured, so using the KL divergence as the other axis shows a potential pareto frontier that we’re working with in these problems.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - The fact that the proposed technique seems to generalize slightly better than previous techniques to harder examples (with less train-test overlap) on CommonGen is interesting, and does validate the technique to some extent, though the margin is relatively small.

Author response: none.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The benchmarks used are somewhat lacking. For text generation in 2023, most comparisons for state of the art methods are made by comparisons to other LLMs because fixed metrics have been found to be lacking. A comparison using a framework like Chatbot Arena (Zheng et al. 2023). would have made the results significantly more convincing. These often use GPT-4 as an evaluator, which has now been shown to be provisionally better than traditional metrics (Liu et al 2023, Min et al 2023, Zhou et al 2023, inter alia). - Even with these quite simple benchmarks, the resulting differences on metrics are small for the task where control is more significant, CommonGen. In IMDB the task-specific metric really only checks if the sentiment score is correct, which is very little information to be using to validate outputs. - The fact that perplexity goes up but output perplexity goes down on IMDB is worrying. I can understand why perplexity would go up: the model is likely collapsing onto a smaller subspace of possibilities, which may still be higher quality. However, the fact that the output perplexity also goes down is worrying: it indicates that after optimization the resultant model is more predictable to LMs which is usually not a good sign for tasks that LMs are bad at in the first place. The results on TL;DR are similarly quite small.

Author response — `clarification` (units 3–12):

> __Chatbot Arena with GPT4 Evaluation__ Thank you for your suggestions. We would like to clarify the scope of our paper:  we focuses on RL finetuning of specific downstream tasks (e.g., generating positive reviews or reddit post summary) instead of generating a general purpose chat model. None of our tasks were for dialogue and general chat/instruction following and thus we don’t find Chatbot Arena to be a relevant evaluation platform for this work. Our evaluation and tasks closely follow other published RLHF papers in 2023, e.g., RL4LM [1],  which is published in ICLR 2023. Also we aimed to us […]

Author response — `new_experiment` (units 13–16):

> __Performance Gain__ Please see our updated results we posted along with the rebuttal for more results with TL;DR. For a quick summary, we show that when doing best-of-n sampling with our RL policies (PPO included), PPO++ shows greater performance improvement than PPO. __Perplexity Goes up but Output Perplexity does down__

Author response — `clarification` (units 17–25):

> We would like to clarify that perplexity is a measure of fluency rather than a measure of how well a generation does on a task. Our evaluation model for output perplexity is GPT2-large. While we agree GPT2-large is not good at the task in terms of optimizing the reward, it is still a valid model that has been widely used to evaluate whether or not the generation is natural and fluent (e.g., see [1-10]). The overall objective that we are optimizing for is $J_{ppo}$, which includes three terms: reward, KL-constraint (i.e., a fluency constraint), and MLE-constraint (i.e., a fluency constraint). W […]

Author response — `clarification` (units 62–70):

> Thank you for clarifying. We agree with the reviewer that reproducing/supporting our quantitative results with strong qualitative evaluations such as human evaluation would strengthen the results in this paper. If not Chatbot Arena, could the reviewer provide examples of other frameworks we could use for tasks? We would like to clarify that both IMDB and CommonGen are part of the GRUE benchmark suite [1] for text generation that was also published in 2023. Furthermore, in [1], the original work evaluated if the automated metrics correlated with human judgments within the benchmark and found th […]

Author response — `clarification` (units 72–75):

> Thank you for clarifying the point of the question. We agree that perplexity is a good proxy to measure fluency and the reviewer is satisfied with the quantitative results of the paper. For measuring how desirable this work's generations are given, similar to the evaluation response, we agree that human evaluation would strengthen the results. Currently, we have example generations from each algorithm from the test set of each task.

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - I’m disappointed to see there’s no study of how this technique scales across model sizes: one could imagine doing this for smaller models, incurring relatively low compute expenses, but no such experiments were conducted. As it is, it is not clear how much these results will generalize to the ever-growing zoo of LLMs.

Author response — `clarification` (units 36–43):

> __Scaling Law Testing__ Here are the LLM breakdowns for our experiments - IMDB: GPT2-base (117M parameters, Causal model) - CommonGen: T5-base (220M parameters, Seq2Seq model) - TL;DR: GPTJ (6B parameters, Causal model) We have the exact hugging-face model specifications in the implementation details in the appendix. Note that we aimed to try varying types of LLMs and sizes of LLMs across our experimentation. We agree that it would be interesting to see how the performance scales w.r.t. Policy model size, but in this work we hoped to focus on improvements beyond PPO when all design choices wer […]

Author response — `concession` (units 78–82):

> We agree with the reviewer that investigating scaling laws would be valuable and are excited about this future work. We wish to emphasize that in this work we focused on improvements beyond PPO when all design choices were held equal. The scales for our models followed previous works in the literature including using exact models proposed and released by the GRUE benchmark suite [1]. We still believe that improvements beyond PPO shown at the same model scale for a given task is orthogonal to the investigation of how RL/RLGF algorithms scale with model size. [1] Is Reinforcement Learning (Not)  […]

**Critique 7** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> - On page 6 you write “While we do not expect the SFT policy π g is as good as the optimal π ⋆ , it is reasonable to expect that d π g provides coverage to d π ⋆ .” Why is this reasonable to expect? It is not a prior clear to me that language models cover the space of optimal solutions well, rather than only covering a small percentage of them. Where is the evidence for this claim?

Author response — `clarification` (units 48–51):

> Here we assume $\pi^*$ as the policy that generates the references in the dataset. Then under the assumption that $\pi_{SFT}$ is well trained on the task with references as labels, we claim that $\pi_{SFT}$ has non-zero support over the space of generations that $\pi^*$ may cover. This claim is empirically supported by the fact that SFT has bounded non-infinity validation perplexity: given the definition of perplexity, the only way we can have bounded validation perplexity is for our model to have non-zero probability of generating the references. In other words, this means that the SFT model  […]

**Critique 8** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> -  What model do you use to calculate output perplexity? I only see you mention GPT-J in passing as an example, not definitively stating what model was used.

Author response — `clarification` (units 45–46):

> We computed Output Perplexity with GPT2-Large. We thank the reviewer for pointing this out and will make this clearer in the final version.

**Critique 9** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> -  On page 7 you write “For training supervised SFT baselines, we consider only the examples with positive labels.”—This is a somewhat unorthodox decision, as it gives little for the model to contrast with or for the user to control at inference time. It basically reduces this to a finetuning problem. Why was this choice made?

Author response — `clarification` (units 53–59):

> We would like to clarify that this choice is standard for the IMDB positive text generation task. The original IMDB dataset does not have any reviews that start negative and finish positive. Thus when training an SFT model, it is standard to focus on the positive -> positive reviews as the task-relevant data for supervised learning. This was done in RL4LMs [1], Direct Preference Optimization [2], as well as popular RLHF codebases such as TRLx [3]. [1] Is Reinforcement Learning (Not) for Natural Language Processing: Benchmarks, Baselines, and Building Blocks for Natural Language Policy Optimiza […]

`[ignored]` Works Referenced ⏐ Liu, Yang, Dan Iter, Yichong Xu, Shuohang Wang, Ruochen Xu, and Chenguang Zhu. ⏐ 2023. ⏐ “G-Eval: NLG Evaluation Using GPT-4 with Better Human Alignment.” arXiv [cs.CL]. arXiv. http://arxiv.org/abs/2303.16634. ⏐ Min, Sewon, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-Tau Yih, Pang Wei Koh, Mohit Iyyer, Luke Zettlemoyer, and Hannaneh Hajishirzi. ⏐ 2023. ⏐ “FActScore: Fine-Grained Atomic Evaluation of Factual Precision in Long Form Text Generation.” arXiv [cs.CL]. arXiv. http://arxiv.org/abs/2305.14251. ⏐ Zheng, Lianmin, Ying Sheng, Wei-Lin Chiang, Hao Zhang, Joseph E. Gonzalez, Ion Stoica. ⏐ “Chatbot Arena: Benchmarking LLMs in the Wild with Elo Ratings.” 2023. https://lmsys.org/blog/2023-05-03-arena/. ⏐ Zhou, Xuhui, Hao Zhu, Leena Mathur, Ruohong Zhang, Haofei Yu, Zhengyang Qi, Louis-Philippe Morency, et al. 2023. ⏐ “SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents.” arXiv [cs.AI]. arXiv. http://arxiv.org/abs/2310.11667.

## Example 8 — review `UXB0YR0j2P` (ICLR 2024)

15 units, 3 critiques, 0 ignored, 5 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper introduced a simple and neat technique to address an important and practical problem in the LLM era.

Author response: none.

**Critique 2** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> It looks like one of those “one simple trick” result and gives the audience an aha moment.

Author response: none.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> I have mixed feelings about this work. While it is in general quite pressing to understand the structure of GPT/LLM, and the authors indeed made some interesting observations, they seem to be quite explicit that they do not care about the execution quality. For example, Delta should be lower bounded but not upper bounded in order to justify using KL divergence/Total variations (smells like a doable fix to provide the other side of inequality; I dont know). In general there is a feeling that the problem is not studied thoroughly. IMO, another major limitation is that if we dont know which model is used to generate the text. In general, one is most interested in determining whether a block of text is from some LLM, not a specific collection of 5-10 widely available models. 1. is it possible to fix the Delta. 2. is it possible to build a stronger result, e.g., so long as an LM is trained through certain mechanism, it will always exhibit the likelihood gap hypothesis?

Author response — `disagreement` (units 4–7):

> **Response**: **We respectfully disagree with this claim**. Execution quality is our top priority: From TabIe 1, our method achieved SOTA results on 4 datasets and 3 models from OpenAI in both black- and white-box scenarios on 16/16 cases regarding AUROC and 13/16 cases regarding TPR.\ Table 3 also confirmed the superior detection quality of our methods on 2 advanced open-sourced models (LLaMa, GPT-NeoX), surpassing baselines in 8/8 cases on AUROC.\ Thus, we are confident that the execution quality is our top priority, and our experimental results demonstrate our method's much higher detection […]

Author response — `clarification` (units 8–13):

> 2. "Delta should be lower bounded but not upper bounded in order to justify using KL divergence/Total variations ..." **Response**: **We want to clarify that this bound is not intended for a low bound of Delta**. Looking at the other side of this inequality, our purpose is to prove that $d_{KL(M, H)} \ge \frac{2\Delta^2}{|| log (.|X) ||^2_{\infty}}$, which means that the difference between the two distributions is significant enough since it is greater than some positive gap.\ So this serves as the low bound of $d_{KL(M, H)}$, rather than the upper bound of $\Delta$. Therefore, even if the $\D […]

Author response — `clarification` (units 14–25):

> 3. "IMO, another major limitation is that if we dont know which model is used to generate the text...." **Response**: We would like to clarify that **we are following the same task-setting as in previous work [1, 2]**: the requirements for known LLM are also the problem settings of the two most famous detection approaches: zero-shot detector DetectGPT [1] and Watermark [2].\ Additionally, as we wrote in the original submission on page 3, “Refer to Appendix B.4 for unknown source model”, **we actually included the experiments for detecting text from unknown sources**. To the best of our knowled […]

Author response — `clarification` (units 29–31):

> **Response:** We would like to first thank the reviewer for raising this interesting question.\ We believe our results are already very strong compared with baselines since our experiments validate the effectiveness of our method on both closed models like text-davinci-003, GPT-3.5-turbo, and GPT-4, as well as open-source models such as GPT-NeoX-20B and LLaMa-13B. Thus, it is evident that it holds for those representative models.\

Author response — `promise_to_fix` (units 32–33):

> However, in terms of “so long as an LM is trained through certain mechanism, it will always exhibit the likelihood gap hypothesis and the possibilities of fixing the Delta.”, we believe that it would be a complicated question because **it involves not only the training mechanism but also factors that might be relevant to the training data, model size, model architecture, and alignment, among others**. We would love to extend our results to more models in the future.\

Author response — `clarification` (units 39–41):

> **Response**: Thanks for the quick feedback and suggestion!\ NO. The kl divergence is not a tester. This kl divergence is intractable for each input text since $\Delta$ can not be exactly computed, as you also mentioned.

Author response — `clarification` (units 42–49):

> Instead, we use it as a theoretical guide to help us empirically detect text.\ As we mentioned, the $\Delta$ is relevant to different training mechanisms, data, model size, model architecture, alignment, etc. Thus, inherited from the DetectGPT hypothesis, we assume such a gap is large enough for us to distinguish between human and AI-written text. But in practice, we have to turn to alternative calculations, such as our proposed Bscore and Wscore, showing impressive performance over previous baselines, as reported in Table 1. Based on our experimental observation, like Figure 2, and the outper […]

Author response — `clarification` (units 53–67):

> First of all, we would like to **clarify a major misunderstanding that we are not designing scoring heuristics to estimate KL divergence that outputs YES when KL divergence is large.** In our previous response, we also clarified that the kl divergence is not a tester.\ Please see below for more explanations. 1. Yes, we agree with your valuable observation that a large KL divergence does not imply a positive llh gap unless you have the other side of inequality.\ Our WScore or BScore is not designed to calculate KL divergence since the human distribution is unknown. Instead, it is used to estima […]

`[post-rebuttal, set aside]` updated: ⏐ I read the rebuttal that clarifies my misunderstanding. ⏐ The current logic in the paper flows as "let's introduce llh gap, then llh gap implies KL large, then let's forget about KL because it is hard to compute/estimate and go back to llh gap"; some text in rebuttal appears to be more clear to me. ⏐ Also, it would be helpful to discuss more on why KL estimation is harder than llh gap (as both are effectively relating human and machine distributions) like llh requires smaller sample from human. ⏐ Nevertheless, I think in general the paper is above iclr bar.

## Example 9 — review `4EMw0SSXNn` (ICLR 2025)

23 units, 12 critiques, 4 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper's main strength lies in its analysis of the importance of different modules for various speech processing tasks.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The findings indicate that, within the encoder-decoder framework, pruning the decoder is more effective for speech translation (ST) and automatic speech recognition (ASR) tasks.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper is well-written and easy to understand with minor typos and incomplete sentences.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> The size of dataset (20 hours) used is too small to make general claims.

Author response — `new_experiment` (units 3–23):

> We appreciate your observation. Indeed, the limited size of the dataset was a valid concern. To address this, we conducted additional experiments by incorporating the VoxForge dataset, which includes the same languages, into the original dataset. This resulted in a joint dataset for ASR task, whose sizes are as follows: | Language | Europarl-ST | + voxforge | | French | 21.06 | 41.04 | | German | 17.71 | 63.40 | | Italian | 20.93 | 37.00 | It is true that the absolute increase in data size is not substantial. However, we believe that this amount of additional data is sufficient to evaluate the […]

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> The authors do not compare their results with any other pruning methods. Like the effect of simply removing the layers, instead of different modules within, on the performance on the given the size of the dataset used in the study.

Author response — `new_experiment` (units 25–55):

> Thank you for your feedback. In response to the feedback, we conducted additional experiments comparing module-based pruning, layer-level skipping, and unstructured pruning. These experiments were carried out using our joint ASR and ST dataset. We report the WER for German ASR, where the encoders and decoders were pruned separately. The sparsity patterns used in these experiments are illustrated in Figure 13 in Appendix C. **Encoder** | Target Sparsity | Module Skip | Layer Skip | | 0.1             | 14.5        | 31.3       | | 0.3             | 15.0        | 32.0       | | 0.5             |  […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> While the paper focuses on reducing inference time, it doesn't address the computational overhead introduced by the dynamic pruning process itself and searching the best sparsity number during finetuning.

Author response — `clarification` (units 63–67):

> > While the paper focuses on reducing inference time, it doesn't address  the computational overhead introduced by the dynamic pruning process  itself and searching the best sparsity number during finetuning. Thank you. We calculated the FLOPs for each sparsity level and added them to Table 1. The computation overhead for determining sparsity during fine-tuning, including both the fine-tuning and evaluation processes, required approximately two days on a single A40 GPU. > Lack majour novelty

**Critique 7** — aspect `novelty`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> Lack major novelty.

Author response — `concession` (units 68–75):

> Although our method is indeed an extension of Peng et al. (2023), we have introduced novel contributions compared to Peng et al. (2023) in the following aspects: - Multilingual and Multitask Training: We trained our model in a multilingual and multitask setting. - Different Utilization of Gumbel-Softmax: We employed Gumbel-Softmax differently in our approach: that is, we used the straight-through Gumbel-Softmax estimator for training pruning masks. We realized that we did not adequately describe the second point in our paper. To address this, we included additional explanations in the section  […]

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> At line 285, the authors make a statement "This supports our initial question regarding the need for a large-scale decoder in ASR systems". This is different form the results in the paper, pruning the decoder a lot does not effect ASR performance much compared to encoder as shown in Figure 2.

Author response: none.

**Critique 9** — aspect `soundness`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> In Figure 1, it is not clear how mean pooling can be applied to the input of the transformer decoder given its autoregressive nature.

Author response — `clarification` (units 83–86):

> Thank you, the diagram could indeed be clearer. The mean pooling applies to the audio information, which is used to control the decoder. This does not interfere with the auto-regressive processing on the decoder side during inference. To clarify this further, we revised Figure 1 (a) and (b) to make it more apparent that this pertains to the audio information.

**Critique 10** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> Not able to understand after reading the paper, if the time reduction is from using the joint finetuned model or individual task finetuned model. I think it is for individual task finetuned models.

Author response — `clarification` (units 87–91):

> > Not able to understand after reading the paper, if the time reduction is from using the joint finetuned model or individual task finetuned  model. I think it is for individual task finetuned models. We apologize for not making this clear in the paper. The model used for inference is trained separately for each task, with individual models fine-tuned for ASR and ST tasks. We included this information in the caption of table 1.

**Critique 11** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> The paper simply extends the work of Peng et al. (2023b) by utilizing the model structure of a speech foundation model to address multilingual and multi-task scenarios and therefore lacks major novelty. Please provide more detailed comparison of their approach to previous work and their novel contributions beyond Peng et al. (2023b).

Author response — `clarification` (units 92–95):

> >  Please provide more detailed comparison  of their approach to previous work and their novel contributions beyond  Peng et al. (2023b). We provided a detailed explanation from the perspective of lack of novelty in response to the previous comment. Specifically, we clarified the differences in the use of Gumbel-Softmax in Section 3.3 and added a detailed formulation in the Appendix A. We also reproduced their results for comparison and included these results in Appendix B. **Reference**

**Critique 12** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> Not suited for joint pruning? As per the results, it is better to prune decoder in multitask setting. But authors report for the ASR and ST tasks SRC-ATT and SELF-ATT are individually important in the decoder. Therefore, the motivation to prune the modules in the joint finetuning is diluted.

Author response: none.

`[ignored]` Typo ? ⏐ [line 130] if out validation data >> if validation data ⏐ I think [at line 285] the sentence is incomplete. ⏐ [Please correct me if I am wrong].

## Example 10 — review `sCZKkXxuMV` (ICLR 2024)

13 units, 6 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> * This study focuses on a unique and critical problem wherein machine learning fairness is examined in an online context, with individual sample instances observed sequentially.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> * In such a scenario, determining group fairness attributes and executing backward propagation to modify model parameters necessitates retaining all prior samples, leading to computational complexities.

Author response: none.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> To address this, the paper introduces an effective framework for forward and backward propagations, taking advantage of statistical summaries from previous samples.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> * The presented algorithm consistently surpasses baseline techniques across all tasks. It is both empirically and theoretically robust and comprehensive.

Author response: none.

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> * Utilizing the aggregate of past statistics to adjust the model parameters poses a challenge. As the model parameters shift with each time step, past statistics, derived from earlier model parameters, might diverge significantly from what would be obtained if the model gradients were calculated using all the previously stored data. I'm curious if the authors could elaborate on the conditions under which using aggregated past gradients to update the current model would be successful or not.

Author response — `clarification` (units 3–9):

> Our proposed method, Aranyani, is a tree structure specialized and related learning algorithm designed to effectively use such aggregated computations. The tree structure is parameterized using a logistic network at each node. We compute fairness gradients by taking the derivative of node outputs. Crucially, this structure allows us to prove that the error in computing the fairness gradients cannot diverge in an unbounded manner. The theoretical results we propose rely solely on the assumptions of bounded inputs, a compact parameter set, and smooth activation functions, as well as a smooth tas […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> * The problem is framed in an online setting where the actual predictive labels are seen after the model makes its predictions. More realistically, if the model consistently underperforms, it could result in a shift in data distribution. Specifically, the minority group might cease supplying data for model updates. Could the author discuss how the proposed algorithm would operate under these circumstances?

Author response — `new_experiment` (units 10–17):

> Indeed understanding the performance of Aranyani under shifts in data distribution is an interesting research question. We have added results in an adversarial setting that is aligned with your proposal and report them in Appendix D (Subsection: Adversarial Stream). Specifically, we construct an adversarial stream of data using the Adult dataset, where we present Aranyani with 90% of the majority class samples followed by the entire minority class and the remaining 10% of the majority class samples. We also experiment with the inverse scenario where the minority class samples are presented bef […]

`[ignored]` Questions are provided in the weakness section.

## Example 11 — review `Wx9Om7UI3i` (ICLR 2024)

33 units, 4 critiques, 6 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> the overall quality of the paper is good, in that it even worked at all, and the lack of adhoc tricks. The biggest strength of this paper is that it has shown that code generation _can be_ done with a value network, despite the large number of state x action pairs needs to be considered, the unavailbility of a good initial Q function, and the volatility of the Q function "blowing up". Evaluation shown that the proposed method is on par with the policy based methods in terms of pass@k metrics. The knowledge that value-based approach for code generation can be done _at all_ is a great merit, and cannot be under stated. I find all the "tricks" presented in this work well founded and easy to understand. The reward hacking part is minimal and frankly very reasonable. Thus I am convinced this approach would work on different program synthesis domains just as well.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> lack of evidence on why we need to do this to begin with The following statement from the conclusion section is a very good motivation " it is recognized being sample-inefficient (see e.g. Nachum et al., 2017), meaning poorly using off-policy data, even data previously generated". Does this work actually demonstrate this with an experiment? I believe it should, to show (in a table) that the proposed method can "learn more with less", with x axis showing the amount of training data, and y-axis some performance metric. In case I have misread the paper and this is indeed one of the experiments, it should be top and foremost contribution this paper needs to claim. Currently this paper reads akin to "we did it because we can" but lacks the justification -- in the form of an experiment -- that this is something valuable to begin with. I could think of many other benefits of having a value function, for instance, sometimes people might want a top-k ranked programs, which could be tricky to do based on only policy, but very intuitive with a value based model. If the authors are able to justify their work with some experimental evidence, showing the advantages of a value-based modeling, this work will be that much better.

Author response — `clarification` (units 33–47):

> Although Nachum et al. [1] does not empirically demonstrate the sample inefficiency of policy-based methods, some empirical evidence could be found from other sources. For instance, [2] states that *``TD-style methods, such as off-policy actor-critic and Q-learning, are more sample-efficient ...''*, and supports this claim with empirical evaluation. Additional empirical comparisons can be found in public benchmarks, such as [OpenAI spinning up benchmark](https://spinningup.openai.com/en/latest/spinningup/bench.html), where policy-based methods often yield lower returns given the same number of […]

Author response — `new_experiment` (units 52–67):

> **A demonstrative experiment.** - **An illustrative MDP.** (An illustrative figure of this MDP can be found [anonymously here](https://www.dropbox.com/scl/fi/u9q95izjbphnfsngo2jit/mdp.pdf?rlkey=g11cvr12sp2kbsjudf8fju6ln&dl=0).) Consider a chain MDP, where there are $n+1$ states $s_0, \ldots, s_n$ with two actions LEFT and RIGHT, where LEFT at $s_i$ proceed to the previous state $s_{i-1}$ with reward $r=1$, and RIGHT always proceed to the next state with  $r=-1$ except moving to the terminal state $s_n$, which has $r = k\times H$, where $k \geq 2$ and $H$ is the episode length. The optimal stra […]

Author response — `clarification` (units 69–71):

> This is indeed one of our considerations. The details, of selecting top-$k$ programs by value functions, are given in Section 4. In addition, for instance, one may also derive beam search strategy that maximizes values rather than likelihood and we certainly agree with the reviewer that having a value function create further opportunities.

**Critique 3** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> this paper would benefit from a Figure1 that outline the overall "workflow" of the method. During reading of the paper, the phrase "which is yet another difficulty one must overcome to train a value function .... we introduce technique X to tackle this problem." The number of tricks quickly adds up, making the paper difficult to follow. I feel the paper is overboard with definition and philosophy of "what is policy-based" and "what is value-based / RL". I believe these things have a very technical definition that the community can all agree with. The clean story could've been "off-policy learning through value iteration for generation would be good, as it use less data. here's how to do it, here's an experiment showing how well we can do as a function of amount of human data required". Defining program synthesis as "generating program from natural language" is imprecise, as there are other works of "program synthesis" that generates program from input-output examples alone, or those that work with constraint solvers that generates programs from correctness specifications. A better wording could benefit here, as I instinctively reacted poorly by the opening definition of program synthesis, thinking it is way too narrow.

Author response — `clarification` (units 15–22):

> | Algorithm | Category     | On/Off-Policy | Objective                                                                                                          | | vanila PG | policy-based | on-policy     | $ L(\pi) = -\mathbb{E}_{\color{blue} \tau\sim\pi} [R(\tau)] $                                                      | | PPO       | policy-based | on-policy     | $ L(\pi) = -\mathbb{E}_{\color{blue} \tau \sim {\pi_k}} [ \frac{\pi(s, a)}{\pi_k(s, a)}\hat{A}(s, a) ] $    | | DQN       | value-based  | off-policy    | $ L(Q) = \mathbb{E}_{\color{blue} (s, a, s', r)\sim D} [(Q-\mathcal{B}^*Q)(s […]

Author response — `concession` (units 73–76):

> Thank you for pointing it out. We realize that we were narrowly focused in terms of program synthesis definition, because we were somewhat limited to the specific APPS dataset. It is very true that the program synthesis problem should be more general. We are delighted to revise our definition to be more accurate and encompassing, in line with the reviewer's suggestion.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> The "go to" solution of program synthesis in the presence of given input-output examples (test cases) is to simply generate a vast number of programs, test all of them against spec through execution, and pick the ones that passed the test cases. Thus, suppose I am a practitioner, the metric that I really care about is, given a synthesis problem, complete with natural language descriptions and a set of input-output test cases, and a time budget of 1 minute, can my synthesizer find a correct program? This allows different methods to be compared head to head. A "dumb" enumerator -- for instance, a bigram generator -- might actually be reasonable of it can generate vast numbers of programs quickly, and a "smart" enumerator might actually be non-performative due to the time it takes to sample a full program to even check. Thus, I would like to ask for the times it take to sample a full program on average, when compared against some of the other policy based methods.

Author response — `new_experiment` (units 78–87):

> We take 5 problems from APPS test set (id 0 - 4) as examples and sampled 1000 programs for each, using one RTX 4090 24GB graphics card, with maximum batch sizes that do not create OOM errors. The table below shows the sampling time (in secs) per 1000 programs, in the format of mean$\pm$std. Our method takes approximately 1.7 to 2.0 times longer to sample. | Temperature | CodeRL (batch size = 66) | Ours (batch size = 44)| | 0.4 | 291.18$\pm$56.08 | 495.78$\pm$189.35 | | 1.0 | 290.88$\pm$56.20 | 595.84$\pm$65.66 | **Remark on faster sampling.** While we originally proposed using $Q$ as logits fo […]

`[ignored]` ## quality: good ⏐ ### that it even worked at all ⏐ ### lack of ad-hoc "tricks" ⏐ ## significance ⏐ ## clarity ⏐ ## time to take sample?

## Example 12 — review `bSDTzReYcN` (ICLR 2025)

28 units, 11 critiques, 7 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The idea to utlize (layer) input-space null projection is built atop the work of GPM (Saha et al'21) in continual learning and its use here for the purposes of teleportation is neat.

Author response: none.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - This extends the applicability of the approach and might draw further interest in these methods.

Author response: none.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The resulting method is also more efficient than symmetry teleport based methods.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - The experiments cover a variety of scenarios, wherein the method results in faster convergence while being as good if not slightly better than the baselines.

Author response: none.

**Critique 5** — aspect `soundness`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> It is unclear how much excess time is being used during the process of teleportation, and if the gains in faster convergence are worth the extra effort.

Author response — `clarification` (units 2–4):

> Zhao et al. (2022) demonstrated that the convergence of symmetry teleportation with respect to loss versus wall-clock time is faster compared to non-teleportation algorithms, consistent with the trends observed in the loss versus epoch graph. Since our results have shown that our method significantly outperforms their symmetry teleportation algorithm in terms of efficiency, it can be reasonably inferred that our approach would exhibit superior performance on the loss versus wall-clock time convergence graph as well. We acknowledge the importance of presenting these graphs and will incorporate  […]

**Critique 6** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> I would like to see if the solutions reached with teleportation differ qualitatively to those reached without. Can the authors make the LMC curves (Frankle et al, 2019) to see if there are barriers between the reached solutions?

Author response — `disagreement` (units 6–11):

> The primary focus of this paper is to extend the teleportation technique to a broader class of functions while proposing a more efficient algorithm. The use of gradnorm as the teleportation objective function was intended as a demonstration of the effectiveness of our method in accelerating convergence and is not necessarily designed to enhance generalization. We appreciate your observation regarding this point, as it highlights an important branch of research concerning the choice of teleportation loss. As demonstrated in Zhao et al. (2023), the selection of teleportation loss can indeed yiel […]

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> I think it would be interesting to compare the results of your method to group action based ones in a simple setting with MLPs to see in what ways the methods differ.

Author response — `disagreement` (units 21–30):

> To date, there are only two teleportation algorithms: symmetry teleportation (Zhao et al., 2022) and the linear approximation method (Mishkin et al., 2024). None of the existing works compare against any other teleportation algorithms, as conducting a fair comparison is extremely challenging. This difficulty arises because the mechanisms for maintaining the invariance of loss during teleportation differ among the approaches. The only reasonable approach we can think of is to compare the methods using their respective best hyperparameter settings. However, grid-searching for the optimal set of  […]

**Critique 8** — aspect `soundness`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> It is not clear to me how much do the hyperparameters of teleportation, as well as SVD thresholds, have to be tuned. Can you present a study showing the robustness (or lack of)?

Author response — `clarification` (units 13–18):

> The sensitivity of teleportation hyperparameters is indeed high, as noted in the discussion section. For instance, Zhao et al. (2022) demonstrated that performance can improve significantly by scheduling more teleportation epochs and steps. The hyperparameters used in our experiments primarily follow the conventions established in their work. The sensitivity of hyperparameters also highlights the need to carefully study the tradeoff between performance and computational cost, which makes algorithmic efficiency even more critical. Therefore, the primary motivation behind our work is to provide  […]

Author response — `clarification` (units 19–19):

> The ablation studies on the threshold of SVD is present in section 4.5.

**Critique 9** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> A lot of the citations are plain wrong. E.g., I don't think the citations are representative, and some are just plain wrong: - Hessian matrix (Sun et al., 2019). - Adam (Kashyap 2022) - ReLU (Agarap, 2018) - MLP (Taud & Mas, 2018). - CNN (Li et al., 2021). - multi-head self-attention layers (Wen et al., 2022).

Author response — `clarification` (units 32–35):

> We sincerely thank you for pointing this out. We have carefully reviewed and updated all citations to ensure they are accurate and appropriately representative of the referenced work. Additionally, we have revised the input space to be explicitly described as the layerwise input space for improved clarity. We have also corrected the title to reflect "Tiny ImageNet" instead of "ImageNet" for consistency.

**Critique 10** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> Instead of input-space, quality it as input space of layers. Otherwise it is confusing.

Author response — `clarification` (units 32–35):

> We sincerely thank you for pointing this out. We have carefully reviewed and updated all citations to ensure they are accurate and appropriately representative of the referenced work. Additionally, we have revised the input space to be explicitly described as the layerwise input space for improved clarity. We have also corrected the title to reflect "Tiny ImageNet" instead of "ImageNet" for consistency.

**Critique 11** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> Also, please fix the image titles to TinyImageNet (which currently say ImageNet).

Author response — `clarification` (units 32–35):

> We sincerely thank you for pointing this out. We have carefully reviewed and updated all citations to ensure they are accurate and appropriately representative of the referenced work. Additionally, we have revised the input space to be explicitly described as the layerwise input space for improved clarity. We have also corrected the title to reflect "Tiny ImageNet" instead of "ImageNet" for consistency.

`[ignored]` - **Wall-clock comparison of convergence:** ⏐ - **Difference in arrived solutions:** ⏐ - **Comparison to group action based method:** ⏐ - **Stability of the hyperparameters**: ⏐ - **Poor referencing of related work:** ⏐ See weaknesses section. ⏐ Regarding presentation, I would also make a few suggestions.

## Example 13 — review `1M1dUwvMyp` (ICLR 2025)

26 units, 14 critiques, 6 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - As LLM deployment differs significantly on edge devices due to limited computing resources and the use of private data, the comprehensive evaluation and criteria for optimization techniques are crucial topics

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - The authors conduct comprehensive and well-defined experiments

Author response: none.

**Critique 3** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The authors’ findings are novel, as they can guide future research directions

Author response: none.

**Critique 4** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> - In the introduction, many statements and findings seem to pertain to training (fine-tuning). Clearly stating the focus and deployment scenario would make the paper’s sections clearer (fine-tuning, inference, or both?)

Author response: none.

**Critique 5** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> - Instead of focusing on individual techniques for LLM deployment, what about combining two or three methods? For example, RAG and LoRA could potentially be applied together

Author response — `disagreement` (units 3–7):

> We appreciate your interest in exploring combined techniques like RAG+PEFT. While this is definitely an interesting direction, there was a practical consideration behind our choice to study these methods separately. In real-world edge deployments, we often encounter scenarios where resource constraints make parameter updating impossible, forcing users to rely solely on RAG-based solutions. Additionally, these two methods serve fundamentally different purposes - RAG allows knowledge integration without touching the model parameters, while PEFT enables model adaptation through careful parameter  […]

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> - I understand the page limit and the authors’ efforts to address this issue, but many supporting results are in the Appendix, making it somewhat difficult to follow thoroughly.

Author response — `concession` (units 8–11):

> Regarding the extensive use of appendices - we hear your concern about reading convenience, and we genuinely apologize for any difficulties this may have caused. We faced a challenging trade-off between providing comprehensive experimental evidence and maintaining a focused main narrative. While we chose to keep detailed results in the appendices for interested readers, we understand this could be better structured. Your feedback helps us recognize the need to better highlight key findings in the main sections while keeping supporting details accessible but not overwhelming.

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> - The authors experiment with specified models on particular devices, considering memory constraints. What about testing similar models on different devices? Training a model for one hour on different devices might yield different insights

Author response — `concession` (units 12–15):

> On the hardware evaluation front, we acknowledge that our primary focus on memory constraints could be expanded. Memory often represents the first bottleneck in edge deployment, which guided our initial focus. However, your suggestion about broader hardware metrics and cross-device comparisons opens up valuable directions for future investigation. This kind of comprehensive evaluation would indeed provide even more practical insights for the community.

**Critique 8** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> - I believe many aspects, including the combination of design choices, remain unexplored in this study. Clearly specifying which aspects or potential experiment cases are covered and which are not would help readers better understand the study’s scope

Author response — `concession` (units 16–19):

> The ultimate goal of our work is to provide empirically-grounded guidance for deploying LLMs on edge devices, moving beyond intuitive assumptions to concrete evidence. We believe our extensive experimental results offer valuable reference points for practitioners while raising important questions for future research. Your thoughtful feedback has helped us identify areas where we can expand our investigation to make the work even more valuable to the community. We're excited to explore these directions in our future research.

**Critique 9** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> I suggest the authors include and compare the computing resources, not only RAM, of the devices to give readers a better understanding of the range of resources considered in the study

Author response — `concession` (units 12–15):

> On the hardware evaluation front, we acknowledge that our primary focus on memory constraints could be expanded. Memory often represents the first bottleneck in edge deployment, which guided our initial focus. However, your suggestion about broader hardware metrics and cross-device comparisons opens up valuable directions for future investigation. This kind of comprehensive evaluation would indeed provide even more practical insights for the community.

**Critique 10** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> Is the focus on computing resources solely on memory?

Author response — `concession` (units 12–15):

> On the hardware evaluation front, we acknowledge that our primary focus on memory constraints could be expanded. Memory often represents the first bottleneck in edge deployment, which guided our initial focus. However, your suggestion about broader hardware metrics and cross-device comparisons opens up valuable directions for future investigation. This kind of comprehensive evaluation would indeed provide even more practical insights for the community.

**Critique 11** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> Can they be considered as alternatives to one another?

Author response — `concession` (units 12–15):

> On the hardware evaluation front, we acknowledge that our primary focus on memory constraints could be expanded. Memory often represents the first bottleneck in edge deployment, which guided our initial focus. However, your suggestion about broader hardware metrics and cross-device comparisons opens up valuable directions for future investigation. This kind of comprehensive evaluation would indeed provide even more practical insights for the community.

**Critique 12** — aspect `clarity`, severity `minor`, polarity `neutral`, target `section`, actionable `True`

> - (minor) Rather than “performance,” please specify the exact metrics measured

Author response: none.

**Critique 13** — aspect `clarity`, severity `minor`, polarity `neutral`, target `figure_table`, actionable `True`

> - Figure 9 shows five models, not 6, as mentioned in the caption.

Author response: none.

**Critique 14** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> - The results suggest that insights vary significantly based on task type or complexity. Is there a way to categorize or quantify task characteristics or difficulty before running the tasks?

Author response — `concession` (units 16–19):

> The ultimate goal of our work is to provide empirically-grounded guidance for deploying LLMs on edge devices, moving beyond intuitive assumptions to concrete evidence. We believe our extensive experimental results offer valuable reference points for practitioners while raising important questions for future research. Your thoughtful feedback has helped us identify areas where we can expand our investigation to make the work even more valuable to the community. We're excited to explore these directions in our future research.

`[ignored]` Including some curiosity in weakness, I also raise the following questions. ⏐ - Appendix A.1 shows different edge devices. ⏐ - In Table 3, the data samples per hour measured by the A10 GPU are illustrated. ⏐ However, as stated earlier, processors like CPUs, GPUs, and mobile-targeted SoCs show significantly different computation times. ⏐ - RAG and LoRA are quite different techniques, with one altering the model structure and the other not. ⏐ I also think they serve different purposes.

## Example 14 — review `QyowjD8GXV` (ICLR 2025)

35 units, 8 critiques, 3 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> This work provides an original extension to morphology+control co-optimization frameworks that explicitly address geometric symmetry in policy learning.

Author response: none.

**Critique 2** — aspect `reproducibility`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The authors made an effort to formalize their policy architecture with mathematical definitions, which should help reduce potential misunderstandings when others attempt to reproduce their results.

Author response: none.

**Critique 3** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> Co-optimization of morphology and control is an important longstanding unsolved problem. Supporting a diverse set of morphologies with a more efficient controller would reduce the time needed for designing morphology-specific network architectures. Attention and effort in this area has significance for robotics and other forms of "embodied intelligence".

Author response: none.

**Critique 4** — aspect `novelty`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> Lack of novelty The primary contribution of this work is a substitution of the reinforcement learning policy module from the Transform2Act approach with an equivariant GNN. Compared to the work cited by authors (Chen et al., 2023 https://arxiv.org/abs/2305.18951) (Chen et al., 2024 https://arxiv.org/abs/2407.12505), this submission appears to be a repackaging of an existing subequivariant reinforcement learning idea with a different problem setup. This submission reuses the same local reference frame (LRF) transformation as in https://arxiv.org/abs/2407.12505 with the same proof process in their appendix. As far as I can tell, the only appreciable difference is the addition of a relatively simple translation to the Og(3) setup in https://arxiv.org/abs/2407.12505 forming Eg(3). A more compelling contribution would include a demonstration of significant differences in results.

Author response — `disagreement` (units 7–21):

> Thank you for your feedback regarding the novelty of our work. We would like to clarify that adapting existing methods to address significant problem setups is a common and valuable approach in impactful research. For instance, AlphaGo combined MCTS with DRL to tackle the complex game of Go; AlphaFold series utilized existing Transformer and diffusion model  to predict protein folding; GPT-3 scaled up transformer models with larger datasets and parameters for natural language processing tasks; and DALL-E employed transformers for text-to-image generation. These examples demonstrate that applyi […]

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> While the authors claimed their setup can inject symmetry into generated morphological designs, their claim is not well supported. 1. Can you provide a concrete analysis of the contribution of subequivariant policy in morphology evolution?

Author response — `clarification` (units 26–37):

> We thank the reviewer for highlighting concerns about symmetry and generalizability across varied morphologies. Our primary goal is not to enforce symmetry in morphology per se, but rather to inject geometric symmetry into the policy module to leverage the symmetry inherent in real-world environments and dynamic systems. This enables a more efficient co-optimization of morphology and control. The resulting symmetry in morphology is an emergent property, not the intended objective of our approach. - To evaluate the effectiveness of our method, we provided visualizations (Fig. 10 for Ant, Fig. 6 […]

Author response — `clarification` (units 40–50):

> > Q1: Can you provide a concrete analysis of the contribution of subequivariant policy in morphology evolution? > Q2: Can you provide morphology metrics figures over time? Such as the length of limbs, and compute the symmetric error of design by comparing the difference of limb length divided by total limb length? Thank you for the thoughtful feedback. We would like to reiterate that our approach focuses on embedding geometric symmetry in the policy module to exploit the inherent symmetry of real-world environments and dynamic systems, thus enhancing the co-optimization of morphology and contr […]

Author response — `new_experiment` (units 83–102):

> > Morphological Evolution Analysis. We acknowledge your suggestion regarding analyzing the features of evolved morphologies over time. To address this, we have incorporated additional visualizations and discussions in the supplementary material to provide more insight into the co-evolution process: - **Step-by-Step Visualization**: As shown in **Figure 10 (main text)**, we present a step-by-step visualization of the morphology transformation within a single episode. This illustrates the trajectory of morphology transformations during one complete episode of training. - **Training (Evolution) P […]

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> Lack of evidence of generalizability Although the symmetry enhancement is the core claim, improved symmetry was only explored within a single basic agent skeleton -- the ant morphology. There was no metric or quantitative analysis to test the consistency of symmetry improvement across varied morphologies, or how the improvement of implementing LRF transformation in the policy module affects the optimization algorithm. Without visualizations of generated morphologies from additional environments, and without a symmetry-based metric to measure the improvement across different setups, it is difficult to assess the claims of the submission. 2. Can you provide morphology metrics figures over time? Such as the length of limbs, and compute the symmetric error of design by comparing the difference of limb length divided by total limb length? 2. Can you analyze the features of the group of evolved morphologies at each point of the timeline using multiple trials, and explain how your policy module affects evolution? 3. Can you run experiments starting from different morphologies, and introduce varying levels of freedom (e.g. only allow attribute transform, allow attribute transform plus morphology transform with a certain degree, fully allow both) for each starting point?

Author response: none.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> Lack of experiment design and analysis Following up on the above point, the only metric that was considered was reward. In two of the three explored benchmark environments (the humanoid and sumo) the morphology transformation was omitted and only attribute transformations were possible. In this reduced setting, it was unclear how morphology metrics changed over time (e.g. the limb lengths on both sides of the agent) should be readily available but was not extracted and analyzed. However the submission claims “integrating morphology evolution with sub-equivariance yielded a synergistic effect” (Sect. 4.3) which is not supported by the experiments and could simply be the policy network producing better control under LRF transformation that are independent of morphology. 4. Can you rewrite the equations, especially 7-17, and move unnecessary details to the appendix to clear space for more experiments?

Author response — `clarification` (units 53–58):

> In Equation (3), the symbol “m” in `mathrm` format represents morphology. In Equations (9-11), “m” is written in standard math font and represents the message in the graph neural network. We will provide further clarification on the notations and formulae in Equations (7-17) to improve readability. These equations are critical to our method and form the core of the subequivariant framework. While the equations themselves are indispensable, we have moved unnecessary derivations to the appendix to ensure the main content remains clear and accessible for all readers. Please refer to our updated p […]

**Critique 8** — aspect `clarity`, severity `major`, polarity `negative`, target `section`, actionable `True`

> Lack of clarity The mathematical notation was inconsistent and rather confusing. For example, symbols like “m” are overloaded with different meanings across subscripts (equation 3), superscripts (equation 3), and variables (equation 9, 10, 11) without further clarification of meaning in a verbal format, which undermines the clarity of the theoretical framework. In addition to restructuring the mathematical framework and standardizing notion, explaining the symbols used in equations with natural language, a few words even, would improve clarity immensely -- a symbol table would be ideal.

Author response: none.

`[ignored]` Originality ⏐ Quality and clarity ⏐ Significance

## Example 15 — review `CEQskxkbUn` (ICLR 2024)

18 units, 7 critiques, 6 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - This method incorporates time information into the branch net using a GNN and enables time extrapolation prediction for PDE.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> - Compared to other GNN-based PDE solvers, GraphDeepONet shows superior accuracy in predicting solution at arbitrary positions on irregular grids.

Author response: none.

**Critique 3** — aspect `soundness`, severity `major`, polarity `positive`, target `general`, actionable `False`

> - The proposed method has a theoretical guarantee that it is universally capable of approximating continuous operators for arbitrary time intervals.

Author response: none.

**Critique 4** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Overall this paper is well-written, and the presentation is clear and easy to follow.

Author response: none.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - 1D Burger equation and 2D shallow water are much easier PDEs. In most papers, 2D incompressible Navier-Stokes equation is considered as a test PDE. I highly recommend authors to add experiments on 2D NS equation to show the effectiveness of their method.

Author response — `new_experiment` (units 5–10):

> **A.** Thank you for the suggestion. As you suggested, it would be beneficial to enhance the demonstration of the strengths of our GraphDeepONet by incorporating experiments on more challenging datasets commonly used in the field of operator learning. We added experiments on the more complex dataset: 2D Navier-Stokes equations. We utilized data from the setting of the 2D Navier-Stokes equations for a viscous, incompressible fluid in vorticity form on the unit torus, as employed in [1,2]. As can be seen in Table 2, our approach exhibits similar trends for the N-S equation across different datas […]

**Critique 6** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> - In table 1, the performance of GraphDeepONet are consistently worse than FNO-2D, and FNO-2D is not a recent model on regular grid. This could be a major weakness. I recommend authors compare their method with state-of-the-art model on regular grids, such as FFNO [2] and GFNO [3].

Author response — `new_experiment` (units 12–23):

> **A.** Thank you for suggesting relevant baselines for comparison. Our focus is on comparing our model with existing graph neural network(GNN)-based models capable of simulating time-dependent PDEs on irregular domains, such as MP-PDE and MAgNet. Consequently, instead of considering variations of FNO, we concentrated on GNN-based PDE solvers for experiment baseline. Therefore, FNO, being a fundamental model in operator learning area, was compared only on regular grids. However, as your insightful suggestion, we have added comparisons with modified FNO models applicable to both regular and irre […]

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - For irregular domain, there are several FNO-based method can handle irregular grids, such as GeoFNO [1] and FFNO[2]. For completeness, I think these methods should also be considered as baselines on irregular grids.

Author response — `new_experiment` (units 12–23):

> **A.** Thank you for suggesting relevant baselines for comparison. Our focus is on comparing our model with existing graph neural network(GNN)-based models capable of simulating time-dependent PDEs on irregular domains, such as MP-PDE and MAgNet. Consequently, instead of considering variations of FNO, we concentrated on GNN-based PDE solvers for experiment baseline. Therefore, FNO, being a fundamental model in operator learning area, was compared only on regular grids. However, as your insightful suggestion, we have added comparisons with modified FNO models applicable to both regular and irre […]

`[ignored]` The evaluation of the proposed methods is not enough, specifically: ⏐ [1] Li, Zongyi, et al. "Fourier neural operator with learned deformations for pdes on general geometries." arXiv preprint arXiv:2207.05209 (2022).\ ⏐ [2] Tran, Alasdair, et al. "Factorized fourier neural operators." arXiv preprint arXiv:2111.13802 (2021). ⏐ \ ⏐ [3] Helwig, Jacob, et al. "Group Equivariant Fourier Neural Operators for Partial Differential Equations." arXiv preprint arXiv:2306.05697 (2023). ⏐ see weakness part

## Example 16 — review `RC50hLD0Xu` (ICLR 2025)

9 units, 6 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The paper offers a comprehensive analysis of challenges in evaluating safeguards for open-weight language models, showing how various factors affect their perceived effectiveness.

Author response: none.

**Critique 2** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. Through case studies of two defense techniques, the authors highlight key failure modes and evaluation pitfalls, revealing the limitations of current methods.

Author response: none.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 3. The insights provide valuable guidance for safety and security research, stressing the need for rigorous testing across diverse scenarios to ensure defense robustness.

Author response: none.

**Critique 4** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. The paper highlights the challenges of creating durable safeguards but does not propose new methods or solutions to address these issues, instead calling for further research, which leaves the problem unresolved.

Author response — `clarification` (units 9–22):

> * **The point of this paper is not to attempt to solve the problem but to establish baseline evaluation principles for future work that attempts to make progress.** A painful lesson we learned from AI security research over the last decade is that many defenses failed to withstand rigorous scrutiny due to flawed or incomplete evaluations (e.g., [1,2]). This highlights the importance of establishing standard baseline evaluation principles for evaluating defenses, as exemplified by [3,4]. Only if we first address the meta-problem of evaluating defenses can we genuinely track progress in building […]

**Critique 5** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2. The analysis is comprehensive but limited to two specific methods (RepNoise and TAR), which narrows its overall applicability. 1. The paper only discusses two defense methods (RepNoise and TAR). Do other potential defenses face similar evaluation challenges?

Author response — `clarification` (units 37–44):

> > The analysis is comprehensive but limited to two specific methods (RepNoise and TAR), which narrows its overall applicability. > The paper only discusses two defense methods (RepNoise and TAR). Do other potential defenses face similar evaluation challenges? Our experiments in this paper are to show how the security evaluations in existing work for durably safeguarding open-weight LLMs are flawed and lead to overestimation of the defenses' effectiveness. We primarily focus on RepNoise and TAR, because these were the only two papers that claim to build durable safeguards for open-weight LLMs b […]

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 3. The detailed exploration of how minor changes in configurations affect performance might be hard to follow for some readers. 2. Could the authors explore potential improvements to the evaluation process or provide preliminary ideas for solutions?

Author response — `clarification` (units 50–52):

> We added a new Table 3 (See L957-L962) to better introduce the hyperparameter configurations used in RepNoise. We have detailed the hyperparameter configurations used by TAR in Tables 1 and 5. **4.

Author response — `new_experiment` (units 56–65):

> In our rebuttal revision, we added Appendix A to provide a more explicit and actionable checklist of items to consider for future evaluations of defenses to avoid similar pitfalls we identified in our paper. The checklist includes tips for: (1) Checking the robustness of the defense against attacks with different random seeds; (2) Employing widely used and thoroughly tested attack implementations for defense evaluation; (3) Ensuring the defense either restricts its threat model to scenarios it can reliably address or undergoes comprehensive evaluation against a wide range of possible attacks w […]

## Example 17 — review `B1N5u5WMZk` (ICLR 2025)

17 units, 4 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. This paper addresses a practical problem by examining the failures of defense mechanisms against jailbreak attacks in LMs.

Author response: none.

**Critique 2** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 2. The authors introduced a unique test case, the "Purple Problem", that isolates enforcement failures through a clear and simple definition.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 3. The authors conducted a systematic evaluation of multiple defense strategies and provided comprehensive insights.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> My primary concern is that the problem setting in this paper may not fully capture the complexities of real queries. 1. The authors utilized a synthetic dataset generated through prompt engineering, which may introduce bias and fail to reflect the distribution of real queries. 2. The method identifies unsafe content simply by preventing the LMs from generating the word "purple", which may fail to address unsafe contents such as indirect harmful statements or different cases for a same claim. 3. Alignment between training data and queries is important as it will impact the quality of the outputs generated by LLMs [1]. Howver, in this paper, the distribution of the queries for evaluation can differ a lot from real-world queries to AI systems, which undermines the reliability of the evaluation results. 4. Some content can be identified as unsafe under most scenarios but may be safe in some specific contexts. For example, "how to kill xxx" is usually unsafe, but "how to kill a process in Linux" is safe and should produce correct answers. This paper classifies the outputs into "yellow" and "purple". Does the Purple Problem cover such cases? 5. Though the authors claim something like "The evaluation protocols in (Zou et al., 2023; Jain et al., 2023; Wei et al., 2023b; Robey et al., 2023; Xiong et al., 2024) all consider an output unsafe if it does not contain strings such as "I’m sorry"" in the paper, the case is different. Semantically, "I'm sorry" implies the answer to the query might be harmful or the LLM does not have enough knowledge to answer the question, thus it can be used as a flag for unsafe answers. However, this paper filters unsafe contents by detecting "purple", which lacks such semantic meaning and may not be an effective indicator.

Author response — `clarification` (units 4–11):

> We thank you for asking this. The Purple Problem does not match distributions but is meant to be an easier version of any real-world complex definition and serve as a lower bound for a testbed. Success in defending against the word ‘purple’ does not imply success on real-queries, but failure to defend against ‘purple’ would mean failure in more complex settings. If enforcements fail in this simple setting, how can we defend in the real world? Under the Purple Problem, we are able to test the full capacity of enforcements and attacks and find that enforcements are vulnerable to adaptive attacks […]

Author response — `clarification` (units 14–20):

> >__The method identifies unsafe content simply by preventing the LMs from generating the word "purple", which may fail to address unsafe contents such as indirect harmful statements or different cases for a same claim.__ We thank the reviewer for pointing this out as the discussion on what the Purple Problem represents is invaluable for our paper. We agree that indirect harmful statements may have a different structure than simply preventing a word. It is more complex. However, the Purple Problem serves as the simplest-case evaluation in the easiest setting. A defense that can prevent the word […]

Author response — `clarification` (units 21–28):

> >__Some content can be identified as unsafe under most scenarios but may be safe in some specific contexts. For example, "how to kill xxx" is usually unsafe, but "how to kill a process in Linux" is safe and should produce correct answers. This paper classifies the outputs into "yellow" and "purple". Does the Purple Problem cover such cases?__ This is exactly what the Purple Problem is trying to address. Since definitions are complex, it is unsure whether defenses fail because they were trained for a poor definition or because the enforcement mechanism is weak. The Purple Problem is a simple an […]

Author response — `clarification` (units 29–35):

> >__Though the authors claim something like "The evaluation protocols in (Zou et al., 2023; Jain et al., 2023; Wei et al., 2023b; Robey et al., 2023; Xiong et al., 2024) all consider an output unsafe if it does not contain strings such as "I’m sorry"" in the paper, the case is different. Semantically, "I'm sorry" implies the answer to the query might be harmful or the LLM does not have enough knowledge to answer the question, thus it can be used as a flag for unsafe answers. However, this paper filters unsafe contents by detecting "purple", which lacks such semantic meaning and may not be an ef […]

`[ignored]` [1] "A holistic approach to undesired content detection in the real world" from OpenAI ⏐ see weakness

## Example 18 — review `j0RpIOEsfz` (ICLR 2025)

21 units, 15 critiques, 6 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> A better understanding of adversarial attacks and robustness of neural networks remains an important topic.

**Critique 2** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> To the best of my knowledge, the paper's conclusion that adversarial robustness can only be $1/\sqrt d$ is already known [1, 2] and has been shown in more general settings.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The theoretical analysis is weak, as all the theorems make important and unrealistic assumptions, i.e. normal distribution of the data, constraints on the weight matrices.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - $\ell_2$ is the only distance considered, several other papers have proposed theoretical analysis with respect to the $\ell_p$ norm (see [1, 2]).

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Theorem 1 spans 2 full pages to show a probabilistic bound over a linear network with several assumptions, but it's unclear why the authors came to all this work, since the distance to the decision boundary for a linear network can be computed in closed form.

**Critique 6** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `False`

> - The paper proposes a total of 7 theorems, each of which is accompanied by a proof.

**Critique 7** — aspect `related_work`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> - The paper does not propose any related work

**Critique 8** — aspect `significance`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> - The paper does not provide usable results

**Critique 9** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The experimental section only proposes toy experiments

**Critique 10** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Instead of presenting a list of theorems, the authors should motivate their analysis and explain why it's interesting.

**Critique 11** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> How can these results help the community?

**Critique 12** — aspect `significance`, severity `major`, polarity `negative`, target `general`, actionable `True`

> Even if the theoretical analysis has assumptions, how can it be useful for real-world applications?

**Critique 13** — aspect `related_work`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> - Authors should propose a related work section and compare their analysis with other work.

**Critique 14** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> How is their analysis better or novel than the competing work?

**Critique 15** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> - Authors should propose real-world experiments, adversarial robustness is now a mature research topic, and large-scale (e.g. ImageNet) experiments should be performed.

`[ignored]` Suggestions for improving the paper: ⏐ [1] Yang et al. Randomised smoothing of all shapes and sizes. ⏐ ICML 2020 ⏐ [2] Kumar et al. Curse of Dimensionality on Randomised Smoothing for Certifiable Robustness. ⏐ ICML 2020 ⏐ See suggestions for improving the paper.

## Example 19 — review `GhiqzVeCDM` (ICLR 2025)

64 units, 5 critiques, 4 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> To the best of my knowledge, the main strength of this work is that it uses real email data spanning a 20-year period from a single individual. This provides a strong foundation for developing a realistic personalized LLM.

Author response: none.

**Critique 2** — aspect `clarity`, severity `major`, polarity `negative`, target `general`, actionable `True`

> I noticed some errors in the presentation of the text, as well as certain aspects of the experimental stage that could have been improved. While the work has a solid foundation, I feel that both the presentation and the development of the experiments were somewhat rushed. Below, I will outline the specific points I identified. I should also mention that the methodology and the creation of the model, called A-clone, do not appear particularly unique to me. The novelty of this work seems to derive primarily from the data, which could potentially impact the model's quality. In the related works section, you mention several papers that, in my opinion, could have influenced and improved your experimental setup. However, it seems that these works were not utilized. It gives the impression that you referenced these papers more for citation purposes than to fully understand them and build upon their ideas. A1) While it is clear from reading the text that your data are in English, this should be explicitly mentioned in both the abstract and the introduction. A2) Typos A2.1) Since you used the abbreviation LLM for Large Language Models (see line 034), you should consistently use this abbreviation throughout the text. Therefore, please revise the text in lines 081, 092, 113, 159, 427, 488, and others. A2.2) The same applies to the abbreviation Supervised Fine-tuning (see line 112). Please correct the term on line 125. A2.3) In several instances, you did not correctly apply spaces, particularly near references. Please review and correct this in lines 083, 088, 089, 098, 099, 101, 102, 204, 209, 248, and so on. A3) As mentioned in the author guidelines (see https://iclr.cc/Conferences/2025/AuthorGuide), you are encouraged to include a Reproducibility Statement at the end of the main text. This statement should detail the efforts made to ensure reproducibility and include any necessary information for those wishing to replicate your results.

Author response — `clarification` (units 4–7):

> **A1)** We now explicitly state in both the abstract and the introduction that the data were in English. **A2.1)** We have modified those parts by using the LLM abbreviation. **A2.2)** We have modified those parts by using the SFT abbreviation. **A2.3)** We have carefully reviewed and corrected the spacing issues for the references throughout the manuscript.

Author response — `new_experiment` (units 8–9):

> **A3)** Thank you for your suggestion. We have added a reproducibility statement at the end of the main paper, located before the references section on page 11.

**Critique 3** — aspect `reproducibility`, severity `major`, polarity `negative`, target `general`, actionable `True`

> B1) In the introduction (lines 042-046), you mention that A-clone is fine-tuned exclusively with private personal data from a typical individual, but you do not mention whether you obtained permission to use that data. Additionally, I did not find any statement from this individual indicating their approval for the use of their data. B2) Admittedly, your experiment is quite interesting, as I have not come across any similar studies in the literature that involve email data collected over a 20-year period from a single user. However, I believe the experiment is limited by the small number of users you selected. While it may be relatively straightforward to clone the characteristics of a single user from an LLM, if your experiment had involved two or more users, it would be harder to guarantee that the approach is effective. In practice, such a tool should be tested on large datasets from various users. This is where an LLM’s capability to distinguish individual characteristics would be most valuable, and generally distinguish if this model overfits the data or really understands the character of a person. B3) Regarding the anonymization of the data, you mention in lines 104-107 that in most cases, the data are anonymized and difficult to trace, which is why you chose not to apply any anonymization technique. However, in my view, anonymization is essential to protect the privacy of the data, especially in your case, where the data span a 20-year period. Failing to implement anonymization could encourage both the academic community and the industry to overlook this crucial aspect of user privacy. B4) Another point I raised concerns the questions you asked the LLM and compared to the ground truth of person A. It’s important to examine the distribution of topics in these questions. For example, in the paper "Does GPT-4 pass the Turing test?" by Cameron R. Jones and Benjamin K. Bergen (2024), which you reference, the authors use a variety of question types, ranging from personal information to general knowledge. This approach helps determine whether the LLM truly understands the personality and behavior of the person or simply overfits to their data. In the same paper, authors gave an option to tester volunteers to explain why they believed a certain response was generated by an AI, which could provide you with further insights into the quality of your model. You mention in lines 137-148 that you use a variety of questions to cover a wide range of topics. Please add a plot that shows the distribution of questions topics to wrong/correct response prediction of tester volunteers.

Author response — `clarification` (units 10–14):

> **B1)** We have revised the manuscript to explicitly state that A's explicit permission was obtained prior to collecting and using their personal data. This clarification has been added to the introduction part (line 050) **B2)** Thank you for your valuable feedback. We fully acknowledge this limitation and agree that expanding the experiment to include multiple users would strengthen the robustness and generalizability of our approach. We have now added this point in the Discussion Section (line 485).

Author response — `clarification` (units 19–21):

> That said, our focus here was not on developing a broadly applicable methodology for cloning but rather on addressing the feasibility, safety, privacy, and societal concerns raised by such a proof-of-concept LLM-clone. This is why we have submitted our work to the "alignment, fairness, safety, privacy, and societal considerations" track. We highlight in line 025, line 476, line 529 that this work is intended as a proof-of-principle.

Author response — `clarification` (units 22–30):

> **B3)** Thank you for your feedback on this critical point. However, we were probably not clear and there may be a misunderstanding. In the "Related Work" section noted by the reviewer, the statement, "additionally, the datasets used for personalization tasks are often anonymized, making it difficult to trace their origins and perform thorough, systematic evaluations," refers to existing public datasets where the identities of the dataset owners—such as the individuals who wrote the emails—are anonymized. This statement is not about our work. Regarding anonymizing our dataset, we would like to […]

Author response — `new_experiment` (units 33–37):

> We have expanded our discussion to provide a more detailed overview of the question sources, topics, and their distribution, as well as the performance of participants during the Turing Test across two distinct subgroups: question source and question topics. These details, along with a subgroup comparison that yielded some interesting insights, have been included in Appendix A.8. To ensure that the LLM's performance is not due to overfitting on training data, we conducted a textual similarity analysis between our training set and test sets using ROUGE-1 and ROUGE-L metrics. Our results demonst […]

Author response — `clarification` (units 73–86):

> Thank you for your acknowledgement and valuable feedback. Indeed, the purpose of our paper is to investigate the feasibility of creating an LLM-clone and to raise awareness of the associated concerns within the community. We have added a dedicated section discussing the ethical implications of our work in section 6 -- Ethical Considerations. Regarding your mention of "fairness and bias detection," we are not entirely certain of the specific context you are referring to. Our primary evaluation focuses on whether the clone can accurately mimic an individual's language behavior. In this context,  […]

**Critique 4** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> B5.1) In general, it seems that many papers can be added since personalized LLMs are a broad topic. For instance, regarding the Turing test, if you refer to the paper 'Cameron R. Jones and Benjamin K. Bergen. Does gpt-4 pass the turing test?, 2024.' you mentioned, there is much richer literature that explains what it entails. I believe it would be beneficial to include a brief paragraph explaining the Turing test and suggesting additional papers for readers who want more detailed information. B5.2) It would be helpful to include a paragraph in the related works section discussing the application of personalized LLMs. Additionally, you could mention potential applications of your model in the introduction to provide more context for its relevance. B5.3) To the best of my knowledge, it seems you have omitted some recent papers related to personalized LLMs that would be valuable to include in the related works section. Examples include "Leveraging LLM Reasoning Enhances Personalized Recommender Systems" (Tsai et al.), "How Good are LLMs in Generating Personalized Advertisements?" (Meguellati et al.), and "Doing Personal LAPS: LLM-Augmented Dialogue Construction for Personalized Multi-Session Conversational Search" (Joko et al.). B5.4) In the introduction, it would be useful to mention the most relevant works related to your paper and clearly state what distinguishes your work from others in the field.

Author response — `clarification` (units 39–43):

> We have incorporated a new paragraph in the Related Work section titled "Turing Test."(lines 113-121). **B5.2)** Thank you for the suggestion. We have already discussed several applications of personalized LLMs in the Related Work section (lines 100–102). We have refined this section by including citations for the papers suggested by the reviewer. However, due to page limitations, we did not expand this into a new paragraph.

Author response — `clarification` (units 45–49):

> **B5.3)** Thanks for recommending these amazing works on personalized LLMs. We now added these works in the related works (lines 100-102). **B5.4)** Thank you for the suggestion. We have already addressed the most relevant works in the Introduction section (lines 44–48) and outlined how our approach differs by addressing the limitations of prior work. Additionally, we have highlighted our main contributions at the end of the Introduction.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> 1) In lines 201-2023, you mention that the responses generated by the LLM in the first prompt were quite long and easily detected and that you later adjusted the length. Have you tried examining the correlation between person A's ground truth responses and A-clone's responses? For example, you could use metrics such as ROUGE-1, ROUGE-L, Persona F1, and Win rate, as suggested in the paper you referenced, "Kai Zhang, Lizhi Qing, Yangyang Kang, and Xiaozhong Liu. Personalized LLM Response Generation with Parameterized Memory Injection" (2024). 2) In lines 198-200, you state that, based on the questions you provided to A and A-clone, the test volunteers (such as A's family) had to predict which response belonged to A. Why didn’t you ask the test volunteers to come up with a set of questions they wanted to test, and then have both A and A-clone respond to those questions, incorporating them into the evaluation process? For example, in the paper you referenced, "Daniel Jannai, Amos Meron, Barak Lenz, Yoav Levine, and Yoav Shoham. Human or Not? A Gamified Approach to the Turing Test" (2023), they describe strategies that helped participants identify whether they were interacting with a chatbot or a human. Having such information for your model would provide deeper insights into its abilities. 3) In lines 203-208, you mention that you applied an SVM to determine if person A’s responses were easily recognized based only on length, with an accuracy of 0.48. Have you considered using a state-of-the-art classification model? In my opinion, this accuracy doesn’t provide much information, given that you used a simple classifier like SVM. 4) In line 770, regarding Table 2, you present some statistics related to the experiment. Did you perform any correlation tests to identify trends between the variables (e.g., gender, age range, etc.) and the test volunteers’ responses? For instance, it’s possible that individuals with a PhD level of education might be better at discerning whether something was generated by an AI.

Author response — `new_experiment` (units 52–55):

> **1** Thank you for suggesting these metrics. In the modified paper, we have incorporated ROUGE-1 and ROUGE-L as new metrics to compare the textual similarities between 701 responses generated by different models, providing an additional layer of evaluation alongside the Turing Test. The results demonstrate that A-clone outperforms the other LLM models, achieving the highest scores in both ROUGE-1 and ROUGE-L. (Check Appendix A.6 for details.)

Author response — `clarification` (units 59–62):

> In fact, this approach aligns precisely with part of what we implemented during the Turing Test question dataset collection. Participants were asked to generate at least 10 questions they wished to ask the clone, resulting in 217 out of the 701 questions originating directly from participants. We now present results categorized by question types in Appendix A.8, and explicitly describe in the main text that some of the questions were participant-generated. (line 155) For further analysis, please refer to Appendix A.8.

Author response — `clarification` (units 63–66):

> **3** Thank you for the feedback. The purpose of using an SVM classifier in the section referred to by the reviewer  was to assess whether response length alone could serve as a predictive factor for distinguishing AI-generated answers. This was motivated by the hypothesis that one possible strategy during the Turing Test could involve evaluating choices simply based on their length. Given that this was a very simple classification task and that there is a single scalar value for each response (its length), we did not seek to use more sophisticated classification models.

Author response — `new_experiment` (units 68–71):

> In our paper, we discussed the potential correlation between *performance* and both *familiarity with A* and *confidence levels in Turing Test*. Beyond these factors, we have not identified any correlation between performance and other demographic variables (*age, gender, etc*). In the appendix A.9, we include a plot that examines the relationship between performance and *education level*, addressing the hypothesis raised by the reviewer. As illustrated in figure 17 and figure 18, no significant correlation can be observed.

`[ignored]` A) Presentation ⏐ B) Experimental ⏐ B5) Related Works Section ⏐ The questions I present in this section are closely related to the Weaknesses section where I share my thoughts, so please review both parts.

## Example 20 — review `e4R7khNS1D` (ICLR 2025)

28 units, 9 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Alignment failed for this review.**

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `section`, actionable `False`

> 1) Clarity & Soundness: Their writing was clear on these points. - They clearly stated their novelty and significant difference from the misspecified bandit algorithm proposed by Dong & Yang. - They tried to demonstrate how they set the lower bound instance by high-level, but an explicit explanation throughout Section 3, with a nice figure. (and also the main difference from Du et al. 2020) - The algorithm itself is also quite simple - it follows a traditional method of elimination algorithms, and thanks to the detailed explanation, I could easily get a sketch about how the proof goes on. The technique is also using some simple Hoeffding's inequality.

**Critique 2** — aspect `novelty`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2) Significance & Novelty: Even though their results are clearly written and easy to understand, many of their results are quite fresh and counter-intuitive. One cannot extend bandit algorithms in this case was quite interesting indeed.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1) Computationally intractable. If I understood correctly, they use an $\epsilon$-net on the candidates for $\theta_h$ - $P_h^0$ starts from all possible $k$-sparse vectors. After that, for each iteration, this algorithm is searching for argmax over all candidates. Also, eventually they proposed an algorithm that provides $\epsilon$-optimal.

**Critique 4** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 2) Even though they tried to show their process transparently, there are some parts that I cannot understand.

**Critique 5** — aspect `clarity`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1) I don't understand the word 'MDP without sample.' Without any trajectory, how could a learning agent learn something? You mean, 'without learning' the error is bounded by $\Omega(H\epsilon)$?

**Critique 6** — aspect `soundness`, severity `minor`, polarity `neutral`, target `section`, actionable `True`

> 2) Also, it is interesting that this algorithm eliminates the 'most promising candidate' first. In bandits, the elimination eliminates all the suboptimal candidates that show less upper bound than the largest lower bound (eliminate an arm i which is max_j LCB_t(j) > UCB_t (i)). Why does this difference happen?

**Critique 7** — aspect `soundness`, severity `minor`, polarity `neutral`, target `section`, actionable `True`

> 3) So what is the optimal size of the parameters, $\epsilon_{net}$ and $\epsilon_{stat}$? I guess they also should be in the scale of $\epsilon$.

**Critique 8** — aspect `soundness`, severity `major`, polarity `neutral`, target `section`, actionable `True`

> 3-1) Also just to clarify, what is $\epsilon$-optimal in here, does this mean $V^* - V(\pi) \leq \epsilon$? If so, according to your final result (Lemma 4.4), for the error $\epsilon'$, one should set $\epsilon/H$. This means now $m$ is proportional to $H^2$ too and the overall sample complexity also should include $H^2$, I believe.

**Critique 9** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 3-2) In that sense, the line 438 is very confusing. Why it is $H^2 \cdot m$, including the $\epsilon_{stat}^2$ in the denominator? You repeat $m$ samplings for $H$ iterations. Shouldn't it be $H\cdot m$?

`[ignored]` Please check the 'Questions' below.

