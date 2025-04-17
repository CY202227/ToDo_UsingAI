from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import numpy as np
import joblib
import os
from datetime import datetime
from models.todo import PriorityEnum
import logging
from typing import List, Optional, Any, Union

logger = logging.getLogger(__name__)

class TodoMLService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = RandomForestClassifier()
        self.model_dir = "ml_models"
        self.model_path = os.path.join(self.model_dir, "todo_priority_model.joblib")
        self.vectorizer_path = os.path.join(self.model_dir, "vectorizer.joblib")
        self.min_samples_for_training = 20
        
        # 创建模型目录
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 尝试加载现有模型
        self.load_model()

    def prepare_features(self, todos: List[Any]) -> np.ndarray:
        """准备特征数据"""
        try:
            texts = [todo.text for todo in todos]
            features = self.vectorizer.transform(texts)
            
            # 添加额外特征
            additional_features = np.array([
                self._extract_additional_features(todo)
                for todo in todos
            ])
            
            return np.hstack((features.toarray(), additional_features))
        except Exception as e:
            logger.error(f"准备特征时发生错误: {str(e)}", exc_info=True)
            raise

    def _extract_additional_features(self, todo: Any) -> List[Union[int, float]]:
        """从待办事项中提取额外特征"""
        try:
            now = datetime.utcnow()
            days_until_due = (todo.due_date - now).days if todo.due_date else 0
            urgent_keywords = ['紧急', '立即', '马上', 'urgent']
            
            return [
                1 if todo.due_date else 0,
                days_until_due,
                len(todo.text.split()),
                1 if any(keyword in todo.text.lower() for keyword in urgent_keywords) else 0
            ]
        except Exception as e:
            logger.error(f"提取额外特征时发生错误: {str(e)}", exc_info=True)
            return [0, 0, 0, 0]

    def prepare_labels(self, todos: List[Any]) -> np.ndarray:
        """准备标签数据"""
        try:
            priority_map = {
                PriorityEnum.LOW: 0,
                PriorityEnum.MEDIUM: 1,
                PriorityEnum.HIGH: 2
            }
            return np.array([priority_map[todo.priority] for todo in todos])
        except Exception as e:
            logger.error(f"准备标签时发生错误: {str(e)}", exc_info=True)
            raise

    def train_model(self, todos: List[Any]) -> Optional[float]:
        """训练模型"""
        if len(todos) < self.min_samples_for_training:
            logger.warning(f"训练样本数量不足: {len(todos)} < {self.min_samples_for_training}")
            return None

        try:
            # 准备数据
            X = self.prepare_features(todos)
            y = self.prepare_labels(todos)

            # 分割训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 训练模型
            self.model.fit(X_train, y_train)

            # 保存模型
            self._save_model()

            # 计算并返回模型准确率
            accuracy = self.model.score(X_test, y_test)
            logger.info(f"模型训练完成，准确率: {accuracy:.2f}")
            return accuracy
            
        except Exception as e:
            logger.error(f"训练模型时发生错误: {str(e)}", exc_info=True)
            return None

    def _save_model(self) -> None:
        """保存模型和向量器"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            logger.info("模型保存成功")
        except Exception as e:
            logger.error(f"保存模型时发生错误: {str(e)}", exc_info=True)
            raise

    def predict_priority(self, todo_text: str, due_date: Optional[datetime] = None) -> PriorityEnum:
        """预测任务优先级"""
        try:
            # 准备特征
            text_features = self.vectorizer.transform([todo_text]).toarray()
            additional_features = np.array([[
                1 if due_date else 0,
                (due_date - datetime.utcnow()).days if due_date else 0,
                len(todo_text.split()),
                1 if any(keyword in todo_text.lower() for keyword in ['紧急', '立即', '马上', 'urgent']) else 0
            ]])
            features = np.hstack((text_features, additional_features))

            # 预测
            prediction = self.model.predict(features)[0]
            
            # 转换预测结果
            priority_map = {
                0: PriorityEnum.LOW,
                1: PriorityEnum.MEDIUM,
                2: PriorityEnum.HIGH
            }
            result = priority_map[prediction]
            logger.info(f"预测完成: text='{todo_text[:50]}...', priority={result}")
            return result
            
        except Exception as e:
            logger.error(f"预测优先级时发生错误: {str(e)}", exc_info=True)
            return PriorityEnum.MEDIUM

    def load_model(self) -> bool:
        """加载已保存的模型"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                logger.info("成功加载已有模型")
                return True
        except Exception as e:
            logger.error(f"加载模型时发生错误: {str(e)}", exc_info=True)
        return False

# 创建全局ML服务实例
ml_service = TodoMLService() 