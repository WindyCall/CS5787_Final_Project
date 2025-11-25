#!/usr/bin/env python3
"""
Cleanup script for redundant trivial files in root results directory.

This script removes the trivial_*.json and trivial_*.csv files from
outputs/results/ since they're now organized in outputs/results/trivial/
"""

import os
import json
from pathlib import Path
from datetime import datetime


def verify_trivial_files():
    """Verify that trivial subdirectory has all files."""

    root_files = {
        'trivial_agent_combined_results.json': 'outputs/results/trivial_agent_combined_results.json',
        'trivial_combined_results_summary.json': 'outputs/results/trivial_combined_results_summary.json',
        'trivial_combined_results_summary.csv': 'outputs/results/trivial_combined_results_summary.csv',
        'trivial_llm_judge_results.json': 'outputs/results/trivial_llm_judge_results.json',
    }

    trivial_files = {
        'trivial_agent_combined_results.json': 'outputs/results/trivial/trivial_agent_combined_results.json',
        'trivial_combined_results_summary.json': 'outputs/results/trivial/trivial_combined_results_summary.json',
        'trivial_combined_results_summary.csv': 'outputs/results/trivial/trivial_combined_results_summary.csv',
        'trivial_llm_judge_results.json': 'outputs/results/trivial/trivial_llm_judge_results.json',
    }

    print("Verifying trivial subdirectory has all files...")
    all_exist = True

    for name, path in trivial_files.items():
        exists = Path(path).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name}")
        if not exists:
            all_exist = False

    return all_exist


def compare_files(file1, file2):
    """Compare two files (JSON or CSV)."""
    if not Path(file1).exists() or not Path(file2).exists():
        return False

    try:
        # For JSON files
        if file1.endswith('.json'):
            with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)
                return data1 == data2
        # For CSV files, compare byte-by-byte
        else:
            with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                return f1.read() == f2.read()
    except Exception as e:
        print(f"  Warning: Could not compare {file1}: {e}")
        return False


def verify_data_integrity():
    """Verify that root and trivial files are identical."""

    print("\nVerifying data integrity...")

    files_to_compare = [
        ('outputs/results/trivial_agent_combined_results.json',
         'outputs/results/trivial/trivial_agent_combined_results.json'),
        ('outputs/results/trivial_combined_results_summary.json',
         'outputs/results/trivial/trivial_combined_results_summary.json'),
        ('outputs/results/trivial_combined_results_summary.csv',
         'outputs/results/trivial/trivial_combined_results_summary.csv'),
        ('outputs/results/trivial_llm_judge_results.json',
         'outputs/results/trivial/trivial_llm_judge_results.json'),
    ]

    all_match = True
    for root_path, trivial_path in files_to_compare:
        if Path(root_path).exists() and Path(trivial_path).exists():
            match = compare_files(root_path, trivial_path)
            status = "✓ IDENTICAL" if match else "✗ DIFFERENT"
            print(f"  {status}: {Path(root_path).name}")
            if not match:
                all_match = False
        else:
            print(f"  ⚠ SKIP: {Path(root_path).name} (one or both missing)")

    return all_match


def create_backup_list(files):
    """Create a backup list of files to be deleted."""

    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'deleted_trivial_files_{timestamp}.txt'

    with open(backup_file, 'w') as f:
        f.write(f"Trivial files deleted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        for file_path in files:
            if Path(file_path).exists():
                size = Path(file_path).stat().st_size
                f.write(f"{file_path} ({size} bytes)\n")

    return backup_file


def delete_trivial_files(files):
    """Delete trivial files from root results directory."""

    deleted_count = 0
    skipped_count = 0

    for file_path in files:
        if Path(file_path).exists():
            try:
                os.remove(file_path)
                print(f"  ✓ Deleted: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"  ✗ Error deleting {file_path}: {e}")
                skipped_count += 1
        else:
            print(f"  ⚠ Already gone: {file_path}")
            skipped_count += 1

    return deleted_count, skipped_count


def main():
    """Main entry point."""

    print("="*80)
    print("CLEANUP TRIVIAL FILES FROM ROOT RESULTS DIRECTORY")
    print("="*80)
    print()

    # Step 1: Verify trivial subdirectory has all files
    print("Step 1: Verify trivial subdirectory has all files")
    print("-"*80)
    if not verify_trivial_files():
        print("\n❌ ERROR: Trivial subdirectory is incomplete!")
        print("Please ensure all files are copied to outputs/results/trivial/ first.")
        return False
    print("✓ Trivial subdirectory is complete\n")

    # Step 2: Verify data integrity
    print("Step 2: Verify data integrity")
    print("-"*80)
    if not verify_data_integrity():
        print("\n❌ ERROR: Files don't match!")
        print("Cleanup aborted to prevent data loss.")
        return False
    print("✓ Data integrity verified\n")

    # Step 3: Identify files to delete
    print("Step 3: Files to delete")
    print("-"*80)

    files_to_delete = [
        'outputs/results/trivial_agent_combined_results.json',
        'outputs/results/trivial_combined_results_summary.json',
        'outputs/results/trivial_combined_results_summary.csv',
        'outputs/results/trivial_llm_judge_results.json',
    ]

    total_size = 0
    existing_files = []

    for file_path in files_to_delete:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size / 1024
            print(f"  - {file_path} ({size:.1f} KB)")
            total_size += size
            existing_files.append(file_path)
        else:
            print(f"  - {file_path} (already deleted)")

    if not existing_files:
        print("\n✓ No files to delete. Everything is clean!")
        return True

    print(f"\nTotal: {len(existing_files)} files, {total_size/1024:.2f} MB")

    # Step 4: Create backup and delete
    print("\n" + "="*80)
    print("Step 4: Delete files")
    print("-"*80)

    print("\nCreating backup list...")
    backup_file = create_backup_list(existing_files)
    print(f"✓ Backup list saved to: {backup_file}")

    print("\nDeleting files...")
    deleted_count, skipped_count = delete_trivial_files(existing_files)

    print("\n" + "="*80)
    print("CLEANUP COMPLETE")
    print("="*80)
    print(f"✓ Deleted: {deleted_count} files")
    print(f"⚠ Skipped: {skipped_count} files")
    print(f"✓ Backup list: {backup_file}")
    print(f"✓ Space freed: ~{total_size/1024:.2f} MB")
    print("\nTrivial files are now organized in outputs/results/trivial/")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
