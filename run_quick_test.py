#!/usr/bin/env python3
"""
Standalone script to run the quick flow test with proper path setup
Now supports testing smart file type routing
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can import the test
from tests.test_quick_flow import run_quick_tests, TestQuickFlow

def run_smart_routing_test():
    """Run a focused test on smart file type routing"""
    print("🚀 SMART FILE TYPE ROUTING TEST")
    print("=" * 50)
    
    tester = TestQuickFlow()
    
    # Step 1: Signup
    print("\n📝 STEP 1: User Registration")
    if not tester.test_signup_with_alias_email():
        print("❌ Signup failed - cannot proceed")
        return False
    
    # Step 2: Test smart routing with both file types
    print("\n🔀 STEP 2: Smart File Type Routing Test")
    routing_results = tester.test_smart_routing_with_both_file_types()
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 SMART ROUTING TEST RESULTS")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for file_type, result in routing_results.items():
        total_tests += 1
        if result is True:
            print(f"✅ {file_type.upper()} file routing: PASS")
            passed_tests += 1
        elif result is False:
            print(f"❌ {file_type.upper()} file routing: FAIL")
        else:
            print(f"⚠️  {file_type.upper()} file routing: SKIPPED (file not found)")
    
    if passed_tests == total_tests and total_tests > 0:
        print(f"\n🎉 ALL ROUTING TESTS PASSED! ({passed_tests}/{total_tests})")
        print("\n✅ Smart routing working correctly:")
        if 'audio' in routing_results and routing_results['audio']:
            print("   • Audio files routed to direct processing")
        if 'video' in routing_results and routing_results['video']:
            print("   • Video files routed to extraction pipeline")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed or skipped")
        print("   📁 Make sure test_audio.mp3 and test_audio.mp4 exist in project root")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--routing":
        # Run focused smart routing test
        run_smart_routing_test()
    else:
        # Run complete test suite
        print("💡 TIP: Use '--routing' flag to test smart routing specifically")
        print("    Example: python run_quick_test.py --routing")
        print()
        run_quick_tests()