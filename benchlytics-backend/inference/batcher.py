import asyncio
import logging
from typing import List, Tuple
from models.llm_manager import llm_manager

logger = logging.getLogger(__name__)

class DynamicBatcher:
    def __init__(self, max_batch_size: int = 16, batch_window_ms: int = 50):
        self.max_size = max_batch_size
        self.window = batch_window_ms / 1000.0
        # self.queues will map model_id to its specific queue
        self.queues = {}
        self.tasks = {}
        
    def _get_queue(self, model_id: str) -> asyncio.Queue:
        if model_id not in self.queues:
            self.queues[model_id] = asyncio.Queue()
            self.tasks[model_id] = asyncio.create_task(self._process_loop(model_id))
        return self.queues[model_id]

    async def add_request(self, prompt: str, model_id: str) -> tuple:
        """Adds request to queue and awaits future. Returns (response_text, token_count, latency)"""
        future = asyncio.get_event_loop().create_future()
        queue = self._get_queue(model_id)
        await queue.put((prompt, future))
        return await future

    async def _process_loop(self, model_id: str):
        queue = self.queues[model_id]
        while True:
            batch = []
            try:
                # Wait infinitely for the first item
                item = await queue.get()
                batch.append(item)
                
                # First item acquired, open the window
                end_time = asyncio.get_event_loop().time() + self.window
                while len(batch) < self.max_size:
                    time_left = end_time - asyncio.get_event_loop().time()
                    if time_left <= 0:
                        break
                    
                    try:
                        next_item = await asyncio.wait_for(queue.get(), timeout=time_left)
                        batch.append(next_item)
                    except asyncio.TimeoutError:
                        break
                        
                # Process the grouped batch
                asyncio.create_task(self._execute_batch(model_id, batch))
                
            except Exception as e:
                logger.error(f"Batch processing error for {model_id}: {e}")

    async def _execute_batch(self, model_id: str, batch: List[tuple]):
        prompts = [item[0] for item in batch]
        futures = [item[1] for item in batch]
        
        try:
            # We concurrently execute them unless the model supports actual batch API.
            # Using asyncio.gather here simulates parallel batch requests to vendors.
            tasks = [llm_manager.generate_response(model_id, p) for p in prompts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for future, res in zip(futures, results):
                if isinstance(res, Exception):
                    future.set_exception(res)
                else:
                    future.set_result(res)
        except Exception as e:
            logger.error(f"Failed to execute batch for {model_id}: {e}")
            for f in futures:
                if not f.done():
                    f.set_exception(e)
