
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

def plot_model_comparison():
    """
    Generates and saves a bar chart comparing the performance of three models.
    """
    # --- Data ---
    model_names = ['Base Model', 'Weak Penalty', 'Strong Penalty']
    valid_ratios = [11, 62, 85]  # As percentages
    efficient_scores = [10.44, 58.54, 78.84]

    x = np.arange(len(model_names))  # the label locations
    width = 0.35  # the width of the bars

    # --- Plotting ---
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plotting the bars
    rects1 = ax.bar(x - width/2, valid_ratios, width, label='Valid Ratio (%)', color='skyblue')
    rects2 = ax.bar(x + width/2, efficient_scores, width, label='Efficiency Score', color='salmon')

    # Add some text for labels, title and axes ticks
    ax.set_ylabel('Scores / Percentage')
    ax.set_title('Model Performance Comparison', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=0, ha="center")
    ax.legend()
    
    # Set Y-axis limit to give some space at the top
    ax.set_ylim(0, 100)

    # Attach a text label above each bar in rects, displaying its height.
    def autolabel(rects, is_percentage=False):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            label = f'{height}%' if is_percentage else f'{height:.2f}'
            ax.annotate(label,
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontweight='semibold')

    autolabel(rects1, is_percentage=True)
    autolabel(rects2)

    fig.tight_layout()

    # --- Save the plot ---
    output_filename = 'evaluation_comparison.png'
    plt.savefig(output_filename, dpi=300)
    print(f"Plot saved as '{output_filename}'")

if __name__ == '__main__':
    plot_model_comparison()
