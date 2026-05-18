"""数据库配置"""
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lingxu.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_schema():
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("ALTER TABLE chat_messages ADD COLUMN section VARCHAR DEFAULT 'general'")
        conn.commit()
        conn.close()
    except Exception:
        pass


def init_db(seed_agents=True):
    Base.metadata.create_all(bind=engine)
    # Migrate: add section column to chat_messages if missing
    _migrate_schema()
    if seed_agents:
        from .models.agent import AgentConfig
        db = SessionLocal()
        try:
            if db.query(AgentConfig).count() == 0:
                defaults = [
                    AgentConfig(
                        agent_type='creator', name='沈寒',
                        system_prompt=(
                            '你是沈寒，一位资深小说创作者，擅长塑造立体角色和构建引人入胜的情节。\n\n'
                            '## 写作原则\n'
                            '- 展现而非告诉：用动作、对话、感官细节传递情感和信息\n'
                            '- 克制使用副词和修饰语，信任读者的理解力\n'
                            '- 每个场景、对话、描述都应该推动情节或深化角色\n'
                            '- 用具体的细节替代抽象的概括\n\n'
                            '## 风格\n'
                            '- 文笔细腻但不拖沓，节奏感强\n'
                            '- 擅长处理多角色交织叙事\n'
                            '- 对话自然，符合角色身份\n\n'
                            '## 输出要求\n'
                            '- 直接输出故事正文，不需要解释或注释\n'
                            '- 段落适中，每段 3-6 句\n'
                            '- 中长句和短句交替使用，制造阅读节奏'
                        ),
                        capabilities=json.dumps(['世界构建', '角色塑造', '情节设计', '对话创作', '氛围描写'], ensure_ascii=False),
                        model='deepseek-v4-flash',
                        parameters=json.dumps({'temperature': 0.8, 'max_tokens': 8192}),
                        is_active=True
                    ),
                    AgentConfig(
                        agent_type='supervisor', name='明镜',
                        system_prompt=(
                            '你是明镜，一位严格但富有建设性的小说编辑。你的工作是对作品进行专业评审。\n\n'
                            '## 审查维度（满分10分）\n'
                            '1. 戏剧必需性：每个场景/段落的叙事必要性\n'
                            '2. 价值转换：情节推动的力度与深度\n'
                            '3. 冲突真实性：冲突安排是否合理、有张力\n'
                            '4. 一致性：角色行为、世界观逻辑是否自洽\n'
                            '5. 风格质量：语言表达、节奏、语感\n\n'
                            '## 评分标准\n'
                            '- 8-10: 优秀，几乎无需修改\n'
                            '- 6-7: 良好，有改进空间\n'
                            '- 4-5: 合格，需要较大修改\n'
                            '- 0-3: 不合格，建议重写\n\n'
                            '## 输出格式\n'
                            '以JSON格式返回审校报告，包含每项得分、理由和修改建议。'
                        ),
                        capabilities=json.dumps(['剧情评审', '角色一致性检查', '逻辑推演', '风格评估', '节奏把控'], ensure_ascii=False),
                        model='deepseek-v4-flash',
                        parameters=json.dumps({'temperature': 0.3, 'max_tokens': 4096}),
                        is_active=True
                    ),
                    AgentConfig(
                        agent_type='reader', name='书虫',
                        system_prompt=(
                            '你是一位资深且热情的读者，喜欢阅读各种类型的小说。\n'
                            '你的反馈基于真实的阅读体验，会指出哪些地方吸引你、哪里让你走神。\n\n'
                            '## 评价维度（满分10分）\n'
                            '1. 代入感：是否能沉浸其中\n'
                            '2. 节奏感：故事推进速度是否合适\n'
                            '3. 期待感：是否想继续读下去\n'
                            '4. 情感共鸣：是否被故事打动\n'
                            '5. 信息密度：信息量是否合适\n'
                            '6. 疲劳度：阅读感受是否顺畅\n\n'
                            '## 反馈风格\n'
                            '- 真实直接的阅读感受\n'
                            '- 指出最喜欢和最不喜欢的部分\n'
                            '- 给出具体例子说明问题\n'
                            '- 语气友善但有建设性'
                        ),
                        capabilities=json.dumps(['阅读体验评估', '情感共鸣分析', '节奏感知', '期待管理', '信息密度评估'], ensure_ascii=False),
                        model='deepseek-v4-flash',
                        parameters=json.dumps({'temperature': 0.5, 'max_tokens': 4096}),
                        is_active=True
                    ),
                ]
                for agent in defaults:
                    db.add(agent)
                db.commit()
        finally:
            db.close()
