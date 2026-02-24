from fastapi import APIRouter, HTTPException

from backend.db.sqlite import get_categories, add_category, update_category, delete_category
from backend.models import CategoryCreate, CategoryResponse

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories():
    categories = await get_categories()
    return categories


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate):
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="카테고리 이름은 비어있을 수 없습니다.")
    try:
        category_id = await add_category(data.name.strip(), data.description)
    except Exception:
        raise HTTPException(status_code=409, detail="이미 존재하는 카테고리입니다.")
    return {"id": category_id, "name": data.name.strip(), "description": data.description}


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def edit_category(category_id: int, data: CategoryCreate):
    # Check if trying to modify '미분류'
    categories = await get_categories()
    target = next((c for c in categories if c["id"] == category_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
    if target["name"] == "미분류":
        raise HTTPException(status_code=400, detail="'미분류' 카테고리는 수정할 수 없습니다.")
    try:
        await update_category(category_id, data.name.strip())
    except Exception:
        raise HTTPException(status_code=409, detail="이미 존재하는 카테고리입니다.")
    return {"id": category_id, "name": data.name.strip(), "description": data.description}


@router.delete("/categories/{category_id}", status_code=204)
async def remove_category(category_id: int):
    categories = await get_categories()
    target = next((c for c in categories if c["id"] == category_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
    if target["name"] == "미분류":
        raise HTTPException(status_code=400, detail="'미분류' 카테고리는 삭제할 수 없습니다.")
    await delete_category(category_id)
