# MOFSynth 3.0

<h1 align="center">
<!--   <img alt="Logo" src="https://raw.githubusercontent.com/livaschar/mofsynth/main/docs/source/images/final_grey-removebg-preview.png" style="width: 500px;"/> -->
<!--   <img alt="Logo" src="https://github.com/livaschar/mofsynth/blob/main/docs/source/images/final_grey-removebg-preview.png" style="width: 500px;"/> -->
  <img alt="Logo" src="https://github.com/livaschar/mofsynth/blob/main/docs/source/images/mofsynth_logo.svg" style="width: 500px;"/>
</h1>

<h4 align="center">

[![Requires Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-g?logo=python&logoColor=blue&label=Python&labelColor=black)](https://www.python.org/downloads/)
[![Read the Docs](https://img.shields.io/badge/latest-b?logo=readthedocs&logoColor=blue&label=Read%20the%20Docs&labelColor=black)](https://mofsynth.readthedocs.io)
[![PyPI](https://img.shields.io/badge/PyPI%20-%20v%202.0.0%20-b?style=flat&logo=pypi&logoColor=blue&logoSize=auto&label=PyPI&labelColor=black)](https://pypi.org/project/mofsynth/)
[![Licensed under GPL-3.0-only](https://img.shields.io/badge/GPL--3.0--only-gold?label=License&labelColor=black)](https://spdx.org/licenses/GPL-3.0-only.html)  

[![Online App](https://img.shields.io/badge/🔥%20MOFSYNTH%20Online-Try%20Now!-red?style=for-the-badge&labelColor=black)](https://mofsynth.website)  

</h4>

## 🔔 Release Note
**From Classical to Quantum calculations!**

We are excited to announce the release of MOFSynth 3.0, a significant leap forward in our commitment to speed, accessibility, and scientific reproducibility.

This new version is fully powered by open-source software, eliminating dependencies on proprietary packages and streamlining deployment across systems.

🚀 What’s New in 3.0:

- **XTB**: Seamlessly switch to XTB for rapid and efficient energy calculations and geometry optimizations.

- **Enhanced Performance**: Enjoy faster execution times and improved scalability.

- **Open Science Ready**: All dependencies are now open source, making MOFSynth fully transparent and reproducible.

✅ Why Upgrade?
Whether you're screening thousands of MOFs or performing high-throughput synth-likelihood predictions, MOFSynth 3.0 delivers the performance and flexibility modern computational chemists demand.

Try it today — open source, faster, and ready for your next breakthrough.

## What is MOFSynth?
MOFSynth is a Python package for **MOF synthesizability evaluation**, with
emphasis on reticular chemistry.

In materials science, especially in the synthesis of metal-organic frameworks (MOFs),
a significant portion of time and effort is spent on the experimental process of synthesizing
and evaluating the viability of MOFs.

MOFSynth aims to provide a simple and efficient interface for evaluating
the synthesizability of metal-organic frameworks (MOFs) in an experiment-ready format,
minimizing the time and labor traditionally required for these experimental preprocessing steps.
This allows researchers to focus more on innovative synthesis and experimental validation
rather than on preparatory tasks.

## ⚙️  Installation

It is strongly recommended to **perform the installation inside a virtual environment**.

```sh
python -m venv <venvir_name>
source <venvir_name>/bin/activate
```

```sh
pip install mofsynth
```

### Requires

To run MOFSynth, the following modules and tools must be present in your system:

1. [**mofid v1.1.0**](https://github.com/snurr-group/mofid): A Python library for MOF identification and characterization.
2. [**XTB v6.0.0**](https://github.com/grimme-lab/xtb): A computational chemistry program package.

## 💻 Browser-Based MOFSynth

Easy to use [Web version](https://mofsynth.website) of the tool.

## 📖 Usage example

Check the [tutorial](https://mofsynth.readthedocs.io/en/latest/tutorial.html).

## :warning: Problems?

You can start by [opening an issue](https://github.com/livaschar/mofsynth/issues) or communicate via [email](mailto:chemp1167@edu.chemistry.uoc.gr).

## 📰 Citing MOFSynth

Please consider citing [this publication](https://pubs.acs.org/doi/full/10.1021/acs.jcim.4c01298) or use the following BibTex.

<details>
<summary>Show BibTex entry</summary>

```bibtex
@article{doi:10.1021/acs.jcim.4c01298,
  author = {Livas, Charalampos G. and Trikalitis, Pantelis N. and Froudakis, George E.},
  title = {MOFSynth: A Computational Tool toward Synthetic Likelihood Predictions of MOFs},
  journal = {Journal of Chemical Information and Modeling},
  volume = {64},
  number = {21},
  pages = {8193-8200},
  year = {2024},
  doi = {10.1021/acs.jcim.4c01298},
  note ={PMID: 39481084},
  URL = {https://doi.org/10.1021/acs.jcim.4c01298},
  eprint = {https://doi.org/10.1021/acs.jcim.4c01298}
  }
```

</details>

## 📑 License

MOFSynth is released under the [GNU General Public License v3.0 only](https://spdx.org/licenses/GPL-3.0-only.html).
