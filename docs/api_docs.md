# API 文档

## 题目服务 (QuestionService)

### 获取题目列表
```python
get_questions(type_id: Optional[int] = None, 
             difficulty_level: Optional[int] = None, 
             page: int = 1, 
             per_page: int = 10) -> List[Dict]
```
获取题目列表，支持按类型和难度筛选，并支持分页。

**参数：**
- type_id: 题目类型ID（可选）
- difficulty_level: 难度等级（可选）
- page: 页码，默认为1
- per_page: 每页数量，默认为10

**返回：**
- 题目列表，每个题目包含完整的题目信息

### 验证答案
```python
verify_answer(question_id: int, 
             user_answer: str, 
             user_id: str = 'test_user') -> Dict
```
验证用户答案是否正确。

**参数：**
- question_id: 题目ID
- user_answer: 用户答案
- user_id: 用户ID，默认为'test_user'

**返回：**
- 包含验证结果的字典

## 用户服务 (UserService)

### 获取用户进度
```python
get_progress(user_id: str) -> Dict
```
获取用户的学习进度统计。

**参数：**
- user_id: 用户ID

**返回：**
- 包含进度统计信息的字典

### 获取答题历史
```python
get_answer_history(user_id: str, 
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[Dict]
```
获取用户的答题历史记录。

**参数：**
- user_id: 用户ID
- start_date: 开始日期（可选）
- end_date: 结束日期（可选）

**返回：**
- 答题历史记录列表

## 评分服务 (ScoringService)

### 评估答案
```python
evaluate_answer(question_id: int,
               user_answer: str,
               question_type: str) -> Dict
```
评估用户答案的正确性和完整性。

**参数：**
- question_id: 题目ID
- user_answer: 用户答案
- question_type: 题目类型

**返回：**
- 包含评分结果的字典

### 生成解析
```python
generate_explanation(question_id: int,
                    user_answer: str,
                    is_correct: bool) -> str
```
使用 AI 生成详细的答案解析。

**参数：**
- question_id: 题目ID
- user_answer: 用户答案
- is_correct: 是否正确

**返回：**
- 生成的解析文本

## 错误代码

| 错误代码 | 描述 |
|---------|------|
| 1001 | 题目不存在 |
| 1002 | 答案格式错误 |
| 1003 | 数据库连接错误 |
| 1004 | API 调用失败 |
| 1005 | 参数验证失败 |

## 使用示例

```python
# 获取选择题列表
questions = question_service.get_questions(type_id=1, difficulty_level=1)

# 验证答案
result = question_service.verify_answer(
    question_id=1,
    user_answer="A",
    user_id="test_user"
)

# 获取用户进度
progress = user_service.get_progress("test_user")

# 评估简答题答案
evaluation = scoring_service.evaluate_answer(
    question_id=7,
    user_answer="用户的回答内容",
    question_type="简答题"
)
```

## 注意事项

1. 所有接口调用需要进行异常处理
2. 答案验证时注意数据类型转换
3. API 调用可能有频率限制
4. 建议实现请求重试机制
5. 注意处理并发请求 