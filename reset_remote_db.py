import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    print("=== Remote Database Reset Tool ===")
    url = input("Please paste your exact DATABASE_URL from your Railway Dashboard here:\n> ").strip()
    
    if not url:
        print("No URL provided. Exiting.")
        return
        
    # Format the URL exactly like your app does
    if "?" in url and "sslmode" in url:
        url = url.split("?")[0]
        
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"\nConnecting and dropping old tables...")
    try:
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE;"))
            await conn.execute(text("CREATE SCHEMA public;"))
            print("SUCCESS! All old 'uuid' tables have been wiped.")
            print("Go to Railway and Redeploy your API. It will recreate the fresh 'integer' tables automatically.")
        await engine.dispose()
    except Exception as e:
        print(f"\nError connecting to database: {e}")

if __name__ == "__main__":
    asyncio.run(main())
