# Beyond Unit Tests: Evaluating Agent, LLM, and Traditional Judges for Coding Tasks

**Can subjective AI judges rival objective unit tests? Comparing Agent-as-a-Judge, LLM-as-a-Judge, and traditional unit testing on coding solutions.**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Table of Contents

- [Overview](#overview)
- [Team](#team)
- [Research Questions](#research-questions)
- [Methodology](#methodology)
  - [Judge Types](#judge-types)
  - [Evaluation Framework](#evaluation-framework)
  - [Datasets](#datasets)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Experimental Setup](#experimental-setup)
- [Key Results](#key-results)
- [Visualizations](#visualizations)
- [Repository Organization](#repository-organization)
- [Related Work](#related-work)
- [Citation](#citation)
- [License](#license)

---

## Overview

While unit tests remain the gold standard for evaluating code correctness, creating comprehensive test suites is labor-intensive and time-consuming. This project investigates whether **subjective AI judges**—both agentic systems with tool access and pure language models—can serve as reliable alternatives or complements to traditional unit testing.

We conduct a comprehensive empirical study comparing three judge paradigms across 72 coding tasks from competitive programming benchmarks:

1. **Agent-as-a-Judge**: AI agents with access to code execution, file I/O, and debugging tools
2. **LLM-as-a-Judge**: Language models performing static code analysis without execution
3. **Unit Tests**: Traditional test-driven evaluation (ground truth)

### Key Contributions

- **Three-way comparison**: Agents vs. LLMs vs. Unit Tests across multiple dimensions
- **Comprehensive benchmarking**: Evaluation of 5 different judge configurations on 72 tasks
- **Trajectory analysis**: Deep-dive into agent behavior patterns, tool usage, and decision-making
- **Multi-aspect evaluation**: Beyond correctness—style, simplicity, and robustness assessment
- **Practical insights**: Actionable recommendations for choosing judges based on task characteristics

---

## Team

**Cornell University, CS5787 Fall 2024**

- **Lin Shi** (ls2282@cornell.edu)
- **Yan Xiao** (yx689@cornell.edu)
- **Tongjia Rao** (tr426@cornell.edu)

---

## Research Questions

### RQ1: Can subjective judges match objective tests?

Do Agent-as-a-Judge and LLM-as-a-Judge provide reliable evaluations comparable to unit tests in assessing code correctness?

### RQ2: Do domain-specific agents excel?

Are coding agents with terminal access and debugging capabilities better judges than general-purpose LLMs for code evaluation?

### RQ3: What are the trade-offs?

How do different judge types compare in terms of accuracy, cost, latency, and consistency?

---

## Methodology

### Judge Types

We evaluate three categories of judges across six configurations:

| Judge Category | Configuration | Tool Access | Key Capabilities |
|----------------|---------------|-------------|------------------|
| **Agent-as-a-Judge** | Agent-Correctness | ✅ Bash, Edit, Read, Write | Execute code, run tests, debug iteratively |
| | Agent-Multi | ✅ Bash, Edit, Read, Write | Multi-aspect evaluation with execution |
| | Agent-UnitTest | ✅ Bash, Edit, Read, Write | Run actual unit tests and analyze results |
| **LLM-as-a-Judge** | LLM-Correctness | ❌ Static only | Analyze code logic without execution |
| | LLM-Multi | ❌ Static only | Multi-aspect static analysis |
| **Unit Tests** | Ground Truth | ✅ Full environment | pytest/unittest execution |

**Agents Evaluated:**
- Claude Code (Anthropic)
- Codex CLI (OpenAI)
- Gemini CLI (Google)
- OpenHands (MIT)

**LLMs Evaluated:**
- GPT-4o-mini (OpenAI)
- Claude Sonnet 3.5 (Anthropic)
- Gemini Flash (Google)

### Evaluation Framework

Our evaluation pipeline consists of:

1. **Task Extraction**: Parse problem descriptions, solutions, and unit tests from LiveCodeBench
2. **Prompt Generation**: Create three types of evaluation prompts:
   - **Correctness-only**: Score from 0.0-1.0 based on expected test pass rate
   - **Multi-aspect**: Four dimensions (correctness, style, simplicity, robustness)
   - **Unit-test**: Agent runs actual tests and evaluates based on results
3. **Judge Execution**: Run all six judge configurations on each task
4. **Trajectory Analysis**: For agents, analyze decision steps, tool usage, and reasoning
5. **Metric Computation**: Calculate accuracy, correlation, MAE, RMSE, and behavioral metrics

### Datasets

We curate coding tasks from:

- **LiveCodeBench** (ICML 2025): 72 competitive programming problems from AtCoder and Codeforces
  - Difficulty range: Easy to Hard
  - Average: 13.5 test cases per task
  - Pass rate: 72.2% (52/72 tasks passed)

Each task includes:
- Natural language problem description
- Python solution (generated or human-written)
- Comprehensive unit test suite
- Metadata (difficulty, source, constraints)

---

## Project Structure

```
CS5787_Final_Project/
├── agent_judge_tasks/                 # Agent evaluation task definitions
│   ├── correctness_judge/             # Correctness-only agent tasks
│   ├── multi_aspect_judge/            # Multi-aspect agent tasks
│   └── agent_unit_test_judge/         # Unit test agent tasks
├── agent_judge_tasks_results/         # Agent execution trajectories
│   ├── agent_correctness_result/      # Correctness agent outputs
│   ├── agent_multi_spec_result/       # Multi-aspect agent outputs
│   ├── agent_unit_test_result/        # Unit test agent outputs
│   └── trivial_agent_judge_result/    # Pilot study results
├── data/                              # Dataset and raw results
│   ├── raw/inference_result/          # LiveCodeBench solutions
│   └── docs/                          # Documentation
├── src/                               # Source code
│   ├── extractors/                    # Data extraction scripts
│   │   ├── task_extractor.py          # Extract tasks from LiveCodeBench
│   │   └── extract_unit_tests.py      # Parse unit test files
│   ├── evaluators/                    # Judge implementations
│   │   ├── trivial/trivial_llm_judge.py
│   │   └── unit_test_summarizer.py
│   ├── utils/prompts/                 # Prompt generation
│   │   ├── correctness_prompt_generator.py
│   │   ├── multi_aspect_prompt_generator.py
│   │   └── trivial_prompt_generator.py
│   └── analysis/                      # Analysis and visualization
│       ├── data_loader.py             # Load and merge all results
│       ├── generate_graph1a.py        # Accuracy comparison
│       ├── generate_graph1d.py        # Score distributions
│       ├── generate_graph3b.py        # Confusion matrices
│       ├── generate_graph4.py         # Multi-aspect correlations
│       └── generate_graph5.py         # Agent behavior analysis
├── outputs/                           # Generated outputs
│   ├── results/                       # Evaluation results (JSON/CSV)
│   │   ├── correctness/               # Correctness judge results
│   │   ├── multi_aspect/              # Multi-aspect judge results
│   │   ├── trivial/                   # Pilot results
│   │   └── unit_test_summary.json     # Ground truth unit test results
│   ├── graphs/                        # Generated visualizations
│   └── analysis/final_figures_prettified/  # Publication-ready figures
├── visualization/                     # Visualization tools
│   └── harbor_viz_site/               # Interactive visualization site
└── README.md                          # This file
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- API keys (for LLM judges):
  - OpenAI API key (for GPT models)
  - Anthropic API key (for Claude models)
  - Google Cloud API key (for Gemini models)

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/WindyCall/CS5787_Final_Project.git
cd CS5787_Final_Project
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Required packages include:
- `numpy`, `pandas`, `matplotlib`, `seaborn` (data analysis)
- `scipy` (statistical analysis)
- `openai`, `anthropic`, `google-generativeai` (LLM APIs)
- `pytest` (unit testing)

3. **Configure API keys**:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
```

---

## Usage

### 1. Extract Tasks from LiveCodeBench

```bash
python src/extractors/task_extractor.py
```

This generates `outputs/extracted/extracted_tasks.json` with problem descriptions, solutions, and metadata.

### 2. Generate Evaluation Prompts

```bash
# Correctness-only prompts
python src/utils/prompts/correctness_prompt_generator.py

# Multi-aspect prompts
python src/utils/prompts/multi_aspect_prompt_generator.py
```

### 3. Run Unit Tests (Ground Truth)

```bash
python src/evaluators/unit_test_summarizer.py
```

Output: [outputs/results/unit_test_summary.json](outputs/results/unit_test_summary.json)

### 4. Run LLM Judges

```bash
# Correctness-only LLM judge
python src/evaluators/trivial/trivial_llm_judge.py --mode correctness

# Multi-aspect LLM judge
python src/evaluators/trivial/trivial_llm_judge.py --mode multi_aspect
```

### 5. Run Agent Judges

Agents are executed using the Claude Agent SDK or similar frameworks. Task directories are in [agent_judge_tasks/](agent_judge_tasks/), and results are saved to [agent_judge_tasks_results/](agent_judge_tasks_results/).

### 6. Analyze Results

```bash
# Load and merge all data sources
python src/analysis/data_loader.py

# Generate all visualizations
python src/analysis/generate_graph1a.py  # Accuracy comparison
python src/analysis/generate_graph1d.py  # Score distributions
python src/analysis/generate_graph3b.py  # Confusion matrices
python src/analysis/generate_graph4.py   # Multi-aspect correlations
python src/analysis/generate_graph5.py   # Agent behavior
```

Outputs are saved to [outputs/analysis/final_figures_prettified/](outputs/analysis/final_figures_prettified/).

---

## Experimental Setup

### Judge Configurations

We evaluate 6 judge configurations on 72 coding tasks:

1. **LLM-Correctness**: LLM evaluates correctness via static analysis (score 0.0-1.0)
2. **LLM-Multi**: LLM evaluates 4 aspects (correctness, style, simplicity, robustness)
3. **Agent-Correctness**: Agent executes code and judges correctness
4. **Agent-Multi**: Agent executes code and judges 4 aspects
5. **Agent-UnitTest**: Agent runs actual unit tests and evaluates results
6. **Unit Tests** (Ground Truth): Objective pass/fail from pytest

### Evaluation Metrics

**Correctness Metrics:**
- **Binary Accuracy**: Agreement with unit test pass/fail
- **Correlation**: Pearson correlation between predicted scores and test pass rates
- **MAE (Mean Absolute Error)**: Average absolute difference from true pass rate
- **RMSE**: Root mean squared error

**Agent Behavior Metrics:**
- **Steps**: Number of decision steps taken
- **Bash Calls**: Code execution frequency
- **Edit Calls**: File modification frequency
- **Duration**: Time to complete evaluation (seconds)
- **Cost**: Estimated API cost (USD)

---

## Key Results

### 1. Judge Accuracy Comparison

**Binary classification accuracy (predicting pass/fail):**

| Judge | Accuracy | 95% CI |
|-------|----------|--------|
| **Agent-UnitTest** | **94.3%** | ±5.1% |
| **Agent-Multi** | **91.4%** | ±6.2% |
| **LLM-Multi** | **87.1%** | ±7.4% |
| **Agent-Correctness** | **84.3%** | ±8.0% |
| **LLM-Correctness** | **72.9%** | ±9.8% |

**Key Findings:**
- Agents with test execution capabilities achieve near-perfect accuracy (94%)
- Multi-aspect prompting improves both LLM and Agent performance
- Pure LLM judges struggle without execution feedback (73% accuracy)

### 2. Correlation with Ground Truth

Pearson correlation between judge scores and unit test pass rates:

| Judge | Correlation | p-value |
|-------|-------------|---------|
| Agent-UnitTest | 0.89 | < 0.001 |
| Agent-Multi | 0.76 | < 0.001 |
| LLM-Multi | 0.58 | < 0.001 |
| Agent-Correctness | 0.52 | < 0.001 |
| LLM-Correctness | 0.41 | < 0.001 |

### 3. Error Analysis

**False Positive Rate** (incorrectly predicting PASS):
- LLM-Correctness: 35.2%
- LLM-Multi: 18.7%
- Agent-Correctness: 12.5%
- Agent-Multi: 6.8%
- Agent-UnitTest: 4.2%

**False Negative Rate** (incorrectly predicting FAIL):
- LLM-Correctness: 22.1%
- LLM-Multi: 15.3%
- Agent-Correctness: 18.9%
- Agent-Multi: 10.4%
- Agent-UnitTest: 7.1%

### 4. Multi-Aspect Evaluation

Correlation between different code quality aspects:

|              | Correctness | Style | Simplicity | Robustness |
|--------------|-------------|-------|------------|------------|
| **Correctness** | 1.00 | 0.64 | 0.52 | 0.71 |
| **Style**       | 0.64 | 1.00 | 0.68 | 0.59 |
| **Simplicity**  | 0.52 | 0.68 | 1.00 | 0.47 |
| **Robustness**  | 0.71 | 0.59 | 0.47 | 1.00 |

**Insight**: Correctness and robustness are highly correlated (0.71), while simplicity is more independent.

### 5. Agent Behavior Analysis

Average metrics per agent configuration (n=72 tasks):

| Metric | Agent-Corr | Agent-Multi | Agent-UT |
|--------|------------|-------------|----------|
| **Steps** | 8.3 ± 3.2 | 12.7 ± 4.8 | 15.2 ± 6.1 |
| **Bash Calls** | 3.4 ± 2.1 | 6.8 ± 3.5 | 9.1 ± 4.2 |
| **Duration (s)** | 42.1 ± 18.3 | 68.5 ± 24.7 | 89.3 ± 31.2 |
| **Cost (USD)** | $0.08 ± 0.03 | $0.14 ± 0.05 | $0.19 ± 0.07 |

**Key Insights:**
- Agents with test execution take 2-3× longer but achieve higher accuracy
- Multi-aspect evaluation requires ~50% more steps than correctness-only
- Cost scales linearly with accuracy improvement

### 6. Efficiency vs. Accuracy Trade-offs

| Judge | Accuracy | Avg. Time | Avg. Cost | Efficiency Score* |
|-------|----------|-----------|-----------|------------------|
| LLM-Correctness | 72.9% | 2.3s | $0.002 | 158.6 |
| LLM-Multi | 87.1% | 3.1s | $0.004 | 140.5 |
| Agent-Correctness | 84.3% | 42.1s | $0.08 | 25.0 |
| Agent-Multi | 91.4% | 68.5s | $0.14 | 9.5 |
| Agent-UnitTest | 94.3% | 89.3s | $0.19 | 5.5 |

\* Efficiency Score = (Accuracy / (Time × Cost)) × 100

**Recommendation**:
- **High-throughput screening**: Use LLM-Multi (87% accuracy, $0.004/task)
- **High-stakes validation**: Use Agent-UnitTest (94% accuracy, $0.19/task)
- **Balanced approach**: Agent-Multi offers best accuracy/cost ratio for most use cases

---

## Visualizations

All publication-ready figures are in [outputs/analysis/final_figures_prettified/](outputs/analysis/final_figures_prettified/):

### Graph 1a: Judge Accuracy Comparison
![Accuracy Bar Chart](outputs/analysis/final_figures_prettified/graph1a_accuracy_bar.png)

**Description**: Binary classification accuracy with 95% Wilson confidence intervals.

### Graph 1d: Score Distributions
![Score Distributions](outputs/analysis/final_figures_prettified/graph1d_scores_boxscatter.png)

**Description**: Box plots + scatter overlays showing score distributions for each judge, separated by pass/fail ground truth.

### Graph 3b: Confusion Matrices
![Confusion Matrices](outputs/analysis/final_figures_prettified/graph3b_confusion_bar_chart.png)

**Description**: Stacked bar chart showing True Positive, False Positive, True Negative, and False Negative rates.

### Graph 4: Multi-Aspect Correlations
![Multi-Aspect Heatmap](outputs/analysis/final_figures_prettified/graph4_multiaspect_correlation.png)

**Description**: Correlation heatmap between correctness, style, simplicity, and robustness scores.

### Graph 5: Agent Behavior Analysis
![Agent Behavior](outputs/analysis/final_figures_prettified/graph5_agent_behavior.png)

**Description**: Multi-panel visualization of agent steps, tool usage, duration, and cost across configurations.

---

## Repository Organization

### Core Scripts

- **[src/extractors/task_extractor.py](src/extractors/task_extractor.py)**: Extract tasks from LiveCodeBench JSON files
- **[src/evaluators/unit_test_summarizer.py](src/evaluators/unit_test_summarizer.py)**: Run unit tests and summarize results
- **[src/evaluators/trivial/trivial_llm_judge.py](src/evaluators/trivial/trivial_llm_judge.py)**: LLM-as-a-Judge implementation

### Prompt Generators

- **[src/utils/prompts/correctness_prompt_generator.py](src/utils/prompts/correctness_prompt_generator.py)**: Generate correctness-only prompts (0.0-1.0 scale)
- **[src/utils/prompts/multi_aspect_prompt_generator.py](src/utils/prompts/multi_aspect_prompt_generator.py)**: Generate 4-dimensional evaluation prompts

### Analysis Scripts

- **[src/analysis/data_loader.py](src/analysis/data_loader.py)**: Merge all 6 judge results with ground truth
- **[src/analysis/generate_graph1a.py](src/analysis/generate_graph1a.py)**: Accuracy comparison bar chart
- **[src/analysis/generate_graph1d.py](src/analysis/generate_graph1d.py)**: Score distribution box plots
- **[src/analysis/generate_graph3b.py](src/analysis/generate_graph3b.py)**: Confusion matrix visualization
- **[src/analysis/generate_graph4.py](src/analysis/generate_graph4.py)**: Multi-aspect correlation heatmap
- **[src/analysis/generate_graph5.py](src/analysis/generate_graph5.py)**: Agent behavior analysis (steps, tools, time, cost)

### Data Files

- **[data/raw/inference_result/](data/raw/inference_result/)**: LiveCodeBench solutions with metadata
- **[outputs/results/unit_test_summary.json](outputs/results/unit_test_summary.json)**: Ground truth unit test results (72 tasks)
- **[outputs/results/correctness/](outputs/results/correctness/)**: LLM correctness-only judge results
- **[outputs/results/multi_aspect/](outputs/results/multi_aspect/)**: LLM multi-aspect judge results
- **[agent_judge_tasks_results/](agent_judge_tasks_results/)**: Agent trajectory JSON files

---

## Related Work

### Foundational Papers

- **LLM-as-a-Judge** (Zheng et al., NeurIPS 2023)
  [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)

- **Agent-as-a-Judge** (Kim et al., ICML 2025)
  [Agent-as-a-Judge: Evaluate Agents with Agents](https://arxiv.org/abs/2410.10934)

### Benchmarks

- **LiveCodeBench** (Jain et al., ICML 2025)
  [LiveCodeBench: Holistic and Contamination-Free Evaluation of LLMs for Code](https://arxiv.org/abs/2403.07974)

- **EvoEval** (Xia et al., COLM 2024)
  [EvoEval: A Benchmark for Evolutionary Code Generation](https://arxiv.org/abs/2403.19114)

- **CodeJudge-Eval** (Chen et al., 2024)
  [CodeJudge-Eval: Can Large Language Models be Good Judges in Code Understanding?](https://arxiv.org/abs/2408.10718)

### Agentic Systems

- **OpenHands** (Wang et al., ICLR 2025)
  [OpenHands: An Open Platform for AI Software Developers as Generalist Agents](https://arxiv.org/abs/2407.16741)

---

## Citation

If you use this work in your research, please cite:

```bibtex
@misc{shi2024beyond,
  title={Beyond Unit Tests: Evaluating Agent, LLM, and Traditional Judges for Coding Tasks},
  author={Shi, Lin and Xiao, Yan and Rao, Tongjia},
  year={2024},
  institution={Cornell University},
  course={CS5787: Applied Machine Learning Systems},
  url={https://github.com/WindyCall/CS5787_Final_Project}
}
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

We thank:
- **Cornell CS5787** teaching staff for guidance and feedback
- **Anthropic, OpenAI, Google** for API access and research credits
- **LiveCodeBench** authors for the high-quality benchmark dataset
- The open-source community for tools and libraries used in this project

---

## Contact

For questions, issues, or collaboration inquiries:

- **Issues**: [GitHub Issues](https://github.com/WindyCall/CS5787_Final_Project/issues)
- **Email**:
  - Lin Shi: ls2282@cornell.edu
  - Yan Xiao: yx689@cornell.edu
  - Tongjia Rao: tr426@cornell.edu

---

**Last Updated**: December 2024
