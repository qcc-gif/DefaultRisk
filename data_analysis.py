import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_analysis_plots(filepath, results_folder):
    # 读取数据
    try:
        data = pd.read_csv(filepath)

        # 创建保存图表的目录
        analysis_folder = os.path.join(results_folder, 'analysis')
        os.makedirs(analysis_folder, exist_ok=True)

        # 1. 相关性热图
        plt.figure(figsize=(10, 8))
        numeric_data = data.select_dtypes(include=['number'])
        sns.heatmap(numeric_data.corr(), annot=True, fmt=".2f", cmap="coolwarm")
        heatmap_path = os.path.join(analysis_folder, 'correlation_heatmap.png')
        plt.title("Correlation Heatmap")
        plt.savefig(heatmap_path)
        plt.close()

        # 2. 各列的分布图
        dist_paths = []
        for col in data.select_dtypes(include=['float', 'int']).columns:
            plt.figure(figsize=(8, 6))
            sns.histplot(data[col], kde=True, color="blue")
            plt.title(f'Distribution of {col}')
            dist_path = os.path.join(analysis_folder, f'distribution_{col}.png')
            plt.savefig(dist_path)
            dist_paths.append(dist_path)
            plt.close()

        # 3. 箱线图
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=data.select_dtypes(include=['float', 'int']))
        boxplot_path = os.path.join(analysis_folder, 'boxplot.png')
        plt.title("Boxplot of Numerical Features")
        plt.savefig(boxplot_path)
        plt.close()

        # 4. 散点图矩阵
        scatter_path = os.path.join(analysis_folder, 'scatter_matrix.png')
        sns.pairplot(data=data.select_dtypes(include=['float', 'int']))
        plt.savefig(scatter_path)
        plt.close()

        return {
            'heatmap': heatmap_path,
            'distributions': dist_paths,
            'boxplot': boxplot_path,
            'scatter_matrix': scatter_path
        }

    except Exception as e:
        print(f"Error during data analysis: {e}")
        return None
