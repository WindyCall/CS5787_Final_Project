#!/usr/bin/env python3
"""
Add LLM judge prompts to extracted_tasks.json

This script takes the extracted_tasks.json file and adds a 'judge_prompt' field
to each task containing the exact prompt that would be sent to the LLM judge.
"""

import json
from pathlib import Path


def create_judge_prompt(problem: str, solution: str) -> str:
    """
    Create prompt asking for 0-1 score with file output.
    
    Score interpretation:
    - 1.0: Perfect solution, handles all cases
    - 0.8-0.9: Very good, minor potential issues
    - 0.6-0.7: Good, but has some issues
    - 0.4-0.5: Partial solution, significant issues
    - 0.2-0.3: Poor solution, major flaws
    - 0.0-0.1: Completely wrong or doesn't address problem
    """
    # Truncate very long problem descriptions
    if len(problem) > 2000:
        problem = problem[:2000] + "\n... (truncated for brevity)"
    
    # Truncate very long solutions
    if len(solution) > 3000:
        solution = solution[:3000] + "\n... (truncated)"
    
    prompt = f"""You are an expert code reviewer. Evaluate the correctness and quality of the following code solution.

**Problem:**
{problem}

**Code Solution:**
```python
{solution}
```

**Your Task:**
Evaluate this solution and provide a confidence score from 0.0 to 1.0 indicating how likely it is to correctly solve the problem.

**Scoring Guidelines:**
- 1.0: Perfect solution, correctly handles all cases including edge cases
- 0.8-0.9: Very strong solution, likely correct with minor potential concerns
- 0.6-0.7: Good solution, but has some notable issues or missing edge cases
- 0.4-0.5: Partial solution with significant correctness concerns
- 0.2-0.3: Poor solution with major logical flaws
- 0.0-0.1: Completely incorrect or doesn't address the problem

**Analysis Criteria:**
1. Does the algorithm logic correctly solve the problem?
2. Are edge cases handled (empty inputs, boundaries, special values)?
3. Is the time/space complexity acceptable for given constraints?
4. Are there any obvious bugs or logical errors?

**Required Action:**
Create a file called `evaluation.txt` with your evaluation in the following format:
```
Score: [0.0-1.0]
Reasoning: [2-3 sentences explaining your score]
```

Do not provide any other output. Only create the evaluation.txt file."""

    return prompt


def add_prompts_to_tasks(input_file: str, output_file: str):
    """
    Add judge prompts to all tasks in the JSON file.
    
    Args:
        input_file: Path to input extracted_tasks.json
        output_file: Path to output file with prompts added
    """
    # Load the data
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_tasks = len(data['tasks'])
    print(f"Processing {total_tasks} tasks...")
    
    # Add prompts to each task
    for i, task in enumerate(data['tasks'], 1):
        problem = task['problem_description']
        solution = task['code_solution']
        
        # Generate the judge prompt
        judge_prompt = create_judge_prompt(problem, solution)
        
        # Add it to the task
        task['judge_prompt'] = judge_prompt
        
        if i % 10 == 0:
            print(f"  Processed {i}/{total_tasks} tasks...")
    
    # Save the updated data
    print(f"\nSaving updated data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully added prompts to all {total_tasks} tasks!")
    print(f"✓ Output saved to: {output_file}")
    
    # Print statistics
    total_prompt_length = sum(len(task['judge_prompt']) for task in data['tasks'])
    avg_prompt_length = total_prompt_length / total_tasks
    
    print(f"\nStatistics:")
    print(f"  Total tasks: {total_tasks}")
    print(f"  Average prompt length: {avg_prompt_length:.0f} characters")
    print(f"  Total prompt size: {total_prompt_length / 1024:.1f} KB")


def main():
    """Main entry point."""

    input_file = "extracted_tasks.json"
    output_file = "extracted_tasks_with_judge_prompts.json"
    print("="*80)
    print("ADDING JUDGE PROMPTS TO EXTRACTED TASKS")
    print("="*80)
    print()
    
    # Process the file
    add_prompts_to_tasks(input_file, output_file)
    
    print("\n" + "="*80)
    print("✅ DONE!")
    print("="*80)


if __name__ == "__main__":
    main()