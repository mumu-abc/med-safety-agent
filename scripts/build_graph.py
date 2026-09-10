"""构建药物知识图谱。"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from app.graph.drug_data import build_graph_from_data

if __name__ == "__main__":
    print("正在构建药物知识图谱...")
    stats = build_graph_from_data()
    print(f"完成! 药物: {stats['drugs']} 个, 相互作用: {stats['interactions']} 条")
