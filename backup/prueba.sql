--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0
-- Dumped by pg_dump version 17.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: FILE; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA "FILE";



--
-- Name: MATERIAL; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA "MATERIAL";



--
-- Name: PAYMENT; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA "PAYMENT";



--
-- Name: USER; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA "USER";



--
-- Name: FU_FI_FILEPKG_GETMTFILEBYFILEIDANDMTID(integer, integer); Type: FUNCTION; Schema: FILE; Owner: postgres
--

CREATE FUNCTION "FILE"."FU_FI_FILEPKG_GETMTFILEBYFILEIDANDMTID"(p_fileid integer, p_mtid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_mtfile integer;
BEGIN
    SELECT ftfmf."mtFile" INTO v_mtfile
    FROM "FILE"."TB_FILE_MTFILES" ftfmf
    WHERE ftfmf."fileId" = p_fileid
      AND ftfmf."mtId" = p_mtid;
    RETURN v_mtfile;
END;
$$;



--
-- Name: SP_FI_FILEPKG_AGREGARARCHIVO(text); Type: PROCEDURE; Schema: FILE; Owner: postgres
--

CREATE PROCEDURE "FILE"."SP_FI_FILEPKG_AGREGARARCHIVO"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
	V_NAME "FILE"."TB_FILE_FILES"."name"%TYPE;
	V_MD5 "FILE"."TB_FILE_FILES"."md5"%TYPE;
	V_BUCKET "FILE"."TB_FILE_FILES"."bucket"%TYPE;
	V_USERID "FILE"."TB_FILE_FILES"."userId"%TYPE;
BEGIN
    P_ID := nextval('"FILE"."TB_FILE_FILES_fileId_seq"');
	V_DATAJSON := p_datatype::json;
	V_NAME := V_DATAJSON->>'name';
	V_MD5 := V_DATAJSON->>'md5';
	V_BUCKET := V_DATAJSON->>'bucket';
	V_USERID := V_DATAJSON->>'userId';
	INSERT INTO "FILE"."TB_FILE_FILES"
		("fileId", "name", "md5", "bucket", "userId")
	VALUES
		(
			P_ID,
			V_NAME,
			V_MD5,
			V_BUCKET,
			V_USERID
		);
END;
$$;



--
-- Name: SP_FI_FILEPKG_AGREGARMTFILE(text); Type: PROCEDURE; Schema: FILE; Owner: postgres
--

CREATE PROCEDURE "FILE"."SP_FI_FILEPKG_AGREGARMTFILE"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_FILEID "FILE"."TB_FILE_MTFILES"."fileId"%TYPE;
    V_MTID "FILE"."TB_FILE_MTFILES"."mtId"%TYPE;
BEGIN
    V_DATAJSON := p_datatype::json;
    V_FILEID := V_DATAJSON->>'fileId';
    V_MTID := V_DATAJSON->>'mtId';
	P_ID := "FILE"."FU_FI_FILEPKG_GETMTFILEBYFILEIDANDMTID"(V_FILEID, V_MTID);
	IF p_id IS NULL THEN
		P_ID := nextval('"FILE"."TB_FILE_MTFILES_mtFile_seq"');
		INSERT INTO "FILE"."TB_FILE_MTFILES"
			("mtFile", "fileId", "mtId")
		VALUES
			(
				P_ID,
				V_FILEID,
				V_MTID
			);
	END IF;
END;
$$;



--
-- Name: SP_FI_FILEPKG_ELIMINARARCHIVO(numeric); Type: PROCEDURE; Schema: FILE; Owner: postgres
--

CREATE PROCEDURE "FILE"."SP_FI_FILEPKG_ELIMINARARCHIVO"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
	DELETE FROM "FILE"."TB_FILE_MTFILES" 
	WHERE "fileId" = p_id;
	DELETE FROM "FILE"."TB_FILE_FILES" 
	WHERE "fileId" = p_id;
END;
$$;



--
-- Name: FU_MA_MATERIALPKG_GETMATERIALIDBYNAME(text); Type: FUNCTION; Schema: MATERIAL; Owner: postgres
--

CREATE FUNCTION "MATERIAL"."FU_MA_MATERIALPKG_GETMATERIALIDBYNAME"(p_materialname text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_materialId integer;
BEGIN
    SELECT 
        mtmm."materialId" INTO v_materialId
    FROM "MATERIAL"."TB_MATERIAL_MATERIALS" mtmm
    WHERE mtmm."name" = p_materialname;
    RETURN v_materialId;
END;
$$;



--
-- Name: FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID(integer, integer); Type: FUNCTION; Schema: MATERIAL; Owner: postgres
--

CREATE FUNCTION "MATERIAL"."FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID"(p_materialid integer, p_thicknessid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_mtid integer;
BEGIN
    SELECT 
		mtmmt."mtId" into v_mtid
	FROM "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS" mtmmt
	WHERE mtmmt."materialId" = p_materialid
		and mtmmt."thicknessId" = p_thicknessid;
    RETURN v_mtid;
END;
$$;



--
-- Name: FU_MA_MATERIALPKG_GETTHICKNESSIDBYNAME(text); Type: FUNCTION; Schema: MATERIAL; Owner: postgres
--

CREATE FUNCTION "MATERIAL"."FU_MA_MATERIALPKG_GETTHICKNESSIDBYNAME"(p_thicknessname text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_thicknessId integer;
BEGIN
    SELECT 
		mtmt."thicknessId" into v_thicknessId
	FROM "MATERIAL"."TB_MATERIAL_THICKNESS" mtmt
	WHERE mtmt."name" = p_thicknessName;
    RETURN v_thicknessId;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_ACTUALIZARMATERIAL(text, numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_ACTUALIZARMATERIAL"(IN p_datatype text, IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_NAME "MATERIAL"."TB_MATERIAL_MATERIALS"."name"%TYPE;
    V_PRICE "MATERIAL"."TB_MATERIAL_MATERIALS"."price"%TYPE;
BEGIN
    V_DATAJSON := p_datatype::json;
    V_NAME  := V_DATAJSON->>'name';
    V_PRICE := (V_DATAJSON->>'price')::integer;
    UPDATE "MATERIAL"."TB_MATERIAL_MATERIALS"
    SET
        "name" = COALESCE(V_NAME, "name"),
        "price" = COALESCE(V_PRICE, "price"),
        "lastmodification" = NOW(),
		"deleted" = false
    WHERE "materialId" = p_id;

END;
$$;



--
-- Name: SP_MA_MATERIALPKG_ACTUALIZARTHICKNESS(text, numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_ACTUALIZARTHICKNESS"(IN p_datatype text, IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_NAME "MATERIAL"."TB_MATERIAL_THICKNESS"."name"%TYPE;
    V_PRICE "MATERIAL"."TB_MATERIAL_THICKNESS"."price"%TYPE;
BEGIN
    V_DATAJSON := p_datatype::json;
    V_NAME  := V_DATAJSON->>'name';
    V_PRICE := (V_DATAJSON->>'price')::integer;
    UPDATE "MATERIAL"."TB_MATERIAL_THICKNESS" SET
        "name"=COALESCE(V_NAME, "name"), 
		"price"=COALESCE(V_PRICE, "price"), 
		"lastmodification"=NOW(),
		"deleted" = false
     WHERE "thicknessId" = p_id;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_AGREGARMATERIAL(text); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_AGREGARMATERIAL"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_NAME "MATERIAL"."TB_MATERIAL_MATERIALS"."name"%TYPE;
    V_PRICE "MATERIAL"."TB_MATERIAL_MATERIALS"."price"%TYPE;
BEGIN
    V_DATAJSON := p_datatype::json;
    V_NAME  := V_DATAJSON->>'name';
    V_PRICE := (V_DATAJSON->>'price')::integer;
	p_id := "MATERIAL"."FU_MA_MATERIALPKG_GETMATERIALIDBYNAME"(V_NAME);
	RAISE NOTICE 'Resultado p_id: % name: %', p_id, V_NAME;
	IF p_id IS NOT NULL THEN
		CALL "MATERIAL"."SP_MA_MATERIALPKG_ACTUALIZARMATERIAL"(p_datatype, p_id);
	ELSE
	    p_id := nextval('"MATERIAL"."TB_MATERIAL_MATERIALS_materialId_seq"');
	    INSERT INTO "MATERIAL"."TB_MATERIAL_MATERIALS"
	        ("materialId", "name", "price", "lastmodification")
	    VALUES
	        (
	            p_id,
	            V_NAME,
	            V_PRICE,
	            NOW()
	        );
	END IF;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_AGREGARMATERIALTHICKNESS(text, numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_AGREGARMATERIALTHICKNESS"(IN p_datatype text, INOUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_MATERIALID "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"."materialId"%TYPE;
    V_THICKNESSID "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"."thicknessId"%TYPE;
BEGIN
	-- Convertir JSON
	V_DATAJSON := p_datatype::json;
	-- Extraer campos
	V_MATERIALID  := V_DATAJSON->>'materialId';
	V_THICKNESSID := V_DATAJSON->>'thicknessId';
	p_id := "MATERIAL"."FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID"(V_MATERIALID, V_THICKNESSID);
	RAISE NOTICE 'Resultado p_id: %', p_id;
	IF p_id IS NOT NULL THEN
		CALL "MATERIAL"."SP_MA_MATERIALPKG_RESTAURARMATERIALTHICKNESS"(p_id);
    ELSE
        p_id := nextval('"MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS_mtId_seq"');
	    -- Insertar
	    INSERT INTO "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
	        ("mtId", "materialId", "thicknessId")
	    VALUES
	        (
	            p_id,
	            V_MATERIALID,
	            V_THICKNESSID
	        );
    END IF;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_AGREGARTHICKNESS(text); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_AGREGARTHICKNESS"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
	p_dos numeric;
    V_NAME "MATERIAL"."TB_MATERIAL_THICKNESS"."name"%TYPE;
    V_PRICE "MATERIAL"."TB_MATERIAL_THICKNESS"."price"%TYPE;
BEGIN
    V_DATAJSON := p_datatype::json;
    V_NAME  := V_DATAJSON->>'name';
    V_PRICE := (V_DATAJSON->>'price')::integer;
	p_id := "MATERIAL"."FU_MA_MATERIALPKG_GETTHICKNESSIDBYNAME"(V_NAME);
	IF p_id IS NOT NULL THEN
		CALL "MATERIAL"."SP_MA_MATERIALPKG_ACTUALIZARTHICKNESS"(p_datatype, p_id);
	ELSE
		p_id := nextval('"MATERIAL"."TB_MATERIAL_THICKNESS_thicknessId_seq"');
	    INSERT INTO "MATERIAL"."TB_MATERIAL_THICKNESS"
	        ("thicknessId", "name", "price", "lastmodification")
	    VALUES
	        (
	            p_id,
	            V_NAME,
	            V_PRICE,
	            NOW()
	        );
	END IF;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_ELIMINARMATERIAL(numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_ELIMINARMATERIAL"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE "MATERIAL"."TB_MATERIAL_MATERIALS"
    SET
        "deleted"=true
    WHERE "materialId" = p_id;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_ELIMINARMATERIALTHICKNESS(numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_ELIMINARMATERIALTHICKNESS"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
    SET
        "deleted"=true
    WHERE "mtId" = p_id;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_ELIMINARTHICKNESS(numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_ELIMINARTHICKNESS"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE "MATERIAL"."TB_MATERIAL_THICKNESS"
    SET
        "deleted"=true
    WHERE "thicknessId" = p_id;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_RESTAURARMATERIAL(numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_RESTAURARMATERIAL"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE "MATERIAL"."TB_MATERIAL_MATERIAL"
    SET
        "deleted"  = false
    WHERE "materialId" = p_id;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_RESTAURARMATERIALTHICKNESS(numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_RESTAURARMATERIALTHICKNESS"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
    SET
        "deleted"  = false
    WHERE "mtId" = p_id;
END;
$$;



--
-- Name: SP_MA_MATERIALPKG_RESTAURARTHICKNESS(numeric); Type: PROCEDURE; Schema: MATERIAL; Owner: postgres
--

CREATE PROCEDURE "MATERIAL"."SP_MA_MATERIALPKG_RESTAURARTHICKNESS"(IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE "MATERIAL"."TB_MATERIAL_THICKNESS"
    SET
        "deleted"  = false
    WHERE "thicknessId" = p_id;
END;
$$;



--
-- Name: SP_PA_PAYMENTPKG_AGREGARIMTPAYMENT(text); Type: PROCEDURE; Schema: PAYMENT; Owner: postgres
--

CREATE PROCEDURE "PAYMENT"."SP_PA_PAYMENTPKG_AGREGARIMTPAYMENT"(IN p_datatype text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_MTID "PAYMENT"."TB_PAYMENT_MTPAYMENT"."mtId"%TYPE;
    V_PAYMENTID "PAYMENT"."TB_PAYMENT_MTPAYMENT"."paymentId"%TYPE;
    V_AMOUNT "PAYMENT"."TB_PAYMENT_MTPAYMENT"."amount"%TYPE;
    p_id integer;
BEGIN
    -- Generar nuevo ID
    p_id := nextval('"PAYMENT"."TB_PAYMENT_MTPAYMENT_mtPayment_seq"');

    -- Convertir JSON
    V_DATAJSON := p_datatype::json;

    -- Extraer campos
    V_MTID      := (V_DATAJSON->>'mtId')::integer;
    V_PAYMENTID := (V_DATAJSON->>'paymentId')::integer;
    V_AMOUNT := (V_DATAJSON->>'amount')::integer;

    -- Insertar registro
    INSERT INTO "PAYMENT"."TB_PAYMENT_MTPAYMENT"
        ("mtPayment", "mtId", "paymentId", "amount")
    VALUES
        (
            p_id,
            V_MTID,
            V_PAYMENTID,
            V_AMOUNT
        );
END;
$$;



--
-- Name: SP_PA_PAYMENTPKG_AGREGARMTPAYMENT(text); Type: PROCEDURE; Schema: PAYMENT; Owner: postgres
--

CREATE PROCEDURE "PAYMENT"."SP_PA_PAYMENTPKG_AGREGARMTPAYMENT"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;
    V_MTID "PAYMENT"."TB_PAYMENT_MTPAYMENT"."mtId"%TYPE;
    V_PAYMENTID "PAYMENT"."TB_PAYMENT_MTPAYMENT"."paymentId"%TYPE;
    V_AMOUNT "PAYMENT"."TB_PAYMENT_MTPAYMENT"."amount"%TYPE;
BEGIN
    -- Generar nuevo ID
    p_id := nextval('"PAYMENT"."TB_PAYMENT_MTPAYMENT_mtPayment_seq"');

    -- Convertir JSON
    V_DATAJSON := p_datatype::json;

    -- Extraer campos
    V_MTID      := (V_DATAJSON->>'mtId')::integer;
    V_PAYMENTID := (V_DATAJSON->>'paymentId')::integer;
	V_AMOUNT := (V_DATAJSON->>'amount')::integer;

    -- Insertar registro
    INSERT INTO "PAYMENT"."TB_PAYMENT_MTPAYMENT"
        ("mtPayment", "mtId", "paymentId", "amount")
    VALUES
        (
            p_id,
            V_MTID,
            V_PAYMENTID,
			V_AMOUNT
        );
END;
$$;



--
-- Name: SP_PA_PAYMENTPKG_AGREGARPAYMENT(text); Type: PROCEDURE; Schema: PAYMENT; Owner: postgres
--

CREATE PROCEDURE "PAYMENT"."SP_PA_PAYMENTPKG_AGREGARPAYMENT"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;

    V_P_ID "PAYMENT"."TB_PAYMENT_PAYMENTS"."p_id"%TYPE;
    V_STATUS "PAYMENT"."TB_PAYMENT_PAYMENTS".status%TYPE;
    V_REFERENCE "PAYMENT"."TB_PAYMENT_PAYMENTS".reference%TYPE;
    V_PAYMENTMETHODID "PAYMENT"."TB_PAYMENT_PAYMENTS"."paymentMethodId"%TYPE;
    V_MT TEXT[];
    V_MTID INTEGER;
    V_AMOUNT "PAYMENT"."TB_PAYMENT_MTPAYMENT"."amount"%TYPE;
BEGIN
    -- Generar nuevo ID
    p_id := nextval('"PAYMENT"."TB_PAYMENT_PAYMENTS_paymentId_seq"');

    -- Convertir JSON a objeto
    V_DATAJSON := p_datatype::json;

    -- Extraer campos desde el JSON
    V_P_ID             := V_DATAJSON->>'p_id';
    V_STATUS           := V_DATAJSON->>'status';
    V_REFERENCE        := V_DATAJSON->>'reference';
    V_PAYMENTMETHODID  := (V_DATAJSON->>'paymentMethodId')::integer;
    V_MT := string_to_array(split_part(V_REFERENCE, '@', 1), '-');
    V_AMOUNT := (V_MT[4])::integer;
    V_MTID := "MATERIAL"."FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID"(
        V_MT[2]::INTEGER, 
        V_MT[3]::INTEGER
    );
    INSERT INTO "PAYMENT"."TB_PAYMENT_PAYMENTS"
        (
            "paymentId", 
            "p_id", 
            "status", 
            "reference", 
            "createdAt", 
            "paymentMethodId"
        )
    VALUES
        (
            p_id,
            V_P_ID,
            V_STATUS,
            V_REFERENCE,
            NOW(),
            V_PAYMENTMETHODID
        );
    CALL "PAYMENT"."SP_PA_PAYMENTPKG_AGREGARIMTPAYMENT"(
        '{"mtId":' || V_MTID::TEXT ||', "paymentId":' || p_id::TEXT || ', "amount":' || V_AMOUNT::TEXT || '}'
    );
END;
$$;



--
-- Name: SP_USU_USERPKG_AGREGARUSUARIO(text); Type: PROCEDURE; Schema: USER; Owner: postgres
--

CREATE PROCEDURE "USER"."SP_USU_USERPKG_AGREGARUSUARIO"(IN p_datatype text, OUT p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;

    V_NAMES "USER"."TB_USU_USERS".names%TYPE;
    V_LASTNAMES "USER"."TB_USU_USERS"."lastNames"%TYPE;
    V_EMAIL "USER"."TB_USU_USERS".email%TYPE;
    V_ADDRESS "USER"."TB_USU_USERS".address%TYPE;
    V_PASSWORD "USER"."TB_USU_USERS".password%TYPE;
    V_ISADMIN "USER"."TB_USU_USERS"."isAdmin"%TYPE;
    V_PHONE "USER"."TB_USU_USERS".phone%TYPE;
BEGIN
    -- Generar nuevo ID
    p_id := nextval('"USER"."TB_USU_USERS_userId_seq"');

    -- Convertir JSON
    V_DATAJSON := p_datatype::json;

    -- Extraer campos
    V_NAMES     := V_DATAJSON->>'names';
    V_LASTNAMES := V_DATAJSON->>'lastNames';
    V_EMAIL     := V_DATAJSON->>'email';
    V_ADDRESS   := V_DATAJSON->>'address';
    V_PASSWORD  := V_DATAJSON->>'password';
    V_ISADMIN   := (V_DATAJSON->>'isAdmin')::boolean;
    V_PHONE     := (V_DATAJSON->>'phone')::bigint;

    -- Insertar
    INSERT INTO "USER"."TB_USU_USERS"
        ("userId", names, "lastNames", email, address, password, "isAdmin", phone)
    VALUES
        (
            p_id,
            V_NAMES,
            V_LASTNAMES,
            V_EMAIL,
            V_ADDRESS,
            V_PASSWORD,
            COALESCE(V_ISADMIN, false),
            V_PHONE
        );
END;
$$;



--
-- Name: SP_USU_USERPKG_EDITARADDRESSUSUARIO(text, numeric); Type: PROCEDURE; Schema: USER; Owner: postgres
--

CREATE PROCEDURE "USER"."SP_USU_USERPKG_EDITARADDRESSUSUARIO"(IN p_datatype text, IN p_id numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    V_DATAJSON JSON;

    V_ADDRESS "USER"."TB_USU_USERS".address%TYPE;
BEGIN
    V_DATAJSON := p_datatype::json;
    V_ADDRESS   := V_DATAJSON->>'address';
    update "USER"."TB_USU_USERS" set
        address = V_ADDRESS
	WHERE "userId" = p_id;
END;
$$;



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: TB_FILE_FILES; Type: TABLE; Schema: FILE; Owner: postgres
--

CREATE TABLE "FILE"."TB_FILE_FILES" (
    "fileId" integer NOT NULL,
    name character varying(255) NOT NULL,
    md5 character(32) NOT NULL,
    bucket character varying(255) NOT NULL,
    "userId" integer NOT NULL,
    date time without time zone DEFAULT now()
);



--
-- Name: TB_FILE_FILES_fileId_seq; Type: SEQUENCE; Schema: FILE; Owner: postgres
--

CREATE SEQUENCE "FILE"."TB_FILE_FILES_fileId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_FILE_FILES_fileId_seq; Type: SEQUENCE OWNED BY; Schema: FILE; Owner: postgres
--

ALTER SEQUENCE "FILE"."TB_FILE_FILES_fileId_seq" OWNED BY "FILE"."TB_FILE_FILES"."fileId";


--
-- Name: TB_FILE_MTFILES; Type: TABLE; Schema: FILE; Owner: postgres
--

CREATE TABLE "FILE"."TB_FILE_MTFILES" (
    "mtFile" integer NOT NULL,
    "fileId" integer,
    "mtId" integer
);



--
-- Name: TB_FILE_MTFILES_mtFile_seq; Type: SEQUENCE; Schema: FILE; Owner: postgres
--

CREATE SEQUENCE "FILE"."TB_FILE_MTFILES_mtFile_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_FILE_MTFILES_mtFile_seq; Type: SEQUENCE OWNED BY; Schema: FILE; Owner: postgres
--

ALTER SEQUENCE "FILE"."TB_FILE_MTFILES_mtFile_seq" OWNED BY "FILE"."TB_FILE_MTFILES"."mtFile";


--
-- Name: TB_MATERIAL_MATERIALS; Type: TABLE; Schema: MATERIAL; Owner: postgres
--

CREATE TABLE "MATERIAL"."TB_MATERIAL_MATERIALS" (
    "materialId" integer NOT NULL,
    name character varying(255) NOT NULL,
    price integer NOT NULL,
    lastmodification timestamp without time zone,
    deleted boolean DEFAULT false
);



--
-- Name: TB_MATERIAL_MATERIALS_materialId_seq; Type: SEQUENCE; Schema: MATERIAL; Owner: postgres
--

CREATE SEQUENCE "MATERIAL"."TB_MATERIAL_MATERIALS_materialId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_MATERIAL_MATERIALS_materialId_seq; Type: SEQUENCE OWNED BY; Schema: MATERIAL; Owner: postgres
--

ALTER SEQUENCE "MATERIAL"."TB_MATERIAL_MATERIALS_materialId_seq" OWNED BY "MATERIAL"."TB_MATERIAL_MATERIALS"."materialId";


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS; Type: TABLE; Schema: MATERIAL; Owner: postgres
--

CREATE TABLE "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS" (
    "mtId" integer NOT NULL,
    "materialId" integer,
    "thicknessId" integer,
    deleted boolean DEFAULT false
);



--
-- Name: TB_MATERIAL_MATERIALTHICKNESS_mtId_seq; Type: SEQUENCE; Schema: MATERIAL; Owner: postgres
--

CREATE SEQUENCE "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS_mtId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_MATERIAL_MATERIALTHICKNESS_mtId_seq; Type: SEQUENCE OWNED BY; Schema: MATERIAL; Owner: postgres
--

ALTER SEQUENCE "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS_mtId_seq" OWNED BY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"."mtId";


--
-- Name: TB_MATERIAL_THICKNESS; Type: TABLE; Schema: MATERIAL; Owner: postgres
--

CREATE TABLE "MATERIAL"."TB_MATERIAL_THICKNESS" (
    "thicknessId" integer NOT NULL,
    name character varying(255) NOT NULL,
    price integer NOT NULL,
    lastmodification timestamp without time zone NOT NULL,
    deleted boolean DEFAULT false
);



--
-- Name: TB_MATERIAL_THICKNESS_thicknessId_seq; Type: SEQUENCE; Schema: MATERIAL; Owner: postgres
--

CREATE SEQUENCE "MATERIAL"."TB_MATERIAL_THICKNESS_thicknessId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_MATERIAL_THICKNESS_thicknessId_seq; Type: SEQUENCE OWNED BY; Schema: MATERIAL; Owner: postgres
--

ALTER SEQUENCE "MATERIAL"."TB_MATERIAL_THICKNESS_thicknessId_seq" OWNED BY "MATERIAL"."TB_MATERIAL_THICKNESS"."thicknessId";


--
-- Name: TB_PAYMENT_MTPAYMENT; Type: TABLE; Schema: PAYMENT; Owner: postgres
--

CREATE TABLE "PAYMENT"."TB_PAYMENT_MTPAYMENT" (
    "mtPayment" integer NOT NULL,
    "mtId" integer,
    "paymentId" integer,
    amount integer DEFAULT 0 NOT NULL
);



--
-- Name: TB_PAYMENT_MTPAYMENT_mtPayment_seq; Type: SEQUENCE; Schema: PAYMENT; Owner: postgres
--

CREATE SEQUENCE "PAYMENT"."TB_PAYMENT_MTPAYMENT_mtPayment_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_PAYMENT_MTPAYMENT_mtPayment_seq; Type: SEQUENCE OWNED BY; Schema: PAYMENT; Owner: postgres
--

ALTER SEQUENCE "PAYMENT"."TB_PAYMENT_MTPAYMENT_mtPayment_seq" OWNED BY "PAYMENT"."TB_PAYMENT_MTPAYMENT"."mtPayment";


--
-- Name: TB_PAYMENT_PAYMENTS; Type: TABLE; Schema: PAYMENT; Owner: postgres
--

CREATE TABLE "PAYMENT"."TB_PAYMENT_PAYMENTS" (
    "paymentId" integer NOT NULL,
    p_id character varying(255) NOT NULL,
    status character varying(255) NOT NULL,
    reference character varying(255) NOT NULL,
    "createdAt" timestamp without time zone NOT NULL,
    "paymentMethodId" integer NOT NULL
);



--
-- Name: TB_PAYMENT_PAYMENTSMETHODS; Type: TABLE; Schema: PAYMENT; Owner: postgres
--

CREATE TABLE "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS" (
    "paymentMethodId" integer NOT NULL,
    "paymentMethod" character varying(255)
);



--
-- Name: TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq; Type: SEQUENCE; Schema: PAYMENT; Owner: postgres
--

CREATE SEQUENCE "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq; Type: SEQUENCE OWNED BY; Schema: PAYMENT; Owner: postgres
--

ALTER SEQUENCE "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq" OWNED BY "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS"."paymentMethodId";


--
-- Name: TB_PAYMENT_PAYMENTS_paymentId_seq; Type: SEQUENCE; Schema: PAYMENT; Owner: postgres
--

CREATE SEQUENCE "PAYMENT"."TB_PAYMENT_PAYMENTS_paymentId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_PAYMENT_PAYMENTS_paymentId_seq; Type: SEQUENCE OWNED BY; Schema: PAYMENT; Owner: postgres
--

ALTER SEQUENCE "PAYMENT"."TB_PAYMENT_PAYMENTS_paymentId_seq" OWNED BY "PAYMENT"."TB_PAYMENT_PAYMENTS"."paymentId";


--
-- Name: TB_USU_USERS; Type: TABLE; Schema: USER; Owner: postgres
--

CREATE TABLE "USER"."TB_USU_USERS" (
    "userId" integer NOT NULL,
    names character varying(50) NOT NULL,
    "lastNames" character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    address character varying(255) NOT NULL,
    password character(64) NOT NULL,
    "isAdmin" boolean DEFAULT false,
    phone bigint NOT NULL
);



--
-- Name: TB_USU_USERS_userId_seq; Type: SEQUENCE; Schema: USER; Owner: postgres
--

CREATE SEQUENCE "USER"."TB_USU_USERS_userId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: TB_USU_USERS_userId_seq; Type: SEQUENCE OWNED BY; Schema: USER; Owner: postgres
--

ALTER SEQUENCE "USER"."TB_USU_USERS_userId_seq" OWNED BY "USER"."TB_USU_USERS"."userId";


--
-- Name: TB_FILE_FILES fileId; Type: DEFAULT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_FILES" ALTER COLUMN "fileId" SET DEFAULT nextval('"FILE"."TB_FILE_FILES_fileId_seq"'::regclass);


--
-- Name: TB_FILE_MTFILES mtFile; Type: DEFAULT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_MTFILES" ALTER COLUMN "mtFile" SET DEFAULT nextval('"FILE"."TB_FILE_MTFILES_mtFile_seq"'::regclass);


--
-- Name: TB_MATERIAL_MATERIALS materialId; Type: DEFAULT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALS" ALTER COLUMN "materialId" SET DEFAULT nextval('"MATERIAL"."TB_MATERIAL_MATERIALS_materialId_seq"'::regclass);


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS mtId; Type: DEFAULT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS" ALTER COLUMN "mtId" SET DEFAULT nextval('"MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS_mtId_seq"'::regclass);


--
-- Name: TB_MATERIAL_THICKNESS thicknessId; Type: DEFAULT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_THICKNESS" ALTER COLUMN "thicknessId" SET DEFAULT nextval('"MATERIAL"."TB_MATERIAL_THICKNESS_thicknessId_seq"'::regclass);


--
-- Name: TB_PAYMENT_MTPAYMENT mtPayment; Type: DEFAULT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_MTPAYMENT" ALTER COLUMN "mtPayment" SET DEFAULT nextval('"PAYMENT"."TB_PAYMENT_MTPAYMENT_mtPayment_seq"'::regclass);


--
-- Name: TB_PAYMENT_PAYMENTS paymentId; Type: DEFAULT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_PAYMENTS" ALTER COLUMN "paymentId" SET DEFAULT nextval('"PAYMENT"."TB_PAYMENT_PAYMENTS_paymentId_seq"'::regclass);


--
-- Name: TB_PAYMENT_PAYMENTSMETHODS paymentMethodId; Type: DEFAULT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS" ALTER COLUMN "paymentMethodId" SET DEFAULT nextval('"PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq"'::regclass);


--
-- Name: TB_USU_USERS userId; Type: DEFAULT; Schema: USER; Owner: postgres
--

ALTER TABLE ONLY "USER"."TB_USU_USERS" ALTER COLUMN "userId" SET DEFAULT nextval('"USER"."TB_USU_USERS_userId_seq"'::regclass);


--
-- Data for Name: TB_FILE_FILES; Type: TABLE DATA; Schema: FILE; Owner: postgres
--

COPY "FILE"."TB_FILE_FILES" ("fileId", name, md5, bucket, "userId", date) FROM stdin;
44	figura (1).dxf	701bfe94cf0a7330b1117665a0f6a70a	original	2	13:42:33.598237
45	panel_ (1).dxf	f4ee1799114bd0eeaede4b22a577cb32	original	2	14:53:11.449309
46	7cueros.dxf	9a09ef15ce4dc8bbca618c9df732c1f7	original	2	19:52:34.114175
49	platina sanduche.dxf	7713a9cdcf9a6d9c818f5ada286b5414	original	2	23:27:02.582285
51	prueba__.dxf	8ce2c0b650d5f203c085c3bc9c22db26	original	2	23:27:35.989726
\.


--
-- Data for Name: TB_FILE_MTFILES; Type: TABLE DATA; Schema: FILE; Owner: postgres
--

COPY "FILE"."TB_FILE_MTFILES" ("mtFile", "fileId", "mtId") FROM stdin;
81	44	7
82	44	16
83	45	16
84	46	16
\.


--
-- Data for Name: TB_MATERIAL_MATERIALS; Type: TABLE DATA; Schema: MATERIAL; Owner: postgres
--

COPY "MATERIAL"."TB_MATERIAL_MATERIALS" ("materialId", name, price, lastmodification, deleted) FROM stdin;
2	acero	10000	2025-11-16 01:36:30.923046	t
6	sin pelo	10	2025-11-25 14:23:23.229045	t
5	nuevo material	1000	2025-11-25 14:18:20.828258	t
7	material1	1000	2025-11-25 14:36:11.362093	t
9	material3	1000	2025-11-25 14:45:17.583528	t
10	material 3	10000	2025-11-25 14:46:28.044645	t
8	material2	1000	2025-11-25 14:37:27.757275	t
11	ahora si	10	2025-11-25 14:48:44.911429	t
12	eliminar	1000	2025-11-25 14:50:17.743407	t
3	Cr acotado	10000	2025-12-04 18:27:13.916515	t
14	CR	0	2025-12-06 18:00:30.956172	f
18	cr	0	2025-12-06 18:00:36.832894	t
30	MAYUSCULAS	0	2025-12-06 17:59:38.01714	t
16	nuevo material xd	1000	2025-12-06 13:01:49.55698	t
13	star man	1000	2025-12-06 12:44:23.382244	t
4	Un nombre bonito	1000	2025-12-04 18:44:55.680038	t
\.


--
-- Data for Name: TB_MATERIAL_MATERIALTHICKNESS; Type: TABLE DATA; Schema: MATERIAL; Owner: postgres
--

COPY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS" ("mtId", "materialId", "thicknessId", deleted) FROM stdin;
8	3	12	f
13	4	17	f
12	3	17	f
7	4	11	f
9	3	11	t
14	13	11	t
16	14	19	f
19	14	17	t
18	14	11	t
17	14	18	t
15	13	18	t
21	13	17	f
20	13	19	f
\.


--
-- Data for Name: TB_MATERIAL_THICKNESS; Type: TABLE DATA; Schema: MATERIAL; Owner: postgres
--

COPY "MATERIAL"."TB_MATERIAL_THICKNESS" ("thicknessId", name, price, lastmodification, deleted) FROM stdin;
12	pepe	100	2025-11-16 03:19:48.130092	t
14	p	10	2025-11-25 19:02:11.664444	t
13	keke	10	2025-11-25 19:01:50.247287	t
17	almacenamiento	100	2025-12-04 18:36:21.165387	f
11	jajajaja	10000	2025-12-04 18:39:50.777695	f
18	nuevo grosor	1000	2025-12-06 13:36:15.019363	f
20	nuevo grasosr de md	500	2025-12-06 13:37:55.324873	t
19	16	0	2025-12-06 18:01:09.965824	f
\.


--
-- Data for Name: TB_PAYMENT_MTPAYMENT; Type: TABLE DATA; Schema: PAYMENT; Owner: postgres
--

COPY "PAYMENT"."TB_PAYMENT_MTPAYMENT" ("mtPayment", "mtId", "paymentId", amount) FROM stdin;
1	\N	\N	0
2	\N	\N	0
3	\N	\N	0
4	\N	\N	0
5	\N	\N	0
6	\N	\N	0
7	\N	\N	0
8	\N	\N	0
9	\N	\N	0
10	\N	\N	0
11	\N	\N	0
12	\N	\N	0
13	\N	\N	0
14	\N	\N	0
15	\N	\N	0
16	\N	\N	0
17	\N	\N	0
18	\N	\N	0
19	\N	\N	0
20	\N	\N	0
21	\N	\N	0
22	\N	\N	0
23	\N	\N	0
24	\N	\N	0
30	16	37	1
31	16	38	1
32	16	39	1
33	16	40	1
34	16	41	1
35	16	42	1
36	16	43	1
37	16	44	2
38	16	45	1
\.


--
-- Data for Name: TB_PAYMENT_PAYMENTS; Type: TABLE DATA; Schema: PAYMENT; Owner: postgres
--

COPY "PAYMENT"."TB_PAYMENT_PAYMENTS" ("paymentId", p_id, status, reference, "createdAt", "paymentMethodId") FROM stdin;
3	197466-1763360327-31819	APPROVED	4-4-11@4@2	2025-11-17 01:18:49.284019	2
4	197466-1763794297-41695	APPROVED	4-4-11@pepe@2	2025-11-22 01:51:42.513104	2
5	197466-1763794370-67630	APPROVED	4-4-11@pepe1@2	2025-11-22 01:52:51.749401	2
6	197466-1763794570-55363	APPROVED	4-4-11@pepe2@2	2025-11-22 01:56:12.507617	2
7	197466-1763794889-47630	APPROVED	4-4-11@pepe3@2	2025-11-22 02:01:30.471075	2
8	197466-1763794971-59651	APPROVED	4-4-11@pepe4@2	2025-11-22 02:02:53.078643	2
9	197466-1763798181-85130	APPROVED	4-4-11@pepe5@11	2025-11-22 02:56:26.705478	2
10	197466-1763798277-49425	APPROVED	4-4-11@pepe6@11	2025-11-22 02:57:59.383165	2
11	197466-1763798397-69585	APPROVED	4-4-11@pepe7@11	2025-11-22 03:00:00.15643	2
12	197466-1763798594-66951	APPROVED	4-4-11@pepe8@11	2025-11-22 03:03:16.101646	2
13	197466-1763798857-74135	APPROVED	4-4-11@pepe9@11	2025-11-22 03:07:39.501358	2
14	197466-1763798955-39313	APPROVED	4-4-11@pepe10@11	2025-11-22 03:09:17.329524	2
15	197466-1763799052-78553	APPROVED	4-4-11@pepe11@11	2025-11-22 03:10:54.16077	2
16	197466-1763799398-95521	APPROVED	4-4-11@pepe12@11	2025-11-22 03:16:40.465312	2
17	197466-1764833819-42677	PENDING	28-14-19@1@2	2025-12-04 02:37:00.38794	2
18	197466-1764863279-31340	APPROVED	28-14-19@da0ca557-a007-49d2-953a-259da6a3af5e@2	2025-12-04 10:48:02.406487	2
19	197466-1764869684-72653	APPROVED	28-14-19@a4aeada7-8659-4363-b68d-f7f19dc6c5b3@2	2025-12-04 12:34:46.316204	1
20	197466-1764887738-17041	APPROVED	28-14-19@9d1c7118-3372-4afb-ad71-ce31c9ea2675@2	2025-12-04 17:35:39.841328	1
21	197466-1764887823-74878	APPROVED	28-14-19@78d67bf6-f444-4039-9100-88ac69b05f97@2	2025-12-04 17:37:04.18935	1
22	197466-1765048798-83185	APPROVED	29-14-19-1@06608fcb-8317-4532-bed0-d5e7aec7f9e3@2	2025-12-06 14:19:59.28149	1
23	197466-1765050056-24553	APPROVED	44-14-19-1@9027cd22-7b2c-4fd2-b198-2d9f259cbed6@2	2025-12-06 14:40:56.665088	1
24	197466-1765050472-37001	APPROVED	44-14-19-1@3dd4bf2e-00ec-44ff-a98d-b4041a82dc7f@2	2025-12-06 14:47:53.345809	1
25	197466-1765050735-26051	APPROVED	44-14-19-1@6afff99b-b92b-4465-a8df-4a97371bb283@2	2025-12-06 14:52:15.405437	1
26	197466-1765050817-46209	APPROVED	45-14-19-1@c2a30356-6f2e-41da-a65f-f34b0bd8736b@2	2025-12-06 14:53:37.918301	1
37	197466-1765063612-50079	APPROVED	44-14-19-1@3dbe058e-93ba-4d6b-9b99-346d9a7ff1d6@2	2025-12-06 18:26:53.30711	1
38	197466-1765328423-93422	APPROVED	46-14-19-1@d51ba0bd-f654-480f-b9fa-bbf11d370934@2	2025-12-09 20:00:24.185537	1
39	197466-1765328754-53320	APPROVED	47-14-19-1@e515a9e8-af22-4ad8-9084-74c902547a65@18	2025-12-09 20:05:55.704512	1
40	197466-1765328917-52411	APPROVED	47-14-19-1@6d64dd25-3862-4801-87a0-334685ecec12@18	2025-12-09 20:08:38.989529	1
41	197466-1765338810-54785	APPROVED	47-14-19-1@dd944ef4-c9aa-4900-a118-6dac5a38c4be@18	2025-12-09 22:53:31.337021	1
42	197466-1765338932-92228	APPROVED	47-14-19-1@04602f90-4b0c-4412-a62e-8eb4d17c398b@18	2025-12-09 22:55:33.750376	1
43	197466-1765339167-10002	APPROVED	47-14-19-1@95c89d80-28a8-4790-80be-d0851907d828@18	2025-12-09 22:59:28.336943	1
44	197466-1765339254-21697	APPROVED	47-14-19-2@9147252e-19e4-4021-a4bd-052a367e00e7@18	2025-12-09 23:00:55.892761	1
45	197466-1765339361-24017	APPROVED	47-14-19-1@3fe6919a-66f6-4722-b7f7-9affbae51944@18	2025-12-09 23:02:42.274625	1
\.


--
-- Data for Name: TB_PAYMENT_PAYMENTSMETHODS; Type: TABLE DATA; Schema: PAYMENT; Owner: postgres
--

COPY "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS" ("paymentMethodId", "paymentMethod") FROM stdin;
1	NEQUI
2	CARD
\.


--
-- Data for Name: TB_USU_USERS; Type: TABLE DATA; Schema: USER; Owner: postgres
--

COPY "USER"."TB_USU_USERS" ("userId", names, "lastNames", email, address, password, "isAdmin", phone) FROM stdin;
10	Luis Alejandro	Giraldo Bola+她s	luis.girlado3@utp.edu.co	cualquiera	58bb29ef2543b85195e80bd0870147a70ea151f517fd11c15e230df9e8b6b410	f	3017222568
11	Luis Alejandro	Giraldo Bola+她s	rangotv56@gmail.com	cualquiera	58bb29ef2543b85195e80bd0870147a70ea151f517fd11c15e230df9e8b6b410	f	3017222568
12	l	p	p@gmail.com	cll 9	58bb29ef2543b85195e80bd0870147a70ea151f517fd11c15e230df9e8b6b410	f	3017222568
14	Luis Alejandro	Giraldo Bola+她s	user1@example.com	saf+地lsjfaslk	58bb29ef2543b85195e80bd0870147a70ea151f517fd11c15e230df9e8b6b410	f	3017222568
2	pepe el mago	Maikel	user@example.com	pepeelmago	473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8	t	3017222568
16	Luis Alejandro	Giraldo Bola+她s	imperioloquendo@gmail.com	calle 8 n 8-68	58bb29ef2543b85195e80bd0870147a70ea151f517fd11c15e230df9e8b6b410	f	3017222568
18	Luis Alejandro	Giraldo Bola+她s	carvajalchr@gmail.com	cll 8 n 8 69	58bb29ef2543b85195e80bd0870147a70ea151f517fd11c15e230df9e8b6b410	f	3017222568
\.


--
-- Name: TB_FILE_FILES_fileId_seq; Type: SEQUENCE SET; Schema: FILE; Owner: postgres
--

SELECT pg_catalog.setval('"FILE"."TB_FILE_FILES_fileId_seq"', 53, true);


--
-- Name: TB_FILE_MTFILES_mtFile_seq; Type: SEQUENCE SET; Schema: FILE; Owner: postgres
--

SELECT pg_catalog.setval('"FILE"."TB_FILE_MTFILES_mtFile_seq"', 85, true);


--
-- Name: TB_MATERIAL_MATERIALS_materialId_seq; Type: SEQUENCE SET; Schema: MATERIAL; Owner: postgres
--

SELECT pg_catalog.setval('"MATERIAL"."TB_MATERIAL_MATERIALS_materialId_seq"', 30, true);


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS_mtId_seq; Type: SEQUENCE SET; Schema: MATERIAL; Owner: postgres
--

SELECT pg_catalog.setval('"MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS_mtId_seq"', 21, true);


--
-- Name: TB_MATERIAL_THICKNESS_thicknessId_seq; Type: SEQUENCE SET; Schema: MATERIAL; Owner: postgres
--

SELECT pg_catalog.setval('"MATERIAL"."TB_MATERIAL_THICKNESS_thicknessId_seq"', 20, true);


--
-- Name: TB_PAYMENT_MTPAYMENT_mtPayment_seq; Type: SEQUENCE SET; Schema: PAYMENT; Owner: postgres
--

SELECT pg_catalog.setval('"PAYMENT"."TB_PAYMENT_MTPAYMENT_mtPayment_seq"', 38, true);


--
-- Name: TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq; Type: SEQUENCE SET; Schema: PAYMENT; Owner: postgres
--

SELECT pg_catalog.setval('"PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS_paymentMethodId_seq"', 2, true);


--
-- Name: TB_PAYMENT_PAYMENTS_paymentId_seq; Type: SEQUENCE SET; Schema: PAYMENT; Owner: postgres
--

SELECT pg_catalog.setval('"PAYMENT"."TB_PAYMENT_PAYMENTS_paymentId_seq"', 45, true);


--
-- Name: TB_USU_USERS_userId_seq; Type: SEQUENCE SET; Schema: USER; Owner: postgres
--

SELECT pg_catalog.setval('"USER"."TB_USU_USERS_userId_seq"', 18, true);


--
-- Name: TB_FILE_FILES TB_FILE_FILES_pkey; Type: CONSTRAINT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_FILES"
    ADD CONSTRAINT "TB_FILE_FILES_pkey" PRIMARY KEY ("fileId");


--
-- Name: TB_FILE_MTFILES TB_FILE_MTFILES_pkey; Type: CONSTRAINT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_MTFILES"
    ADD CONSTRAINT "TB_FILE_MTFILES_pkey" PRIMARY KEY ("mtFile");


--
-- Name: TB_FILE_FILES UQ_TB_FILE_FILES_md5_userId; Type: CONSTRAINT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_FILES"
    ADD CONSTRAINT "UQ_TB_FILE_FILES_md5_userId" UNIQUE ("userId", md5);


--
-- Name: TB_MATERIAL_MATERIALS TB_MATERIAL_MATERIALS_pkey; Type: CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALS"
    ADD CONSTRAINT "TB_MATERIAL_MATERIALS_pkey" PRIMARY KEY ("materialId");


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS TB_MATERIAL_MATERIALTHICKNESS_pkey; Type: CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
    ADD CONSTRAINT "TB_MATERIAL_MATERIALTHICKNESS_pkey" PRIMARY KEY ("mtId");


--
-- Name: TB_MATERIAL_THICKNESS TB_MATERIAL_THICKNESS_pkey; Type: CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_THICKNESS"
    ADD CONSTRAINT "TB_MATERIAL_THICKNESS_pkey" PRIMARY KEY ("thicknessId");


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS UQ_MATERIAL_MATERIALTHICKNESS_MATERIALID_THICKNESSID; Type: CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
    ADD CONSTRAINT "UQ_MATERIAL_MATERIALTHICKNESS_MATERIALID_THICKNESSID" UNIQUE ("materialId", "thicknessId");


--
-- Name: TB_MATERIAL_MATERIALS UQ_TB_MATERIAL_MATERIALS_NAME; Type: CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALS"
    ADD CONSTRAINT "UQ_TB_MATERIAL_MATERIALS_NAME" UNIQUE (name);


--
-- Name: TB_MATERIAL_THICKNESS UQ_TB_MATERIAL_THICKNESS_NAME; Type: CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_THICKNESS"
    ADD CONSTRAINT "UQ_TB_MATERIAL_THICKNESS_NAME" UNIQUE (name);


--
-- Name: TB_PAYMENT_MTPAYMENT TB_PAYMENT_MTPAYMENT_pkey; Type: CONSTRAINT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_MTPAYMENT"
    ADD CONSTRAINT "TB_PAYMENT_MTPAYMENT_pkey" PRIMARY KEY ("mtPayment");


--
-- Name: TB_PAYMENT_PAYMENTSMETHODS TB_PAYMENT_PAYMENTSMETHODS_pkey; Type: CONSTRAINT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS"
    ADD CONSTRAINT "TB_PAYMENT_PAYMENTSMETHODS_pkey" PRIMARY KEY ("paymentMethodId");


--
-- Name: TB_PAYMENT_PAYMENTS TB_PAYMENT_PAYMENTS_pkey; Type: CONSTRAINT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_PAYMENTS"
    ADD CONSTRAINT "TB_PAYMENT_PAYMENTS_pkey" PRIMARY KEY ("paymentId");


--
-- Name: TB_USU_USERS TB_USU_USERS_pkey; Type: CONSTRAINT; Schema: USER; Owner: postgres
--

ALTER TABLE ONLY "USER"."TB_USU_USERS"
    ADD CONSTRAINT "TB_USU_USERS_pkey" PRIMARY KEY ("userId");


--
-- Name: TB_USU_USERS UQ_TB_USU_USERS_EMAIL; Type: CONSTRAINT; Schema: USER; Owner: postgres
--

ALTER TABLE ONLY "USER"."TB_USU_USERS"
    ADD CONSTRAINT "UQ_TB_USU_USERS_EMAIL" UNIQUE (email);


--
-- Name: IN_TB_MATERIAL_MATERIALS; Type: INDEX; Schema: MATERIAL; Owner: postgres
--

CREATE INDEX "IN_TB_MATERIAL_MATERIALS" ON "MATERIAL"."TB_MATERIAL_MATERIALS" USING btree (name);


--
-- Name: IN_TB_MATERIAL_THICKNESS; Type: INDEX; Schema: MATERIAL; Owner: postgres
--

CREATE INDEX "IN_TB_MATERIAL_THICKNESS" ON "MATERIAL"."TB_MATERIAL_THICKNESS" USING btree (name);


--
-- Name: TB_FILE_FILES TB_FILE_FILES_userId_fkey; Type: FK CONSTRAINT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_FILES"
    ADD CONSTRAINT "TB_FILE_FILES_userId_fkey" FOREIGN KEY ("userId") REFERENCES "USER"."TB_USU_USERS"("userId");


--
-- Name: TB_FILE_MTFILES TB_FILE_MTFILES_fileId_fkey; Type: FK CONSTRAINT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_MTFILES"
    ADD CONSTRAINT "TB_FILE_MTFILES_fileId_fkey" FOREIGN KEY ("fileId") REFERENCES "FILE"."TB_FILE_FILES"("fileId");


--
-- Name: TB_FILE_MTFILES TB_FILE_MTFILES_mtId_fkey; Type: FK CONSTRAINT; Schema: FILE; Owner: postgres
--

ALTER TABLE ONLY "FILE"."TB_FILE_MTFILES"
    ADD CONSTRAINT "TB_FILE_MTFILES_mtId_fkey" FOREIGN KEY ("mtId") REFERENCES "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"("mtId");


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS TB_MATERIAL_MATERIALTHICKNESS_materialId_fkey; Type: FK CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
    ADD CONSTRAINT "TB_MATERIAL_MATERIALTHICKNESS_materialId_fkey" FOREIGN KEY ("materialId") REFERENCES "MATERIAL"."TB_MATERIAL_MATERIALS"("materialId");


--
-- Name: TB_MATERIAL_MATERIALTHICKNESS TB_MATERIAL_MATERIALTHICKNESS_thicknessId_fkey; Type: FK CONSTRAINT; Schema: MATERIAL; Owner: postgres
--

ALTER TABLE ONLY "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"
    ADD CONSTRAINT "TB_MATERIAL_MATERIALTHICKNESS_thicknessId_fkey" FOREIGN KEY ("thicknessId") REFERENCES "MATERIAL"."TB_MATERIAL_THICKNESS"("thicknessId");


--
-- Name: TB_PAYMENT_MTPAYMENT TB_PAYMENT_MTPAYMENT_mtId_fkey; Type: FK CONSTRAINT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_MTPAYMENT"
    ADD CONSTRAINT "TB_PAYMENT_MTPAYMENT_mtId_fkey" FOREIGN KEY ("mtId") REFERENCES "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS"("mtId");


--
-- Name: TB_PAYMENT_MTPAYMENT TB_PAYMENT_MTPAYMENT_paymentId_fkey; Type: FK CONSTRAINT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_MTPAYMENT"
    ADD CONSTRAINT "TB_PAYMENT_MTPAYMENT_paymentId_fkey" FOREIGN KEY ("paymentId") REFERENCES "PAYMENT"."TB_PAYMENT_PAYMENTS"("paymentId");


--
-- Name: TB_PAYMENT_PAYMENTS TB_PAYMENT_PAYMENTS_paymentMethodId_fkey; Type: FK CONSTRAINT; Schema: PAYMENT; Owner: postgres
--

ALTER TABLE ONLY "PAYMENT"."TB_PAYMENT_PAYMENTS"
    ADD CONSTRAINT "TB_PAYMENT_PAYMENTS_paymentMethodId_fkey" FOREIGN KEY ("paymentMethodId") REFERENCES "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS"("paymentMethodId");


--
-- PostgreSQL database dump complete
--

