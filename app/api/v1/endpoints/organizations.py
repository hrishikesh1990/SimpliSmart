from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
import string
from app.core import deps
from app.schemas.organization import Organization, OrganizationCreate
from app.models.organization import Organization as OrganizationModel
from app.models.user import User

router = APIRouter()


def generate_invite_code(length: int = 8) -> str:
    """Generate a random invite code"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/", response_model=Organization)
def create_organization(*,
                        db: Session = Depends(deps.get_db),
                        organization_in: OrganizationCreate,
                        current_user: User = Depends(deps.get_current_user)):
    """Create a new organization and set the current user as a member"""
    # Generate a unique invite code
    while True:
        invite_code = generate_invite_code()
        exists = db.query(OrganizationModel).filter(
            OrganizationModel.invite_code == invite_code).first()
        if not exists:
            break

    # Create new organization
    organization = OrganizationModel(name=organization_in.name,
                                     invite_code=invite_code)

    # Add organization to database
    db.add(organization)
    db.commit()
    db.refresh(organization)

    # Add current user to organization
    current_user.organization_id = organization.id
    db.add(current_user)
    db.commit()

    return organization


@router.post("/{invite_code}/join")
def join_organization(*,
                      db: Session = Depends(deps.get_db),
                      invite_code: str,
                      current_user: User = Depends(deps.get_current_user)):
    """Join an organization using an invite code"""
    # Check if user is already in an organization
    if current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of an organization")

    # Find organization by invite code
    organization = db.query(OrganizationModel).filter(
        OrganizationModel.invite_code == invite_code).first()

    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid invite code")

    # Add user to organization
    current_user.organization_id = organization.id
    db.add(current_user)
    db.commit()

    return {
        "message": f"Successfully joined organization: {organization.name}"
    }


@router.get("/current", response_model=Organization)
def get_current_organization(current_user: User = Depends(
    deps.get_current_user),
                             db: Session = Depends(deps.get_db)):
    """Get the current user's organization"""
    if not current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User is not a member of any organization")

    organization = db.query(OrganizationModel).filter(
        OrganizationModel.id == current_user.organization_id).first()

    return organization
