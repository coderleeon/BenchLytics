from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
import datetime
from .session import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    experiments = relationship("ExperimentRun", back_populates="task")

class ExperimentRun(Base):
    __tablename__ = "experiment_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    prompt_variation = Column(String, default="default")
    iterations = Column(Integer, default=1)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    task = relationship("Task", back_populates="experiments")
    results = relationship("BenchmarkResult", back_populates="experiment")

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiment_runs.id"))
    model_name = Column(String, index=True)
    output = Column(String)
    
    # Metrics
    latency_ms = Column(Float)
    token_count = Column(Integer)
    cost = Column(Float)
    
    # Evaluation Scores
    score_correctness = Column(Float)
    score_clarity = Column(Float)
    score_reasoning = Column(Float)
    confidence_score = Column(Float)
    hallucination_flag = Column(Integer, default=0) # 0 = false, 1 = true
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    experiment = relationship("ExperimentRun", back_populates="results")
