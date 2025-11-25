#!/usr/bin/env python3
"""
Generate a pretty error distribution graph from LLM judge results
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Load results
with open('./outputs/results/llm_judge_results.json') as f:
    data = json.load(f)

# Extract data
results = data['results']
valid_results = [r for r in results if r['llm_score'] >= 0]

llm_scores = np.array([r['llm_score'] for r in valid_results])
actual_scores = np.array([r['actual_accuracy'] for r in valid_results])

# Calculate differences (prediction errors)
differences = llm_scores - actual_scores

# Create figure with smaller size
fig, ax = plt.subplots(figsize=(6, 4))

# Create histogram with beautiful styling
n, bins, patches = ax.hist(differences, bins=20, 
                           color='#FFA07A',  # Light salmon/coral color
                           edgecolor='white', 
                           linewidth=1.5,
                           alpha=0.85)

# Add shadow effect to each bar
for patch in patches:
    # Keep the light coral color
    patch.set_facecolor('#FFA07A')
    # Add darker shadow edge
    patch.set_edgecolor('#CD5C5C')
    patch.set_linewidth(2)

# Add vertical line at zero with shadow effect
ax.axvline(x=0, color='#E74C3C', linestyle='--', linewidth=3, 
          label='Perfect Prediction', alpha=0.9, zorder=5)
# Shadow for the line
ax.axvline(x=0, color='#C0392B', linestyle='--', linewidth=3.5, 
          alpha=0.3, zorder=4)

# Styling
ax.set_xlabel('Prediction Error', 
             fontsize=18, fontweight='bold', labelpad=10)
ax.set_ylabel('Frequency', fontsize=18, fontweight='bold', labelpad=10)

# Increase tick label size
ax.tick_params(axis='both', which='major', labelsize=13)

# Add grid with subtle styling
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8, axis='y')
ax.set_axisbelow(True)

# Add legend with larger font
ax.legend(fontsize=15, framealpha=0.95, shadow=True, 
         loc='upper right', edgecolor='gray')

# Add statistics text box in corner
metrics = data['metrics']
stats_text = f"MAE: {metrics['mae']:.3f}\nRMSE: {metrics['rmse']:.3f}"

# Create shadow effect for text box
ax.text(0.022, 0.978, stats_text, 
       transform=ax.transAxes,
       fontsize=15,
       verticalalignment='top',
       bbox=dict(boxstyle='round', facecolor='#555555', 
                alpha=0.3, edgecolor='none', pad=0.6),
       zorder=2)

# Main text box on top
ax.text(0.02, 0.98, stats_text, 
       transform=ax.transAxes,
       fontsize=15,
       verticalalignment='top',
       fontweight='bold',
       bbox=dict(boxstyle='round', facecolor='wheat', 
                alpha=0.9, edgecolor='#8B7355', linewidth=2,
                pad=0.6),
       zorder=3)

# Set spine colors
for spine in ax.spines.values():
    spine.set_edgecolor('#CCCCCC')
    spine.set_linewidth(1.5)

# Tight layout
plt.tight_layout()

# Save with high DPI
output_path = './outputs/graphs/error_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', 
           facecolor='white', edgecolor='none')

print(f"✓ Graph saved to: {output_path}")
print(f"  Evaluated {len(valid_results)} tasks")
print(f"  Mean error: {np.mean(differences):.3f}")
print(f"  Std error: {np.std(differences):.3f}")

plt.close()