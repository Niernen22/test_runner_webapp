CREATE OR REPLACE PACKAGE BODY TEST_RUNNER_REPO.TABLECOPY_PACKAGE AS
   FUNCTION TABLE_EXISTS(
       p_TABLE_OWNER VARCHAR2,
       p_TABLE_NAME VARCHAR2
   ) RETURN BOOLEAN IS
       v_exists NUMBER;
   BEGIN
       BEGIN
           SELECT COUNT(*)
           INTO v_exists
           FROM dba_tables
           WHERE table_name = p_TABLE_NAME
             AND owner = p_TABLE_OWNER;

           IF v_exists = 1 THEN
               RETURN TRUE;
           END IF;
       EXCEPTION
           WHEN NO_DATA_FOUND THEN
               NULL;
       END;

       BEGIN
           EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || p_TABLE_OWNER || '.' || p_TABLE_NAME || '@ODS_PROD';
           RETURN TRUE;
       EXCEPTION
           WHEN OTHERS THEN
               RETURN FALSE;
       END;
   END TABLE_EXISTS;

-----------------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE TND_TABLESPACE_CHECK (
    p_source_schema VARCHAR2,
    p_source_table VARCHAR2,
    p_target_schema VARCHAR2,
    p_target_table VARCHAR2,
    p_tnd_filter DATE) IS

   v_tnd_name VARCHAR2(20);
   v_tablespace_name VARCHAR2(30);
   v_tablespace_count NUMBER;
   v_datafile_path VARCHAR2(100);
   v_datafile_size NUMBER;
   v_autoextend_size NUMBER;
   v_bigfile VARCHAR2(10);
   v_datafile_paths CLOB := EMPTY_CLOB();
   v_datafile_count NUMBER;
BEGIN
   v_tnd_name := 'P_' || TO_CHAR(p_tnd_filter, 'YYYYMMDD');

--1. TABLESPACE CHECK
    FOR tablespacecheck IN (
    SELECT DISTINCT TABLESPACE_NAME
    FROM DBA_TAB_PARTITIONS@ODS_PROD
    WHERE TABLE_OWNER = p_source_schema
    AND TABLE_NAME = p_source_table
    AND PARTITION_NAME = v_tnd_name)

    LOOP
    v_tablespace_name := tablespacecheck.TABLESPACE_NAME;

   SELECT COUNT(*)
   INTO v_tablespace_count
   FROM DBA_DATA_FILES
   WHERE TABLESPACE_NAME = v_tablespace_name;

   IF v_tablespace_count > 0 THEN
      DBMS_OUTPUT.PUT_LINE('Tablespace ' || v_tablespace_name || ' exists.');
   ELSE
      DBMS_OUTPUT.PUT_LINE('Tablespace ' || v_tablespace_name || ' does not exist, creating..');

--2. BIGFILE?
   SELECT BIGFILE
   INTO v_bigfile
   FROM DBA_TABLESPACES@ODS_PROD
   WHERE TABLESPACE_NAME = v_tablespace_name;

   IF v_bigfile = 'NO' THEN

--3. MULTIPLE DATAFILES?
   SELECT COUNT(*)
   INTO v_datafile_count
   FROM dba_data_files@ODS_PROD
   WHERE tablespace_name = v_tablespace_name;

--4. NO BIGFILE, SINGLE DATAFILE:
   IF v_datafile_count = 1 THEN

  --4/A/1. AUTOEXTEND SIZE (%)
  SELECT
  (SELECT VALUE FROM SYS.V_$PARAMETER WHERE name = 'db_block_size') *
  (SELECT INCREMENT_BY FROM DBA_DATA_FILES@ODS_PROD WHERE TABLESPACE_NAME = v_tablespace_name) / 1024 /1024
  INTO v_autoextend_size
  FROM dual;

  --3/A/2. DATAFILE SIZE (%)
  SELECT v_autoextend_size/4 INTO v_datafile_size
  FROM dual;


   --3/A/3. DATAFILE PATH
   SELECT REPLACE(FILE_NAME, '/ODSD/', '/RDWD/')
   INTO v_datafile_path
   FROM DBA_DATA_FILES@ODS_PROD
   WHERE TABLESPACE_NAME = v_tablespace_name;

   EXECUTE IMMEDIATE 'CREATE TABLESPACE ' || v_tablespace_name ||
                  ' DATAFILE ''' || v_datafile_path || ''' SIZE ' || v_datafile_size || 'M'|| ' AUTOEXTEND ON NEXT ' || v_autoextend_size || 'M';
  DBMS_OUTPUT.PUT_LINE('Created tablespace ' || v_tablespace_name);

--4. NO BIGFILE, MULTIPLE DATAFILE:
   ELSIF v_datafile_count > 1 THEN

   --4/B/0. DATAFILE PATHS
   FOR datafile_path_info IN (
       SELECT REPLACE(FILE_NAME, '/ODSD/', '/RDWD/') AS DATAFILE_PATH_NAME,
              (SELECT INCREMENT_BY FROM DBA_DATA_FILES@ODS_PROD WHERE FILE_NAME = datafile_path.FILE_NAME) AS INCREMENT_BY
       FROM DBA_DATA_FILES@ODS_PROD datafile_path
       WHERE TABLESPACE_NAME = v_tablespace_name
   )
   LOOP
   --4/B/1. AUTOEXTEND SIZE
       SELECT (SELECT VALUE FROM SYS.V_$PARAMETER WHERE name = 'db_block_size') *
              (datafile_path_info.INCREMENT_BY) / 1024 / 1024
       INTO v_autoextend_size
       FROM dual;

   --4/B/2. DATAFILE SIZE
       SELECT v_autoextend_size / 4 INTO v_datafile_size FROM dual;
   --4/B/3. DATAFILE PATHS NAMES
       v_datafile_path := datafile_path_info.DATAFILE_PATH_NAME;
       v_datafile_paths := v_datafile_paths || ', ''' || v_datafile_path || ''' SIZE ' || v_datafile_size || 'M AUTOEXTEND ON NEXT ' || v_autoextend_size || 'M';
   END LOOP;

   v_datafile_paths := SUBSTR(v_datafile_paths, 3);

   EXECUTE IMMEDIATE 'CREATE TABLESPACE ' || v_tablespace_name ||
                     ' DATAFILE ' || v_datafile_paths;

   DBMS_OUTPUT.PUT_LINE('Created tablespace ' || v_tablespace_name || ' with datafiles ' || v_datafile_paths);


   --4/C.
   ELSE
   DBMS_OUTPUT.PUT_LINE('Problem with finding datafile for ' || v_tablespace_name);
   END IF;

--5.BIGFILE TABLESPACE
   ELSIF v_bigfile = 'YES' THEN

  --5/1. AUTOEXTEND SIZE (%)
  SELECT
  (SELECT VALUE FROM SYS.V_$PARAMETER WHERE name = 'db_block_size') *
  (SELECT INCREMENT_BY FROM DBA_DATA_FILES@ODS_PROD WHERE TABLESPACE_NAME = v_tablespace_name) / 1024 /1024
  INTO v_autoextend_size
  FROM dual;

  --5/2. DATAFILE SIZE (%)
  SELECT v_autoextend_size/4 INTO v_datafile_size
  FROM dual;


   --5/3. DATAFILE PATH
   SELECT REPLACE(FILE_NAME, '/ODSD/', '/RDWD/')
   INTO v_datafile_path
   FROM DBA_DATA_FILES@ODS_PROD
   WHERE TABLESPACE_NAME = v_tablespace_name;

   EXECUTE IMMEDIATE 'CREATE TABLESPACE ' || v_tablespace_name ||
                  ' DATAFILE ''' || v_datafile_path || ''' SIZE ' || v_datafile_size || 'M'|| ' AUTOEXTEND ON NEXT ' || v_autoextend_size || 'M';
  DBMS_OUTPUT.PUT_LINE('Created tablespace ' || v_tablespace_name);

  ELSE
    DBMS_OUTPUT.PUT_LINE('No information found about ' || v_tablespace_name);
  END IF;
 END IF;
END LOOP;
END TND_TABLESPACE_CHECK;
--------------------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE COMMON_COLUMNS (
        p_source_schema VARCHAR2,
        p_source_table VARCHAR2,
        p_target_schema VARCHAR2,
        p_target_table VARCHAR2) IS
        v_common_columns NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_common_columns
    FROM (SELECT COLUMN_NAME FROM all_tab_columns@ODS_PROD WHERE TABLE_NAME = p_source_table AND OWNER = p_source_schema) t1
    JOIN (SELECT COLUMN_NAME FROM all_tab_columns WHERE TABLE_NAME = p_target_table AND OWNER = p_target_schema) t2
    ON t1.COLUMN_NAME = t2.COLUMN_NAME;

    IF v_common_columns = 0 THEN
    DBMS_OUTPUT.PUT_LINE('No columns in common. Exiting...');
    RETURN;
    END IF;
END COMMON_COLUMNS;

--------------------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE COPY_COLUMNS (
  p_source_schema VARCHAR2,
  p_source_table VARCHAR2,
  p_target_schema VARCHAR2,
  p_target_table VARCHAR2) IS
  v_column_list CLOB;
  v_dblink_sql VARCHAR2(20) := '@ODS_PROD';

BEGIN
    SELECT LISTAGG(t1.COLUMN_NAME, ', ') WITHIN GROUP (ORDER BY t1.COLUMN_NAME)
    INTO v_column_list
    FROM (SELECT COLUMN_NAME FROM all_tab_columns@ODS_PROD WHERE TABLE_NAME = p_source_table AND OWNER = p_source_schema) t1
    JOIN (SELECT COLUMN_NAME FROM all_tab_columns WHERE TABLE_NAME = p_target_table AND OWNER = p_target_schema) t2
    ON t1.COLUMN_NAME = t2.COLUMN_NAME;

    EXECUTE IMMEDIATE 'INSERT INTO ' || p_target_schema || '.' || p_target_table || ' (' || v_column_list || ') ' ||
                  'SELECT ' || v_column_list || ' FROM ' || p_source_schema || '.' || p_source_table || v_dblink_sql;

    DBMS_OUTPUT.PUT_LINE('Data copied.');
END COPY_COLUMNS;
--------------------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE COPY_COLUMNS_TND (
  p_tnd_filter DATE,
  p_source_schema VARCHAR2,
  p_source_table VARCHAR2,
  p_target_schema VARCHAR2,
  p_target_table VARCHAR2) IS
  v_column_list CLOB;
  tnd_column NUMBER;
  v_dblink_sql VARCHAR2(20) := '@ODS_PROD';

BEGIN
    SELECT COUNT(*)
    INTO tnd_column
    FROM all_tab_columns
    WHERE table_name = p_target_table
    AND owner = p_target_schema
    AND column_name LIKE '%TND%';

    IF tnd_column > 0 THEN

    SELECT LISTAGG(t1.COLUMN_NAME, ', ') WITHIN GROUP (ORDER BY t1.COLUMN_NAME)
    INTO v_column_list
    FROM (SELECT COLUMN_NAME FROM all_tab_columns@ODS_PROD WHERE TABLE_NAME = p_source_table AND OWNER = p_source_schema) t1
    JOIN (SELECT COLUMN_NAME FROM all_tab_columns WHERE TABLE_NAME = p_target_table AND OWNER = p_target_schema) t2
    ON t1.COLUMN_NAME = t2.COLUMN_NAME;

    EXECUTE IMMEDIATE 'INSERT INTO ' || p_target_schema || '.' || p_target_table || ' (' || v_column_list || ') ' ||
                      'SELECT ' || v_column_list || ' FROM ' || p_source_schema || '.' || p_source_table || v_dblink_sql ||
                      ' WHERE TND = :1' USING p_tnd_filter;
    DBMS_OUTPUT.PUT_LINE('Data copied where TND = ' || TO_CHAR(p_tnd_filter, 'yyyy-mm-dd') || '.');

    ELSE

   TABLECOPY_PACKAGE.COPY_COLUMNS
    (p_source_schema => p_source_schema,
     p_source_table => p_source_table,
     p_target_schema => p_target_schema,
     p_target_table => p_target_table
     );
     END IF;
END COPY_COLUMNS_TND;
--------------------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE TABLESPACE_CHECK (
    p_source_schema VARCHAR2,
    p_source_table VARCHAR2,
    p_target_schema VARCHAR2,
    p_target_table VARCHAR2) IS
   v_partition_name VARCHAR2(30);
   v_tablespace_name VARCHAR2(30);
   v_tablespace_count NUMBER;
   v_partition_count NUMBER;
   v_datafile_path VARCHAR2(100);
   v_datafile_size NUMBER;
   v_autoextend_size NUMBER;
   v_bigfile VARCHAR2(10);
   v_datafile_paths CLOB := EMPTY_CLOB();
   v_datafile_count NUMBER;
BEGIN
--1. TABLESPACE CHECK
     FOR partitioncheck IN(
    SELECT partition_name
    FROM DBA_TAB_PARTITIONS@ODS_PROD
    WHERE TABLE_OWNER = p_source_schema
    AND TABLE_NAME = p_source_table)

    LOOP
    v_partition_name := partitioncheck.partition_name;

    SELECT COUNT(*)
    INTO v_partition_count
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_OWNER = p_target_schema
    AND TABLE_NAME = p_target_table
    AND PARTITION_NAME = v_partition_name;

   IF v_partition_count > 0 THEN
      DBMS_OUTPUT.PUT_LINE('Partition ' || v_partition_name || ' exists, new tablespace is not needed.');
   ELSE
      DBMS_OUTPUT.PUT_LINE('Partition ' || v_partition_name || ' does not exists, checking tablespace..');

    SELECT TABLESPACE_NAME
    INTO v_tablespace_name
    FROM DBA_TAB_PARTITIONS@ODS_PROD
    WHERE TABLE_OWNER = p_source_schema
    AND TABLE_NAME = p_source_table
    AND PARTITION_NAME = v_partition_name;

   SELECT COUNT(*)
   INTO v_tablespace_count
   FROM DBA_DATA_FILES
   WHERE TABLESPACE_NAME = v_tablespace_name;

   IF v_tablespace_count > 0 THEN
      DBMS_OUTPUT.PUT_LINE('Tablespace ' || v_tablespace_name || ' exists.');
   ELSE
      DBMS_OUTPUT.PUT_LINE('Tablespace ' || v_tablespace_name || ' does not exist, creating..');

--2. BIGFILE?
   SELECT BIGFILE
   INTO v_bigfile
   FROM DBA_TABLESPACES@ODS_PROD
   WHERE TABLESPACE_NAME = v_tablespace_name;

   IF v_bigfile = 'NO' THEN

--3. MULTIPLE DATAFILES?
   SELECT COUNT(*)
   INTO v_datafile_count
   FROM dba_data_files@ODS_PROD
   WHERE tablespace_name = v_tablespace_name;

--4. NO BIGFILE, SINGLE DATAFILE:
   IF v_datafile_count = 1 THEN

  --4/A/1. AUTOEXTEND SIZE (%)
  SELECT
  (SELECT VALUE FROM SYS.V_$PARAMETER WHERE name = 'db_block_size') *
  (SELECT INCREMENT_BY FROM DBA_DATA_FILES@ODS_PROD WHERE TABLESPACE_NAME = v_tablespace_name) / 1024 /1024
  INTO v_autoextend_size
  FROM dual;

  --3/A/2. DATAFILE SIZE (%)
  SELECT v_autoextend_size/4 INTO v_datafile_size
  FROM dual;


   --3/A/3. DATAFILE PATH
   SELECT REPLACE(FILE_NAME, '/ODSD/', '/RDWD/')
   INTO v_datafile_path
   FROM DBA_DATA_FILES@ODS_PROD
   WHERE TABLESPACE_NAME = v_tablespace_name;

   EXECUTE IMMEDIATE 'CREATE TABLESPACE ' || v_tablespace_name ||
                  ' DATAFILE ''' || v_datafile_path || ''' SIZE ' || v_datafile_size || 'M'|| ' AUTOEXTEND ON NEXT ' || v_autoextend_size || 'M';
  DBMS_OUTPUT.PUT_LINE('Created tablespace ' || v_tablespace_name);

--4. NO BIGFILE, MULTIPLE DATAFILE:
   ELSIF v_datafile_count > 1 THEN

   --4/B/0. DATAFILE PATHS
   FOR datafile_path_info IN (
       SELECT REPLACE(FILE_NAME, '/ODSD/', '/RDWD/') AS DATAFILE_PATH_NAME,
              (SELECT INCREMENT_BY FROM DBA_DATA_FILES@ODS_PROD WHERE FILE_NAME = datafile_path.FILE_NAME) AS INCREMENT_BY
       FROM DBA_DATA_FILES@ODS_PROD datafile_path
       WHERE TABLESPACE_NAME = v_tablespace_name
   )
   LOOP
   --4/B/1. AUTOEXTEND SIZE
       SELECT (SELECT VALUE FROM SYS.V_$PARAMETER WHERE name = 'db_block_size') *
              (datafile_path_info.INCREMENT_BY) / 1024 / 1024
       INTO v_autoextend_size
       FROM dual;

   --4/B/2. DATAFILE SIZE
       SELECT v_autoextend_size / 4 INTO v_datafile_size FROM dual;
   --4/B/3. DATAFILE PATHS NAMES
       v_datafile_path := datafile_path_info.DATAFILE_PATH_NAME;
       v_datafile_paths := v_datafile_paths || ', ''' || v_datafile_path || ''' SIZE ' || v_datafile_size || 'M AUTOEXTEND ON NEXT ' || v_autoextend_size || 'M';
   END LOOP;

   v_datafile_paths := SUBSTR(v_datafile_paths, 3);

   EXECUTE IMMEDIATE 'CREATE TABLESPACE ' || v_tablespace_name ||
                     ' DATAFILE ' || v_datafile_paths;

   DBMS_OUTPUT.PUT_LINE('Created tablespace ' || v_tablespace_name || ' with datafiles ' || v_datafile_paths);


   --4/ERROR.
   ELSE
   DBMS_OUTPUT.PUT_LINE('Problem with finding datafile for ' || v_tablespace_name);
   END IF;

--5.BIGFILE TABLESPACE
   ELSIF v_bigfile = 'YES' THEN

  --5/1. AUTOEXTEND SIZE (%)
  SELECT
  (SELECT VALUE FROM SYS.V_$PARAMETER WHERE name = 'db_block_size') *
  (SELECT INCREMENT_BY FROM DBA_DATA_FILES@ODS_PROD WHERE TABLESPACE_NAME = v_tablespace_name) / 1024 /1024
  INTO v_autoextend_size
  FROM dual;

  --5/2. DATAFILE SIZE (%)
  SELECT v_autoextend_size/4 INTO v_datafile_size
  FROM dual;


   --5/3. DATAFILE PATH
   SELECT REPLACE(FILE_NAME, '/ODSD/', '/RDWD/')
   INTO v_datafile_path
   FROM DBA_DATA_FILES@ODS_PROD
   WHERE TABLESPACE_NAME = v_tablespace_name;

   EXECUTE IMMEDIATE 'CREATE TABLESPACE ' || v_tablespace_name ||
                  ' DATAFILE ''' || v_datafile_path || ''' SIZE ' || v_datafile_size || 'M'|| ' AUTOEXTEND ON NEXT ' || v_autoextend_size || 'M';
  DBMS_OUTPUT.PUT_LINE('Created tablespace ' || v_tablespace_name);

  --5/ERROR.
  ELSE
    DBMS_OUTPUT.PUT_LINE('No information found about ' || v_tablespace_name);

  END IF;
 END IF;
END IF;
END LOOP;
END TABLESPACE_CHECK;
--------------------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE PARTITION_CURSOR_RANGE (
   p_target_schema VARCHAR2,
   p_target_table VARCHAR2,
   p_source_schema VARCHAR2,
   p_source_table VARCHAR2) IS
  v_xml_cursor SYS_REFCURSOR;
  v_PARTITION_NAME VARCHAR2(30);
  V_TABLESPACE_NAME VARCHAR2(30);
  V_HIGH_VALUE VARCHAR2(4000);
  v_partition_count NUMBER;
  v_date_value DATE;
  v_column_datatype VARCHAR (20);
BEGIN
    OPEN v_xml_cursor FOR
    WITH xmlform AS (
        SELECT DBMS_XMLGEN.GETXMLTYPE('SELECT PARTITION_NAME, HIGH_VALUE, TABLE_NAME, TABLE_OWNER, TABLESPACE_NAME FROM DBA_TAB_PARTITIONS@ODS_PROD WHERE table_name = ''' || p_source_table || ''' AND table_owner = ''' || p_source_schema || '''') AS x
        FROM dual
    )
    SELECT xmltab.PARTITION_NAME, xmltab.HIGH_VALUE, xmltab.TABLESPACE_NAME
    FROM xmlform
    CROSS JOIN XMLTABLE(
        '/ROWSET/ROW'
        PASSING xmlform.x
        COLUMNS
            PARTITION_NAME VARCHAR2(30) PATH 'PARTITION_NAME',
            HIGH_VALUE VARCHAR2(4000) PATH 'HIGH_VALUE',
            TABLE_NAME VARCHAR2(30) PATH 'TABLE_NAME',
            TABLE_OWNER VARCHAR2(30) PATH 'TABLE_OWNER',
            TABLESPACE_NAME VARCHAR2(30) PATH 'TABLESPACE_NAME'
    ) xmltab;

    LOOP
        FETCH v_xml_cursor INTO v_PARTITION_NAME, V_HIGH_VALUE, V_TABLESPACE_NAME;
        EXIT WHEN v_xml_cursor%NOTFOUND;

    --partíció létezés check

SELECT COUNT(*)
    INTO v_partition_count
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_NAME = p_target_table
    AND PARTITION_NAME = v_PARTITION_NAME
    AND TABLE_OWNER = p_target_schema;

    IF v_partition_count = 0 THEN
    SELECT DATA_TYPE
    INTO v_column_datatype
    FROM DBA_TAB_COLUMNS@ODS_PROD
    WHERE TABLE_NAME = p_source_table
    AND COLUMN_NAME IN (SELECT COLUMN_NAME
                       FROM dba_part_key_columns@ODS_PROD
                       WHERE TABLE_NAME = p_source_table)
    FETCH FIRST 1 ROWS ONLY;
    DBMS_OUTPUT.PUT_LINE('Table partitioned by ' || v_column_datatype || ' datatype column');

    IF v_column_datatype = 'DATE' OR v_column_datatype = 'TIMESTAMP' THEN

       v_date_value := TO_DATE(SUBSTR(V_HIGH_VALUE, INSTR(V_HIGH_VALUE, '''') + 2, 10), 'YYYY-MM-DD');
       DBMS_OUTPUT.PUT_LINE('Partition Name: ' || v_PARTITION_NAME || ', High Value: ' || V_HIGH_VALUE || ', Date Value: ' || to_char(v_DATE_VALUE, 'YYYY-MM-DD'));
       EXECUTE IMMEDIATE 'ALTER TABLE ' || p_target_schema || '.' || p_target_table || ' ADD PARTITION ' || v_PARTITION_NAME || ' VALUES LESS THAN (TO_DATE(''' || TO_CHAR(v_DATE_VALUE, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')) TABLESPACE ' || V_TABLESPACE_NAME;
    END IF;

    ELSE
      DBMS_OUTPUT.PUT_LINE('Partition already exists. No need to copy.');
    END IF;
    END LOOP;

    CLOSE v_xml_cursor;

 END PARTITION_CURSOR_RANGE;

-----------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE TRUNCATE_TND_TABLE (
   p_tnd_filter DATE,
   p_source_schema VARCHAR2,
   p_source_table VARCHAR2,
   p_target_schema VARCHAR2,
   p_target_table VARCHAR2) IS
   v_tnd_name VARCHAR2(30);
   v_tnd_partition NUMBER;
   v_partitioned_by_tnd NUMBER;
   v_partition_type1 VARCHAR2(30);
   v_partition_type2 VARCHAR2(30);
BEGIN
     SELECT COUNT(*)
     INTO v_partitioned_by_tnd
     FROM dba_part_key_columns
     WHERE NAME = p_target_table
     AND COLUMN_NAME = 'TND';

     IF v_partitioned_by_tnd > 0 THEN

    SELECT PARTITIONING_TYPE
    INTO v_partition_type1
    FROM All_PART_TABLES@ODS_PROD
    WHERE TABLE_NAME = p_source_table
    AND OWNER = p_source_schema
    AND ROWNUM = 1;

    SELECT PARTITIONING_TYPE
    INTO v_partition_type2
    FROM All_PART_TABLES
    WHERE TABLE_NAME = p_target_table
    AND OWNER = p_target_schema
    AND ROWNUM = 1;

--ha range partitioned, akkor p_tnd_filter+1 truncate
    IF v_partition_type1 = 'RANGE' AND v_partition_type2 = 'RANGE' THEN

     v_tnd_name := 'P_' || TO_CHAR(p_tnd_filter + 1, 'YYYYMMDD');

     SELECT COUNT(*)
     INTO v_tnd_partition
     FROM DBA_TAB_PARTITIONS
     WHERE TABLE_NAME = p_target_table
     AND TABLE_OWNER = p_target_schema
     AND PARTITION_NAME = v_tnd_name;

     IF v_tnd_partition  > 0 THEN
         EXECUTE IMMEDIATE 'ALTER TABLE ' || p_target_schema || '.' || p_target_table ||' TRUNCATE PARTITION ' || v_tnd_name;
         DBMS_OUTPUT.PUT_LINE('Partition ' || v_tnd_name || ' deleted.');

         ELSE
           EXECUTE IMMEDIATE 'DELETE FROM ' || p_target_schema || '.' || p_target_table ||
           ' WHERE TND = TO_DATE(''' || TO_CHAR(p_tnd_filter, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')';
           DBMS_OUTPUT.PUT_LINE('Rows where TND is ' || v_tnd_name || ' deleted.');
    END IF;

--ha list partitioned, akkor p_tnd_filter truncate
   ELSIF v_partition_type1 = 'LIST' AND v_partition_type2 = 'LIST' THEN
     v_tnd_name := 'P_' || TO_CHAR(p_tnd_filter, 'YYYYMMDD');

     SELECT COUNT(*)
     INTO v_tnd_partition
     FROM DBA_TAB_PARTITIONS
     WHERE TABLE_NAME = p_target_table
     AND TABLE_OWNER = p_target_schema
     AND PARTITION_NAME = v_tnd_name;

     IF v_tnd_partition  > 0 THEN
         EXECUTE IMMEDIATE 'ALTER TABLE ' || p_target_schema || '.' || p_target_table || ' TRUNCATE PARTITION ' || v_tnd_name;
         DBMS_OUTPUT.PUT_LINE('Partition ' || v_tnd_name || ' deleted.');

         ELSE
           EXECUTE IMMEDIATE 'DELETE FROM ' || p_target_schema || '.' || p_target_table ||
           ' WHERE TND = TO_DATE(''' || TO_CHAR(p_tnd_filter, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')';
           DBMS_OUTPUT.PUT_LINE('Rows where TND is ' || v_tnd_name || ' deleted.');
    END IF;
    END IF;
    ELSE
           DBMS_OUTPUT.PUT_LINE('Tables have different or unknown partitioning types.');
           EXECUTE IMMEDIATE 'DELETE FROM ' || p_target_schema || '.' || p_target_table ||
           ' WHERE TND = TO_DATE(''' || TO_CHAR(p_tnd_filter, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')';
           DBMS_OUTPUT.PUT_LINE('Rows where TND is ' || v_tnd_name || ' deleted.');

    END IF;
END TRUNCATE_TND_TABLE;

------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE PARTITION_CURSOR_LIST (
   p_target_schema VARCHAR2,
   p_target_table VARCHAR2,
   p_source_schema VARCHAR2,
   p_source_table VARCHAR2) IS
  v_xml_cursor SYS_REFCURSOR;
  v_PARTITION_NAME VARCHAR2(30);
  V_HIGH_VALUE VARCHAR2(4000);
  V_TABLESPACE_NAME VARCHAR2(30);
  v_partition_count NUMBER;
  v_date_value DATE;
  v_column_datatype VARCHAR (20);
BEGIN
    OPEN v_xml_cursor FOR
    WITH xmlform AS (
        SELECT DBMS_XMLGEN.GETXMLTYPE('SELECT PARTITION_NAME, HIGH_VALUE, TABLE_NAME, TABLE_OWNER, TABLESPACE_NAME FROM DBA_TAB_PARTITIONS@ODS_PROD WHERE table_name = ''' || p_source_table || ''' AND table_owner = ''' || p_source_schema || '''') AS x
        FROM dual
    )
    SELECT xmltab.PARTITION_NAME, xmltab.HIGH_VALUE, xmltab.TABLESPACE_NAME
    FROM xmlform
    CROSS JOIN XMLTABLE(
        '/ROWSET/ROW'
        PASSING xmlform.x
        COLUMNS
            PARTITION_NAME VARCHAR2(30) PATH 'PARTITION_NAME',
            HIGH_VALUE VARCHAR2(4000) PATH 'HIGH_VALUE',
            TABLE_NAME VARCHAR2(30) PATH 'TABLE_NAME',
            TABLE_OWNER VARCHAR2(30) PATH 'TABLE_OWNER',
            TABLESPACE_NAME VARCHAR2(30) PATH 'TABLESPACE_NAME'
    ) xmltab;

    LOOP
        FETCH v_xml_cursor INTO v_PARTITION_NAME, V_HIGH_VALUE, V_TABLESPACE_NAME;
        EXIT WHEN v_xml_cursor%NOTFOUND;

    --partíció létezés check
    SELECT COUNT(*)
    INTO v_partition_count
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_NAME = p_target_table
    AND PARTITION_NAME = v_PARTITION_NAME
    AND TABLE_OWNER = p_target_schema;

    IF v_partition_count = 0 THEN

    SELECT DATA_TYPE
    INTO v_column_datatype
    FROM DBA_TAB_COLUMNS@ODS_PROD
    WHERE TABLE_NAME = p_source_table
    AND COLUMN_NAME IN (SELECT COLUMN_NAME
                       FROM dba_part_key_columns@ODS_PROD
                       WHERE TABLE_NAME = p_source_table)
    FETCH FIRST 1 ROWS ONLY;
    DBMS_OUTPUT.PUT_LINE('Table partitioned by ' || v_column_datatype || ' datatype column');

    IF v_column_datatype = 'DATE' OR v_column_datatype = 'TIMESTAMP' THEN

       v_date_value := TO_DATE(SUBSTR(V_HIGH_VALUE, INSTR(V_HIGH_VALUE, '''') + 2, 10), 'YYYY-MM-DD');
       DBMS_OUTPUT.PUT_LINE('Partition Name: ' || v_PARTITION_NAME || ', High Value: ' || V_HIGH_VALUE || ', Date Value: ' || to_char(v_DATE_VALUE, 'YYYY-MM-DD'));
       EXECUTE IMMEDIATE 'ALTER TABLE ' || p_target_schema || '.' || p_target_table || ' ADD PARTITION ' || v_PARTITION_NAME || ' VALUES (TO_DATE(''' || TO_CHAR(v_DATE_VALUE, 'YYYY-MM-DD') || ''', ''YYYY-MM-DD'')) TABLESPACE '|| V_TABLESPACE_NAME;
    END IF;

    ELSE
      DBMS_OUTPUT.PUT_LINE('Partition already exists. No need to copy.');
    END IF;
    END LOOP;

    CLOSE v_xml_cursor;

 END PARTITION_CURSOR_LIST;

-----------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE RANGE_OR_LIST (
    p_source_schema VARCHAR2,
    p_source_table VARCHAR2,
    p_target_schema VARCHAR2,
    p_target_table VARCHAR2) IS
    v_partition_type1 VARCHAR2(30);
    v_partition_type2 VARCHAR2(30);
    v_column_list CLOB;
BEGIN
    SELECT PARTITIONING_TYPE
    INTO v_partition_type1
    FROM All_PART_TABLES@ODS_PROD
    WHERE TABLE_NAME = p_source_table AND ROWNUM = 1;

    SELECT PARTITIONING_TYPE
    INTO v_partition_type2
    FROM All_PART_TABLES
    WHERE TABLE_NAME = p_target_table AND ROWNUM = 1;

    IF v_partition_type1 = 'RANGE' AND v_partition_type2 = 'RANGE' THEN
        DBMS_OUTPUT.PUT_LINE('Both tables are range partitioned.');

        --------------------TABLESPACE_CHECK procedúra
        TABLECOPY_PACKAGE.TABLESPACE_CHECK(
        p_source_schema => p_source_schema,
        p_source_table => p_source_table,
        p_target_schema => p_target_schema,
        p_target_table => p_target_table
        );
        -------------PARTITION_CURSOR_RANGE (split? lesz majd ez)
        TABLECOPY_PACKAGE.PARTITION_CURSOR_RANGE (
        p_source_schema => p_source_schema,
        p_source_table => p_source_table,
        p_target_schema => p_target_schema,
        p_target_table => p_target_table
        );
    ELSIF v_partition_type1 = 'LIST' AND v_partition_type2 = 'LIST' THEN
        DBMS_OUTPUT.PUT_LINE('Both tables are list partitioned.');
        --------------------TABLESPACE_CHECK procedúra
        TABLECOPY_PACKAGE.TABLESPACE_CHECK(
        p_source_schema => p_source_schema,
        p_source_table => p_source_table,
        p_target_schema => p_target_schema,
        p_target_table => p_target_table
        );
        -------------PARTITION_CURSOR_LIST procedúra
        TABLECOPY_PACKAGE.PARTITION_CURSOR_LIST(
        p_source_schema => p_source_schema,
        p_source_table => p_source_table,
        p_target_schema => p_target_schema,
        p_target_table => p_target_table
        );
    ELSE
        DBMS_OUTPUT.PUT_LINE('Tables have different or unknown partitioning types.');
    END IF;

    EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE(p_source_table || ' and/or '|| p_target_table || ' is not partitioned.');

END RANGE_OR_LIST;
---------------------------------------------------------------------------------------------------------------------------------------------------
PROCEDURE RANGE_OR_LIST_TND (
    p_tnd_filter DATE,
    p_source_schema VARCHAR2,
    p_source_table VARCHAR2,
    p_target_schema VARCHAR2,
    p_target_table VARCHAR2) IS
    v_partition_type1 VARCHAR2(30);
    v_partition_type2 VARCHAR2(30);
    v_column_list CLOB;
    v_tnd_name VARCHAR2(30);
    v_partition_count NUMBER;
    V_TABLESPACE_NAME VARCHAR2(30);
BEGIN

    SELECT PARTITIONING_TYPE
    INTO v_partition_type1
    FROM All_PART_TABLES@ODS_PROD
    WHERE TABLE_NAME = p_source_table AND ROWNUM = 1;

    SELECT PARTITIONING_TYPE
    INTO v_partition_type2
    FROM All_PART_TABLES
    WHERE TABLE_NAME = p_target_table AND ROWNUM = 1;

    IF v_partition_type1 = 'RANGE' AND v_partition_type2 = 'RANGE' THEN
        DBMS_OUTPUT.PUT_LINE('Both tables are range partitioned.');
--------------------TND_TABLESPACE_CHECK procedúra
    TABLECOPY_PACKAGE.TND_TABLESPACE_CHECK
       (p_tnd_filter => p_tnd_filter,
        p_source_schema => p_source_schema,
        p_source_table => p_source_table,
        p_target_schema => p_target_schema,
        p_target_table => p_target_table
        );

     v_tnd_name := 'P_' || TO_CHAR(p_tnd_filter + 1, 'YYYYMMDD');

    SELECT COUNT(*)
    INTO v_partition_count
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_NAME = p_target_table
    AND PARTITION_NAME = v_tnd_name
    AND TABLE_OWNER = p_target_schema;

    IF v_partition_count = 0 THEN

    SELECT TABLESPACE_NAME
    INTO V_TABLESPACE_NAME
    FROM DBA_TAB_PARTITIONS@ODS_PROD
    WHERE TABLE_NAME = p_source_table
    AND TABLE_OWNER = p_source_schema
    AND PARTITION_NAME = v_tnd_name;

    DBMS_OUTPUT.PUT_LINE('Partition Name: ' || v_tnd_name);
    EXECUTE IMMEDIATE 'ALTER TABLE ' || p_target_schema || '.' || p_target_table || ' ADD PARTITION ' || v_tnd_name || ' VALUES LESS THAN (DATE ''' || TO_CHAR(p_tnd_filter + 1, 'YYYY-MM-DD') || ''') TABLESPACE ' || V_TABLESPACE_NAME;
    DBMS_OUTPUT.PUT_LINE('Partition ' || v_tnd_name || ' created.');

    ELSE
    DBMS_OUTPUT.PUT_LINE('Partition ' || v_tnd_name || ' already exists.');
    END IF;

    ELSIF v_partition_type1 = 'LIST' AND v_partition_type2 = 'LIST' THEN
        DBMS_OUTPUT.PUT_LINE('Both tables are list partitioned.');
--------------------TND_TABLESPACE_CHECK procedúra
    TABLECOPY_PACKAGE.TND_TABLESPACE_CHECK
       (p_tnd_filter => p_tnd_filter,
        p_source_schema => p_source_schema,
        p_source_table => p_source_table,
        p_target_schema => p_target_schema,
        p_target_table => p_target_table
        );

     v_tnd_name := 'P_' || TO_CHAR(p_tnd_filter, 'YYYYMMDD');

    SELECT COUNT(*)
    INTO v_partition_count
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_NAME = p_target_table
    AND PARTITION_NAME = v_tnd_name
    AND TABLE_OWNER = p_target_schema;

    IF v_partition_count = 0 THEN

    SELECT TABLESPACE_NAME
    INTO V_TABLESPACE_NAME
    FROM DBA_TAB_PARTITIONS@ODS_PROD
    WHERE TABLE_NAME = p_source_table
    AND TABLE_OWNER = p_source_schema
    AND PARTITION_NAME = v_tnd_name;

    DBMS_OUTPUT.PUT_LINE('Partition Name: ' || v_tnd_name);
    EXECUTE IMMEDIATE 'ALTER TABLE ' || p_target_schema || '.' || p_target_table || ' ADD PARTITION ' || v_tnd_name || ' VALUES (DATE ''' || TO_CHAR(p_tnd_filter, 'YYYY-MM-DD') || ''') TABLESPACE ' || V_TABLESPACE_NAME;
    DBMS_OUTPUT.PUT_LINE('Partition ' || v_tnd_name || ' created.');

    ELSE
    DBMS_OUTPUT.PUT_LINE('Partition ' || v_tnd_name || ' already exists.');
    END IF;

    ELSE
        DBMS_OUTPUT.PUT_LINE('Tables have different or unknown partitioning types.');
    END IF;

    EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE(p_source_table || ' and/or '|| p_target_table || ' is not partitioned.');

END RANGE_OR_LIST_TND;
---------------------------------------------------------------------------------------------------------------------------------------------------
    PROCEDURE TABLECOPY (
        p_source_schema VARCHAR2,
        p_source_table VARCHAR2,
        p_target_schema VARCHAR2,
        p_target_table VARCHAR2,
        p_TRUNCATE BOOLEAN DEFAULT FALSE,
        p_tnd_filter DATE DEFAULT NULL
    ) AS
        v_column_list CLOB;
        v_PARTITION_NAME VARCHAR2(30);
        V_HIGH_VALUE VARCHAR2(4000);
        v_xml_cursor SYS_REFCURSOR;
        v_date_value DATE;
        v_partition_count NUMBER;
        v_source_table_exists BOOLEAN;
        v_target_table_exists BOOLEAN;
        v_common_columns NUMBER;
        v_high_value_t VARCHAR2(4000);
        v_partition_name_t VARCHAR2(30);
        v_partitioned_by_tnd NUMBER;
        v_datafile_paths CLOB := EMPTY_CLOB();
        v_tnd_name VARCHAR2(20);
        v_tnd_partition NUMBER;
        tnd_column NUMBER;
        v_dblink_sql VARCHAR2(20);
   v_partition_type1 VARCHAR2(30);
   v_partition_type2 VARCHAR2(30);

        v_partition_name VARCHAR2(30);
        v_tablespace_name VARCHAR2(30);
        v_tablespace_count NUMBER;
        v_datafile_path VARCHAR2(100);
        v_datafile_size NUMBER;
        v_autoextend_size NUMBER;
        v_bigfile VARCHAR2(10);
        v_datafile_count NUMBER;

BEGIN
--------------------Léteznek a táblák?
    v_source_table_exists := TABLECOPY_PACKAGE.TABLE_EXISTS(p_source_schema, p_source_table);
    IF NOT v_source_table_exists THEN
        RAISE_APPLICATION_ERROR(-20002, 'Table not found: ' || p_source_table);
    END IF;

    v_target_table_exists := TABLECOPY_PACKAGE.TABLE_EXISTS(p_source_schema, p_source_table);
    IF NOT v_target_table_exists THEN
        RAISE_APPLICATION_ERROR(-20002, 'Table not found: ' || p_source_table);
    END IF;

--------------------Vannak közös oszlopaik?
    TABLECOPY_PACKAGE.COMMON_COLUMNS(
    p_source_schema => p_source_schema,
    p_source_table => p_source_table,
    p_target_schema => p_target_schema,
    p_target_table => p_target_table
    );

--------------------Ha nincs TND szűrés...
    IF p_tnd_filter IS NULL THEN
     -----------------HA nincs TND szűrés és truncatelni kell...
     IF p_TRUNCATE = TRUE THEN
     EXECUTE IMMEDIATE 'TRUNCATE TABLE ' || p_target_schema || '.' || p_target_table;
     DBMS_OUTPUT.PUT_LINE(p_target_table || ' truncated');
     END IF;

    -----------------Ha nincs TND szűrés Range vagy List partíciók + táblaterek, adatok másolása
    TABLECOPY_PACKAGE.RANGE_OR_LIST(
    p_source_schema => p_source_schema,
    p_source_table => p_source_table,
    p_target_schema => p_target_schema,
    p_target_table => p_target_table
    );

   TABLECOPY_PACKAGE.COPY_COLUMNS
    (p_source_schema => p_source_schema,
     p_source_table => p_source_table,
     p_target_schema => p_target_schema,
     p_target_table => p_target_table
     );
--------------------Ha van TND szűrés...
     ELSE
     -----------------HA van TND szűrés és truncatelni kell...
     IF p_TRUNCATE = TRUE THEN
    TABLECOPY_PACKAGE.TRUNCATE_TND_TABLE
    (p_tnd_filter => p_tnd_filter,
     p_source_schema => p_source_schema,
     p_source_table => p_source_table,
     p_target_schema => p_target_schema,
     p_target_table => p_target_table
     );
     END IF;

    v_tnd_name := 'P_' || TO_CHAR(p_tnd_filter, 'YYYYMMDD');

    SELECT COUNT(*)
    INTO v_tnd_partition
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_NAME = p_target_table
    AND TABLE_OWNER = p_target_schema
    AND PARTITION_NAME = v_tnd_name;
    --------------------Ha van TND szűrés, de nincs meg a hozzátartozó partíció
    IF v_tnd_partition = 0 THEN

    SELECT COUNT(*)
    INTO v_partition_count
    FROM DBA_TAB_PARTITIONS
    WHERE TABLE_NAME = p_target_table
    AND TABLE_OWNER = p_target_schema;

    IF v_partition_count > 0 THEN

    --------------------Ha van TND szűrés, de nincs meg a hozzátartozó partíció, de partícionált, Range vagy List partíciók + táblaterek, adatok másolása
    TABLECOPY_PACKAGE.RANGE_OR_LIST_TND(
    p_tnd_filter => p_tnd_filter,
    p_source_schema => p_source_schema,
    p_source_table => p_source_table,
    p_target_schema => p_target_schema,
    p_target_table => p_target_table
    );

   TABLECOPY_PACKAGE.COPY_COLUMNS
    (p_source_schema => p_source_schema,
     p_source_table => p_source_table,
     p_target_schema => p_target_schema,
     p_target_table => p_target_table
     );
-----------------Ha van TND szűrés, de nincs meg a hozzátartozó partíció, nem partícionált, adatok másolása
    ELSE
    TABLECOPY_PACKAGE.COPY_COLUMNS_TND(
    p_tnd_filter => p_tnd_filter,
    p_source_schema => p_source_schema,
    p_source_table => p_source_table,
    p_target_schema => p_target_schema,
    p_target_table => p_target_table
    );

    END IF;
    ELSE
    --------------------Ha van TND szűrés, megvan a hozzátartozó partíció, Range vagy List partíciók + táblaterek, adatok másolása

    TABLECOPY_PACKAGE.RANGE_OR_LIST_TND(
    p_tnd_filter => p_tnd_filter,
    p_source_schema => p_source_schema,
    p_source_table => p_source_table,
    p_target_schema => p_target_schema,
    p_target_table => p_target_table
    );

    TABLECOPY_PACKAGE.COPY_COLUMNS_TND(
    p_tnd_filter => p_tnd_filter,
    p_source_schema => p_source_schema,
    p_source_table => p_source_table,
    p_target_schema => p_target_schema,
    p_target_table => p_target_table
    );

    END IF;

 END IF;
COMMIT;
END TABLECOPY;
END TABLECOPY_PACKAGE;
/
