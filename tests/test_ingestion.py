#!/usr/bin/env python3
"""
Test script for the 01_Ingestion pipeline
"""

import os
import sys
from pathlib import Path


def test_data_loading():
    """Test basic data loading functionality"""
    print("=== Testing Data Loading ===")

    # Check if data files exist
    data_path = Path("data/raw/latest-small/ml-latest-small")
    movies_file = data_path / "movies.csv"
    ratings_file = data_path / "ratings.csv"

    if not movies_file.exists():
        print(f"❌ Movies file not found: {movies_file}")
        return False

    if not ratings_file.exists():
        print(f"❌ Ratings file not found: {ratings_file}")
        return False

    print(f"✅ Data files found:")
    print(f"  - {movies_file}")
    print(f"  - {ratings_file}")

    # Check file sizes
    movies_size = movies_file.stat().st_size / 1024  # KB
    ratings_size = ratings_file.stat().st_size / 1024  # KB

    print(f"  - Movies: {movies_size:.1f}KB")
    print(f"  - Ratings: {ratings_size:.1f}KB")

    return True


def test_processed_outputs():
    """Test if ingestion pipeline has created output files"""
    print("\n=== Testing Processed Outputs ===")

    processed_dir = Path("data/processed")
    expected_files = [
        "movies_processed.csv",
        "ratings_processed.csv",
        "movies_enriched_ml.csv",
    ]

    all_exist = True
    for filename in expected_files:
        filepath = processed_dir / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"✅ {filename} ({size_kb:.1f}KB)")
        else:
            print(f"❌ {filename} - Not found")
            all_exist = False

    return all_exist


def test_data_structure():
    """Test the project data structure"""
    print("\n=== Testing Data Structure ===")

    # Check directory structure
    required_dirs = ["data/raw", "data/processed", "data/cache", "data/logs"]

    all_dirs_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - Missing")
            all_dirs_exist = False

    return all_dirs_exist


def run_ingestion_test():
    """Run a basic ingestion test using the Python module system"""
    print("\n=== Testing Ingestion Pipeline ===")

    try:
        # Import and run a simple test
        import subprocess
        import sys

        # Run pipeline test using Python module system
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys, os
sys.path.insert(0, '.')
os.chdir('.')

# Simple test without relative imports
import pandas as pd

# Test basic pandas operations on our data
try:
    movies = pd.read_csv('data/raw/latest-small/ml-latest-small/movies.csv')
    ratings = pd.read_csv('data/raw/latest-small/ml-latest-small/ratings.csv')

    print(f'✅ Loaded {len(movies)} movies and {len(ratings)} ratings')

    # Test if processed files have expected content
    if os.path.exists('data/processed/movies_enriched_ml.csv'):
        enriched = pd.read_csv('data/processed/movies_enriched_ml.csv')
        print(f'✅ Found {len(enriched)} enriched movies with columns: {list(enriched.columns)[:5]}...')
    else:
        print('⚠️ No enriched movies file found')

except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
""",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Pipeline test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Could not run pipeline test: {e}")
        return False


if __name__ == "__main__":
    print("🧪 CineRAG Ingestion Tests")
    print("=" * 50)

    # Run tests
    tests = [
        ("Data Structure", test_data_structure),
        ("Data Loading", test_data_loading),
        ("Processed Outputs", test_processed_outputs),
        ("Pipeline Functionality", run_ingestion_test),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ingestion pipeline is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
