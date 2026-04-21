from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import time
import logging

from database.session import get_db
from database.models import Task, ExperimentRun, BenchmarkResult
from models.llm_manager import llm_manager
from evaluation.judge import judge_engine
from utils.logger import log_experiment

logger = logging.getLogger(__name__)

router = APIRouter()

class BenchmarkRequest(BaseModel):
    task: str
    models: List[str]
    prompt_variation: Optional[str] = "default"
    iterations: Optional[int] = 1

class ExperimentResponse(BaseModel):
    experiment_id: int
    message: str

@router.post("/benchmark", response_model=ExperimentResponse)
async def start_benchmark(req: BenchmarkRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Create Task or find existing
    db_task = Task(description=req.task)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 2. Create Experiment Run
    db_experiment = ExperimentRun(
        task_id=db_task.id,
        prompt_variation=req.prompt_variation,
        iterations=req.iterations,
        status="running"
    )
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    
    # Run the benchmark asynchronously
    background_tasks.add_task(run_experiment, db_experiment.id, req.task, req.models, req.iterations)
    
    return {"experiment_id": db_experiment.id, "message": "Experiment started in background."}

async def run_experiment(experiment_id: int, task: str, models: List[str], iterations: int):
    # This must create its own DB session for safety in background
    from database.session import SessionLocal
    db = SessionLocal()
    
    try:
        experiment = db.query(ExperimentRun).filter(ExperimentRun.id == experiment_id).first()
        if not experiment: return
        
        # We will loop through iterations and execute models in parallel for each iteration
        for iterate in range(iterations):
            tasks = []
            # Schedule generation for each model parallelly
            for model_id in models:
                tasks.append(execute_model_evaluation(model_id, task, experiment_id, db))
            
            await asyncio.gather(*tasks)
            
        experiment.status = "completed"
        db.commit()
        logger.info(f"Experiment {experiment_id} successfully completed {iterations} iterations.")
    except Exception as e:
        logger.error(f"Experiment {experiment_id} failed: {e}")
        db.rollback()
        experiment = db.query(ExperimentRun).filter(ExperimentRun.id == experiment_id).first()
        if experiment:
            experiment.status = "failed"
            db.commit()
    finally:
        db.close()

async def execute_model_evaluation(model_id: str, prompt: str, experiment_id: int, db: Session):
    try:
        # 1. Generation (via InferenceOptimization Layer)
        from inference.router import InferenceRouter
        response_text, token_count, latency = await InferenceRouter.process_request(prompt, model_id, client_id=f"exp_{experiment_id}")
        
        # 2. Evaluation
        scores = await judge_engine.evaluate(prompt, response_text)
        
        # 3. Cost Tracking
        cost_per_1k = llm_manager.get_pricing(model_id)
        total_cost = (token_count / 1000.0) * cost_per_1k
        
        # 4. Save to DB
        result = BenchmarkResult(
            experiment_id=experiment_id,
            model_name=model_id,
            output=response_text,
            latency_ms=latency,
            token_count=token_count,
            cost=total_cost,
            score_correctness=scores["score_correctness"],
            score_clarity=scores["score_clarity"],
            score_reasoning=scores["score_reasoning"],
            confidence_score=scores["confidence_score"],
            hallucination_flag=scores["hallucination_flag"]
        )
        db.add(result)
        db.commit()
        
        # 5. MLOps Experiment Tracking
        log_experiment(
            run_id=f"exp_{experiment_id}_{model_id}_{int(time.time())}",
            task=prompt,
            model_name=model_id,
            output=response_text,
            scores=scores,
            latency=latency,
            status="success"
        )
    except Exception as e:
        logger.error(f"Failed model evaluation for {model_id} on exp {experiment_id}: {e}")
        log_experiment(
            run_id=f"exp_{experiment_id}_{model_id}_{int(time.time())}",
            task=prompt,
            model_name=model_id,
            output=str(e),
            scores={},
            latency=0.0,
            status="failed"
        )

@router.get("/experiments/{experiment_id}")
def get_experiment_status(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(ExperimentRun).filter(ExperimentRun.id == experiment_id).first()
    if not exp: return {"error": "Not found"}
    
    results = db.query(BenchmarkResult).filter(BenchmarkResult.experiment_id == experiment_id).all()
    
    return {
        "status": exp.status,
        "results": results
    }

@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    # Simple unoptimized overview mapping models to avg correctness and totals
    from sqlalchemy import func
    
    stats = db.query(
        BenchmarkResult.model_name,
        func.avg(BenchmarkResult.score_correctness).label('avg_correctness'),
        func.avg(BenchmarkResult.latency_ms).label('avg_latency'),
        func.sum(BenchmarkResult.cost).label('total_cost'),
        func.avg(BenchmarkResult.hallucination_flag).label('avg_hallucination_rate')
    ).group_by(BenchmarkResult.model_name).all()
    
    board = []
    for stat in stats:
        board.append({
            "model": stat.model_name,
            "avg_correctness": round(stat.avg_correctness or 0, 2),
            "avg_latency": round(stat.avg_latency or 0, 2),
            "total_cost": round(stat.total_cost or 0, 6),
            "avg_hallucination_rate": round(stat.avg_hallucination_rate or 0, 2),
        })
        
    return {"leaderboard": sorted(board, key=lambda x: x["avg_correctness"], reverse=True)}

@router.get("/models")
def get_models():
    # Helper for frontend forms
    return {"models": list(llm_manager.models_config.keys())}
