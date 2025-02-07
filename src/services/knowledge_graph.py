from typing import Dict, List, Set, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import logging
import networkx as nx
import matplotlib.pyplot as plt
from ..database.db_manager import DatabaseManager
from .deep_learning_manager import DeepLearningManager

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """知识图谱管理类"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.dl_manager = DeepLearningManager()
        self.graph = nx.Graph()
        
    def build_knowledge_graph(self) -> Dict:
        """构建知识图谱"""
        # 获取所有题目和标签
        query = """
            SELECT q.question_id, q.content, 
                   GROUP_CONCAT(t.tag_name) as tags,
                   dl.level_name as difficulty
            FROM questions q
            LEFT JOIN question_tag_relations qtr ON q.question_id = qtr.question_id
            LEFT JOIN question_tags t ON qtr.tag_id = t.tag_id
            JOIN difficulty_levels dl ON q.difficulty_level = dl.level_id
            WHERE q.is_active = TRUE
            GROUP BY q.question_id, q.content, dl.level_name
        """
        results = self.db_manager.execute_query(query)
        
        if not results:
            logger.warning("没有找到任何题目")
            return {}
        
        # 构建知识点关联网络
        graph = {}
        for row in results:
            q_id = row['question_id']
            content = row['content']
            # 使用新的API调用方式获取嵌入向量
            embedding = self.dl_manager.get_text_embedding(content)
            tags = row['tags'].split(',') if row['tags'] else []
            difficulty = row['difficulty']
            
            graph[q_id] = {
                'content': content,
                'embedding': embedding,
                'tags': tags,
                'difficulty': difficulty,
                'related_questions': []
            }
            
            # 添加到NetworkX图
            self.graph.add_node(q_id, 
                              content=content,
                              tags=tags,
                              difficulty=difficulty)
            
        # 计算题目间的关联关系
        question_ids = list(graph.keys())
        for i, q1_id in enumerate(question_ids):
            for q2_id in question_ids[i+1:]:
                similarity = cosine_similarity(
                    [graph[q1_id]['embedding']], 
                    [graph[q2_id]['embedding']]
                )[0][0]
                
                if similarity > 0.7:  # 设置相似度阈值
                    graph[q1_id]['related_questions'].append(q2_id)
                    graph[q2_id]['related_questions'].append(q1_id)
                    # 添加边到NetworkX图
                    self.graph.add_edge(q1_id, q2_id, weight=similarity)
                    
        return graph
        
    def get_related_questions(self, question_id: int, max_distance: int = 2) -> List[Dict]:
        """获取与指定题目相关的题目"""
        if not self.graph.has_node(question_id):
            return []
            
        related = []
        # 使用BFS获取指定距离内的所有相关题目
        for node in nx.single_source_shortest_path_length(self.graph, question_id, cutoff=max_distance):
            if node != question_id:
                node_data = self.graph.nodes[node]
                related.append({
                    'question_id': node,
                    'content': node_data['content'],
                    'tags': node_data['tags'],
                    'difficulty': node_data['difficulty'],
                    'similarity': self.graph[question_id][node]['weight'] if self.graph.has_edge(question_id, node) else 0
                })
                
        # 按相似度排序
        related.sort(key=lambda x: x['similarity'], reverse=True)
        return related
        
    def get_knowledge_path(self, start_id: int, end_id: int) -> List[int]:
        """获取两个题目之间的知识路径"""
        try:
            path = nx.shortest_path(self.graph, start_id, end_id, weight='weight')
            return path
        except nx.NetworkXNoPath:
            return []
            
    def get_central_questions(self, top_k: int = 10) -> List[Tuple[int, float]]:
        """获取知识图谱中最重要的题目"""
        if not self.graph:
            return []
            
        # 计算中心性指标
        centrality = nx.eigenvector_centrality(self.graph, weight='weight')
        # 按中心性排序
        sorted_questions = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_questions[:top_k]
        
    def get_knowledge_clusters(self, n_clusters: int = 5) -> Dict[int, Set[int]]:
        """获取知识点聚类"""
        if not self.graph:
            return {}
            
        # 使用社区检测算法
        communities = nx.community.louvain_communities(self.graph, weight='weight')
        # 如果社区数量超过要求，合并最小的社区
        while len(communities) > n_clusters:
            communities = sorted(communities, key=len)
            communities[-2].update(communities[-1])
            communities.pop()
            
        return {i: set(community) for i, community in enumerate(communities)}
        
    def visualize_graph(self, output_path: str = 'knowledge_graph.png') -> None:
        """可视化知识图谱"""
        if not self.graph:
            logger.warning("图谱为空，无法可视化")
            return
            
        plt.figure(figsize=(12, 8))
        
        # 设置节点颜色（按难度）
        difficulty_colors = {
            '入门': '#90CAF9',  # 浅蓝
            '初级': '#81C784',  # 浅绿
            '中级': '#FFB74D',  # 橙色
            '高级': '#E57373',  # 红色
            '专家': '#9575CD'   # 紫色
        }
        
        node_colors = [difficulty_colors.get(self.graph.nodes[node]['difficulty'], '#BDBDBD') 
                      for node in self.graph.nodes()]
        
        # 设置节点大小（按连接数）
        node_sizes = [3000 * self.graph.degree(node) for node in self.graph.nodes()]
        
        # 绘制图形
        pos = nx.spring_layout(self.graph)
        nx.draw_networkx_nodes(self.graph, pos, 
                             node_color=node_colors,
                             node_size=node_sizes,
                             alpha=0.7)
        nx.draw_networkx_edges(self.graph, pos, 
                             edge_color='gray',
                             width=[d['weight'] * 2 for (u, v, d) in self.graph.edges(data=True)],
                             alpha=0.5)
        
        # 添加图例
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                    markerfacecolor=color, label=diff,
                                    markersize=10)
                         for diff, color in difficulty_colors.items()]
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.title('知识图谱可视化')
        plt.axis('off')
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"知识图谱已保存至 {output_path}") 