"""
Standalone test for EXA Deep Researcher orchestrator
Tests the research workflow without LiveKit dependencies
"""
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-orchestrator")

# Load environment - try current directory first, then parent directories
load_dotenv(dotenv_path=Path(__file__).parent / '.env')
if not os.environ.get("EXA_API_KEY"):
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

# Mock JobContext for testing
class MockJobContext:
    """Mock JobContext for testing"""
    def __init__(self):
        self.room = None

# Import after env is loaded
from agent.exa_client import EXAClient
from orchestrator import ResearchOrchestrator
from livekit.plugins import openai

async def test_exa_connection():
    """Test EXA API connection"""
    logger.info("=" * 60)
    logger.info("TEST 1: EXA API Connection")
    logger.info("=" * 60)
    
    try:
        client = EXAClient(api_key=os.environ.get("EXA_API_KEY"))
        logger.info("EXA client initialized")
        
        # Test search
        from schemas import EXASearchParams
        params = EXASearchParams(
            query="artificial intelligence",
            num_results=3
        )
        
        results = await client.search(params)
        logger.info(f"Search returned {len(results)} results")
        
        if results:
            logger.info(f"  First result: {results[0].title[:60]}...")
            logger.info(f"  URL: {results[0].url}")
        
        return True
        
    except Exception as e:
        logger.error(f"EXA connection test failed: {e}")
        return False


async def test_brief_generation():
    """Test research brief generation"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Brief Generation")
    logger.info("=" * 60)
    
    try:
        # Create mock context
        ctx = MockJobContext()
        
        # Create clients
        exa_client = EXAClient(api_key=os.environ.get("EXA_API_KEY"))
        llm = openai.LLM(model="gpt-4o-mini")
        
        # Create orchestrator
        orchestrator = ResearchOrchestrator(
            ctx=ctx,
            exa_client=exa_client,
            llm=llm,
        )
        
        # Test brief generation
        query = "What are the latest developments in quantum computing?"
        brief, title = await orchestrator.write_brief("test-123", query)
        
        logger.info(f"Brief generated")
        logger.info(f"  Title: {title}")
        logger.info(f"  Brief: {brief[:200]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Brief generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_subtopic_decomposition():
    """Test research decomposition into subtopics"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Subtopic Decomposition")
    logger.info("=" * 60)
    
    try:
        # Create mock context
        ctx = MockJobContext()
        
        # Create clients
        exa_client = EXAClient(api_key=os.environ.get("EXA_API_KEY"))
        llm = openai.LLM(model="gpt-4o-mini")
        
        # Create orchestrator
        orchestrator = ResearchOrchestrator(
            ctx=ctx,
            exa_client=exa_client,
            llm=llm,
        )
        
        # Test decomposition
        brief = "Research the impact of artificial intelligence on healthcare, focusing on diagnostic accuracy and patient outcomes"
        subtopics = await orchestrator.supervise("test-123", brief)
        
        logger.info(f"Decomposed into {len(subtopics)} subtopics:")
        for i, topic in enumerate(subtopics, 1):
            logger.info(f"  {i}. {topic}")
        
        return True
        
    except Exception as e:
        logger.error(f"Subtopic decomposition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_research_workflow():
    """Test complete research workflow"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Full Research Workflow (Mini)")
    logger.info("=" * 60)
    
    try:
        # Create mock context
        ctx = MockJobContext()
        
        # Create clients
        exa_client = EXAClient(api_key=os.environ.get("EXA_API_KEY"))
        llm = openai.LLM(model="gpt-4o-mini")
        
        # Status callback
        async def status_cb(request_id, phase, title, message, stats):
            logger.info(f"  [{phase}] {title}: {message}")
        
        # Notes callback
        async def notes_cb(request_id, note):
            logger.info(f"  [NOTE] {note.subtopic}: {len(note.citations)} citations")
        
        # Report callback
        async def report_cb(request_id, title, report, num_sources):
            logger.info(f"  [REPORT] {title} - {len(report)} chars, {num_sources} sources")
        
        # Create orchestrator
        orchestrator = ResearchOrchestrator(
            ctx=ctx,
            exa_client=exa_client,
            llm=llm,
            status_callback=status_cb,
            notes_callback=notes_cb,
            report_callback=report_cb,
        )
        
        # Override max iterations for quick test
        orchestrator.max_iterations = 2
        orchestrator.max_results_per_search = 5
        
        # Run workflow
        query = "CRISPR gene editing applications"
        
        logger.info(f"Query: {query}")
        
        # Step 1: Brief
        brief, title = await orchestrator.write_brief("test-123", query)
        logger.info(f"Brief: {title}")
        
        # Step 2: Decompose
        subtopics = await orchestrator.supervise("test-123", brief)
        logger.info(f"Subtopics: {len(subtopics)}")
        
        # Step 3: Research first subtopic only (for speed)
        if subtopics:
            note = await orchestrator.research_subtopic("test-123", subtopics[0], 0)
            logger.info(f"Research note: {len(note.summary_markdown)} chars")
            logger.info(f"  Citations: {len(note.citations)}")
            
            # Step 4: Generate mini report
            notes = [note]
            report = await orchestrator.generate_final_report(
                "test-123",
                title,
                brief,
                notes
            )
            logger.info(f"Final report: {len(report)} chars")
            logger.info(f"\nReport preview:\n{report[:500]}...\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("Starting EXA Deep Researcher Tests")
    logger.info(f"EXA_API_KEY: {'Set' if os.environ.get('EXA_API_KEY') else 'Missing'}")
    logger.info(f"OPENAI_API_KEY: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Missing'}")
    
    if not os.environ.get("EXA_API_KEY"):
        logger.error("EXA_API_KEY not set! Please set it in .env file")
        return 1
    
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set! Skipping LLM-dependent tests")
        logger.info("Set OPENAI_API_KEY in .env to run full tests")
    
    results = []
    
    # Run tests
    results.append(("EXA Connection", await test_exa_connection()))
    
    # Only run LLM tests if OPENAI_API_KEY is set
    if os.environ.get("OPENAI_API_KEY"):
        results.append(("Brief Generation", await test_brief_generation()))
        results.append(("Subtopic Decomposition", await test_subtopic_decomposition()))
        results.append(("Full Workflow", await test_full_research_workflow()))
    else:
        logger.warning("Skipping LLM-dependent tests (OPENAI_API_KEY not set)")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

