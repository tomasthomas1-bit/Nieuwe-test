from fastapi import APIRouter

# Dit creëert een APIRouter instance
router = APIRouter()

# Definieer je eerste endpoint
# Dit endpoint reageert op een GET-verzoek naar /
@router.get("/")
async def root():
    return {"message": "Hello World"}

# Definieer een ander endpoint
# Dit endpoint reageert op een GET-verzoek naar /items/{item_id}
@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
