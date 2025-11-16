from enum import Enum

class ExceptionsEnum(Enum):
    pass
    
class MaterialSql(Enum):
    getAllMaterials="""
        SELECT 
            mtmm."materialId" as "materialId",
            mtmm.name as "name",
            mtmm.price as "price",
            mtmm."lastmodification" AS "lastmodification"
        FROM "MATERIAL"."TB_MATERIAL_MATERIALS" mtmm
        WHERE mtmm."deleted" = false
    """
    getMaterialById="""
        SELECT 
            mtmm."materialId" as "materialId",
            mtmm.name as "name",
            mtmm.price as "price",
            mtmm."lastmodification" AS "lastmodification"
        FROM "MATERIAL"."TB_MATERIAL_MATERIALS" mtmm
        WHERE mtmm."materialId" = $1
    """
    addNewMaterial="""
        call "MATERIAL"."SP_MA_MATERIALPKG_AGREGARMATERIAL"($1, $2)
    """
    changeMaterial="""
        call "MATERIAL"."SP_MA_MATERIALPKG_ACTUALIZARMATERIAL"($1, $2)
    """
    deleteMaterial="""
        call "MATERIAL"."SP_MA_MATERIALPKG_ELIMINARMATERIAL"($1)
    """
    getAllThickness="""
        SELECT 
            mtmt."thicknessId" as "thicknessId",
            mtmt."name" as "name",
            mtmt."price" as "price",
            mtmt."lastmodification" as "lastModification"
        FROM "MATERIAL"."TB_MATERIAL_THICKNESS" mtmt
        WHERE mtmt."deleted" = false
    """
    getAllThicknessByMaterialId="""
        SELECT 
            mtmmt."mtId" as "mtId",
            mtmt."thicknessId" as "thicknessId",
            mtmt."name" as "name",
            mtmt."price" as "price",
            mtmt."lastmodification" as "lastModification"
        FROM "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS" mtmmt
        LEFT JOIN "MATERIAL"."TB_MATERIAL_THICKNESS" mtmt
            ON mtmt."thicknessId" = mtmmt."thicknessId"
        WHERE mtmmt."materialId" = $1
            AND mtmmt."deleted" = false
            AND mtmt."deleted" = false
    """
    addNewThickness="""
        call "MATERIAL"."SP_MA_MATERIALPKG_AGREGARTHICKNESS"($1, $2)
    """
    changeThickness="""
        call "MATERIAL"."SP_MA_MATERIALPKG_ACTUALIZARTHICKNESS"($1, $2)
    """
    deleteThickness="""
        call "MATERIAL"."SP_MA_MATERIALPKG_ELIMINARTHICKNESS"($1)
    """
    getMtIdByMaterialIdThicknessId="""
        SELECT 
            mtmmt."mtId" as "mtId"
        FROM "MATERIAL"."TB_MATERIAL_MATERIALTHICKNESS" mtmmt
        WHERE mtmmt."materialId" = $1 and mtmmt."thicknessId" = $2
    """
    addMaterialThickness="""
        call "MATERIAL"."SP_MA_MATERIALPKG_AGREGARMATERIALTHICKNESS"($1, $2)
    """
    deleteMaterialThickness="""
        call "MATERIAL"."SP_MA_MATERIALPKG_ELIMINARMATERIALTHICKNESS"($1)
    """