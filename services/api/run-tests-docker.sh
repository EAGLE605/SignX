#!/bin/bash
# ============================================================================
# Test Runner Script - Run pytest in isolated Docker environment
# ============================================================================
#
# Usage:
#   ./run-tests-docker.sh                  # Run all tests
#   ./run-tests-docker.sh tests/unit/      # Run specific test directory
#   ./run-tests-docker.sh -k test_name     # Run tests matching name
#
# Environment:
#   BUILD_CACHE=0  # Force rebuild without cache
#
# Examples:
#   BUILD_CACHE=0 ./run-tests-docker.sh    # Rebuild and run all tests
#   ./run-tests-docker.sh tests/unit/ -v   # Run unit tests with verbose output
#
# ============================================================================

set -euo pipefail

# Configuration
IMAGE_NAME="signx-api-test"
IMAGE_TAG="latest"
CONTAINER_NAME="signx-api-test-runner"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Determine build cache option
BUILD_CACHE="${BUILD_CACHE:-1}"
if [ "$BUILD_CACHE" = "0" ]; then
    BUILD_ARGS="--no-cache"
    log_warn "Building without cache (BUILD_CACHE=0)"
else
    BUILD_ARGS=""
fi

# Build test image
log_info "Building test Docker image..."
docker build \
    $BUILD_ARGS \
    -f Dockerfile.test \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    .

if [ $? -ne 0 ]; then
    log_error "Docker build failed"
    exit 1
fi

log_info "Test image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"

# Remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_info "Removing existing container: ${CONTAINER_NAME}"
    docker rm -f "${CONTAINER_NAME}" > /dev/null 2>&1
fi

# Prepare test arguments
TEST_ARGS="$@"
if [ -z "$TEST_ARGS" ]; then
    TEST_ARGS="tests/"
    log_info "No test path specified, running all tests in tests/"
fi

# Run tests in Docker container
log_info "Running tests with args: ${TEST_ARGS}"
echo ""
echo "========================================================================"
echo " Running pytest in isolated Docker environment"
echo "========================================================================"
echo ""

docker run \
    --name "${CONTAINER_NAME}" \
    --rm \
    -e PYTHONHASHSEED=0 \
    -e TESTING=1 \
    -e DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test_db" \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    pytest ${TEST_ARGS}

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    log_info "✅ All tests passed!"
else
    log_error "❌ Tests failed with exit code: ${EXIT_CODE}"
fi

exit $EXIT_CODE
