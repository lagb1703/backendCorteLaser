

class StorageService:
    
    __instance: 'StorageService | None' = None
    
    @staticmethod
    def getInstance():
        if StorageService.__instance is None:
            StorageService.__instance = StorageService()
        return StorageService.__instance
    
    def __init__(self):
        pass