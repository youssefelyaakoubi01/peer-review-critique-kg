# 20 random reviews of run `check_v1` (seed 0)

Review text is public content from OpenReview. `[ignored]` units are in no critique.

## Example 1 — review `422QIJ6TqR` (ICLR 2024)

21 units, 10 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The author theoretically analysis the drawbacks of the clean guided methods and provide some results to proof their claims.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 2. The author propose a method to solve the problem, and conduct experiments to its effectiveness.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 3. Except the style transfer part, the motivation is clear and the paper is well-written.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. About the style transfer task, I do not think it is appropriate to appear in this paper. According to my understanding, the goal of this paper is to bridging the performance gap between clean and noised sample-based methods. However, the experiment of style transfer task has no relationship with this topic. Therefore, I think the author better give an explanation about why conducting this part of experiments. Besides, according to the above reason, I also recommend the author to remove Section 2.3.

Author response — `clarification` (units 7–11):

> While we understand the concern, the purpose of incorporating this experiment was two-fold. The first is that previous methods based on noised samples are not suitable for conditional generation tasks on unlabeled datasets, such as arbitrary style transfer. By achieving arbitrary style transfer, we underscore the potential and flexibility offered by our clean sample-based method. Secondly, the effectiveness of our proposed method is further demonstrated through comparisons and ablation studies on style-transfer task. For a more comprehensive analysis, we include a comparison with the results f […]

**Critique 5** — aspect `related_work`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 2. Lacking the results of other works on improving clean-estimation guidance in style transfer task.

Author response — `new_experiment` (units 12–14):

> To ensure a fair comparison, we set the total sampling steps for FreeDoM to be 1110 steps, incorporating its time-travel strategy, while our method uses 1000 ddpm steps for sampling. We find that results from FreeDoM contains dotted noise and shows a inferior sampling quality. As the results show, our method outperforms FreeDoM on both $ L_{content} $ and $ L_{style}$.

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 3. The authors claim in Section 4.2 that the clean classifier+guidance function proves to be less reliable than the noise-robust classifier. Could the authors give a more direct proof like Figure 2?

Author response — `clarification` (units 21–24):

> In Appendix.C.2, we have supplemented our discussion with several sample sequnences of clean-estimations obtained during the denoising process in Figure 10. Upon examining these figures, it becomes evident that the clean-estimation is unstable during the denoising process(eg. in the red boxes). This instability subsequently results in an inconsistent guidance gradient throughout the denoising process. > Q4(1): The authors do not clarify which table is the results of this experiment.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4. About the experiments in Section 5.1: 1) the authors do not clarify which table is the results of this experiment 2) the authors mention FreeDoM and Universal Guidance in the paper, but only provide the results of ADM+FreeDoM. What about the results of DiT+FreeDoM and DiT/ADM+Universal Guidance? 5. The authors is recommended to prove the results of other methods on image generation task for comparison.

Author response — `new_experiment` (units 25–33):

> Thanks for pointing out this issue. We have made the necessary addition in the PDF, referencing `As shown in Tab. 1' in Section 5.1. > Q4(2): The authors mention FreeDoM and Universal Guidance in the paper, but only provide the results of ADM+FreeDoM. We have add the following comparison with DiT + FreeDoM here. We only provide the DiT + FreeDoM results here because FreeDoM is a follow-up work of Universal Guidance which shares a similar time-travel strategy and shows superior results. To ensure a fair comparison with our method, we have calibrated the total sampling steps for FreeDoM to close […]

**Critique 8** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 6. In Section 5.2, there is no description about what is I_cs.

Author response — `clarification` (units 44–45):

> Thank you for highlighting this oversight. We have now updated Section 5.2 to include the necessary explanation:  `The differences between the content image $I_c$ and the stylized image $I_{cs}$ is expressed as'.

**Critique 9** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 7. In Section 5.3, the ablation results on style transfer task indicate that "Raw+Filtering & Suppression" can achieve the best results on L_content. However, it's results on L_style is only the third best. Does this indicate that "Raw+Filtering & Suppression" tends to preserve the original image's features rather than transferring to a new style?

Author response — `new_experiment` (units 47–52):

> However, it's results on $ L_{style} $ is only the third best. In Section 4.3, we provide an overarching insight that suppressing the early gradient can enhance the sampling quality. We employ the simplest linear scheme to demonstrate this effect. However, we acknowledge that more effective suppression schemes may exist. For instance, we discovered that the suppression scheme $\tilde{g_t} = \frac{\sqrt{\bar\alpha_t}}{\sqrt{1-\bar\alpha_t}}\bar{g_t}$ yields superior results for the style-transfer task, achieving both the lowest content error ($L_{content} = 4.69$) and the most optimal style err […]

**Critique 10** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `general`, actionable `False`

> See weaknesses.

Author response: none.

## Example 2 — review `r40GN1Wttt` (ICLR 2024)

14 units, 5 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `related_work`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. Contrary to prior results, the paper finds the self-correct methods in prior research such as Kim et al. (2023); Shinn et al. (2023) make use of oracle labels to guide the self-correction process.

Author response: none.

**Critique 2** — aspect `related_work`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 2. For self-correction through multi-agent debate (Du et al., 2023; Liang et al., 2023) to improve reasoning where multiple instances of an LLM critique each other’s responses, the paper's results reveal that its efficacy is no better than self-consistency when considering an equivalent number of responses, highlighting the limitations of such an approach.

Author response: none.

**Critique 3** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. Intrinsic self-correction, defined as the model endeavors to rectify its initial responses based solely on its inherent capabilities without the crutch of external feedback, is not very clear to me. Does recall examples from parameter knowledge (see paper below) considered intrinsic self-correction? Large Language Models as Analogical Reasoners https://arxiv.org/pdf/2310.01714 2. It is not clear which prior papers have the various problems exposed. It would be very helpful to put them in a table. Furthermore, please provide details on where prior methods rely on oracle labels, specific problems on poorly constructed pre-prompts, specific benchmark results that are wrong. For example, I do not seem to locate which part Shinn et al. (2023) have the problems.

Author response — `new_experiment` (units 12–17):

> The table below summarizes the issues of prior methods as you suggested, and we added this table to Appendix C in our revision. | Method                                              | Issue                                      | | RCI (Kim et al., 2023); Reflexion (Shinn et al., 2023) | Use of oracle labels                        | | Multi-Agent Debate (Du et al., 2023)                | Unfair comparison to self-consistency       | | Self-Refine (Madaan et al., 2023)                   | Suboptimal pre-hoc prompt design            | Regarding the use of oracle labels, in Appendix C.2 of Kim et  […]

**Critique 4** — aspect `significance`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> The paper exposes an intriguing problem in prior work on self-correction of LLMs that shows, to the contrary that LLMs can not self-correct reasoning yet.

Author response: none.

**Critique 5** — aspect `related_work`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> However, it is still not clear how we should think about all the techniques to improve reasoning without external feedback. Does breakdown a problem into sub-problem and do step-wise verification paired with self-consistency considered self-correction? It would be very helpful to put all these techniques into perspective.

Author response — `clarification` (units 21–22):

> As discussed in our Section 5 “Employing self-consistency as a method of self-verification”, breaking down a problem into sub-problems and conducting step-wise verification paired with self-consistency can be helpful. Another promising future direction is exploring how to enable LLMs to interact with and learn from external feedback (e.g., interacting with the environment), though this falls outside the scope of "intrinsic self-correction" discussed in our paper.

## Example 3 — review `VheTUFyeNe` (ICLR 2024)

31 units, 15 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The proposed DEER method is well-motivated and presented clearly

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The theoretical results seem sound, though I only skimmed the proofs to follow the arguments, rather than check every detail line-by-line

Author response: none.

**Critique 3** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> - The method is general and can be applicable to a host of nonlinear differential equation methods such as neural ODEs and any nonlinear RNN (e.g. LSTM, GRU, etc) of broad interest to the sequence modeling community.

Author response: none.

**Critique 4** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The method has the advantage of theoretically having quadratic convergence.

Author response: none.

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> Experimental results support the claim that this method should lead to nearly equivalent results (up to numerical precision) as evaluating the nonlinear ODE sequentially

Author response: none.

**Critique 6** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - For small hidden sizes, the empirical speed ups are substantial

Author response: none.

**Critique 7** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> - The biggest weakness of the paper is the empirical results, particularly related to performance. Only two tasks are considered, a synthetic physics system where HNNs are trained and the EigenWorms task where a GRU is trained. - For the EigenWorms task, the GRU does not significantly perform that much better than several of the baselines and is outperformed by others. It is claimed that the DEER method enables faster training and thus experimentation to identify optimal GRU architectures. But is this the best the GRU could do?

Author response: none.

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> -  It would have been interesting to see the DEER method applied to some of the other methods such as LEM or UnICORNN since they could presumably be trained with the DEER method also. Would they maintain the same performance? Could better performance be achieved with the DEER method since they could potentially be trained faster and thus be hyperparameter tuned more? An exploration of this would strengthen the paper and broaden the impact.

Author response: none.

**Critique 9** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - A greater variety of tasks would increase the impact of the paper and potentially broaden the audience. E.g. there are many other common sequential "long sequence" tasks ranging from sequential MNIST, sequential CIFAR, to the LRA benchmarks. It would have been interesting to see how a nonlinear RNN such as GRU performed on LRA.

Author response: none.

**Critique 10** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> - There are many interesting theoretical results pushed to the Appendix. The authors might potentially consider packaging some of the formal statements as propositions in the main paper, to signpost the results and guide the reader to understand the rigor behind the method as well as point to the location of the proofs more explicitly in the Appendix.

Author response: none.

**Critique 11** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - A weakness of the proposed method is the cubic complexity in the hidden size that the DEER method incurs. This limits scalability and the applicability of the method to larger scale systems. This is mentioned, but perhaps a further discussion of potential paths to address this could be interesting and helpful.

Author response: none.

**Critique 12** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> 1. Can you somehow quantify the claim that the DEER method can improve the performance of the GRU since it allows more hyperparameter tuning? Perhaps report the results of a single sequential GRU run, and then show the improvement that can be achieved by hyperparameter tuning the GRU for multiple runs (allowed by the parallelization of the DEER method).

Author response — `new_experiment` (units 5–7):

> We ran hyperparameters tuning during the discussion period as the reviewer suggested and we can achieve the improvement for GRU from 82.1% to 88.0%, beating a more modern technique Neural RDE. We will update the results in the paper. [comment]: <> (<p style="color:blue">[TODO: put in the paper ???]</p>)

**Critique 13** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> 2. Can you apply the DEER method to LEM and/or UniCORNN and report the results and compare the runtimes?

Author response — `new_experiment` (units 9–14):

> We have ran experiments using DEER on LEM. It is more challenging to reproduce their results than we thought as running the code from the official repository does not really reproduce the results on the paper. So we used DEER method to tune the hyperparameters efficiently and we can obtain similar results to their paper. With DEER, one experiment can run in less than 30 minutes, while with the code from the official repository, it took us 6 hours to run an experiment. We will put the results in the paper. [comment]: <> (We have added the results in our paper in [???])

**Critique 14** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> 3. Can we add more tasks? Is it possible to run a GRU or other nonlinear RNN on Long Range Arena? Or does the cubic complexity of DEER prevent running large enough models for some of these tasks? Can we at least add other common RNN benchmarks such as sequential CIFAR?

Author response — `new_experiment` (units 16–24):

> > Can we add more tasks? Is it possible to run a GRU or other nonlinear RNN on Long Range Arena? Or does the cubic complexity of DEER prevent running large enough models for some of these tasks? Can we at least add other common RNN benchmarks such as sequential CIFAR? Yes, we have added a new experiment result on sequential CIFAR-10 (sCIFAR-10) using multiple head GRU with different strides. We can get around the cubic complexity of DEER by splitting the GRU into multiple heads. For example, instead of using correlated 256 states, we split them into 16 heads with 16 states each. We ran an expe […]

**Critique 15** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 4. Can you add a PDE example (discussed in the appendix)?

Author response — `clarification` (units 25–29):

> > Can you add a PDE example (discussed in the appendix)? Although DEER can be used for PDE, the focus of our paper is for one dimensional differential equation (i.e. ODE or discrete difference equation). Applying it for a PDE would require writing the solver of the linear equation which would take a significant amount of effort. Exploring this direction is a possible future work. For now, we put an example on how to apply DEER framework to a simple PDE case in the Appendix.

## Example 4 — review `TfFfwg8i9n` (ICLR 2024)

15 units, 11 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. This method is relatively straightforward and easy to understand.

Author response: none.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> By selecting the most relevant video segments, it reduces computational load, enhancing the efficiency and accuracy of the QA system. 2. Facing the growing content of long videos, this method provides a new perspective in the field of video understanding and retrieval.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. Loss of detail: Although the method reduces distractions, key information might still be lost in the process of reducing visual tokens.

Author response — `clarification` (units 4–23):

> When reducing visual tokens to improve efficiency, how is key information ensured not to be missed? Response: Retrieval plays a very important role in reducing visual tokens, especially for long videos. For example, for a video of 180 seconds, we have 45 chunks in total. By retrieving the top 5 question-related chunks, the vision tokens are reduced by 89%. Targeting at dropping the question-irrelevant chunks, we try to ensure the key information is not missed. On the other hand, we found the spatial-temporal pooling to reduce the number of tokens in a chunk can still preserve the main informat […]

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2. Lack of a dynamic adjustment mechanism: The model seems to lack the capability to dynamically adjust the number of selected video segments based on the content of the video, which could lead to information overload or oversimplification in some scenarios.

Author response — `concession` (units 35–40):

> >2.Lack of a dynamic adjustment mechanism: The model seems to lack the capability to dynamically adjust the number of selected video segments based on the content of the video, which could lead to information overload or oversimplification in some scenarios. Response: We also believe that a dynamic mechanism would result in superior results and would leave this as future work. For example, we could analyze the learned affinity scores from the retrieval and investigate whether some statistic characteristics are helpful to produce reasonable prediction. Fortunately, we find the hyper-parameter o […]

**Critique 5** — aspect `reproducibility`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 3. Resource consumption issues: Despite the reduction in the number of visual tokens, the overall resource consumption of the model (such as computational resources, memory, etc.) has not been fully discussed.

Author response — `new_experiment` (units 41–53):

> Response: Thanks for the good suggestion. We added the discussion in the revised appendix. The computational cost comes from two parts. The first part is to encode the video frames through the CLIP encoder and the spatial-temporal pooling to get chunks. The second part is the retrieval of $K=5$ chunks and put them to LLM for inference. The spatial-temporal pooing and retrieval is very fast and negligible. On a single A100, we tested 120 60s videos from Social-IQ 2.0 and calculated the average inference time cost for a video. For a single video, the first part for vision feature extraction take […]

**Critique 6** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 4. Regarding the selection of K, although the authors have explained it in the experimental section, the ablation of K still warrants exploration.

Author response — `clarification` (units 54–56):

> Response: Thank you. Please see the ablation study from the global responses for all reviewers. >5.Hyperparameter λ.

**Critique 7** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 1. How does the model handle the diversity and complexity of video content? Can it effectively process different types (such as documentaries, movies, news reports, etc.) and styles of videos?

Author response — `clarification` (units 60–66):

> >6.How does the model handle the diversity and complexity of video content? Can it effectively process different types (such as documentaries, movies, news reports, etc.) and styles of videos? Responds: Testing datasets contain diverse videos, ranging from movies, wild videos, first person videos, etc. For videos of different types and styles, our model presents consistent improvement over baseline models and previous methods. This benefits from the designed retrieval mechanism that can select the question-relevant video chunks for video understanding, avoiding the submergence of most informat […]

**Critique 8** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 2. When reducing visual tokens to improve efficiency, how is key information ensured not to be missed?

Author response — `clarification` (units 67–71):

> Whether it has good generalization capabilities for Out-Of-Distribution (OOD) data is worth discussing. Response: The model has high generalizability. Our method outperforms baseline models and previous methods in the zero-shot setting tests (Table 2 and 3 in the manuscript), which contain diverse OOD data. The generalizability is also attributed to the generalizable LLM and CLIP vision encoder, which have already trained on abundant language data and diverse vision data. >8.What about the real-time processing capability for long-duration videos?

**Critique 9** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 3. What is the model's generalizability? Whether it has good generalization capabilities for Out-Of-Distribution (OOD) data is worth discussing.

Author response — `clarification` (units 72–82):

> Is the model suitable for real-time video streams or scenarios requiring immediate responses? Response: Our approach is capable of real-time inference. The computational cost comes from two parts. The first part is to encode the video frames through the CLIP encoder and the spatial-temporal pooling to get chunks. The second part is the retrieval of K=5 chunks and put them to LLM for inference. The spatial-temporal pooing and retrieval is very fast and negligible. We tested 120 60s videos from Social-IQ 2.0 and calculated the average inference time cost for a video. For a single video, the firs […]

**Critique 10** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 4. What about the real-time processing capability for long-duration videos? Is the model suitable for real-time video streams or scenarios requiring immediate responses?

Author response: none.

**Critique 11** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> 5. In the ablation study section, the article does not conduct descriptive experiments on the hyperparameters used, such as $\lambda$ and K.

Author response — `clarification` (units 54–56):

> Response: Thank you. Please see the ablation study from the global responses for all reviewers. >5.Hyperparameter λ.

## Example 5 — review `t4b5zd13vT` (ICLR 2024)

35 units, 9 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> + The focus of this work, that is, the behavior of SGD, is an important and relevant topic to the community.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> + Some of the findings on the differences between SGD and (noisy) GD might be interesting.

Author response: none.

**Critique 3** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> + The calculation of the stationary distribution of SGD for diagonal linear networks should be new to my knowledge.

Author response: none.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - Some statements/writing are not precise and might be misleading. See more in the Question section. - Some messages are already known from prior papers. For example, it is known (references are actually mentioned in this work) that SGD should not be approximated by gradient flow or gradient Langevin dynamic and that the SGD noise is parameter dependent. This paper should have been more careful in terms of clarifying the contributions. - Not sure how relevant is the theory in this paper to practice.

Author response — `clarification` (units 3–34):

> Weaknesses: **1. Some statements/writing are not precise and might be misleading. See more in the Question section.** Thanks for this criticism. We have done our best to update the manuscript to improve the precision of our language. See our answers below. **2. Some messages are already known from prior papers. For example, it is known (references are actually mentioned in this work) that SGD should not be approximated by gradient flow or gradient Langevin dynamic and that the SGD noise is parameter dependent. This paper should have been more careful in terms of clarifying the contributions.** […]

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 1. Discussions before Theorem 1. This might not be true. For example, $(u \\max \\{ w x, 0 \\} -y)\^2$ is rescaling symmetric only for non-negative $\\lambda$.

Author response — `clarification` (units 35–45):

> **1: Discussions before Theorem 1. "....For example, it appears in any neural network with the ReLU activation". This might not be true. For example $(u\max\{wx,0\}-y)^2$,  is rescaling symmetric only for non-negative $\lambda$.** Thanks for this comment. We are afraid to say that this is a misunderstanding of our result. Theorem 1 also holds for the rescaling symmetry in the positive real axis. In fact, Theorem 1 only requires the rescaling symmetry to hold in the vicinity of $\lambda = 1$. Namely, the only condition that is required to prove Theorem 1 is the infinitesimal transformation $\el […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 2. Theorem 1 and the follow-up discussions. Note that $C\_1 $ and $C\_2$ are functions of $u$ and $v$. Therefore, $\\lambda\_{1m}, \\lambda\_{1M}, \\lambda\_{2m}, \\lambda\_{2M}$ are not constants but functions of $u$ and $v$. Hence, eqs (5) or (6) do not directly imply that $u$ and $v$ are approximately balanced. Could the authors make some clarifications?

Author response — `new_experiment` (units 46–56):

> **2: Theorem 1 and the follow-up discussions. Note that $C_1$ and $C_2$ are functions of $u$ and $v$. Therefore, $\lambda_{1m},\lambda_{1M},\lambda_{2m},\lambda_{2M}$ are not constants but functions of $u$ and $v$. Hence, eqs (5) or (6) do not directly imply that $u$ and $v$ are approximately balanced. Could the authors make some clarifications?** This is a good and sharp question. It is true that $C_1$ and $C_2$ are functions of $u$ and $v$. However, at the end of the training, when the model stabilizes with a local minimum valley, $C_1$ and $C_2$ will be approximately stationary and time-ind […]

**Critique 7** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> 3. Discussions after eq (8). There seems to be a typo in the display after "....can be upper-bounded by an exponentially decreasing function in time:...". Please clarify. In addition, in eq(7), the coefficient $\\alpha\_1 v\^2 - 2\\alpha\_2 v  + \\alpha\_3$ is not a constant but a function of $v$ (hence a function of $u$ and $w$). So the statement that "....can be upper-bounded by an exponentially decreasing function in time" might not be accurate.

Author response — `clarification` (units 57–66):

> **3: Discussions after eq (8). There seems to be a typo in the display after "....can be upper-bounded by an exponentially decreasing function in time:...". Please clarify. In addition, in eq(7), the coefficient $\alpha_1v^2-2\alpha_2v+\alpha_3$ is not a constant but a function of $v$ (hence a function of $u$ and $w$). So the statement that "....can be upper-bounded by an exponentially decreasing function in time" might not be accurate.** Thanks for this question. This is not a typo. While the expression $\alpha_1v^2-2\alpha_2v+\alpha_3$ is a function of $v$, it can be lower bounded the decay  […]

**Critique 8** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 4. Discussions after eq (9). There might be a typo in the definition of $C(v)$. It should be the variance of the gradient of the loss.

Author response — `clarification` (units 67–72):

> There might be a typo in the definition of $C(v)$. It should be the variance of the gradient of the loss.** Thanks for pointing this out. This is indeed a typo. We have corrected this part to $C(v)=\text{Var}[\nabla_v\ell(v,x)]=\cdots$ in the updated manuscript. **5: "These relations imply that $C$ can be quite independent of $L$, contrary to popular beliefs in the literature...".

**Critique 9** — aspect `related_work`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 5. "These relations imply that $C$ can be quite independent of $L$, contrary to popular beliefs in the literature...". Here, should the word "independent" be revised to "dependent"? 6. The diagonal linear network studied in this paper takes a 1-dimnensional input. However, prior works consider diagonal linear network with a multivariate input. So the setting in this work might be limited compared to prior works. Overall, I feel the theory in this work is not entirely precise. Plus, the model setup is limited, and the results might not be general and might be strongly rely on this particular setup.

Author response — `clarification` (units 73–80):

> Here, should the word "independent" be revised to "dependent"?** Thanks for this question. Here, we say "independent" because the noise only depends on the variance of the data $x^2$ and $xy$, which do not enter the loss function $L$. In general, the variance and the expectation of the same data are independent of each other. Also, while both $C$ and $L$ are functions of $u$ and $w$, their functional dependencies are different and unrelated to each other. This tells us that the noise is determined by the higher-order structure of the data, which is contrary to previous arguments in Ref. [23,27 […]

`[ignored]` See more in the Question section. ⏐ "....For example, it appears in any neural network with the ReLU activation".

## Example 6 — review `uLTHQBcnem` (ICLR 2024)

30 units, 9 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The presentation of this paper is clear and easy to follow.

**Critique 2** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> 2. Preserving generic knowledge in foundation models during continual learning and providing quantitative assessment for generic knowledge loss is meaningful.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 3. The results based on the CLIP model are good.

**Critique 4** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 1. The quantitative evaluation of generic knowledge loss can only be applied to vision-language models. Specifically, such control set Accuracy (C.) is represented by the zero-shot performance differences between the tuned and frozen pre-trained models, which cannot be obtained for pre-trained unimodal models.

**Critique 5** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 2. The reasons for **only** updating the (first) MLP layer in each transformer block are not sufficient. This paper ignores the discussion of other components, such as the attention block and normalization layers. The previous work [A] mentioned in this paper does not suggest that MLP layers are more important than other layers. Besides, as for fine-tuning ViT, [B] suggested that "fine-tuning attention is all you need" since tuning attention weights are more efficient than tuning MLP parameters while reaching similar performance. It is supposed to include such discussion since this paper claims to find an efficient way for tuning foundation models.

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> On the other hand, the generalization of the Parameter Selection operation may be limited if it cannot automatically select parameters when all parameters of the transformer are included without the manual Localization operation.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 4. Missing comparisons and discussion. This work compares two baselines, FLYP [C] and ZSCL [D], in the main text (and two prompt-based methods in the appendix). Note that FLYP was not proposed for the continual setting. Therefore, this paper combines it with four continual learning methods, which makes sense. However, a closely related (but not mentioned) work [E] indicated that the pre-trained foundation model can naturally preserve generic knowledge even when tuning all parameters continually. It is supposed to include discussion and comparisons with [E] as a baseline to support this work.

**Critique 8** — aspect `related_work`, severity `minor`, polarity `negative`, target `reference`, actionable `True`

> 5. (Minor) Lots of reference links are invalid, which makes it hard to read. References. [A] Transformer Feed-Forward Layers Are Key-Value Memories. EMNLP 2021. [B] Three things everyone should know about Vision Transformers. ECCV 2022. [C] Finetune like you pretrain: Improved finetuning of zero-shot vision models. CVPR 2023. [D] Preventing Zero-Shot Transfer Degradation in Continual Learning of Vision-Language Models. ICCV 2023. [E] SLCA: Slow Learner with Classifier Alignment for Continual Learning on a Pre-trained Model. ICCV 2023.

**Critique 9** — aspect `other`, severity `minor`, polarity `neutral`, target `general`, actionable `False`

> See Weaknesses part for details.

## Example 7 — review `105WCNdhLZ` (ICLR 2024)

38 units, 8 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The problem of imbalanced data in multi-class classification is interesting.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> RG outperforms existing techniques in balanced accuracy

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> (BA) in one dataset. The efficacy of RG is not well demonstrated. In Table 1, RG only outperforms in one of 3 metrics in one of 2 datasets. For the multi-class problem only one dataset is used. The choice of datasets could be improved. The 9 classes in CIFAR 10 are quite different and merging to simulate a single majority class might have a quite diversified class. For example, a majority class has many images of dogs, but the different kinds (subclasses/clusters) of dogs have commonalities to be dogs. Hence, Binary CIFAR 10 might not be a good dataset to use. Binary HAM10000 on "dermatoscopic images of 7 common skin lesions" is more appropriate.

Author response — `new_experiment` (units 4–7):

> - More datasets: We acknowledge the limitation that we only have one multi-class dataset, and have addressed this issue by extending our experiment to include a new multi-class task. Specifically, we take the financial phasebank dataset (Malo et al. (2014)), which consists of 4840 sentences of English-language financial news categorized by sentiment with a label frequency of 2,879 (neutral), 1,363 (positive), and 604 (negative). We have shown that in the new dataset, RG surpasses other baselines and remains dominant. For more information about the experiment setups and results, we would kindly […]

**Critique 4** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> The presentation could be improved. For example: Sec 2.2: Sum aggregation was discussed, but it seems to be not used in any experiments. Also, the motivation for Sum aggregation was not discussed. Sec. 2.2 does not discuss how clusters are formed via regrouping. k-means is mentioned in 4.1 Setting of experiment.

Author response — `clarification` (units 16–22):

> - Presentation: We would like to thank the reviewer for the comments on the presentation, we have addressed them as follows: - Aggregation: We performed an ablation study to show the impact aggregation method in Appendix B, where max aggregation is found to be marginally better in comparison to sum aggregation, but since the difference is not too large it is recommended to try both methods. We have added some explanation for both aggregation methods in Sec 2.2 to avoid confusion. - Clustering Method: In Appendix B, we also explored the role of clustering algorithms in the performance of the pr […]

**Critique 5** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> RG+WCE: since RG tries to balanced class sizes, why do you need WCE (weighted cross entropy)? Why did WCE help? Could you describe WCE or cite a source?

Author response — `clarification` (units 24–27):

> - Why WCE is required with RG?: WCE is the weighted version of cross entropy loss where each sample is weighted by the inverse of the corresponding class frequency, so that classes with fewer samples get higher weights, check Elkan (2001) for the general concept of reweighting. Since we are using K-means algorithm to perform clustering and assign pseudo labels, the resulting classes are not guaranteed to be balanced. Hence, along with CE, we have also reported results that use WCE loss function. - AUPRC/AP metric clarification: AUPRC is a metric that calculates the area under precision-recall  […]

**Critique 6** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> p7. "Considering that AUPRC is agnostic to the decision rule and is often approximated by AP given finite sample sizes"--any citations or

Author response — `clarification` (units 27–30):

> - AUPRC/AP metric clarification: AUPRC is a metric that calculates the area under precision-recall curve, where each point is based on a specific threshold (decision rule). Hence, AUPRC (similar to AUROC) is independent of the choice of decision rule. Average Precision (AP) is known to be an unbiased estimate of AUPRC (Boyd et al. (2013)). We have added the reference in the paper as well.

**Critique 7** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> evidence to support the statement?

Author response — `clarification` (units 39–41):

> Area under the precision-recall curve: point estimates and confidence intervals. In Machine Learning and Knowledge Discovery in Databases: European Conference, ECML PKDD 2013, Prague, Czech Republic, September 23-27, 2013, Proceedings, Part III 13 (pp. 451-466).

**Critique 8** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> Fig. 5, caption: airplane, not apple ?

Author response — `clarification` (units 23–23):

> - Image Caption: We have fixed the typo in the image caption, it should have been airplane instead of apple.

## Example 8 — review `kD3P4tedtm` (ICLR 2024)

13 units, 6 critiques, 3 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper is well-written and presents its ideas clearly.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> The effectiveness of the proposed timestep annealing scheme in text-to-3D generation using SDS is demonstrated.

Author response: none.

**Critique 3** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> 1. There are several existing works that have proposed timestep schedulings, such as two-stage samplings in ProlificDreamer [1] and the non-increasing timestep annealing scheme in HIFA [2]. These methods have been available on arXiv for a while. Given the rapidly evolving nature of this field, even if not officially published, it would be beneficial for the authors to compare the proposed Gaussian PDF with these existing approaches.

Author response — `new_experiment` (units 5–12):

> Nonetheless, we agree with the reviewer's comment and compare our method with the timestep schedules proposed by HiFA and ProlificDreamer, as shown in Section F (Figure 16) in the Appendix. Compared with our results, both competitors fail to generate geometric details. We argue that the reasons for their failures are different: - HiFA’s timestep schedule favors training with small t, where high gradient variance leads to color bias and simplified geometry. We also mentioned these effects in Figure 11 and Figure 13. As an exception, the original HiFA paper uses an iterative SDS optimization tha […]

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> 2. The enhancement of TP-VSD is intriguing. However, the authors have presented only one example in Fig.1. It is recommended to provide additional visual results, especially for a wider range of objects and scenes as demonstrated in ProlificDreamer.

Author response — `new_experiment` (units 13–16):

> More results of TP-VSD.** Thank you for the suggestion. We now provide more results of TP-VSD on a wider range of objects and scenes in Section G (Figure 17) in the Appendix. **W3.

**Critique 5** — aspect `significance`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 3. While the proposed improvement is a valuable technique, its contribution as an ICLR paper may be limited.

Author response — `disagreement` (units 17–22):

> Contribution as an ICLR paper may be limited.** With all due respect, we would like to argue differently. Improving sampling quality and efficiency has been an important subject for diffusion-guided image generation. However, optimization-based 3D generation is known to be time-consuming with sub-optimal generation results, yet understanding and addressing the inefficiencies stemming from the formulation of random t-sampling has been overlooked, which is the focus of our work. We would like to quote reviewer DnQ9 that _"It studies an aspect of using diffusion model for 3D diffusion model -- ho […]

**Critique 6** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> I am curious if there exists a concrete theoretical deduction for the timestep annealing scheme that could explain which specific timestep annealing scheme should be employed.

Author response — `clarification` (units 24–28):

> Concrete theoretical deduction for timestep annealing scheme.** Thank you for the question. In this paper, we aim to provide a general guideline for timestep sampling, which should a) be monotonically non-increasing for coarse-to-fine generation and to avoid inefficiency b) suppress the sampling of small timesteps to avoid high-variance gradients c) encourage the sampling of medium (content-related) timesteps for most informative guidance. The proposed timestep annealing scheme is an empirically robust one across prompts, but as pointed out by reviewer iLxc, different prompts may work best und […]

`[ignored]` [1] ****ProlificDreamer: High-Fidelity and Diverse Text-to-3D Generation with Variational Score Distillation, Wang et al., NeurIPS 2023. ⏐ **** ⏐ [2] ****HiFA: High-fidelity Text-to-3D with Advanced Diffusion Guidance, Zhu et al., 2023.****

## Example 9 — review `2WoJs9OwlX` (ICLR 2024)

42 units, 5 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `major`, polarity `positive`, target `general`, actionable `False`

> The main strengths of this paper are: 1. its rigorousness in making clear, concise statements of its findings (except for one important "detail" discuss under weaknesses); 2. a formal characterization of the power of transformers with CoT, for which results have come out only very, very recently (after the ICLR submission deadline); 3. carefully crafted arguments and proofs around rounding of numbers when performing addition of $n$ numbers, a key step used in multiple prior papers unless less realistic assumptions; and 4. empirical evaluation to support the theory, which is often missing in similar theoretical characterizations of transformer variants in the past. I have not read the proofs in detail (esp. the material in the appendix), but the results and approach intuitively appear plausible.

Author response: none.

**Critique 2** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> I really have only one, albeit big, concern about the paper, namely **the formal model of transformers being studied is different not only from all prior theoretical works but also from practical use of transformers**. This is made worse by the lack of a discussion of this difference. Consequently, while the results appear to tighten prior upper bounds and provide novel lower bounds, they really are applicable to a different model. Specifically, the authors assume a model of transformers that is **non-uniform** (in the sense it is used in circuit complexity), namely, for each $n$, there is a **different** transformer. As they state in Defn 3.4, "for every ... $n$, there is a $L$-layer ... transformer". This means that one needs a *family* of transformers, one for each input size $n$, to solve a given problem, and the weights of the transformer for input length $n$ may have nothing to do with that of the transformer for input lengths $n+1$. To specify such a family, one thus needs to specify an infinite family of unrelated weights, which obviously is unrealistic. In contrast, in practice, one trains a transformer on inputs of certain lengths, freezes those weights, and then uses the same frozen-weights transformers for inputs (and chains-of-thought) of arbitrary lengths. In fact, inspired by this, the theoretical research on the representation power of transformers in the past 2-3 years has gone in the opposite direction---from non-uniform upper bounds, to tighter and tigher uniform bounds (e.g., log-space uniform, log-time uniform, FO-uniform, etc.). Importantly, all along, the model of transformers used was uniform. The *non-uniformity* of the model assumed here has other, well-known undesirable consequences also seen in non-uniform circuits---it allows transformers to **trivially solve certain undecidable problems**, namely any undecidable unary problem, over the alphabet $\{1\}$. E.g., it can solve the halting problem expressed in unary, just like all non-uniform circuit classes (including P/poly) can. Besides being unrealistic, this raises a question about the meaningfulness of the technique used to prove the main result (Theorem 3.3). In order to simulate a circuit of size $T(n)$, one must somehow *embed* the circuit into the transformer as the transformer needs to know what circuit to compute. As seen from the proof of it in the appendix, the authors have a creative solution: they put the description of the circuit in the *positional embedding* of the transformer. While interesting and unique, this has two undesirable implications: 1. The positional embedding for inputs of length $n$ is allowed to be arbitrarily different from the positional embeding for inputs of length, say, $n+1$ (because there is no uniformity constraint between the circuits for the two respective sizes, $n$ and $n+1$), which departs heavily from practice. 2. It means that the proposed construction must include some **uncomputable / undecidable positional embeddings**! To see this, consider any undecidable unary problem $P$ in P/poly. The typical polysize circuit construction for $P$ is to have, for each $n$, a trivial circuit $C_n$ that outputs a $1$ if and only if $1^n$ is in that undecidable language (e.g., $1^n$ is the unary encoding of the $n$-th Halting problem). Thus, by the authors' construction, there is a trivial transformer that decides the same language---and its embedding of the first position computes membership in that undecidable language! In other words, the embedding itself in not computable by any reasonable model of computation. To summarize this, while the construction is correct to my understanding, it is for a formal model that departs from practice and assumes a lot of power (e.g., that of having access to potentially uncomputable embeddings). At the very least, these limitations and their implications should be clearly discussed in the paper.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> * In the abstract, the statement "with $T$ steps of CoT, constant-depth transformers ... can solve ..." should be qualified with T being at most a polynomial in $n$. * In the 2nd last line of page one, I think you mean "encoder-only" rather than "decoder-only"; or single-step decoder. * In line 3 of section 2, do you mean $\phi(bin_k(x)) = x$ rather than $\ldots = 0$? * In the 2nd paragraph of section 2, where is the input length limited to $n_\max$? * page 3, two lines before defn 3: "over more two" => "over more than two"

Author response: none.

**Critique 4** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 1. Please see my main concern above regarding non-uniformity. I don't really have any specific question around it, though I wonder what you think about the non-uniformity issue above and how, if you choose to, would you incorporate it in a revised version of the paper.

Author response — `disagreement` (units 1–3):

> **Q1: Our computation model is non-uniform.** > **Response**: Thanks you for your this critical question and constructive feedbacks. Please refer to our general response on the non-uniformty issue to all the reviewers.

**Critique 5** — aspect `soundness`, severity `major`, polarity `neutral`, target `section`, actionable `True`

> 2. After Theorem 3.2, you mention that an analog of this theorem remains open for log-precision transformers even with a constant number of bits for the exponent. Could you elaborate why one can't just absorb the constant bits of the exponent into additional constant bits of the significand? Perhaps you can illustrate it with what goes wrong if one has $1$ bit for the exponent?

Author response — `clarification` (units 5–12):

> Why cannot we absorb constant bits of exponent into additional constant bits of the significand?** > **Response**: A short answer is that the existing proof of $\mathsf{TC}^0$ upper bound relies on the fact that the addition among fixed point numbers satisfy the association rule (assuming no overflow happens), and floating point numbers with any non-zero bits for the exponent does not satisfy the association rule. Taking the floating point system defined in our manuscript as an example, let both the number of exponents and precision, namely, $e$ and $s$ be $1$, we have $\mathbb{F} _{1,1} = \{- […]

`[ignored]` **Minor points**

## Example 10 — review `lxPosBP7P5` (ICLR 2024)

17 units, 12 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The idea of defining code symmetries as semantics-preserving transformations, enabling precise reasoning within LLMs is somewhat interesting.

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> To evaluate the approach, four analysis tasks that require a deep understanding of code behavior such that they are expected to stay invariant to code symmetries were considered.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> Also a set of real-world semantics-preserving transformations

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> beyond PDG automorphisms to evaluate SYMC’s generalization in the experiments.

Author response — `new_experiment` (units 6–25):

> Thanks for bringing up the robustness angle against adversarial attacks. The key approach we started off from this paper is the development of a code model with **provable robustness by construction** against semantics-preserving code permutations. Guided by this framework, we proved that our approach is verifiably robust against any possible adversarial permutations, and thus not bound by minimal perturbations assumed in many adversarial attacks [1]. We leave exploring other code symmetry groups and their robustness guarantees as future work. [1] Pierazzi, Fabio, Feargus Pendlebury, Jacopo Co […]

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> The paper needs more evaluations, e.g. an evaluation of the robustness of SYMC using the adversarial attack methods based on code transformations.

Author response — `clarification` (units 33–44):

> **Q2: Have you tried to compare with "GraphCodeBERT: Pre-training code representations with data flow", which is a state-of-the-art method considering the inherent structure of code, in your evaluation?** Thanks for pointing out the related works. We will add more discussion to GraphCodeBERT and other related works. To answer your specific question, we include the new evaluation results we have obtained during the rebuttal. As shown in the following, we compare SymC to the baselines including GraphCodeBERT. Significantly, SymC outperforms GrahCodeBert by 19.9%, even when it is pre-trained with […]

**Critique 6** — aspect `clarity`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> Some contents are not well presented/stated.

Author response — `clarification` (units 44–53):

> **Q3: Page 5, "PDG ($V_{PDG}$,$E_{PDG}$) is a super graph of $\mathcal{IG}$, sharing the same vertices but having a superset of edges ($E_{PDG}\subseteq E_{\mathcal{IG}}$), because we consider all memory accesses as aliasing, making PDG a conservative construction of $\mathcal{IG}$", If you "consider all memory accesses as aliasing", which is apparently a very weak encoding of the program semantics, it seems there would be too many aliases in the programs, making most statements unexchangeable to accomplish semantics-preserving statement permutations?** We will clarify this point by adding con […]

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> Q: As stated in the paper, current code LLMs struggle with generalization to new code. Have you tried to evaluate the robustness of SYMC using the adversarial attack methods based on code transformations? The evaluation may make your method more convincing.

Author response — `clarification` (units 56–60):

> Sorry for the confusion. Yes, the positive and negative distance corresponds to $p_{ij}$ and $n_{ij}$, respectively. The positive distance denotes the distance from node $V_i$ to the lowest common ancestor of node i and j, $T_{ij}$. The negative distance denotes the distance from node $V_j$ to $T_{ij}$. We will make the explanation more clear in the paper.

**Critique 8** — aspect `related_work`, severity `major`, polarity `negative`, target `reference`, actionable `True`

> Q: Have you tried to compare with "Graphcodebert: Pre-training code representations with data flow", which is a state-of-the-art method considering the inherent structure of code, in your evaluation?

Author response — `clarification` (units 61–63):

> **Q5: Page 2, "SYMC enforces its output to stay invariant via keeping its learned representation G-equivariant, where the code representation $(e_1, e_2, e_3, e_4)$ is transformed into $(e_2, e_3, e_4, e_1)$ xxx", should "$(e_2, e_3, e_4, e_1)$" be "$(e_2, e_1, e_3, e_4)$" as shown in Figure 1a?** Great catch! We have fixed the mistake in the updated paper.

**Critique 9** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> Q: Page 5, "PDG (VPDG,EPDG) is a super graph of IG, sharing the same vertices but having a superset of edges (EPDG ⊇ EIG), because we consider all memory accesses as aliasing, making PDG a conservative construction of IG", If you "consider all memory accesses as aliasing", which is apparently a very weak encoding of the program semantics, it seems there would be too many aliases in the programs, making most statements unexchangeable to accomplish semantics-preserving statement permutations?

Author response — `clarification` (units 65–68):

> Which lines are for Aut(PDG)-equivariant self-attention layers and which are for the Aut(PDG)-invariant ones?** Figure 4a shows the performance drop when we set the subsequent self-attention layers Aut(PDG)-*invariant*, not Aut(PDG)-*equivariant*, starting from 2nd, 4th, 6th self-attention layer (see caption of Figure 4). This is to demonstrate having equivariance in the code representation learning is important, compared to making it invariant throughout all the layers. We will clarify this in the paper.

**Critique 10** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> Q: Page 6, "Each entry dij is a 2-value tuple (pij , nij), indicating the shortest path from the lowest common ancestor of Vi and Vj , denoted as Tij , to Vi and Vj , respectively", is pij the positive distances and nij the negative distances as denoted in the next paragraph? Also, what do you mean by positive distances and negative distances?

Author response: none.

**Critique 11** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> Q: Page 2, "SYMC enforces its output to stay invariant via keeping its learned representation G-equivariant, where the code representation (e1, e2, e3, e4) is transformed into (e2, e3, e4, e1) xxx", should "(e2, e3, e4, e1)" be "(e2, e1, e3, e4)" as shown in Figure 1a?

Author response: none.

**Critique 12** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> Q: Page 9, the lines labeled 2nd, 4th, 6th in Figure 4a. Which lines are for Aut(PDG)-equivariant self-attention layers and which are for the Aut(PDG)-invariant ones?

Author response: none.

## Example 11 — review `ItMb4N6wVd` (ICLR 2024)

21 units, 13 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1.	The novel formulation, adopting from certificate for adversarial robustness, is very interesting and could potentially be applied in practice

Author response: none.

**Critique 2** — aspect `clarity`, severity `minor`, polarity `positive`, target `section`, actionable `False`

> 2.	The analysis and explanation of the proposed methodologies, described in Algorithm 1 is very clear and comprehensive.

Author response: none.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 3.	The theoretical analysis of the performance guarantees of Algorithm 1 and 2 is novel and useful for different strategies to explore the regions

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 4.	Numerical results are abundant, including large-scale images datasets and synthetic datasets.

Author response — `clarification` (units 1–9):

> > Despite that the authors mentioned in Section 8 Discussion that the $l_\infty$ ball can potentially be generalized to hyper-rectangles or $l_p$ balls, all these hyper-balls may not carry semantic meanings of the samples. Therefore even if we can certificate that the pseudo-samples within the hyper-balls have high fidelity, those pseudo-samples may not carry meaningful information... Yes you are right that all examples in a region may not be realistic input examples in the domain lying on the data manifold. In such cases one could after the region is found consider only realistic examples in  […]

**Critique 5** — aspect `significance`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 1.	Despite that the authors mentioned in Section 8 Discussion that the l_\infinty ball can potentially be generalized to hyper-rectangles or l_p balls, all these hyper-balls may not carry semantic meanings of the samples. Therefore even if we can certificate that the pseudo-samples within the hyper-balls have high fidelity, those pseudo-samples may not carry meaningful information, since human interpretation on images is very different from Euclidean distances. It is encouraged that the authors address this concern with a discussion.

Author response — `clarification` (units 11–14):

> > The connection between the Algorithm 1 and Algorithm 2 proposed in Section 4 seems to be detached from the original optimization formulated in equation 1. Algorithm 1 decides on a width $w$ and Algorithm 2 tries to certify that width (i.e. check if $f_{x_0}(x) \ge \theta \quad \forall x \in B_\infty(x_0, w)$). If certified, Algorithm 1 chooses a bigger width which again Algorithm 2 tries to certify. Thus, the two algorithms are tightly linked to the optimization formulated in eq. 1, where we are trying to find the maximum possible (certified) width.

**Critique 6** — aspect `soundness`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> 2.	The connection between the Algorithm 1 and Algorithm 2 proposed in Section 4 seems to be detached from the original optimization formulated in equation 1. It is encouraged that the authors strengthen the connection.

Author response — `clarification` (units 15–17):

> > It is encouraged that the authors include more discussion on different explanation functions, or give concrete examples in Section 2. Example explanation functions would be linear like in LIME, logistic regression, small decision trees, rule lists, interpretable neural architectures such as CoFrNet. We have now mentioned some of these in Section 2.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> 3.	The authors mention several advantages of the novel explainability certificate, including stability of the explanations and explanation reuse, but did not provide numerical results or analysis on these benefits over existing explainable AI tools. It is encouraged that the authors

Author response — `clarification` (units 28–37):

> > The authors mention several advantages of the novel explainability certificate, including stability of the explanations and explanation reuse, but did not provide numerical results or analysis on these benefits over existing explainable AI tools. Our approach compliments the current work in XAI where XAI toolkits (viz. AIX360, Captum, InterpretML, etc.) contain predominantly explanation methods and/or (quality) metrics. One can take these methods and metrics and apply our approach on top to obtain trust regions, which could be used for any of the applications outlined in the introduction. As […]

**Critique 8** — aspect `novelty`, severity `minor`, polarity `neutral`, target `reference`, actionable `True`

> 4.	This certificate is closely related to adversarial examples, and in related literature there are also studies on the maximal hyper-balls that will not suffer from a decision change. Their algorithm is also similar to the searching algorithm proposed in Algorithm 1. The novelty here is the quality metric and the explanation function.

Author response — `clarification` (units 18–24):

> > Is it possible to extend the techniques to features? A thing to note here is that when we find trust regions we are finding instances in the input space where an explanation, which are typically feature importances, is valid for all of them. In other words, the feature importances hold for all examples in that region. Hence, we are highlighting important features in that region. However, if your goal is to find features that are similar one could potentially transpose the data matrix and find regions of similar features, where the explanations would now point to important instances. > It is  […]

**Critique 9** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> It is encouraged that the authors include more discussion on different explanation functions, or give concrete examples in Section 2.

Author response — `clarification` (units 24–24):

> > It is encouraged that the authors add visualization of the regions, provide some intuitive explanations, with simple (semi-)synthetic data.

**Critique 10** — aspect `significance`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> 5.	In XAI, the explainability of features is sometimes more important than individual samples. Is it possible to extend the techniques to features?

Author response — `clarification` (units 18–24):

> > Is it possible to extend the techniques to features? A thing to note here is that when we find trust regions we are finding instances in the input space where an explanation, which are typically feature importances, is valid for all of them. In other words, the feature importances hold for all examples in that region. Hence, we are highlighting important features in that region. However, if your goal is to find features that are similar one could potentially transpose the data matrix and find regions of similar features, where the explanations would now point to important instances. > It is  […]

**Critique 11** — aspect `clarity`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> 6.	One of the most important aspects in XAI tools is visualization. It is encouraged that the authors add visualization of the regions, provide some intuitive explanations, with simple (semi-)synthetic data.

Author response — `clarification` (units 24–24):

> > It is encouraged that the authors add visualization of the regions, provide some intuitive explanations, with simple (semi-)synthetic data.

**Critique 12** — aspect `other`, severity `minor`, polarity `neutral`, target `general`, actionable `False`

> Please refer to the Weaknesses.

Author response: none.

**Critique 13** — aspect `other`, severity `minor`, polarity `neutral`, target `general`, actionable `False`

> I will consider raising the scores if the authors could adequately address my questions in the rebuttal.

Author response: none.

## Example 12 — review `c3WwaxjOHq` (ICLR 2024)

15 units, 9 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> ●	The paper addresses the limitations of existing benchmarks for multivariate time series anomaly detection (MTSAD) and proposes a new benchmark framework.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `positive`, target `experiment`, actionable `False`

> ●	It presents a novel benchmark for MTSAD, with the largest real-world dataset to date, which covers diverse anomaly types and scenarios in a complex and large-scale system.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> ●	The paper compares 14 machine learning and deep learning models using various evaluation metrics, providing an analysis of their performance.

**Critique 4** — aspect `reproducibility`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> ●	It makes the benchmark and dataset open-sourced, which can facilitate future research and applications in MTSAD.

**Critique 5** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> ●	It is unclear how the new benchmark addresses the flaws in existing benchmarks and datasets, as mentioned in the paper. ●	How does the proposed benchmark address the limitations and flaws of existing benchmarks and datasets?

**Critique 6** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> ●	The paper does not discuss the limitations or potential biases of the proposed benchmark and dataset. ●	What are the potential limitations or biases of the new benchmark and dataset, and how are they addressed?

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> ●	It does not provide a thorough analysis of the strengths and weaknesses of the compared algorithms, focusing more on the experimental results. ●	Can the authors provide a more in-depth analysis of the strengths and weaknesses of the compared algorithms, beyond the experimental results?

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> Ever since the benchmark paper in Neurips22, I see a good number of similar papers. Benchmarking is an exercise I must applaud but detecting anomalies must be done on data sets which have a wide range of anomalies (1- many). The methods which are evaluated--how do they perform on test data sets with no anomalies? How many false flags do they raise?

**Critique 9** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> Have you tested the algorithms on public datasets (AWS, yahoo etc)?

## Example 13 — review `tilAxMcoJh` (ICLR 2024)

41 units, 6 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Work is relevant to ICLR and adherent to the recent body of research on RL.

Author response: none.

**Critique 2** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The idea of generating a Curriculum of tasks to learn how to play against a population of opponents is reasonable and has good applicability to practical applications.

Author response: none.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> - Authors present evaluation domains of high complexity (as far as 1x1 domains go).

Author response: none.

**Critique 4** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> - The approach is very unclear from the general modeling to how the experiments were performed. It's very hard to judge if the modeling is realistic and the experiments were carried out in a fair way. I will break down the main sources of confusion below: -- It is not clear to me what is the "population" of agents that the ego agent has to beat on equation (2). In a practical application, is the agent expected to have to beat an unknown population of agents? If the population is unknown (which sounds to me a more realistic modeling), how is the agent able to generate the strategies it plays against when the curriculum is created? If the population of opponents is known beforehand (which sounds very unrealistic for most applications), it explains how the agent can generate the curriculum. -- I don't quite understand what is a "solution" for the GA so that crossover and mutation is applied. The agent can realistically pick which opponent it is going to play against for a particular episode, what else composes the "curriculum task:? how are those combined/mutated. Those are key elements of the proposed algorithm and are not clearly explained in the main text of the paper. In special, I cannot understand what the agent has the power to manipulate to generate a new "curriculum task". -- The "blind agent" sounds to be a very ad hoc addition to the algorithm. How should this blind agent be developed for a new domain? Is there an automated way of generating it? I assume just generating an agent with random actions would have no effect given that for any reasonably-complex task a random agent would be very easily beaten. -- It's not clear what are the 5 "baseline opponents" used to test the algorithms in the experimental evaluation. Are the agents aware of those opponents and able to use them for training for as long as they have remaining training steps? or are they held out just for generating metrics. An interesting way of validating the algorithms would be to have a number of high-performance strategies they can manipulate to play against during training, and a number of unknown strategies that are never seen by the agents and only used for calculating the performance metrics. In this way you would actually be evaluating how general is the learned strategy. -- How strong are the strategies that the agents had to beat in the experiments, and how were them learned? In the evaluation, there should be at least one adaptive agent that is given time to learn how to "hack" the ego agent strategy.

Author response — `clarification` (units 3–87):

> Point 1: Since we are using a minmax formulation for equation 2, Ξ is the curriculum of scenarios (opponent policy-environment parameter pairs) that the ego agent π has difficulty in solving. Therefore, the opponent policy would be the one that minimizes the zero-sum return of the ego agent π for the given environment parameter ψ Point 2: A curriculum Ξ consists of scenarios ξ. Scenario defines opponent policy π_opp and environment parameters ψ. Using a genetic algorithm, we would migrate the distribution of scenarios in a curriculum that minimizes the zero-sum outcome for the ego agent and ma […]

**Critique 5** — aspect `related_work`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - THe literature review was very limited on the transfer of information and curriclum in multi-agent systems. I was surprised that the authors did not mention the first survey to suggest to develop multi-agent curricula of evolving strategies: Silva, Felipe Leno Da, and Anna Helena Reali Costa. "A survey on transfer learning for multiagent reinforcement learning systems." Journal of Artificial Intelligence Research 64 (2019): 645-703. Also, while the agents knowing and controlling the opponent strategies sounds unrealistic, they could easily model then and build Curricula based on modeled versions of those opponents: Stefano V. Albrecht, Peter Stone, Autonomous agents modelling other agents: A comprehensive survey and open problems, Artificial Intelligence, Volume 258, 2018. One issue that some Curriculum Learning approaches observed is that it is hard to figure out how many tasks have to be generated. One popular approach executes a random walk based on the task transferability to prune huge Curricula: Silva, F. L. D., & Costa, A. H. R. (2018, July). Object-oriented curriculum generation for reinforcement learning. In Proceedings of the 17th international conference on autonomous agents and multiagent systems (pp. 1026-1034).

Author response — `clarification` (units 44–56):

> Point 6: We thank the reviewer for making suggestions on papers to cite. We agree that these papers are relevant to and share interesting insights about our approach and will include the citations in our final draft. We thank the reviewer for the helpful feedback! Here's part 2 of our response. Question 1: The agent has no knowledge about the real opponent population it’s going to face in the test time. One of the main motivations for using a zero-sum formulation is that by using such formulation, we can turn the multi-agent problem into minmax problem, reducing the area the curriculum has to  […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `neutral`, target `general`, actionable `True`

> 1) How much knowledge do the agents have about the real "opponent population". 2) What exactly is manipulated by the GA to generate new tasks? 3) Why is the "blind agent" development not added to the algorithm? 4) Where do the strategy from the opponents in the experiments come from? Are there adaptive agents as opponents?

Author response — `clarification` (units 48–56):

> Question 1: The agent has no knowledge about the real opponent population it’s going to face in the test time. One of the main motivations for using a zero-sum formulation is that by using such formulation, we can turn the multi-agent problem into minmax problem, reducing the area the curriculum has to search. Question 2: The Genetic Algorithm has control over the environmental parameters and the choice of opponents (RL agents loaded from previous checkpoints or Blind Agents genetically optimized). Question 3: Blind Agents are not developed by humans. They are optimized by a genetic algorithm  […]

## Example 14 — review `mQ22n7s8RS` (ICLR 2024)

25 units, 8 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The paper tackles an important problem.

**Critique 2** — aspect `related_work`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> It has a detailed discussion of related works.

**Critique 3** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> Performance improvements are consistent.

**Critique 4** — aspect `soundness`, severity `blocking`, polarity `negative`, target `general`, actionable `True`

> 1. The proposed method is too trivial. It simply searches a classwise scaling factor on the validation set. There is also no insight provided, e.g., why does the proposed classwise scaling bring improvements in the target metric? How does the optimal scaling factor differ for various metrics?

**Critique 5** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> 2. The comparison with baselines is potentially unfair. Since the scaling factors are found by greedy search on the validation set, they can be regarded as trainable parameters. Hence the proposed method effectively leverages the validation set as additional training data. Hence direct comparison with baselines is unfair.

**Critique 6** — aspect `clarity`, severity `blocking`, polarity `negative`, target `section`, actionable `True`

> 3. The paper is poorly written. For example, in the first paragraph of the introduction, the concept of "group" and "minority group" is discussed without proper introduction. The claim that "there has been little exploration for a comprehensive evaluation that considers both metrics jointly" is not convincing, as there are many works studying the tradeoff between in-distribution and out-of-distribution accuracy [1*]. Despite the simplicity of the method, it is poorly explained, e.g., what is the detailed procedure of greedy search? Is it by gradient descent or brute-force trial from a pre-determined list? Section 3.3 is especially confusing: what are the cluster centroids used for? How to perform step 2? How to determine the cluster membership?

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `negative`, target `experiment`, actionable `True`

> Other suggestions & questions 1. It is recommended to include the dataset statistics (train/val/test set), especially because the proposed method leverages the val set. 2. Beyond numerical results, it is more interesting to see some qualitative examples of how the proposed approach improves baselines.

**Critique 8** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> See weaknesses.

`[ignored]` [1*] Calibrated ensembles can mitigate accuracy tradeoffs under distribution shift. ⏐ UAI 2022.

## Example 15 — review `OpsThIQ6Jd` (ICLR 2024)

12 units, 7 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> 1. The imperfection of learned reward models is indeed an important topic for PbRL.

**Critique 2** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> 2. The proposed method is verified on a variety of manipulation tasks.

**Critique 3** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. The assumption that learned reward models can identify low-preference regions more precisely than high-preference regions is quite strong but lacks justification and verification. More in-depth investigations, especially quantitative ones, are necessary here. For example, this is affected by the way preference queries are generated, which is not considered in this paper.

**Critique 4** — aspect `soundness`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 2. Label scarcity is an issue for both online PbRL and offline PbRL, and semi-supervised learning is a natural fit for this setting. For example, a solution is already proposed in [1]. Yet this paper does not discuss or offer results for semi-supervised learning approach.

**Critique 5** — aspect `soundness`, severity `minor`, polarity `negative`, target `general`, actionable `True`

> 3. The paper does not consider the quality of labels, i.e. label noise, which is an apparent issue as the proposed method leverages estimated returns for ranking trajectories.

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> 1. Could you provide justification and evidence for the assumption mentioned in Weakness #1?

**Critique 7** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> 2. How does this method perform on the human-generated dataset provided by PT?

`[ignored]` [1] SURF Semi-supervised Reward Learning with Data Augmentation for Feedback-efficient Preference-based Reinforcement Learning

## Example 16 — review `1YcysWy8tS` (ICLR 2024)

39 units, 7 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The problem is very interesting, the method is simple yet effective.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The current approach requires finetuning classifiers as well as training diffusion models to be a joint model.

Author response: none.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> This work removes this limitation and shows that the off-the-shelf classifier has the potential to outperform noise-aware models.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `blocking`, polarity `negative`, target `experiment`, actionable `True`

> Although the work is very interesting, there are still some questions: 1. The comparison is not so comprehensive. Since the main baseline should be the noise-aware classifier, the work provides little comparison in Table 5. More metrics such as IS, sFID, Precision and Recall should be included. 2. In Table 5, results for IMN64x64 as well as IMN256x256 for DDPM from Dhariwal and Nichol (2021) is missing. Whether or not the method can perform well on other resolutions. 3. Does off-the-shelf classifier guidance provide conditional information for the unconditional diffusion model? In my belief, the main objective of the guidance should be providing conditional information for the unconditional diffusion model rather than just improving the generated image quality. In Table 5, the Diffusion model on ImageNet128x128 is conditionally trained. Thus, the conditional information from an off-the-shelf classifier is not important. Results for combining off-the-shelf classifiers with unconditional models should be included. 4. How off-the-shelf models Resnet can be used with ImageNet64x64 or ImageNet128x128 although these models are trained on ImageNet224x224? Besides, the generated images are clip to be in range of [-1; 1], how does it fit with model trained with input images normalized by ImageNet datasets? 5. There is a fatal gap in the modeling part in Algorithm 1, in the sampling equation $\hat{x}_{t-1} \sim \mathcal{N}(\mu + \gamma _t g, \sigma _t)$. In the original paper by Dhariwal and Nichol (2021), the sampling resulted from the $\log(p _{ \theta }(x_t|x _{t+1}) p _{\phi}(y|x_t))$. However, given the structure of Algorithm1, this equation is no longer valid since the gradient is taken regarding $x _0 (t)$ instead of $x_t$. In order to apply the same sampling process, even when $x_0(t)$ is forward through the classifier, the gradient should be taken regarding $x_t$. 6. I guess from the point (5), this is the main reason why the method can not be applied to DDIM? 7. Ablation study is missing, it is quite vague to understand which proposed scheme is the main course for the improvement. From my understanding, there are three main differences from normal classifier guidance which are: * Gradients via $x_0(t)$ instead of $x_t$ * Guidance schedule * $\tau _2$ temperature However, discussion on the contribution of each of them is missing 8. Given three contributions as in (7), does the performance of the noise-aware classifier guidance also get improvements? 9. Besides Resnet, how are other architectures such as DenseNet, Transformers? Do they also work with this scheme? 10. CLIP guidance should be compared against the noise-aware CLIP guidance 11. The connection from 4.1, 4.2, 4.3 and 4.4, 4.5 as well as the design of the algorithm lacks some connections. It seems that the paper is written in hurry so that the format of the paper is not really good as well as some errors in equations: 1. Equation (2) should be $\log exp(\tau f _{y(x)})$? Check format of the equation (2) also. 2. Equation (3) should be $\log exp(\tau _1 f _{y(x)})$?

Author response — `new_experiment` (units 3–91):

> ## "The comparison is not so comprehensive. Since the main baseline should be the noise-aware classifier, the work provides little comparison in Table 5. More metrics such as IS, sFID, Precision and Recall should be included." In our research, we aim to demonstrate the potential of the more accessible traditional ResNet classifier and prove that even without specifically noise-finetuned, the off-the-shelf classifier can guide the diffusion to generate high-quality sampling: FID: 2.19 in ImageNet128x128) not only largely surpass the noise-aware fine-tuned classifier guided diffusion [Dhariwal e […]

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> See the weaknesses.

Author response: none.

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `section`, actionable `True`

> The work is interesting and potential, yet there are a number of concerns as well as writting.

Author response: none.

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> Will raise the score if all concerns are solved.

Author response: none.

## Example 17 — review `AIrci2WHF5` (ICLR 2024)

28 units, 17 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Phrasing the problem of drug discovery as a meta-learning problem and using graph neural networks as encoders for neural processes is in the reviewer's opinion both original and reasonable.

Author response: none.

**Critique 2** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The paper is well written and easy to follow, and the problems of meta-learning in drug discovery is well delineated.

Author response: none.

**Critique 3** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The approach of fine-tuning is intuitive and seems reasonable.

Author response: none.

**Critique 4** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The main contribution of the paper is the usage of vanilla NPs with an encoder that is an adapted graph neural network of a previously introduced method [1] . In total, the contribution seems too incremental and too little.

Author response: none.

**Critique 5** — aspect `clarity`, severity `major`, polarity `negative`, target `section`, actionable `True`

> - The description of the methodology itself (molecular graph attentive encoder) is not detailed enough and very superficial (in total 5 lines of the entire manuscript).

Author response — `clarification` (units 2–7):

> **Insufficient description of the GNN architecture** We thank the reviewer for raising this point. We would like to explain that the architecture of the GNN used by our MG-NPs is based on a very popular architecture (Attentive FP [1]) whose paper we reference and can be checked by the readers. The adaptation procedure is a bit trickier to replicate than the architecture (especially the one using MAML), so we used more space on that section instead, given the length constraints. We explain the differences between Attentive FP and our GNN in Appendix C.3.2. In addition, if our article is accepte […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `general`, actionable `True`

> - The fine-tuning and MAML approaches for parameter adaption described in the paper are of little novelty. In addition, the theoretical benefit and motivation of the MAML tuning is not clear to the reviewer since NPs can generally already be considered as meta learnerns.? Empirically, the MAML tuning sometimes improves and sometimes worsens predictive performance (see, e.g., Table~1 FP-CNP with FP-CNP (MAML) or MG-LNP with MG-LNL (MAML)).

Author response — `disagreement` (units 8–12):

> **Fine-tuning and MAML for parameter adaptation are of little novelty.** As far as we know, we are the first to propose parameter adaptation for NPs during meta-testing. The reason why parameter adaptation could be helpful is that the meta-learning done by a NP, and the adaptation based on the contexts, are not necessarily perfect. Unlike a Gaussian process, which will make accurate predictions on the context points it has seen during its evaluation, a NP has no theoretical guarantees of accuracy on the context points. We exploit context predictions' errors to improve adaptation to meta-test f […]

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The experimental section seems very thin and more evaluations with missing competing methods should be made. See, e.g., [2] as a reference.

Author response: none.

**Critique 8** — aspect `related_work`, severity `minor`, polarity `negative`, target `reference`, actionable `True`

> - The reference section is incomplete and sometimes incorrect. For instance, the "Attention is all you need" paper is from 2017 and not from 2023 and misses the conference information. - The authors fail to cite relevant literature on graph neural processes, e.g. [3].

Author response — `clarification` (units 13–18):

> **Incorrect citations in bibliography** We thank the reviewer for catching this error! We have investigating the source and it appears the mistaken citations had been downloaded from arXiv. For example, the button "Export BibTeX citation" on the arXiv page of "Attention is all you need" ( https://arxiv.org/abs/1706.03762 ) yields a citation without the conference information and with the year 2023. We were unaware arXiv worked in this way. We apologize for this error, which we have now amended.

**Critique 9** — aspect `related_work`, severity `minor`, polarity `neutral`, target `reference`, actionable `False`

> [1] https://pubs.acs.org/doi/10.1021/acs.jmedchem.9b00959

Author response: none.

**Critique 10** — aspect `related_work`, severity `minor`, polarity `neutral`, target `reference`, actionable `False`

> [2] https://arxiv.org/abs/2205.02708

Author response: none.

**Critique 11** — aspect `related_work`, severity `minor`, polarity `neutral`, target `reference`, actionable `False`

> [3] https://arxiv.org/abs/2305.18719

Author response: none.

**Critique 12** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> - Some clarifications of the math of the encoder structure or an illustrative figure would in the reviewer's opinion improve the quality of the manuscript. While background on NPs is explained in sufficient detail (both in the main manuscript as well as the appendix), the actual method is not described at all.

Author response — `clarification` (units 2–7):

> **Insufficient description of the GNN architecture** We thank the reviewer for raising this point. We would like to explain that the architecture of the GNN used by our MG-NPs is based on a very popular architecture (Attentive FP [1]) whose paper we reference and can be checked by the readers. The adaptation procedure is a bit trickier to replicate than the architecture (especially the one using MAML), so we used more space on that section instead, given the length constraints. We explain the differences between Attentive FP and our GNN in Appendix C.3.2. In addition, if our article is accepte […]

**Critique 13** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> - The authors could evaluate the case where a NP has both a latent and deterministic encoder. See, e.g., [2]

Author response: none.

**Critique 14** — aspect `experimental_comparison`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> - As far as I can tell, the authors do not compare themselves against recent methods such as in [1]. Is this true and if so is there any reason for that?

Author response — `new_experiment` (units 47–48):

> We thank the reviewer for raising this point. ADKF-IFT [3] is now included as a baseline.

**Critique 15** — aspect `soundness`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> - LNPs are generally harder to train then CNPs. Is the poor performance of LNPs due to this fact or how can it be explained? Is it because the authors seemed to have trained only for a fixed number of iterations and not until converge (see Appendix C3.7)?

Author response — `clarification` (units 49–58):

> **Why do LNPs perform worse than CNPs?** Initially, we trained CNPs and LNPs for the same amount of iterations in order to promote an equalitarian allocation of resources and a fair comparison. However, we believed the LNP did not perform so well partly because its regularization term promoted underfitting and made reaching a good optimum challenging. Therefore, we attempted trainining during twice the number of iterations (6000 epochs). However, after 3000 epochs the results did not change substantially. In addition, in order to facilitate reaching a good optimum, we trained two versions of e […]

**Critique 16** — aspect `related_work`, severity `minor`, polarity `neutral`, target `reference`, actionable `False`

> [1] https://arxiv.org/abs/2205.02708

Author response: none.

**Critique 17** — aspect `related_work`, severity `minor`, polarity `neutral`, target `reference`, actionable `False`

> [2] https://arxiv.org/abs/1901.05761

Author response: none.

## Example 18 — review `djmyVVuIaL` (ICLR 2024)

13 units, 10 critiques, 1 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The paper is well-written and well-motivated.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - The proposed PB-LLM scheme is easy to follow and straightforward to understand.

Author response: none.

**Critique 3** — aspect `significance`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> - Exploring to improve the memory and/or storage efficiency using quantization (and algorithmic approximation in general) of LLMs is a promising research direction.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - Only Llama 7B is studied as the LLM for PB-LLM and all other baselines. Thus, it's not clear how the PB-LLM method performs on larger-scale models.

Author response — `new_experiment` (units 1–21):

> ## To Weakness 1 & Question 1: Extensive Experiments on LLaMA-13B and LLaMA-30B. > Weakness 1: Only Llama 7B is studied as the LLM for PB-LLM and all other baselines. Thus, it's not clear how the PB-LLM method performs on larger-scale models. Question 1: How does PB-LLM's performance vary among various sizes of Llama models, e.g., 7B-65B? Thank you for acknowledging the various aspects of our work and for your valuable recommendation. In response, we have extended our experimentation to include larger LLaMA models, specifically LLaMA-13B and LLaMA-30B, to gauge the scalability of our PB-LLM me […]

**Critique 5** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - Only pre-trained base models are experimented with those models, however, are usually not deployed directly as applications.

Author response — `new_experiment` (units 22–40):

> ## To Weakness 2 & Question 2: Extensive Experiments on Vicuna-7B. > Weakness 1: Only pre-trained base models are experimented with those models, however, are usually not deployed directly as applications. Question 1: Only pre-trained base models are experimented with those models, however, are usually not deployed directly as applications. Thanks for your suggestion. We are testing the performance of PB-LLM on Vicuna-7B (we use this checkpoint from huggingface: https://huggingface.co/AlekseyKorshuk/vicuna-7b). The results will come out in 8 hours. **Nov/19/2023 Results Update:** We acknowledg […]

**Critique 6** — aspect `soundness`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> - The LLM quantization scheme is motivated using an angle of GPU memory efficiency. However, the actual GPU memory usage before and after binarization/quantization is not studied in this paper.

Author response — `new_experiment` (units 41–57):

> ## To Weakness 3 & Question 3: actual GPU memory saving. >  To Weakness 3: The LLM quantization scheme is motivated using an angle of GPU memory efficiency. However, the actual GPU memory usage before and after binarization/quantization is not studied in this paper. Question 3: What is the actual GPU memory saving look like for PB-LLM and all considered baselines? We acknowledge the importance of understanding the actual GPU memory usage before and after binarization/quantization. Unfortunately, our team lacks dedicated GPU implementation experts, which hindered us from providing a comprehensi […]

**Critique 7** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> - How does PB-LLM's performance vary among various sizes of Llama models, e.g., 7B-65B?

Author response — `new_experiment` (units 1–21):

> ## To Weakness 1 & Question 1: Extensive Experiments on LLaMA-13B and LLaMA-30B. > Weakness 1: Only Llama 7B is studied as the LLM for PB-LLM and all other baselines. Thus, it's not clear how the PB-LLM method performs on larger-scale models. Question 1: How does PB-LLM's performance vary among various sizes of Llama models, e.g., 7B-65B? Thank you for acknowledging the various aspects of our work and for your valuable recommendation. In response, we have extended our experimentation to include larger LLaMA models, specifically LLaMA-13B and LLaMA-30B, to gauge the scalability of our PB-LLM me […]

**Critique 8** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> - How does PB-LLM perform for aligned/instruction fine-tuned models, e.g., Alpaca and/or Vicuna?

Author response — `new_experiment` (units 22–40):

> ## To Weakness 2 & Question 2: Extensive Experiments on Vicuna-7B. > Weakness 1: Only pre-trained base models are experimented with those models, however, are usually not deployed directly as applications. Question 1: Only pre-trained base models are experimented with those models, however, are usually not deployed directly as applications. Thanks for your suggestion. We are testing the performance of PB-LLM on Vicuna-7B (we use this checkpoint from huggingface: https://huggingface.co/AlekseyKorshuk/vicuna-7b). The results will come out in 8 hours. **Nov/19/2023 Results Update:** We acknowledg […]

**Critique 9** — aspect `experimental_comparison`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> To what extent will the binarization scheme affect the model's performance say on the Hugging Face leaderboard [1]?

Author response — `new_experiment` (units 41–57):

> ## To Weakness 3 & Question 3: actual GPU memory saving. >  To Weakness 3: The LLM quantization scheme is motivated using an angle of GPU memory efficiency. However, the actual GPU memory usage before and after binarization/quantization is not studied in this paper. Question 3: What is the actual GPU memory saving look like for PB-LLM and all considered baselines? We acknowledge the importance of understanding the actual GPU memory usage before and after binarization/quantization. Unfortunately, our team lacks dedicated GPU implementation experts, which hindered us from providing a comprehensi […]

**Critique 10** — aspect `reproducibility`, severity `major`, polarity `neutral`, target `experiment`, actionable `True`

> - What is the actual GPU memory saving look like for PB-LLM and all considered baselines?

Author response — `new_experiment` (units 41–57):

> ## To Weakness 3 & Question 3: actual GPU memory saving. >  To Weakness 3: The LLM quantization scheme is motivated using an angle of GPU memory efficiency. However, the actual GPU memory usage before and after binarization/quantization is not studied in this paper. Question 3: What is the actual GPU memory saving look like for PB-LLM and all considered baselines? We acknowledge the importance of understanding the actual GPU memory usage before and after binarization/quantization. Unfortunately, our team lacks dedicated GPU implementation experts, which hindered us from providing a comprehensi […]

`[ignored]` [1] https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard

## Example 19 — review `BW4BpMpXgs` (ICLR 2024)

43 units, 5 critiques, 2 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The algorithm is clean and well-presented, and the idea of using Brownian motion to generate samples to learn reachability constraints is interesting. The fact that PCLaSt can be used for both deep RL and more traditional path planning (Table 1) demonstrates a good level of flexibility and suggests broad potential impact. The experiments which are presented show promising results, in particular demonstrating better conformance between the latent space representation and the

Author response: none.

**Critique 2** — aspect `experimental_comparison`, severity `major`, polarity `negative`, target `experiment`, actionable `True`

> There are a several experiments for which results are not presented which I think are necessary to clarify the benefits of this approach. In particular, the related work lists HOMER and DRIML as methods which attempt to encode reachability information in the latent space. However, these techniques are only included in the experiments on exogenous information, and not in the experiments on goal-conditioned RL. Similarly, I'd be interested in the results you can obtain using the hierarchical planner with alternative latent space learning techniques besides PCLaSt. More generally, I'm a bit confused by the relation of PCLaSt to HOMER and DRIML. The related work section argues that these two approaches are different from PCLaSt because they don't deal with exogenous noise. However, in the technical development of the paper, it seems that the denoising effects are due primarily to ACRO, whereas the contribution of PCLaSt is primarily in enforcing state-space geometry.

Author response — `disagreement` (units 1–6):

> >  “… HOMER and DRIML …” We primarily compete and build upon ACRO as it showed that it does better than HOMER and DRIML to remove exogenous noise. Note that HOMER uses a leveled structure which is unwieldy in practice (it’s a theoretical algorithm) and DRIML uses rewards so it requires a different information access structure than PCLast to apply. > “… Hierarchical Planner with other latent state spaces…” As we investigated with other latent-state representations, we found that they lead to poor clustering of states for abstraction as shown for ACRO in Fig 1 (b) and Fig 4 ( third-row); making  […]

**Critique 3** — aspect `clarity`, severity `minor`, polarity `negative`, target `section`, actionable `True`

> On a more minor notes, while the presentation is generally clear there is one omission that I found confusing at first. In Section 3.3, the process for generating samples for the contrastive loss omits a description of how $s_t$ and $s_{t+k}$ are generated based on $y$.

Author response: none.

**Critique 4** — aspect `soundness`, severity `minor`, polarity `neutral`, target `experiment`, actionable `True`

> In general, reachability is not symmetrical (for example, it will not be symmetrical in systems with momentum). However, the contrastive loss in Equation 2 minimizes the (symmetrical) distance between states when one is reachable from the other. Is there a theoretical or intuitive reason that this mismatch

Author response — `concession` (units 6–11):

> > In general, reachability is not symmetrical (for example, it will not be symmetrical in systems with momentum). However, the contrastive loss in Equation 2 minimizes the (symmetrical) distance between states when one is reachable from the other. Is there a theoretical or intuitive reason that this mismatch wouldn't hinder planning in systems with highly non-symmetrical reachability properties? This is an interesting aspect, and we can consider investigating it further in future work. One probable approach would be extend our current loss with weighted loss based on some reachability score of […]

**Critique 5** — aspect `soundness`, severity `minor`, polarity `neutral`, target `general`, actionable `True`

> wouldn't hinder planning in systems with highly non-symmetrical reachability properties? From my understanding of the paper, it seems that the noise filtering effects of PCLaSt are largely shared with ACRO. Is there some explanation of why PCLaSt

Author response — `clarification` (units 11–13):

> > “…PCLaSt seems to be so much more effective in Figure 6?” PCLast helps in learning representation which maintains metric space between states. Intuitively, this eases the inter and extrapolation between states for policy, helping with better generalization.

`[ignored]` true dynamics of the environment (Figure 4). ⏐ seems to be so much more effective in Figure 6?

## Example 20 — review `NOdpAbVWa1` (ICLR 2024)

19 units, 9 critiques, 0 ignored, 0 set aside as post-rebuttal.

**Critique 1** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The general structure is clear.

Author response: none.

**Critique 2** — aspect `soundness`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> The method is simple in general.

Author response: none.

**Critique 3** — aspect `clarity`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> It’s easy to follow.

Author response: none.

**Critique 4** — aspect `experimental_comparison`, severity `minor`, polarity `positive`, target `experiment`, actionable `False`

> The performance is good, with a large margin over other methods.

Author response: none.

**Critique 5** — aspect `novelty`, severity `minor`, polarity `positive`, target `general`, actionable `False`

> It’s also a nice try to include the predicted text into the learning process.

Author response — `clarification` (units 14–21):

> We would like to draw the reviewer’s attention that LipVoicer utilises the **unsupervised text** at **inference time**, whereas Lip2Speech uses the **ground-truth text** for **training** in the form of an additional loss term. Integrating the textual modality with the audio at inference time is not straightforward, and it considerably changes the algorithmic approach that needs to be taken. The words in the textual modality bear no information about their timing, duration and intonation. As Tables 1-4 demonstrate,  by using the classifier guidance, LipVoicer manages to deploy the text fairly b […]

**Critique 6** — aspect `clarity`, severity `major`, polarity `negative`, target `figure_table`, actionable `True`

> (1) I am a little confused with fig1.a. The output of the lipreading module is the predicted text. The output of the ASR modules is also the predicted text. There should be no connections from the output of the predicted text to the ASR module? The ASR module should take the output of MelGen as input? without the text predicted from LR module?

Author response — `clarification` (units 22–31):

> **Response:** Lipvoicer does indeed use existing algorithms as key components, but the key contribution and innovation is in the use of predicted text from lipreading in the speech generation process. We show that we can use a lip-reading network to acquire the textual modality without any additional supervision, and use the extracted text in the speech generation process in a way which significantly increases the intelligibility while maintaining speech quality. A benefit of the design of LipVoicer is that it is highly modular - every single block in the architecture, e.g. MelGen/lip-reader/A […]

**Critique 7** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> (2) Lip2speech (Kim et al.(2023)) takes the ground-truth text as input to constrain the learning process and has shown the success of the role of text modality in this task. In this paper, the work uses the predicted text instead of the ground truth as Lip2Speech. But the manner is similar to Kim et al.(2022). So, besides using the predicted text with an existing method, is there some new contributions in the view of methodology?

Author response — `clarification` (units 33–38):

> **Response:** Our main claim is that the text modality, even if it is not perfect, can be of great help to audio generation from video. Therefore we do not argue that our method will perform well with a bad lip-reader, we rather say that the existing lip-readers can greatly boost performance. This is further corroborated in the ablation study we show in Table 7. A lip-reader with WER=32.3% is already not so good, and we show that LipVoicer is adversely affected by it. The better the lip-reader gets, the better our model performs.

**Critique 8** — aspect `clarity`, severity `minor`, polarity `negative`, target `figure_table`, actionable `True`

> (1) I am a little confused about the fig.1(a) as described above.

Author response: none.

**Critique 9** — aspect `novelty`, severity `major`, polarity `negative`, target `general`, actionable `True`

> (2) The modules and manners in the framework seems to be not new in the view of methodology, with the lipreading module, MelGen, text alignment manners already proposed by other works. Could the authors give a clarification of the contributions? Maybe I miss something? (3) The performance using the predicted text is already very appealing, but the involved lip reading model are almost the best two ones at present, with WER=19% and 26%. if the lip reading performance has been a much low value, e.g. WER=50%, what would be the performance here like?

Author response: none.

