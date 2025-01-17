CREATE OR REPLACE PACKAGE TEST_RUNNER_REPO.TEST_PACKAGE IS
  FUNCTION TEST_RUNNER(v_id IN TESTS.ID%TYPE) RETURN NUMBER;
  PROCEDURE RUN_TEST(v_id IN TESTS.ID%TYPE, V_RUN_ID IN NUMBER);
END TEST_PACKAGE;
/
