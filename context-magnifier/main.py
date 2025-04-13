import asyncio
from app.main_window import run_main_window
from app.zoom_window import run_zoom_window

# async def main():
#     main_win_task = asyncio.create_task(run_main_window())
#     zoom_win_task = asyncio.create_task(run_zoom_window())

#     await zoom_win_task
#     await main_win_task

if __name__ == "__main__":
    # asyncio.run(main()) 
    asyncio.run(run_zoom_window())
    asyncio.run(run_main_window())
