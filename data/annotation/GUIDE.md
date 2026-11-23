# Annotation guide: labels of review critiques

Version 1 (draft to be reviewed by the annotators before they start).

## 1. Purpose

A language model cut ICLR reviews into *critiques* (one independent point each) and gave
five labels to every critique. You label a sample of 500 critiques by hand. Your labels
are the reference against which the labels of the model are scored; the model's labels
are not shown to you, on purpose.

## 2. Rules of the exercise

- Work **alone**. Do not discuss an item with the other annotator before both files are
  complete. Disagreements are settled together afterwards, in a separate file.
- Do **not** open `sample_key.parquet` (it holds the labels of the model) and do not
  ask a language model to label for you.
- Label what the **reviewer wrote**, not whether the reviewer is right, and not what
  you think of the paper.
- Use only this guide. If a case is not covered, choose the closest value and explain
  in the `comment` column.

## 3. The file

`to_annotate_<your letter>.csv`, one row per critique. Open it with a spreadsheet
(LibreOffice: character set UTF-8, separator comma) and save it in the same CSV format.

| Column | Content |
|---|---|
| `item_id` | identifier of the item; do not change it |
| `critique` | the text to label |
| `context` | the review around the critique; the critique is between `>>>` and `<<<`; `[...]` means that the rest of the review is not shown; `[strengths]`, `[weaknesses]`, `[questions]` are the fields of the review form |
| `aspect`, `severity`, `polarity`, `target`, `actionable` | **to fill**, with exactly one of the values listed below, in lower case |
| `comment` | optional: doubts, several points in one critique, text that is not a critique |

Every label cell must be filled for every row.

## 4. General principles

1. **Label the critique, read the context.** The context helps to understand the
   critique (what "this" refers to, which section of the form it comes from). The
   labels describe the marked text only.
2. **One value per label.** If the critique mixes several points, label the main one
   (the one the reviewer develops most; the first one if they are equal) and write
   `several points` in `comment`.
3. **Text that is not a critique** (a heading, a pointer such as "see above", a
   summary of the paper). Label it as well as you can and write `not a critique` in
   `comment`. These rows tell us how often the cutting step went wrong.
4. **No outside knowledge.** You do not see the paper, its scores or its decision, and
   you should not look for them.

## 5. The labels

### 5.1 `aspect`: what the critique is about

| Value | Definition |
|---|---|
| `novelty` | originality of the idea or contribution with respect to prior work |
| `soundness` | technical correctness, validity of the method, the theory, the assumptions or the claims |
| `experimental_comparison` | experiments, baselines, datasets, ablations, evaluation protocol, empirical results |
| `clarity` | writing, organisation, presentation, notation, readability of figures |
| `reproducibility` | code, data, hyper-parameters or details needed to reproduce the work |
| `significance` | importance, motivation, usefulness or impact of the problem or of the results |
| `related_work` | missing or wrong citations, positioning with respect to the literature |
| `other` | none of the above |

Examples:

- `novelty`: "The proposed loss is a minor variation of the one in [X]; the contribution is incremental." (constructed)
- `soundness`: "The proof of Theorem 2 assumes that the gradients are bounded, which does not hold for the model used." (constructed)
- `experimental_comparison`: "There is no comparison with existing methods, so it is hard to assess how the proposed approach comparing with SOTA."
- `clarity`: "The paper is well-organized and clearly written."
- `reproducibility`: "The learning rate, batch size and number of seeds are not reported, and no code is provided." (constructed)
- `significance`: "This paper targets at an interesting and valuable question."
- `related_work`: "Recent work on retrieval-augmented training is not cited or discussed." (constructed)
- `other`: "The paper exceeds the page limit." (constructed)

Borderline cases:

- **`soundness` or `experimental_comparison`?** A missing or insufficient experiment,
  baseline, dataset or ablation is `experimental_comparison`, even when the reviewer
  says that a claim is therefore not supported. A flaw in the reasoning, the method,
  the theory or an assumption is `soundness`.
- **`novelty` or `related_work`?** "This was already done in X" or "the idea is
  incremental" is `novelty`. "X is not cited or discussed" is `related_work`.
- **`related_work` or `experimental_comparison`?** "Compare experimentally with X" is
  `experimental_comparison`. "Discuss how the work differs from X" is `related_work`.
- **`clarity` or `reproducibility`?** A detail needed to *understand* the paper is
  `clarity`. A detail needed to *run it again* (hyper-parameters, code, data, seeds)
  is `reproducibility`.
- **`significance`**: motivation, practical use, impact. "The improvement is small"
  is `significance` when the reviewer doubts that the result matters, and
  `experimental_comparison` when the reviewer doubts the measurement itself.
- Use `other` only when no aspect fits (ethics, formatting rules, the reviewing
  process). It should be rare.

### 5.2 `severity`: weight of the point in the reviewer's assessment

| Value | Definition |
|---|---|
| `blocking` | a negative point that, if not resolved, makes the paper unacceptable according to the reviewer |
| `major` | an important point (serious weakness, or a central strength) |
| `minor` | a secondary point, a suggestion, a detail, a generic remark |

- `blocking` needs a **signal from the reviewer** that the point decides the outcome:
  "fatal flaw", "cannot be accepted unless", "this is the main reason for my
  recommendation", "the central claim is wrong". A serious weakness without such a
  signal is `major`. `blocking` is never used for a strength.
- `major`: the reviewer presents the point as important, develops it, or it concerns
  the core of the paper (the main claim, the main experiment, the main idea).
- `minor`: typos, presentation details, optional suggestions, curiosity questions, and
  brief generic praise ("the paper is well written").
- Judge from the text and its context, not from where the critique sits in the form:
  a point listed under "weaknesses" can be `minor`.

Examples:

- `blocking`: "Without a comparison on a standard benchmark I cannot recommend acceptance." (constructed)
- `major`: "There is no comparison with existing methods, so it is hard to assess how the proposed approach comparing with SOTA."
- `major` (strength): "The experimental evaluation and discussion are adequate, and the results convincingly support the main claims."
- `minor`: "Experiments results are impressive with high precision." (brief generic praise)
- `minor`: "Another question would be the paper discussed both DB-based and subTB based objectives. What about other objectives?"

### 5.3 `polarity`

| Value | Definition |
|---|---|
| `negative` | a weakness, a criticism, or a request that points to a shortcoming |
| `positive` | a strength or a praise |
| `neutral` | a clarification question or a remark without judgment |

- A question is `neutral` when it only asks for information ("What about other
  objectives?"). It is `negative` when it implies that something is missing or wrong
  ("Why not test other baselines? It seems like a small comparison").
- A suggestion that points to a shortcoming ("the authors should add an ablation") is
  `negative`.
- A critique that praises and criticises: label the main point (principle 2).

### 5.4 `target`: what the critique points at

| Value | Definition |
|---|---|
| `section` | a specific section, paragraph, equation, definition or part of the text |
| `figure_table` | a figure or a table |
| `experiment` | an experiment, a result, a baseline, a dataset, an ablation |
| `reference` | a citation or a related paper |
| `general` | the paper, the method or the idea as a whole |

- Choose the **most specific** thing the critique names. "Figure 3 is unreadable" is
  `figure_table`; "Section 4.2 does not define I_cs" is `section`; "the results on
  ImageNet are weak" is `experiment`; "the paper does not cite X" is `reference`.
- A request to add a figure or a table ("visual examples of the feature maps would
  help") is `figure_table`.
- A result discussed through a table ("in Table 2 the gain is within the noise"): the
  point is about the result, so `experiment`; use `figure_table` when the point is
  about the table or figure itself (readability, missing caption, missing figure).
- `general` when nothing specific is named: the method, the idea, the writing as a
  whole.

### 5.5 `actionable`

| Value | Definition |
|---|---|
| `true` | the authors can act on the critique with a concrete change or answer: add an experiment, fix a claim, clarify a passage, answer a question |
| `false` | praise, and remarks that call for no action |

- Any question that the authors can answer is `true`.
- A criticism with nothing concrete to do or answer ("I do not find the topic
  interesting") is `false`.

## 6. Worked examples

Critiques of three ICLR 2024 reviews that are not in the sample (they are the examples
given to the model, written by hand).

| Critique | aspect | severity | polarity | target | actionable |
|---|---|---|---|---|---|
| "A multi-modal approach using transformer architecture is technically sound, and the novelty and technical contribution is reasonable." | soundness | minor | positive | general | false |
| "The paper claims that high performance partially comes from multimodal learning, an ablation study will be interesting to verify this claim." | experimental_comparison | minor | negative | experiment | true |
| "How to determine whether high-quality region masks can be generated? If some visual examples of intermediate feature maps that illustrate this property are added, the proposed method can become compelling." | soundness | minor | negative | figure_table | true |
| "The author(s) use two energy-based decomposition schemes as a base-line [...]. Why not test other base-lines? It seems like a small comparison [...]" | experimental_comparison | major | negative | experiment | true |
| "Another question would be the paper discussed both DB-based and subTB based objectives. What about other objectives?" | experimental_comparison | minor | neutral | experiment | true |

## 7. When you are done

Check that no label cell is empty, save the file as CSV under the same name, and say
so. The agreement between the two annotators is computed first; the items on which you
differ are then listed in `disagreements.csv`, where you write the label you agree on
together in the `consensus` column.
