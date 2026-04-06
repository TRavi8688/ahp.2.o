import os
import sys
import asyncio

# Ensure the root directory is in the path
sys.path.append(os.getcwd())

from arq import run_worker
from app.workers.arq_worker import WorkerSettings

if __name__ == "__main__":
    print("Starting AHP 2.0 ARQ AI Worker (Enterprise Edition)...")
    try:
        # Python 3.14 FIX: Manually create and set the event loop before calling run_worker.
        # This satisfies arq's internal call to asyncio.get_event_loop() 
        # without triggering the "Loop already running" error from asyncio.run().
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        run_worker(WorkerSettings)
    except KeyboardInterrupt:
        print("\nWorker stopped by user.")
    except Exception as e:
        print(f"\nCRITICAL WORKER ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
