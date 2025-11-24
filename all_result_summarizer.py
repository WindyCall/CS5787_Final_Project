
#!/usr/bin/env python3
"""
Combine all evaluation results into comprehensive JSON and CSV files.

Combines:
- Unit test results
- LLM judge results (gpt-4o-mini)
- Agent judge results (OpenHands)
- Problem descriptions and solutions
"""

import json
import csv
from pathlib import Path


def normalize_task_id(task_id):
    """Normalize task ID for matching across files."""
    # Convert to lowercase and handle different variations
    task_id_lower = task_id.lower()
    # Remove extra underscores from agent format
    if '__' in task_id_lower:
        parts = task_id_lower.split('__')
        if len(parts) >= 3:
            # Format like: "3676__s8cb3xn__QumB7ck" -> "3676__s8cb3xn"
            return '__'.join(parts[:2])
    return task_id_lower


def load_data():
    """Load all JSON files from current directory."""
    with open('agent_combined_results.json', 'r') as f:
        agent_data = json.load(f)
    
    with open('llm_judge_results.json', 'r') as f:
        llm_data = json.load(f)
    
    with open('unit_test_summary.json', 'r') as f:
        unit_test_data = json.load(f)
    
    with open('extracted_tasks_with_judge_prompts.json', 'r') as f:
        task_data = json.load(f)
    
    return agent_data, llm_data, unit_test_data, task_data


def create_task_lookup(task_data):
    """Create lookup dictionary for task details."""
    lookup = {}
    for task in task_data['tasks']:
        task_id_norm = normalize_task_id(task['task_id'])
        lookup[task_id_norm] = task
    return lookup


def create_unit_test_lookup(unit_test_data):
    """Create lookup dictionary for unit test results."""
    lookup = {}
    for result in unit_test_data['per_task_results']:
        task_id_norm = normalize_task_id(result['task_id'])
        lookup[task_id_norm] = result
    return lookup


def create_llm_lookup(llm_data):
    """Create lookup dictionary for LLM judge results."""
    lookup = {}
    for result in llm_data['results']:
        task_id_norm = normalize_task_id(result['task_id'])
        lookup[task_id_norm] = result
    return lookup


def combine_results(agent_data, llm_data, unit_test_data, task_data):
    """Combine all results into unified format."""
    
    # Create lookups
    task_lookup = create_task_lookup(task_data)
    unit_test_lookup = create_unit_test_lookup(unit_test_data)
    llm_lookup = create_llm_lookup(llm_data)
    
    combined = []
    
    # Process agent results (which has task IDs as keys)
    for agent_task_id, agent_result in agent_data['tasks'].items():
        task_id_norm = normalize_task_id(agent_task_id)
        
        # Get corresponding data from other sources
        task_info = task_lookup.get(task_id_norm, {})
        unit_test_info = unit_test_lookup.get(task_id_norm, {})
        llm_info = llm_lookup.get(task_id_norm, {})
        
        # Calculate unit test score
        if unit_test_info:
            total = unit_test_info.get('total_tests', 0)
            passed = unit_test_info.get('passed_tests', 0)
            unit_test_score = passed / total if total > 0 else 0.0
        else:
            unit_test_score = 0.0
            total = 0
            passed = 0
        
        # Build combined record
        record = {
            'id': agent_task_id,
            'problem_title': task_info.get('problem_title', 'N/A'),
            'problem_description': task_info.get('problem_description', 'N/A'),
            'code_solution': task_info.get('code_solution', 'N/A'),
            'unit_test_score': unit_test_score,
            'unit_test_passed': passed,
            'unit_test_total': total,
            'unit_test_status': unit_test_info.get('status', 'UNKNOWN'),
            'unit_test_details': f"{passed}/{total} tests passed - {unit_test_info.get('status', 'UNKNOWN')}",
            'llm_judge_score': llm_info.get('llm_score', None),
            'llm_judge_reasoning': llm_info.get('reasoning', 'N/A'),
            'llm_model': 'gpt-4o-mini',
            'agent_judge_score': agent_result.get('score', None),
            'agent_judge_reasoning': agent_result.get('reasoning', 'N/A'),
            'agent_model': 'openhands',
        }
        
        combined.append(record)
    
    # Sort by ID
    combined.sort(key=lambda x: x['id'])
    
    return combined


def create_summary_json(combined_results, agent_data, llm_data, unit_test_data):
    """Create summary JSON with metrics and results."""
    
    # Calculate overall metrics
    total_tasks = len(combined_results)
    
    # Unit test metrics
    unit_passed = sum(1 for r in combined_results if r['unit_test_status'] == 'PASSED')
    avg_unit_score = sum(r['unit_test_score'] for r in combined_results) / total_tasks if total_tasks > 0 else 0
    
    # LLM judge metrics
    llm_scores = [r['llm_judge_score'] for r in combined_results if r['llm_judge_score'] is not None]
    avg_llm_score = sum(llm_scores) / len(llm_scores) if llm_scores else 0
    
    # Agent judge metrics
    agent_scores = [r['agent_judge_score'] for r in combined_results if r['agent_judge_score'] is not None]
    avg_agent_score = sum(agent_scores) / len(agent_scores) if agent_scores else 0
    
    # Calculate correlations (simplified - just for tasks with all scores)
    complete_tasks = [r for r in combined_results 
                     if r['llm_judge_score'] is not None and r['agent_judge_score'] is not None]
    
    summary = {
        'overview': {
            'total_tasks': total_tasks,
            'evaluation_date': '2024-11-23',
            'llm_model': 'gpt-4o-mini',
            'agent_model': 'openhands'
        },
        'metrics': {
            'unit_tests': {
                'total_evaluated': total_tasks,
                'passed': unit_passed,
                'failed': total_tasks - unit_passed,
                'pass_rate': unit_passed / total_tasks if total_tasks > 0 else 0,
                'average_score': avg_unit_score
            },
            'llm_judge': {
                'total_evaluated': len(llm_scores),
                'average_score': avg_llm_score,
                'min_score': min(llm_scores) if llm_scores else 0,
                'max_score': max(llm_scores) if llm_scores else 0,
                'correlation_with_unit_tests': llm_data.get('metrics', {}).get('correlation', None),
                'mae': llm_data.get('metrics', {}).get('mae', None),
                'binary_accuracy': llm_data.get('metrics', {}).get('binary_accuracy', None)
            },
            'agent_judge': {
                'total_evaluated': len(agent_scores),
                'average_score': avg_agent_score,
                'min_score': min(agent_scores) if agent_scores else 0,
                'max_score': max(agent_scores) if agent_scores else 0,
                'perfect_score_count': agent_data.get('summary', {}).get('perfect_score_count', 0)
            }
        },
        'detailed_results': combined_results
    }
    
    return summary


def write_csv(combined_results, output_path):
    """Write results to CSV file with specified column order."""
    
    fieldnames = [
        'ID',
        'Problem Description', 
        'Solution (Model solution from Claude4.5haiku)',
        'Unit test Scores',
        'LLM Judgment Score',
        'Agent Judgement Score',
        'Unittest details',
        'LLM Judgement Reasoning',
        'Agent Judgement Reasoning',
        'LLM name',
        'Agent LLM name'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in combined_results:
            # Map to CSV format
            row = {
                'ID': record['id'],
                'Problem Description': record['problem_description'][:500] + '...' if len(record['problem_description']) > 500 else record['problem_description'],
                'Solution (Model solution from Claude4.5haiku)': record['code_solution'][:500] + '...' if len(record['code_solution']) > 500 else record['code_solution'],
                'Unit test Scores': f"{record['unit_test_score']:.2f}",
                'LLM Judgment Score': f"{record['llm_judge_score']:.2f}" if record['llm_judge_score'] is not None else 'N/A',
                'Agent Judgement Score': f"{record['agent_judge_score']:.2f}" if record['agent_judge_score'] is not None else 'N/A',
                'Unittest details': record['unit_test_details'],
                'LLM Judgement Reasoning': record['llm_judge_reasoning'],
                'Agent Judgement Reasoning': record['agent_judge_reasoning'],
                'LLM name': record['llm_model'],
                'Agent LLM name': record['agent_model']
            }
            writer.writerow(row)


def main():
    """Main execution."""
    print("="*80)
    print("COMBINING EVALUATION RESULTS")
    print("="*80)
    print()
    
    # Load data
    print("Loading data files...")
    agent_data, llm_data, unit_test_data, task_data = load_data()
    print(f"✓ Agent results: {len(agent_data.get('tasks', {}))} tasks")
    print(f"✓ LLM results: {len(llm_data.get('results', []))} tasks")
    print(f"✓ Unit test results: {len(unit_test_data.get('per_task_results', []))} tasks")
    print(f"✓ Task descriptions: {len(task_data.get('tasks', []))} tasks")
    print()
    
    # Combine results
    print("Combining results...")
    combined_results = combine_results(agent_data, llm_data, unit_test_data, task_data)
    print(f"✓ Combined {len(combined_results)} complete task records")
    print()
    
    # Create summary JSON
    print("Creating summary JSON...")
    summary_json = create_summary_json(combined_results, agent_data, llm_data, unit_test_data)
    
    # Write JSON output
    json_output = 'combined_results_summary.json'
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(summary_json, f, indent=2, ensure_ascii=False)
    print(f"✓ JSON saved to: {json_output}")
    
    # Write CSV output
    print("Creating CSV file...")
    csv_output = 'combined_results_summary.csv'
    write_csv(combined_results, csv_output)
    print(f"✓ CSV saved to: {csv_output}")
    print()
    
    # Print summary statistics
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print()
    print(f"Total Tasks: {summary_json['overview']['total_tasks']}")
    print()
    print("Unit Tests:")
    print(f"  Pass Rate: {summary_json['metrics']['unit_tests']['pass_rate']:.1%}")
    print(f"  Average Score: {summary_json['metrics']['unit_tests']['average_score']:.3f}")
    print()
    print("LLM Judge (gpt-4o-mini):")
    print(f"  Tasks Evaluated: {summary_json['metrics']['llm_judge']['total_evaluated']}")
    print(f"  Average Score: {summary_json['metrics']['llm_judge']['average_score']:.3f}")
    print(f"  Correlation with Unit Tests: {summary_json['metrics']['llm_judge']['correlation_with_unit_tests']:.3f}")
    print(f"  Binary Accuracy: {summary_json['metrics']['llm_judge']['binary_accuracy']:.1%}")
    print()
    print("Agent Judge (OpenHands):")
    print(f"  Tasks Evaluated: {summary_json['metrics']['agent_judge']['total_evaluated']}")
    print(f"  Average Score: {summary_json['metrics']['agent_judge']['average_score']:.3f}")
    print(f"  Perfect Scores: {summary_json['metrics']['agent_judge']['perfect_score_count']}")
    print()
    print("="*80)
    print("✅ DONE!")
    print("="*80)


if __name__ == '__main__':
    main()