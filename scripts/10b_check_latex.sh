#!/usr/bin/env bash
# Phase 10: compiles every LaTeX table and every PDF figure of results/ in a two-column
# test document, to check that they compile and fit the page of a paper.
#
#   scripts/10b_check_latex.sh          # writes build/preview/preview.pdf, prints errors and overfull boxes
#
# Needs pdflatex. Nothing in results/ is modified. The page is A4 with margins of 2 cm,
# in two columns. A figure is placed at its own size: in one column if it fits, over the
# two columns otherwise, scaled down if it is wider than the text.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=build/preview
mkdir -p "$OUT"
{
    cat <<'TEX'
\documentclass[10pt,twocolumn]{article}
\usepackage[a4paper,margin=2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{booktabs,graphicx,amsmath,amssymb}
\newsavebox\figurebox
\newcommand\showfigure[2]{%
  \sbox\figurebox{\includegraphics{#1}}%
  \ifdim\wd\figurebox>\columnwidth
    \begin{figure*}[t]\centering
    \ifdim\wd\figurebox>\textwidth \typeout{FIGURE SCALED DOWN: #2, \the\wd\figurebox\space to \the\textwidth}\resizebox{\textwidth}{!}{\usebox\figurebox}\else\usebox\figurebox\fi
    \caption{\texttt{#2}}\end{figure*}%
  \else
    \begin{figure}[t]\centering\usebox\figurebox\caption{\texttt{#2}}\end{figure}%
  \fi\clearpage}
\begin{document}
\title{Tables and figures of the results (check of their layout)}\date{}\maketitle
\typeout{TEXT WIDTH: \the\textwidth}\typeout{COLUMN WIDTH: \the\columnwidth}
TEX
    for table in results/tables/paper/*.tex; do
        echo "\\input{../../$table}\\clearpage"
    done
    for figure in results/figures/*.pdf; do
        echo "\\showfigure{../../$figure}{$(basename "$figure" .pdf | sed 's/_/\\_/g')}"
    done
    echo '\end{document}'
} > "$OUT/preview.tex"
( cd "$OUT" && pdflatex -interaction=nonstopmode -halt-on-error preview.tex > preview.out 2>&1 ) || {
    echo "pdflatex failed:"; grep -n -A 3 '^!' "$OUT/preview.log" | head -n 40; exit 1; }
echo "compiled: $OUT/preview.pdf: $(grep -c '\\input{' "$OUT/preview.tex") tables, $(grep -c '\\showfigure{\.' "$OUT/preview.tex") figures, $(grep -o 'Output written on preview.pdf ([0-9]* pages' "$OUT/preview.log" | grep -o '[0-9]* pages')"
echo "text width $(grep -o 'TEXT WIDTH: [0-9.]*pt' "$OUT/preview.log"), column width $(grep -o 'COLUMN WIDTH: [0-9.]*pt' "$OUT/preview.log")"
echo "figures wider than the text, scaled down: $(grep -c '^FIGURE SCALED DOWN' "$OUT/preview.log" || true)"
grep '^FIGURE SCALED DOWN' "$OUT/preview.log" || true
echo "overfull boxes: $(grep -c '^Overfull' "$OUT/preview.log" || true)"
grep -n 'results/tables\|^Overfull' "$OUT/preview.log" | grep -B 1 '^[0-9]*:Overfull' | cut -c1-120 || true
