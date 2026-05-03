# Marimo

**A reactive Python notebook where cells re-execute automatically when their dependencies change — and the whole notebook is a valid Python file.**

Unlike Jupyter, Marimo notebooks have no hidden state: execution order is determined by data dependencies, not cell position. This makes them reproducible and diffable. Notebooks export cleanly as scripts or standalone web apps, which is why it was chosen over Streamlit for Hermes — the output is a printable monthly cost report, not a live dashboard, and reproducibility matters more than interactivity. First used in the Hermes arc42 ADR (2026-05-03).

*First encountered: 2026-05-03*
