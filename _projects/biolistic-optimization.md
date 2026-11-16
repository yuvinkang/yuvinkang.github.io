---
title: "Biolistic Transformation"
year: "2025"
order: 2
role: "First author · Ng Lab, University College Dublin"
tools: ["PDS-1000/He gene gun", "Plasmid prep & particle coating", "GUS histochemistry", "Python (SciPy)"]
tags: ["Plant biotech", "Gene gun", "Statistics"]
summary: "Does target distance change how well a gene gun transforms plant cells? I ran the experiment, and the honest answer reframed the question."
scene: biolistics
layout: biolistics
paper: /assets/files/biolistics-paper.pdf
paper_title: "Optimization of Helium Pressure and Target Distance in Biolistic Transformation of Allium cepa Epidermis"
authors: "Yuvin Kang, Frances Downey, Carl Ng"
image: ""
---

I ran this study at University College Dublin with Dr. Carl Ng, from bombardment through statistics to writing. The goal was practical: biolistic transformation is the only delivery method that works across most plant species, but its results swing wildly between runs, which makes it hard to use in manufacturing.

- **Designed and ran** the comparison: two target distances at a fixed 1,100 psi, 31 samples bombarded, stained, and counted under light microscopy.
- **Chose statistics to fit the data**, not the hoped-for answer — Shapiro-Wilk showed both groups were far from normal, so I used Mann-Whitney U rather than a t-test.
- **Caught a confound in the protocol**: stacking plates more than two high during incubation produced dead plates inside the stack and over-stained ones outside. Limiting stack height fixed it.
- **Wrote the paper**, including what the result means for plant cell culture manufacturing of galantamine, an Alzheimer's drug.
