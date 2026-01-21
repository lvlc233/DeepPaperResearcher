from typing import List
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from base.pg.service import ReaderRepository
from base.pg.entity import Layer, Annotation as AnnotationEntity
from service.reader.schema import View, Annotation, Rect
from controller.api.reader.schema import AnnotationRequest, ViewResponse, AnnotationResponse

class ViewService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_views(self, paper_id: UUID, user_id: UUID) -> List[View]:
        layers = await ReaderRepository.get_layers_by_paper(self.session, paper_id, user_id)
        
        views = []
        for layer in layers:
            annotations = []
            if layer.annotations:
                for ann in layer.annotations:
                    # Parse rects (List[dict] -> List[Rect])
                    rects_list = []
                    if ann.rects:
                        for r in ann.rects:
                            try:
                                rects_list.append(Rect(**r))
                            except:
                                pass
                    
                    annotations.append(Annotation(
                        id=ann.id,
                        type=ann.type,
                        rect=rects_list,
                        content=ann.content,
                        color=ann.color
                    ))
            
            views.append(View(
                id=layer.id,
                name=layer.name,
                visible=layer.visible,
                annotations=annotations
            ))
            
        return views

    async def create_view(self, paper_id: UUID, name: str, user_id: UUID) -> ViewResponse:
        layer = Layer(
            id=uuid4(),
            paper_id=paper_id,
            user_id=user_id,
            name=name,
            visible=True
        )
        created_layer = await ReaderRepository.create_layer(self.session, layer)
        return ViewResponse(
            id=created_layer.id,
            name=created_layer.name,
            visible=created_layer.visible
        )

    async def rename_view(self, view_id: UUID, name: str, user_id: UUID) -> None:
        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id:
            raise HTTPException(status_code=404, detail="View not found")
        
        layer.name = name
        await ReaderRepository.update_layer(self.session, layer)

    async def enable_view(self, view_id: UUID, enable: bool, user_id: UUID) -> None:
        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id:
            raise HTTPException(status_code=404, detail="View not found")
        
        layer.visible = enable
        await ReaderRepository.update_layer(self.session, layer)

    async def delete_view(self, view_id: UUID, user_id: UUID) -> None:
        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id:
            raise HTTPException(status_code=404, detail="View not found")
        
        await ReaderRepository.delete_layer(self.session, layer)

    async def get_annotations(self, paper_id: UUID, view_id: UUID, user_id: UUID) -> AnnotationResponse:
        # Verify layer ownership
        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id or layer.paper_id != paper_id:
            raise HTTPException(status_code=404, detail="View not found")
            
        # We need to reload annotations if they are not loaded, but get_layer_by_id might not load them.
        # However, ReaderRepository.get_layers_by_paper uses selectinload.
        # Let's assume for now we need to fetch them or they are lazy loaded (AsyncSession requires explicit load usually).
        # Better to rely on what we have. Since we need to return AnnotationResponse which contains List[Annotation] (Pydantic).
        
        # Re-using get_views logic or fetching specifically. 
        # Ideally ReaderRepository should have get_annotations_by_layer.
        # But for now let's use the layer object if it has annotations loaded.
        # If not, we might need to query.
        # Let's implement a simple fetch in Repository if needed, or trust lazy loading if configured (but async requires await).
        
        # To be safe, let's just query the layer with annotations again or add a method in repo.
        # Or I can use get_layers_by_paper filtering by ID.
        
        # Let's add a robust way.
        # For now, I'll assume I can access it or I'll query it.
        # Actually, let's use a new method in Repository: get_layer_with_annotations
        
        # Given constraints, I will use existing `get_layers_by_paper` and filter, or just trust `get_layer_by_id` if I modify it to load annotations.
        # But I can't modify Repository easily without reading it all.
        # `ReaderRepository.get_layer_by_id` implementation:
        # statement = select(Layer).where(Layer.id == layer_id)
        # It does NOT use selectinload.
        
        # So I should modify ReaderRepository to load annotations or add a new method.
        # Or I can just query annotations directly if I had `get_annotations_by_layer_id`.
        # Repository has `get_annotation_by_id` but not list.
        
        # Wait, I can just use `get_views` and filter by view_id. It's inefficient but safe.
        views = await self.get_views(paper_id, user_id)
        target_view = next((v for v in views if v.id == view_id), None)
        
        if not target_view:
             raise HTTPException(status_code=404, detail="View not found")
             
        return AnnotationResponse(items=target_view.annotations)

    async def add_annotation(self, paper_id: UUID, view_id: UUID, req: AnnotationRequest, user_id: UUID) -> None:
        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id or layer.paper_id != paper_id:
            raise HTTPException(status_code=404, detail="View not found")
            
        annotation = AnnotationEntity(
            id=uuid4(),
            layer_id=view_id,
            type=req.type,
            rects=[r for r in req.rect], # Store as JSON compatible list of dicts
            content=req.content,
            color=req.color
        )
        await ReaderRepository.create_annotation(self.session, annotation)

    async def update_annotation(self, paper_id: UUID, view_id: UUID, annotation_id: UUID, req: AnnotationRequest, user_id: UUID) -> None:
        annotation = await ReaderRepository.get_annotation_by_id(self.session, annotation_id)
        if not annotation:
             raise HTTPException(status_code=404, detail="Annotation not found")
             
        # Check ownership via layer
        if annotation.layer_id != view_id:
             raise HTTPException(status_code=400, detail="Annotation does not belong to this view")
             
        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id:
             raise HTTPException(status_code=403, detail="Permission denied")

        annotation.type = req.type
        annotation.rects = [r for r in req.rect]
        annotation.content = req.content
        annotation.color = req.color
        
        await ReaderRepository.update_annotation(self.session, annotation)

    async def delete_annotation(self, paper_id: UUID, view_id: UUID, annotation_id: UUID, user_id: UUID) -> None:
        annotation = await ReaderRepository.get_annotation_by_id(self.session, annotation_id)
        if not annotation:
             raise HTTPException(status_code=404, detail="Annotation not found")
             
        if annotation.layer_id != view_id:
             raise HTTPException(status_code=400, detail="Annotation does not belong to this view")

        layer = await ReaderRepository.get_layer_by_id(self.session, view_id)
        if not layer or layer.user_id != user_id:
             raise HTTPException(status_code=403, detail="Permission denied")
             
        await ReaderRepository.delete_annotation(self.session, annotation)
