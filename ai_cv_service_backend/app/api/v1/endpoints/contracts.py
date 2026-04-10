from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import settings
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.models import Company, User
from app.models.enums import ContractDocumentType, ContractStatus, ContractType, UserRole
from app.schemas.contract import (
    ContractCreateRequest,
    ContractDetailResponse,
    ContractDocumentResponse,
    ContractHistoryResponse,
    ContractRenewRequest,
    ContractResponse,
    ContractStatusUpdateRequest,
    ContractTargetResponse,
    ContractTerminateRequest,
    ContractUpdateRequest,
)
from app.services.contract_service import ContractService
from app.services.storage_service import StorageService

router = APIRouter()


def _days_to_expiry(end_date: date | None) -> int | None:
    if end_date is None:
        return None
    return (end_date - date.today()).days


def _serialize_contract(contract, *, include_history: bool = False, expiring_threshold_days: int = 30) -> dict:
    days_to_expiry = _days_to_expiry(contract.end_date)
    expiring_soon = (
        contract.status == ContractStatus.ACTIVE.value
        and days_to_expiry is not None
        and 0 <= days_to_expiry <= expiring_threshold_days
    )
    payload = {
        "id": contract.id,
        "contract_code": contract.contract_code,
        "title": contract.title,
        "employee_id": contract.employee_id,
        "employee_name": contract.employee.full_name if contract.employee else None,
        "employee_email": contract.employee.email if contract.employee else None,
        "company_id": contract.company_id,
        "source_application_id": contract.source_application_id,
        "contract_type": contract.contract_type,
        "status": contract.status,
        "start_date": contract.start_date,
        "end_date": contract.end_date,
        "signed_at": contract.signed_at,
        "salary_amount": contract.salary_amount,
        "salary_currency": contract.salary_currency,
        "benefits": contract.benefits,
        "terms": contract.terms,
        "notes": contract.notes,
        "termination_reason": contract.termination_reason,
        "terminated_at": contract.terminated_at,
        "version": contract.version,
        "is_current": contract.is_current,
        "previous_contract_id": contract.previous_contract_id,
        "created_by_id": contract.created_by_id,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at,
        "days_to_expiry": days_to_expiry,
        "expiring_soon": expiring_soon,
        "documents": [ContractDocumentResponse.model_validate(doc).model_dump() for doc in contract.documents],
    }

    if include_history:
        histories = sorted(contract.status_history, key=lambda item: item.changed_at, reverse=True)
        payload["history"] = [ContractHistoryResponse.model_validate(entry).model_dump() for entry in histories]

    return payload


async def _resolve_company_scope(
    *,
    current_user: User,
    db: AsyncSession,
    company_id: int | None,
) -> int:
    if current_user.role.name == UserRole.HR.value:
        if current_user.company_id is None:
            fallback_company = await db.scalar(select(Company).where(Company.deleted_at.is_(None)).order_by(Company.id.asc()))
            if not fallback_company:
                raise AppException("No company found. Create a company first.", status_code=400)
            current_user.company_id = fallback_company.id
            await db.commit()
            await db.refresh(current_user)

        if company_id is not None and company_id != current_user.company_id:
            raise AppException("Forbidden", status_code=403)

        return int(current_user.company_id)

    if company_id is not None:
        return company_id

    fallback_company = await db.scalar(select(Company).where(Company.deleted_at.is_(None)).order_by(Company.id.asc()))
    if not fallback_company:
        raise AppException("No company found", status_code=400)
    return fallback_company.id


@router.get("/targets", response_model=list[ContractTargetResponse])
async def list_contract_targets(
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> list[ContractTargetResponse]:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    items = await ContractService(db).list_targets(scope_company_id)
    return [ContractTargetResponse.model_validate(item) for item in items]


@router.get("", response_model=dict)
async def list_contracts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    company_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    status: ContractStatus | None = Query(default=None),
    contract_type: ContractType | None = Query(default=None),
    employee_id: int | None = Query(default=None),
    current_only: bool = Query(default=True),
    expiring_in_days: int | None = Query(default=None, ge=0, le=365),
    expiring_threshold_days: int = Query(default=30, ge=1, le=180),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)

    contracts, total = await service.list_contracts(
        company_id=scope_company_id,
        page=page,
        page_size=page_size,
        q=q,
        status=status.value if status else None,
        contract_type=contract_type.value if contract_type else None,
        employee_id=employee_id,
        current_only=current_only,
        expiring_in_days=expiring_in_days,
    )

    return {
        "items": [
            ContractResponse.model_validate(
                _serialize_contract(item, include_history=False, expiring_threshold_days=expiring_threshold_days)
            ).model_dump()
            for item in contracts
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=ContractResponse)
async def create_contract(
    payload: ContractCreateRequest,
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    contract = await ContractService(db).create_contract(
        company_id=scope_company_id,
        created_by_id=current_user.id,
        payload=payload,
    )
    return ContractResponse.model_validate(_serialize_contract(contract))


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: int,
    company_id: int | None = Query(default=None),
    expiring_threshold_days: int = Query(default=30, ge=1, le=180),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractDetailResponse:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    contract = await ContractService(db).get_contract(contract_id, scope_company_id)
    return ContractDetailResponse.model_validate(
        _serialize_contract(contract, include_history=True, expiring_threshold_days=expiring_threshold_days)
    )


@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    payload: ContractUpdateRequest,
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)
    contract = await service.get_contract(contract_id, scope_company_id)
    updated = await service.update_contract(contract, payload, current_user.id)
    return ContractResponse.model_validate(_serialize_contract(updated))


@router.patch("/{contract_id}/status", response_model=ContractResponse)
async def update_contract_status(
    contract_id: int,
    payload: ContractStatusUpdateRequest,
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    if payload.status == ContractStatus.DRAFT:
        raise AppException("Draft status is no longer supported", status_code=400)

    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)
    contract = await service.get_contract(contract_id, scope_company_id)
    updated = await service.transition_status(
        contract=contract,
        target_status=payload.status,
        changed_by_id=current_user.id,
        note=payload.note,
    )
    return ContractResponse.model_validate(_serialize_contract(updated))


@router.post("/{contract_id}/renew", response_model=ContractResponse)
async def renew_contract(
    contract_id: int,
    payload: ContractRenewRequest,
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)
    contract = await service.get_contract(contract_id, scope_company_id)
    renewed = await service.renew_contract(contract=contract, payload=payload, renewed_by_id=current_user.id)
    return ContractResponse.model_validate(_serialize_contract(renewed))


@router.post("/{contract_id}/terminate", response_model=ContractResponse)
async def terminate_contract(
    contract_id: int,
    payload: ContractTerminateRequest,
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)
    contract = await service.get_contract(contract_id, scope_company_id)
    terminated = await service.terminate_contract(
        contract=contract,
        reason=payload.reason,
        terminated_by_id=current_user.id,
        terminated_at=payload.terminated_at,
    )
    return ContractResponse.model_validate(_serialize_contract(terminated))


@router.post("/{contract_id}/documents", response_model=ContractDocumentResponse)
async def upload_contract_document(
    contract_id: int,
    file: UploadFile = File(...),
    document_type: ContractDocumentType = Form(...),
    notes: str | None = Form(default=None),
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ContractDocumentResponse:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)
    contract = await service.get_contract(contract_id, scope_company_id)

    path = await StorageService.save_upload(file, settings.CONTRACT_DOC_DIR, StorageService.allowed_contract_doc_types)
    document = await service.add_document(
        contract=contract,
        document_type=document_type.value,
        file_name=file.filename or "contract-document",
        file_path=path,
        mime_type=file.content_type,
        notes=notes,
        uploaded_by_id=current_user.id,
    )
    return ContractDocumentResponse.model_validate(document)


@router.get("/{contract_id}/history", response_model=list[ContractHistoryResponse])
async def list_contract_history(
    contract_id: int,
    company_id: int | None = Query(default=None),
    current_user: User = Depends(require_roles(UserRole.HR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> list[ContractHistoryResponse]:
    scope_company_id = await _resolve_company_scope(current_user=current_user, db=db, company_id=company_id)
    service = ContractService(db)
    contract = await service.get_contract(contract_id, scope_company_id)
    history = await service.list_history(contract.id)
    return [ContractHistoryResponse.model_validate(item) for item in history]
