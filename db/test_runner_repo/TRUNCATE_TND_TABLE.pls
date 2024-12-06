CREATE OR REPLACE PROCEDURE TEST_RUNNER_REPO.TRUNCATE_TND_TABLE (
   p_CEL_SEMA IN VARCHAR2,
   p_CEL_TABLA IN VARCHAR2,
   p_TND_SZURES IN DATE DEFAULT NULL
) IS
   v_tnd_name VARCHAR2(30);
   v_tnd_partition NUMBER;
   v_partitioned_by_tnd NUMBER;
   v_tnd_column NUMBER;
BEGIN
    IF p_TND_SZURES IS NULL THEN
        EXECUTE IMMEDIATE 'TRUNCATE TABLE ' || p_CEL_SEMA || '.' || p_CEL_TABLA;
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO v_partitioned_by_tnd
    FROM dba_part_key_columns
    WHERE OWNER = p_CEL_SEMA
    AND NAME = p_CEL_TABLA
    AND COLUMN_NAME = 'TND';

    IF v_partitioned_by_tnd > 0 THEN
        v_tnd_name := 'P_' || TO_CHAR(p_TND_SZURES, 'YYMMDD');

        SELECT COUNT(*)
        INTO v_tnd_partition
        FROM DBA_TAB_PARTITIONS
        WHERE TABLE_NAME = p_CEL_TABLA
        AND TABLE_OWNER = p_CEL_SEMA
        AND PARTITION_NAME = v_tnd_name;

        IF v_tnd_partition > 0 THEN
            EXECUTE IMMEDIATE 'ALTER TABLE ' || p_CEL_SEMA || '.' || p_CEL_TABLA || ' TRUNCATE PARTITION ' || v_tnd_name;
        ELSE
            EXECUTE IMMEDIATE 'DELETE FROM ' || p_CEL_SEMA || '.' || p_CEL_TABLA || ' WHERE TND = TO_DATE(''' || TO_CHAR(p_TND_SZURES, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')';
        END IF;
    ELSE
        SELECT COUNT(*)
        INTO v_tnd_column
        FROM dba_tab_columns
        WHERE TABLE_NAME = p_CEL_TABLA
        AND OWNER = p_CEL_SEMA
        AND column_name = 'TND';

        IF v_tnd_column > 0 THEN
            EXECUTE IMMEDIATE 'DELETE FROM ' || p_CEL_SEMA || '.' || p_CEL_TABLA || ' WHERE TND = TO_DATE(''' || TO_CHAR(p_TND_SZURES, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')';
        ELSE
            EXECUTE IMMEDIATE 'TRUNCATE TABLE ' || p_CEL_SEMA || '.' || p_CEL_TABLA;
        END IF;
    END IF;

END;
