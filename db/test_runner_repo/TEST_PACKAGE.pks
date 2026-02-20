CREATE OR REPLACE PACKAGE TEST_PACKAGE IS

  -- Executes ONE test run immediately
  FUNCTION TEST_RUNNER(
      v_id IN TESTS.ID%TYPE
  ) RETURN NUMBER;

  -- Internal execution logic (called by scheduler job)
  PROCEDURE RUN_TEST(
      v_id     IN TESTS.ID%TYPE,
      v_run_id IN NUMBER
  );

  -- Schedules a test (one-time or recurring)
  PROCEDURE TEST_SCHEDULER(
      v_id        IN TESTS.ID%TYPE,
      p_start_date     IN TIMESTAMP,
      p_repeat_interval IN VARCHAR2,
      p_created_by     IN VARCHAR2
  );
  
END TEST_PACKAGE;
