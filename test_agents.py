#!/usr/bin/env python3
"""
Test NBA Simulator Agents - Phase 3 Verification
"""

def test_agent_imports():
    """Test that all agents can be imported"""
    print("=" * 60)
    print("TESTING AGENT IMPORTS")
    print("=" * 60)
    
    try:
        from nba_simulator.agents import (
            BaseAgent,
            AgentState,
            AgentPriority,
            AgentMetrics,
            MasterAgent,
            QualityAgent,
            IntegrationAgent,
            NBAStatsAgent,
            DeduplicationAgent,
            HistoricalAgent,
            HooprAgent,
            BasketballReferenceAgent,
            ExecutionPhase,
            QualityCheck,
            IntegrationMatch,
            ConflictResolution,
            BBRefTier,
        )
        print("✅ All agent imports successful!")
        print(f"  - BaseAgent: {BaseAgent.__name__}")
        print(f"  - MasterAgent: {MasterAgent.__name__}")
        print(f"  - QualityAgent: {QualityAgent.__name__}")
        print(f"  - IntegrationAgent: {IntegrationAgent.__name__}")
        print(f"  - NBAStatsAgent: {NBAStatsAgent.__name__}")
        print(f"  - DeduplicationAgent: {DeduplicationAgent.__name__}")
        print(f"  - HistoricalAgent: {HistoricalAgent.__name__}")
        print(f"  - HooprAgent: {HooprAgent.__name__}")
        print(f"  - BasketballReferenceAgent: {BasketballReferenceAgent.__name__}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enum_types():
    """Test enum types"""
    print("\n" + "=" * 60)
    print("TESTING ENUM TYPES")
    print("=" * 60)
    
    try:
        from nba_simulator.agents import (
            AgentState,
            AgentPriority,
            ExecutionPhase,
            QualityCheck,
            ConflictResolution,
            BBRefTier
        )
        
        print(f"✅ AgentState values: {[s.value for s in AgentState]}")
        print(f"✅ AgentPriority values: {[p.value for p in AgentPriority]}")
        print(f"✅ ExecutionPhase values: {[e.value for e in ExecutionPhase]}")
        print(f"✅ QualityCheck values: {[q.value for q in QualityCheck]}")
        print(f"✅ ConflictResolution values: {[c.value for c in ConflictResolution]}")
        print(f"✅ BBRefTier values: {[t.value for t in BBRefTier]}")
        return True
    except Exception as e:
        print(f"❌ Enum test failed: {e}")
        return False


def test_base_agent():
    """Test BaseAgent abstract class"""
    print("\n" + "=" * 60)
    print("TESTING BASE AGENT")
    print("=" * 60)
    
    try:
        from nba_simulator.agents import BaseAgent, AgentState, AgentPriority
        
        # Check BaseAgent has required methods
        required_methods = [
            'initialize',
            'execute',
            'cleanup',
            'health_check',
            'get_state',
            'generate_report'
        ]
        
        for method in required_methods:
            if hasattr(BaseAgent, method):
                print(f"✅ BaseAgent.{method} exists")
            else:
                print(f"❌ BaseAgent.{method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ BaseAgent test failed: {e}")
        return False


def test_master_agent_instantiation():
    """Test MasterAgent can be created"""
    print("\n" + "=" * 60)
    print("TESTING MASTER AGENT INSTANTIATION")
    print("=" * 60)
    
    try:
        from nba_simulator.agents import MasterAgent, AgentState
        
        # Create MasterAgent
        config = {
            'max_retries': 3,
            'timeout_seconds': 300,
            'enable_reporting': True
        }
        
        master = MasterAgent(config=config)
        
        print(f"✅ MasterAgent created: {master.__class__.__name__}")
        print(f"  - Agent ID: {master.agent_id}")
        print(f"  - State: {master.state}")
        print(f"  - Config: {master.config}")
        
        # Test initialize
        master.initialize()
        print(f"✅ MasterAgent initialized")
        print(f"  - State after init: {master.state}")
        
        return True
    except Exception as e:
        print(f"❌ MasterAgent instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_agent():
    """Test QualityAgent"""
    print("\n" + "=" * 60)
    print("TESTING QUALITY AGENT")
    print("=" * 60)
    
    try:
        from nba_simulator.agents import QualityAgent, QualityCheck
        
        config = {
            'min_quality_score': 85.0,
            'enable_strict_mode': False
        }
        
        quality = QualityAgent(config=config)
        print(f"✅ QualityAgent created: {quality.__class__.__name__}")
        print(f"  - Agent ID: {quality.agent_id}")
        print(f"  - Min quality score: {config['min_quality_score']}")
        
        # Check QualityCheck enum
        print(f"✅ QualityCheck types: {[q.value for q in QualityCheck]}")
        
        return True
    except Exception as e:
        print(f"❌ QualityAgent test failed: {e}")
        return False


def test_file_structure():
    """Verify agent file structure"""
    print("\n" + "=" * 60)
    print("TESTING FILE STRUCTURE")
    print("=" * 60)
    
    from pathlib import Path
    
    agents_dir = Path("nba_simulator/agents")
    expected_files = [
        "__init__.py",
        "base_agent.py",
        "master.py",
        "quality.py",
        "integration.py",
        "nba_stats.py",
        "deduplication.py",
        "historical.py",
        "hoopr.py",
        "bbref.py"
    ]
    
    all_exist = True
    total_size = 0
    
    for filename in expected_files:
        filepath = agents_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            print(f"✅ {filename} ({size:,} bytes)")
        else:
            print(f"❌ {filename} MISSING")
            all_exist = False
    
    print(f"\n✅ Total: {len(expected_files)} files, {total_size:,} bytes ({total_size/1024:.1f} KB)")
    
    return all_exist


def test_agent_registration():
    """Test agent registration with MasterAgent"""
    print("\n" + "=" * 60)
    print("TESTING AGENT REGISTRATION")
    print("=" * 60)
    
    try:
        from nba_simulator.agents import (
            MasterAgent,
            QualityAgent,
            IntegrationAgent,
            NBAStatsAgent
        )
        
        # Create master agent
        master = MasterAgent(config={'max_retries': 3})
        master.initialize()
        
        # Create and register child agents
        quality = QualityAgent(config={'min_quality_score': 85.0})
        integration = IntegrationAgent(config={})
        nba_stats = NBAStatsAgent(config={})
        
        # Register agents
        master.register_agent(quality)
        master.register_agent(integration)
        master.register_agent(nba_stats)
        
        print(f"✅ Registered 3 agents with MasterAgent")
        print(f"  - QualityAgent: {quality.agent_id}")
        print(f"  - IntegrationAgent: {integration.agent_id}")
        print(f"  - NBAStatsAgent: {nba_stats.agent_id}")
        
        return True
    except Exception as e:
        print(f"❌ Agent registration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 NBA SIMULATOR AGENTS TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Agent Imports", test_agent_imports()))
    results.append(("Enum Types", test_enum_types()))
    results.append(("Base Agent", test_base_agent()))
    results.append(("File Structure", test_file_structure()))
    results.append(("Master Agent", test_master_agent_instantiation()))
    results.append(("Quality Agent", test_quality_agent()))
    results.append(("Agent Registration", test_agent_registration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Agent system verified!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
