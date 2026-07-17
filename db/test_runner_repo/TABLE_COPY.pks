CREATE OR REPLACE PACKAGE TABLECOPY_PACKAGE AS
    FUNCTION SOURCE_EXISTS(
        p_TABLE_OWNER VARCHAR2,
        p_TABLE_NAME VARCHAR2
    ) RETURN BOOLEAN;

    FUNCTION TARGET_EXISTS(
        p_TABLE_OWNER VARCHAR2,
        p_TABLE_NAME VARCHAR2
    ) RETURN BOOLEAN;

    PROCEDURE TABLECOPY (
        p_source_schema VARCHAR2,
        p_source_table VARCHAR2,
        p_target_schema VARCHAR2,
        p_target_table VARCHAR2,
        p_truncate BOOLEAN DEFAULT FALSE,
        p_tnd_filter DATE DEFAULT NULL,
        p_row_limit NUMBER DEFAULT NULL
    );

    PROCEDURE TABLECOPY_MAX (
        p_source_schema VARCHAR2,
        p_source_table VARCHAR2,
        p_target_schema VARCHAR2,
        p_target_table VARCHAR2,
        p_truncate BOOLEAN DEFAULT FALSE,
        p_row_limit NUMBER DEFAULT NULL
    );

    PROCEDURE TABLECOPY_CURRENT (
        p_source_schema VARCHAR2,
        p_source_table VARCHAR2,
        p_target_schema VARCHAR2,
        p_target_table VARCHAR2,
        p_truncate BOOLEAN DEFAULT FALSE,
        p_row_limit NUMBER DEFAULT NULL
    );
END TABLECOPY_PACKAGE;
