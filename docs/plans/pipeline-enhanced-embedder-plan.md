# Enhanced Embedder Retry Logic - GOAP Implementation Plan

## Executive Summary

This document outlines a Goal-Oriented Action Planning (GOAP) approach to enhance the retry logic in `src/agents/pipeline/embedder.py`. The enhancement will implement a simplified 3-retry mechanism with exponential backoff (1s, 2s, 4s) and comprehensive error logging while maintaining backward compatibility.

---

## GOAP State Analysis

### Current State (What IS True Now)

**Existing Capabilities:**
- ✅ Retry logic exists with exponential backoff
- ✅ Current max_retries configurable (default: 5)
- ✅ Handles RateLimitError, APIError, and APIConnectionError
- ✅ Exponential backoff formula: `initial_delay * (2 ** retry_count)`
- ✅ Max delay cap exists (60s default)
- ✅ Basic logging on warnings and errors
- ✅ Returns success=False with error message on failure
- ✅ Comprehensive test coverage exists

**Current Retry Behavior:**
```python
# Lines 145-209: _embed_batch_with_retry method
- Retries up to max_retries (default: 5)
- Initial delay: 1.0s (configurable)
- Max delay: 60.0s (configurable)
- Logs: "Rate limit hit. Retrying in {delay}s (attempt X/Y)"
- Logs: "API error: {error}. Retrying in {delay}s (attempt X/Y)"
- Raises exception after max retries exceeded
```

**Current Limitations:**
- ❌ Default max_retries=5 exceeds requirement of 3
- ❌ Retry delays not fixed to 1s, 2s, 4s (calculated dynamically)
- ❌ Logging doesn't include all required details (error type, full error message)
- ❌ No structured error details in final failure response
- ❌ Exception raised instead of clean error response

### Goal State (What SHOULD Be True)

**Target Capabilities:**
- ✅ Exactly 3 retry attempts maximum
- ✅ Fixed exponential backoff: 1s, 2s, 4s
- ✅ Detailed logging per retry: attempt number, error type, error message, wait time
- ✅ Comprehensive error response with all retry details
- ✅ Clean error handling without raising exceptions
- ✅ Backward compatibility maintained
- ✅ All existing tests pass
- ✅ New tests validate enhanced behavior

**Enhanced Retry Behavior:**
```python
# Target implementation
- Retries: exactly 3 attempts
- Delays: [1.0, 2.0, 4.0] seconds (fixed)
- Enhanced logging per attempt:
  * Attempt number (1/3, 2/3, 3/3)
  * Error type (RateLimitError, APIError, etc.)
  * Full error message
  * Wait time before retry
- Final failure response includes:
  * success: False
  * error: Main error message
  * error_details: {
      retry_count: int,
      last_error_type: str,
      last_error_message: str,
      retry_delays: List[float]
    }
```

---

## GOAP Action Plan

### Phase 1: Configuration Enhancement

**Action 1.1: Update EmbeddingConfig Defaults**

**Preconditions:**
- EmbeddingConfig dataclass exists (line 49-58)
- Current max_retries=5, initial_retry_delay=1.0

**Effects:**
- max_retries changed to 3
- Adds retry_delays field with [1.0, 2.0, 4.0]
- Maintains backward compatibility via optional parameters

**Implementation:**
```python
@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    batch_size: int = 100
    max_retries: int = 3  # Changed from 5
    retry_delays: List[float] = None  # New field
    initial_retry_delay: float = 1.0  # Deprecated but maintained
    max_retry_delay: float = 60.0  # Deprecated but maintained
    timeout: int = 30

    def __post_init__(self):
        """Initialize retry_delays if not provided"""
        if self.retry_delays is None:
            self.retry_delays = [1.0, 2.0, 4.0]
```

**Cost:** 1 unit (low complexity)
**Risk:** Low (backward compatible)

---

**Action 1.2: Add Error Details Structure**

**Preconditions:**
- Need structured error response format

**Effects:**
- Creates RetryErrorDetails dataclass
- Enables comprehensive error reporting

**Implementation:**
```python
@dataclass
class RetryErrorDetails:
    """Details about retry attempts"""
    retry_count: int
    last_error_type: str
    last_error_message: str
    retry_delays: List[float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'retry_count': self.retry_count,
            'last_error_type': self.last_error_type,
            'last_error_message': self.last_error_message,
            'retry_delays': self.retry_delays
        }
```

**Cost:** 1 unit (low complexity)
**Risk:** None (new addition)

---

### Phase 2: Enhanced Retry Logic

**Action 2.1: Refactor _embed_batch_with_retry Method**

**Preconditions:**
- Current method exists (lines 145-209)
- Uses recursive retry with dynamic delay calculation
- Raises exceptions on max retries

**Effects:**
- Uses fixed retry_delays list
- Collects all retry attempt details
- Returns tuple (embeddings, error_details) instead of raising
- Enhanced logging with all required information

**Implementation:**
```python
def _embed_batch_with_retry(
    self,
    texts: List[str],
    retry_count: int = 0,
    retry_history: Optional[List[Dict[str, Any]]] = None
) -> tuple[Optional[List[List[float]]], Optional[RetryErrorDetails]]:
    """
    Embed a batch of texts with enhanced retry logic.

    Args:
        texts: List of text strings to embed
        retry_count: Current retry attempt number
        retry_history: History of retry attempts

    Returns:
        Tuple of (embeddings, error_details)
        - embeddings: List of vectors or None on failure
        - error_details: RetryErrorDetails or None on success
    """
    if retry_history is None:
        retry_history = []

    try:
        response = self.client.embeddings.create(
            input=texts,
            model=self.config.model,
            dimensions=self.config.dimensions
        )

        embeddings = [item.embedding for item in response.data]
        logger.info(f"Successfully embedded {len(texts)} texts")
        return embeddings, None

    except (RateLimitError, APIError, APIConnectionError) as e:
        error_type = type(e).__name__
        error_message = str(e)

        # Log the error
        logger.warning(
            f"Embedding API error on attempt {retry_count + 1}: "
            f"type={error_type}, message={error_message}"
        )

        # Check if we can retry
        if retry_count >= self.config.max_retries:
            # Max retries exceeded
            logger.error(
                f"Max retries ({self.config.max_retries}) exceeded. "
                f"Total attempts: {retry_count + 1}"
            )

            error_details = RetryErrorDetails(
                retry_count=retry_count,
                last_error_type=error_type,
                last_error_message=error_message,
                retry_delays=[h['delay'] for h in retry_history]
            )
            return None, error_details

        # Calculate delay from fixed list
        delay = self.config.retry_delays[retry_count]

        # Log retry attempt with full details
        logger.warning(
            f"Retry attempt {retry_count + 1}/{self.config.max_retries}: "
            f"error_type={error_type}, "
            f"error_message={error_message}, "
            f"wait_time={delay}s"
        )

        # Record this attempt
        retry_history.append({
            'attempt': retry_count + 1,
            'error_type': error_type,
            'error_message': error_message,
            'delay': delay
        })

        # Wait before retry
        time.sleep(delay)

        # Recursive retry
        return self._embed_batch_with_retry(
            texts,
            retry_count + 1,
            retry_history
        )
```

**Cost:** 3 units (moderate complexity)
**Risk:** Medium (changes core retry logic)

---

**Action 2.2: Update _process_batch Method**

**Preconditions:**
- _process_batch calls _embed_batch_with_retry (line 227)
- Expects list of vectors returned

**Effects:**
- Handles new tuple return type (embeddings, error_details)
- Propagates error details to caller
- Maintains existing functionality

**Implementation:**
```python
def _process_batch(
    self,
    batch: List[Chunk]
) -> tuple[Optional[List[Embedding]], Optional[RetryErrorDetails]]:
    """
    Process a single batch of chunks.

    Args:
        batch: List of chunks to embed

    Returns:
        Tuple of (embeddings, error_details)
    """
    start_time = time.time()

    # Extract texts
    texts = [chunk.text for chunk in batch]

    # Get embeddings with retry logic
    vectors, error_details = self._embed_batch_with_retry(texts)

    if vectors is None:
        # Retry failed
        logger.error(f"Failed to process batch of {len(batch)} chunks")
        return None, error_details

    # Create Embedding objects
    embeddings = []
    for chunk, vector in zip(batch, vectors):
        embeddings.append(Embedding(
            chunk_id=chunk.chunk_id,
            vector=vector,
            model=self.config.model,
            dimensions=len(vector)
        ))

    elapsed = time.time() - start_time
    avg_time = elapsed / len(batch)

    logger.info(
        f"Processed batch of {len(batch)} chunks in {elapsed:.2f}s "
        f"({avg_time:.3f}s per embedding)"
    )

    return embeddings, None
```

**Cost:** 2 units (moderate complexity)
**Risk:** Medium (changes method signature)

---

**Action 2.3: Update process Method**

**Preconditions:**
- process method calls _process_batch (line 291)
- Currently catches all exceptions generically

**Effects:**
- Handles partial batch failures
- Returns comprehensive error details
- Maintains backward-compatible response format

**Implementation:**
```python
def process(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process chunks and generate embeddings.

    Args:
        chunks: List of chunk dictionaries with 'chunk_id' and 'text' fields

    Returns:
        Dictionary with success status, embeddings, and error details
    """
    if not chunks:
        logger.warning("No chunks provided")
        return {
            'success': True,
            'embeddings': [],
            'metadata': {
                'total_chunks': 0,
                'total_batches': 0,
                'model': self.config.model
            }
        }

    try:
        # Convert to Chunk objects
        chunk_objects = [Chunk.from_dict(c) for c in chunks]

        # Validate chunks
        for chunk in chunk_objects:
            if not chunk.text:
                raise ValueError(f"Chunk {chunk.chunk_id} has no text content")

        # Batch chunks
        batches = self._batch_chunks(chunk_objects)
        logger.info(
            f"Processing {len(chunk_objects)} chunks in {len(batches)} batches "
            f"(batch_size={self.config.batch_size})"
        )

        # Process batches
        all_embeddings = []
        failed_batches = []

        for i, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {i}/{len(batches)}")
            batch_embeddings, error_details = self._process_batch(batch)

            if batch_embeddings is None:
                # Batch failed after all retries
                failed_batches.append({
                    'batch_number': i,
                    'chunk_count': len(batch),
                    'error_details': error_details.to_dict() if error_details else {}
                })
                logger.error(
                    f"Batch {i}/{len(batches)} failed after {error_details.retry_count} retries"
                )
            else:
                all_embeddings.extend(batch_embeddings)

        # Determine overall success
        success = len(failed_batches) == 0

        # Build response
        response = {
            'success': success,
            'embeddings': [emb.to_dict() for emb in all_embeddings],
            'metadata': {
                'total_chunks': len(chunk_objects),
                'total_batches': len(batches),
                'successful_batches': len(batches) - len(failed_batches),
                'failed_batches': len(failed_batches),
                'model': self.config.model,
                'dimensions': self.config.dimensions
            }
        }

        if not success:
            response['error'] = f"{len(failed_batches)} batch(es) failed after retries"
            response['error_details'] = {
                'failed_batch_count': len(failed_batches),
                'failed_batches': failed_batches
            }

        return response

    except Exception as e:
        logger.error(f"Error processing chunks: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'embeddings': [],
            'error_details': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }
```

**Cost:** 3 units (moderate complexity)
**Risk:** Medium (changes response structure)

---

### Phase 3: Testing & Validation

**Action 3.1: Update Existing Tests**

**Preconditions:**
- Test file exists at tests/test_embedder.py
- Current tests expect exceptions on failure
- Tests verify exponential backoff calculation

**Effects:**
- Tests updated for new return signature
- Tests validate error_details structure
- Tests verify fixed retry delays

**Changes Required:**

1. **test_embed_batch_success** (line 132-153)
   - Update to handle tuple return: `embeddings, error_details = agent._embed_batch_with_retry(texts)`
   - Assert `error_details is None`

2. **test_embed_batch_rate_limit_retry** (line 157-179)
   - Update to handle tuple return
   - Verify error_details is None on success after retry

3. **test_embed_batch_max_retries_exceeded** (line 183-197)
   - Change from `assertRaises` to checking return value
   - Verify `embeddings is None`
   - Verify `error_details is not None`
   - Assert error_details contains correct retry_count, error_type, etc.

4. **test_exponential_backoff_calculation** (line 271-295)
   - Update to verify fixed delays [1.0, 2.0, 4.0]
   - Remove dynamic calculation assertions

**Cost:** 2 units (test updates)
**Risk:** Low (improves test coverage)

---

**Action 3.2: Add New Enhanced Retry Tests**

**Preconditions:**
- Updated implementation exists

**Effects:**
- Validates exact retry behavior
- Tests comprehensive error details
- Ensures backward compatibility

**New Tests:**

```python
@patch('agents.pipeline.embedder.OpenAI')
@patch('time.sleep')
def test_enhanced_retry_with_fixed_delays(self, mock_sleep, mock_openai):
    """Test that retry delays are exactly [1.0, 2.0, 4.0]"""
    mock_client = Mock()
    mock_client.embeddings.create.side_effect = RateLimitError('Rate limit')
    mock_openai.return_value = mock_client

    agent = EmbedderAgent()
    embeddings, error_details = agent._embed_batch_with_retry(['test'])

    # Verify failure
    self.assertIsNone(embeddings)
    self.assertIsNotNone(error_details)

    # Verify exact delays
    calls = [call[0][0] for call in mock_sleep.call_args_list]
    self.assertEqual(calls, [1.0, 2.0, 4.0])

    # Verify error details
    self.assertEqual(error_details.retry_count, 3)
    self.assertEqual(error_details.retry_delays, [1.0, 2.0, 4.0])
    self.assertEqual(error_details.last_error_type, 'RateLimitError')


@patch('agents.pipeline.embedder.OpenAI')
def test_enhanced_error_details_structure(self, mock_openai):
    """Test comprehensive error details in response"""
    mock_client = Mock()
    mock_client.embeddings.create.side_effect = APIError('API Error')
    mock_openai.return_value = mock_client

    agent = EmbedderAgent()
    chunks = [{'chunk_id': 'chunk-1', 'text': 'Test text'}]

    result = agent.process(chunks)

    # Verify failure response structure
    self.assertFalse(result['success'])
    self.assertIn('error', result)
    self.assertIn('error_details', result)

    # Verify error details content
    error_details = result['error_details']
    self.assertIn('failed_batch_count', error_details)
    self.assertIn('failed_batches', error_details)

    failed_batch = error_details['failed_batches'][0]
    self.assertIn('error_details', failed_batch)

    batch_error = failed_batch['error_details']
    self.assertEqual(batch_error['retry_count'], 3)
    self.assertEqual(batch_error['last_error_type'], 'APIError')
    self.assertEqual(batch_error['retry_delays'], [1.0, 2.0, 4.0])


@patch('agents.pipeline.embedder.OpenAI')
@patch('time.sleep')
def test_retry_logging_details(self, mock_sleep, mock_openai):
    """Test that retry logging includes all required details"""
    mock_client = Mock()
    mock_client.embeddings.create.side_effect = [
        RateLimitError('Rate limit exceeded'),
        Mock(data=[Mock(embedding=[0.1] * 1536)])
    ]
    mock_openai.return_value = mock_client

    agent = EmbedderAgent()

    with self.assertLogs(level='WARNING') as log_context:
        embeddings, error_details = agent._embed_batch_with_retry(['test'])

    # Verify success after retry
    self.assertIsNotNone(embeddings)
    self.assertIsNone(error_details)

    # Verify logging contains required details
    log_output = ' '.join(log_context.output)
    self.assertIn('Retry attempt 1/3', log_output)
    self.assertIn('error_type=RateLimitError', log_output)
    self.assertIn('wait_time=1.0s', log_output)


def test_backward_compatibility_with_old_config(self):
    """Test that old configuration style still works"""
    # Old style config without retry_delays
    config = EmbeddingConfig(
        max_retries=5,
        initial_retry_delay=2.0
    )

    # Should auto-initialize retry_delays
    self.assertEqual(config.retry_delays, [1.0, 2.0, 4.0])
    self.assertEqual(config.max_retries, 5)  # Still uses provided value
```

**Cost:** 2 units (new tests)
**Risk:** None (validation only)

---

### Phase 4: Documentation & Integration

**Action 4.1: Update Docstrings**

**Preconditions:**
- Code changes implemented
- New behavior defined

**Effects:**
- Clear documentation of retry behavior
- Updated method signatures documented
- Error response format documented

**Updates Required:**

1. Module docstring (lines 2-19): Add retry behavior details
2. EmbedderAgent class docstring (lines 96-105): Document enhanced retry
3. _embed_batch_with_retry docstring: Document new return type and error_details
4. process method docstring: Document error_details in response

**Cost:** 1 unit (documentation)
**Risk:** None

---

**Action 4.2: Update README/Documentation**

**Preconditions:**
- Implementation complete

**Effects:**
- Users understand new error response format
- Migration guide for existing users
- Examples of error handling

**Updates:**
- src/agents/pipeline/README.md: Add retry behavior section
- docs/agents/embedder-agent.md: Update with error handling examples

**Cost:** 1 unit (documentation)
**Risk:** None

---

## Success Criteria

### Functional Requirements

✅ **FR1: Exactly 3 Retry Attempts**
- Test: Verify max_retries = 3 in default config
- Test: Mock failures and count API call attempts (should be 4 total: initial + 3 retries)

✅ **FR2: Fixed Exponential Backoff [1s, 2s, 4s]**
- Test: Mock sleep() and verify exact delays
- Test: Verify retry_delays = [1.0, 2.0, 4.0] in config

✅ **FR3: Comprehensive Retry Logging**
- Test: Capture logs and verify presence of:
  - Attempt number (1/3, 2/3, 3/3)
  - Error type (RateLimitError, APIError, etc.)
  - Error message
  - Wait time (1.0s, 2.0s, 4.0s)

✅ **FR4: Detailed Error Response**
- Test: Verify error response includes:
  - success: False
  - error: error message
  - error_details: {retry_count, last_error_type, last_error_message, retry_delays}

✅ **FR5: Backward Compatibility**
- Test: All existing tests pass
- Test: Old configuration style works
- Test: Response format compatible with existing consumers

### Non-Functional Requirements

✅ **NFR1: Code Quality**
- All type hints present
- Docstrings updated
- Follows existing code style
- No linting errors

✅ **NFR2: Test Coverage**
- All new code paths tested
- Edge cases covered
- Integration tests pass
- Coverage ≥ 90%

✅ **NFR3: Performance**
- No performance degradation
- Retry delays accurate
- Logging overhead minimal

---

## Implementation Milestones

### Milestone 1: Configuration & Data Structures (Day 1)
- [ ] Update EmbeddingConfig with new defaults
- [ ] Add RetryErrorDetails dataclass
- [ ] Add __post_init__ for retry_delays
- [ ] Run existing tests (should still pass)

**Deliverable:** Updated configuration with backward compatibility

---

### Milestone 2: Core Retry Logic (Day 2)
- [ ] Refactor _embed_batch_with_retry with enhanced logging
- [ ] Change return type to tuple
- [ ] Implement fixed retry delay logic
- [ ] Collect and return error details

**Deliverable:** Enhanced retry method with comprehensive error handling

---

### Milestone 3: Integration (Day 2-3)
- [ ] Update _process_batch to handle new signature
- [ ] Update process method for batch failure handling
- [ ] Add error_details to response format
- [ ] Test end-to-end flow

**Deliverable:** Fully integrated enhanced retry logic

---

### Milestone 4: Testing (Day 3-4)
- [ ] Update existing tests for new signatures
- [ ] Add tests for fixed retry delays
- [ ] Add tests for error details structure
- [ ] Add tests for logging details
- [ ] Add backward compatibility tests
- [ ] Verify 100% of new code covered

**Deliverable:** Comprehensive test suite with ≥90% coverage

---

### Milestone 5: Documentation & Review (Day 4-5)
- [ ] Update all docstrings
- [ ] Update README files
- [ ] Add migration guide
- [ ] Code review
- [ ] Final testing

**Deliverable:** Production-ready enhanced embedder

---

## Testing Strategy

### Unit Tests

**Test Categories:**

1. **Configuration Tests**
   - Default retry_delays initialization
   - Custom retry_delays
   - Backward compatibility

2. **Retry Logic Tests**
   - Fixed delay sequence [1.0, 2.0, 4.0]
   - Max retries enforcement (3 attempts)
   - Success after partial retries
   - Different error types (RateLimitError, APIError, APIConnectionError)

3. **Error Details Tests**
   - RetryErrorDetails structure
   - Error details in batch failures
   - Error details in process response
   - Partial batch failure handling

4. **Logging Tests**
   - Retry attempt logging format
   - Error type logging
   - Error message logging
   - Wait time logging

### Integration Tests

**Scenarios:**

1. **End-to-End Success**
   - Process multiple batches successfully
   - Verify correct embeddings returned

2. **End-to-End with Retries**
   - Transient failures on some batches
   - Successful recovery after retries
   - Correct embeddings for successful batches

3. **End-to-End Complete Failure**
   - All retries exhausted
   - Comprehensive error response
   - No partial embeddings returned

4. **Mixed Success/Failure**
   - Some batches succeed
   - Some batches fail after retries
   - Correct partial results
   - Accurate error details

### Manual Testing

**Checklist:**

- [ ] Run with real OpenAI API (successful case)
- [ ] Trigger rate limits and observe retries
- [ ] Verify log output format
- [ ] Test with various batch sizes
- [ ] Validate error response structure
- [ ] Check backward compatibility with old configs

---

## Risk Assessment & Mitigation

### High Risk Items

**Risk 1: Breaking Existing Consumers**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Maintain backward-compatible response structure
  - Add error_details as optional new field
  - Keep success/error/embeddings fields unchanged
  - Extensive integration testing

**Risk 2: Changed Method Signatures**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Internal methods (_embed_batch_with_retry, _process_batch) are private
  - Public API (process) maintains signature
  - Only return value structure enhanced

### Medium Risk Items

**Risk 3: Test Coverage Gaps**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Comprehensive test plan
  - Unit + integration tests
  - Manual testing with real API

**Risk 4: Performance Degradation**
- **Probability:** Very Low
- **Impact:** Low
- **Mitigation:**
  - Retry delays actually reduce total time (3 retries vs 5)
  - Logging overhead minimal
  - Benchmark testing

### Low Risk Items

**Risk 5: Configuration Confusion**
- **Probability:** Low
- **Impact:** Low
- **Mitigation:**
  - Clear documentation
  - Sensible defaults
  - Backward compatibility

---

## Rollback Plan

### Immediate Rollback Triggers

1. **Critical Test Failures**
   - If >10% of existing tests fail
   - If core functionality broken

2. **Integration Issues**
   - Downstream systems break
   - Response format incompatible

3. **Performance Problems**
   - >20% increase in processing time
   - Memory leaks detected

### Rollback Procedure

1. **Git Revert**
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. **Verification**
   - Run full test suite
   - Verify original behavior restored
   - Check downstream systems

3. **Post-Mortem**
   - Document what went wrong
   - Update plan
   - Re-attempt with fixes

---

## Dependencies

### Internal Dependencies

- **src/agents/pipeline/embedder.py** - Primary file to modify
- **tests/test_embedder.py** - Test file to update
- **docs/agents/embedder-agent.md** - Documentation to update
- **src/agents/pipeline/README.md** - README to update

### External Dependencies

- **openai** package - No version changes needed
- **Python 3.8+** - No changes
- **logging** module - Standard library
- **time** module - Standard library
- **typing** module - Standard library

### No Breaking Dependencies

- No changes to other pipeline agents
- No changes to external APIs
- No changes to configuration file formats

---

## Cost-Benefit Analysis

### Development Cost

| Phase | Effort (Hours) | Complexity |
|-------|----------------|------------|
| Configuration | 2 | Low |
| Core Retry Logic | 4 | Medium |
| Integration | 3 | Medium |
| Testing | 5 | Medium |
| Documentation | 2 | Low |
| **Total** | **16** | **Medium** |

### Benefits

**Quantitative:**
- **Reduced total retry time:** 5 retries → 3 retries = 40% reduction in max retry duration
- **Fixed delays:** 1+2+4 = 7s max vs potential 1+2+4+8+16 = 31s (77% reduction)
- **Better observability:** 100% of retry attempts logged with details

**Qualitative:**
- **Improved debugging:** Comprehensive error details
- **Better user experience:** Clearer error messages
- **Maintainability:** Simpler, more predictable retry logic
- **Compliance:** Meets exact requirements (3 retries, fixed delays)

### ROI

- **Development:** 16 hours
- **Maintenance savings:** ~2 hours/month (easier debugging)
- **Break-even:** 8 months
- **Long-term value:** High (better reliability, easier troubleshooting)

---

## GOAP Path Summary

### State Space Navigation

**Initial State → Goal State Path:**

```
S0: Current implementation (5 retries, dynamic delays)
  ↓ Action 1.1: Update EmbeddingConfig
S1: Config has max_retries=3, retry_delays=[1.0, 2.0, 4.0]
  ↓ Action 1.2: Add RetryErrorDetails
S2: Error details structure defined
  ↓ Action 2.1: Refactor _embed_batch_with_retry
S3: Enhanced retry with fixed delays and error collection
  ↓ Action 2.2: Update _process_batch
S4: Batch processing handles error details
  ↓ Action 2.3: Update process method
S5: Top-level API returns comprehensive errors
  ↓ Action 3.1: Update existing tests
S6: All tests pass with new behavior
  ↓ Action 3.2: Add new tests
S7: Enhanced behavior fully validated
  ↓ Action 4.1: Update docstrings
S8: Code fully documented
  ↓ Action 4.2: Update README/docs
S9: GOAL STATE - Production ready enhanced embedder
```

### Total Path Cost

| Phase | Actions | Total Cost | Cumulative |
|-------|---------|------------|------------|
| Phase 1 | 2 | 2 units | 2 |
| Phase 2 | 3 | 8 units | 10 |
| Phase 3 | 2 | 4 units | 14 |
| Phase 4 | 2 | 2 units | 16 |
| **Total** | **9** | **16 units** | **16** |

### Optimal Path Validation

This is the optimal path because:

1. **Sequential dependencies respected:** Config → Logic → Integration → Tests → Docs
2. **Minimal rework:** Each action builds on previous
3. **Incremental validation:** Tests verify each phase
4. **Low risk:** Backward compatibility maintained throughout
5. **Clear rollback points:** Each milestone is independently testable

---

## Appendix A: Code Diff Preview

### Before: Current _embed_batch_with_retry

```python
def _embed_batch_with_retry(
    self,
    texts: List[str],
    retry_count: int = 0
) -> List[List[float]]:
    try:
        response = self.client.embeddings.create(...)
        embeddings = [item.embedding for item in response.data]
        return embeddings

    except RateLimitError as e:
        if retry_count >= self.config.max_retries:
            logger.error(f"Max retries ({self.config.max_retries}) exceeded")
            raise

        delay = min(
            self.config.initial_retry_delay * (2 ** retry_count),
            self.config.max_retry_delay
        )

        logger.warning(f"Rate limit hit. Retrying in {delay:.2f}s...")
        time.sleep(delay)
        return self._embed_batch_with_retry(texts, retry_count + 1)
```

### After: Enhanced _embed_batch_with_retry

```python
def _embed_batch_with_retry(
    self,
    texts: List[str],
    retry_count: int = 0,
    retry_history: Optional[List[Dict[str, Any]]] = None
) -> tuple[Optional[List[List[float]]], Optional[RetryErrorDetails]]:
    if retry_history is None:
        retry_history = []

    try:
        response = self.client.embeddings.create(...)
        embeddings = [item.embedding for item in response.data]
        logger.info(f"Successfully embedded {len(texts)} texts")
        return embeddings, None

    except (RateLimitError, APIError, APIConnectionError) as e:
        error_type = type(e).__name__
        error_message = str(e)

        logger.warning(
            f"Embedding API error on attempt {retry_count + 1}: "
            f"type={error_type}, message={error_message}"
        )

        if retry_count >= self.config.max_retries:
            logger.error(
                f"Max retries ({self.config.max_retries}) exceeded. "
                f"Total attempts: {retry_count + 1}"
            )
            error_details = RetryErrorDetails(
                retry_count=retry_count,
                last_error_type=error_type,
                last_error_message=error_message,
                retry_delays=[h['delay'] for h in retry_history]
            )
            return None, error_details

        delay = self.config.retry_delays[retry_count]

        logger.warning(
            f"Retry attempt {retry_count + 1}/{self.config.max_retries}: "
            f"error_type={error_type}, "
            f"error_message={error_message}, "
            f"wait_time={delay}s"
        )

        retry_history.append({
            'attempt': retry_count + 1,
            'error_type': error_type,
            'error_message': error_message,
            'delay': delay
        })

        time.sleep(delay)
        return self._embed_batch_with_retry(texts, retry_count + 1, retry_history)
```

**Key Differences:**
- ✅ Returns tuple instead of raising exception
- ✅ Uses fixed retry_delays list instead of calculation
- ✅ Tracks retry_history for comprehensive error details
- ✅ Enhanced logging with all required information
- ✅ Returns RetryErrorDetails on failure

---

## Appendix B: Error Response Examples

### Success Response (Unchanged)

```json
{
  "success": true,
  "embeddings": [
    {
      "chunk_id": "chunk-1",
      "vector": [0.1, 0.2, ...],
      "model": "text-embedding-3-small",
      "dimensions": 1536
    }
  ],
  "metadata": {
    "total_chunks": 1,
    "total_batches": 1,
    "successful_batches": 1,
    "failed_batches": 0,
    "model": "text-embedding-3-small",
    "dimensions": 1536
  }
}
```

### Enhanced Failure Response (New)

```json
{
  "success": false,
  "error": "1 batch(es) failed after retries",
  "embeddings": [],
  "metadata": {
    "total_chunks": 100,
    "total_batches": 1,
    "successful_batches": 0,
    "failed_batches": 1,
    "model": "text-embedding-3-small",
    "dimensions": 1536
  },
  "error_details": {
    "failed_batch_count": 1,
    "failed_batches": [
      {
        "batch_number": 1,
        "chunk_count": 100,
        "error_details": {
          "retry_count": 3,
          "last_error_type": "RateLimitError",
          "last_error_message": "Rate limit exceeded. Please retry after 60s.",
          "retry_delays": [1.0, 2.0, 4.0]
        }
      }
    ]
  }
}
```

### Partial Failure Response (New)

```json
{
  "success": false,
  "error": "1 batch(es) failed after retries",
  "embeddings": [
    {
      "chunk_id": "chunk-1",
      "vector": [...],
      "model": "text-embedding-3-small",
      "dimensions": 1536
    },
    // ... 99 more successful embeddings from first batch
  ],
  "metadata": {
    "total_chunks": 200,
    "total_batches": 2,
    "successful_batches": 1,
    "failed_batches": 1,
    "model": "text-embedding-3-small",
    "dimensions": 1536
  },
  "error_details": {
    "failed_batch_count": 1,
    "failed_batches": [
      {
        "batch_number": 2,
        "chunk_count": 100,
        "error_details": {
          "retry_count": 3,
          "last_error_type": "APIConnectionError",
          "last_error_message": "Connection timeout",
          "retry_delays": [1.0, 2.0, 4.0]
        }
      }
    ]
  }
}
```

---

## Appendix C: Log Output Examples

### Enhanced Retry Logs

```
2025-12-16 10:30:15 - embedder - INFO - Processing 150 chunks in 2 batches (batch_size=100)
2025-12-16 10:30:15 - embedder - INFO - Processing batch 1/2
2025-12-16 10:30:16 - embedder - INFO - Successfully embedded 100 texts
2025-12-16 10:30:16 - embedder - INFO - Processed batch of 100 chunks in 1.23s (0.012s per embedding)

2025-12-16 10:30:16 - embedder - INFO - Processing batch 2/2
2025-12-16 10:30:17 - embedder - WARNING - Embedding API error on attempt 1: type=RateLimitError, message=Rate limit exceeded
2025-12-16 10:30:17 - embedder - WARNING - Retry attempt 1/3: error_type=RateLimitError, error_message=Rate limit exceeded, wait_time=1.0s
2025-12-16 10:30:18 - embedder - WARNING - Embedding API error on attempt 2: type=RateLimitError, message=Rate limit exceeded
2025-12-16 10:30:18 - embedder - WARNING - Retry attempt 2/3: error_type=RateLimitError, error_message=Rate limit exceeded, wait_time=2.0s
2025-12-16 10:30:20 - embedder - WARNING - Embedding API error on attempt 3: type=RateLimitError, message=Rate limit exceeded
2025-12-16 10:30:20 - embedder - WARNING - Retry attempt 3/3: error_type=RateLimitError, error_message=Rate limit exceeded, wait_time=4.0s
2025-12-16 10:30:24 - embedder - WARNING - Embedding API error on attempt 4: type=RateLimitError, message=Rate limit exceeded
2025-12-16 10:30:24 - embedder - ERROR - Max retries (3) exceeded. Total attempts: 4
2025-12-16 10:30:24 - embedder - ERROR - Failed to process batch of 50 chunks
2025-12-16 10:30:24 - embedder - ERROR - Batch 2/2 failed after 3 retries
```

**Log Information Provided:**
- ✅ Attempt number with format "X/Y"
- ✅ Error type (RateLimitError, APIError, etc.)
- ✅ Full error message
- ✅ Wait time in seconds
- ✅ Total attempts when max exceeded
- ✅ Batch-level failure summary

---

## Conclusion

This GOAP-based implementation plan provides a systematic, low-risk approach to enhancing the embedder retry logic. By following the phased action plan with clear preconditions, effects, and validation, we can deliver the required functionality while maintaining backward compatibility and comprehensive test coverage.

**Key Takeaways:**
1. **Minimal changes required:** Only 9 focused actions
2. **Low risk:** Backward compatibility maintained
3. **High value:** Better debugging, clearer errors, predictable behavior
4. **Well-tested:** Comprehensive test strategy
5. **Production-ready:** Clear success criteria and rollback plan

The implementation follows GOAP principles of state-space navigation with optimal path selection, ensuring we reach the goal state efficiently with minimal cost and risk.
