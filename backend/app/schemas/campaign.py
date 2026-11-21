from pydantic import BaseModel, Field


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1)
    geo: str = Field(min_length=1)
    offer_id: int = Field(gt=0)


class CreateCampaignResponse(BaseModel):
    id: int


class CampaignListItem(BaseModel):
    id: int
    name: str


class OfferListItem(BaseModel):
    id: int
    name: str