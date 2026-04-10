from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models import Application, Contract, ContractDocument, ContractStatusHistory, Job, User
from app.models.enums import ApplicationStatus, ContractStatus


class ContractService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _generate_contract_code(company_id: int) -> str:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        suffix = uuid4().hex[:6].upper()
        return f"CTR-{company_id}-{day}-{suffix}"

    @staticmethod
    def _validate_dates(start_date: date, end_date: date | None) -> None:
        if end_date and end_date < start_date:
            raise AppException("end_date must be greater than or equal to start_date", status_code=400)

    @staticmethod
    def _derive_lifecycle_status(*, start_date: date, end_date: date | None) -> ContractStatus:
        # With only 3 supported statuses, lifecycle is derived from end_date.
        if end_date is not None and end_date < date.today():
            return ContractStatus.EXPIRED
        return ContractStatus.ACTIVE

    @staticmethod
    def _build_contract_title(candidate_name: str, job_title: str) -> str:
        title = f"Hợp đồng lao động - {candidate_name} - {job_title}"
        return title[:160]

    @staticmethod
    def _can_transition(current: ContractStatus, target: ContractStatus) -> bool:
        if target == ContractStatus.DRAFT:
            return False

        allowed = {
            ContractStatus.DRAFT: {ContractStatus.ACTIVE, ContractStatus.EXPIRED, ContractStatus.TERMINATED},
            ContractStatus.ACTIVE: {ContractStatus.EXPIRED, ContractStatus.TERMINATED},
            ContractStatus.EXPIRED: {ContractStatus.ACTIVE, ContractStatus.TERMINATED},
            ContractStatus.TERMINATED: set(),
        }
        if current == target:
            return True
        return target in allowed.get(current, set())

    async def _append_history(
        self,
        *,
        contract_id: int,
        from_status: ContractStatus | None,
        to_status: ContractStatus,
        changed_by_id: int | None,
        note: str | None,
    ) -> None:
        self.db.add(
            ContractStatusHistory(
                contract_id=contract_id,
                from_status=from_status.value if from_status else None,
                to_status=to_status.value,
                changed_by_id=changed_by_id,
                note=note,
            )
        )

    async def _get_accepted_application(self, *, company_id: int, source_application_id: int) -> Application:
        application = await self.db.scalar(
            select(Application)
            .join(Job, Job.id == Application.job_id)
            .options(
                selectinload(Application.candidate),
                selectinload(Application.job),
            )
            .where(
                Application.id == source_application_id,
                Application.status == ApplicationStatus.ACCEPTED.value,
                Job.company_id == company_id,
                Job.deleted_at.is_(None),
            )
        )
        if not application:
            raise AppException("Only accepted candidates can be contracted", status_code=400)

        candidate = application.candidate
        if not candidate or candidate.deleted_at is not None or not candidate.is_active:
            raise AppException("Accepted candidate is not available", status_code=400)

        return application

    async def list_targets(self, company_id: int) -> list[dict]:
        accepted_applications = (
            await self.db.scalars(
                select(Application)
                .join(Job, Job.id == Application.job_id)
                .options(
                    selectinload(Application.candidate),
                    selectinload(Application.job),
                )
                .where(
                    Application.status == ApplicationStatus.ACCEPTED.value,
                    Job.company_id == company_id,
                    Job.deleted_at.is_(None),
                )
                .order_by(Application.created_at.desc())
            )
        ).all()

        results: list[dict] = []
        for application in accepted_applications:
            candidate = application.candidate
            job = application.job
            if not candidate or not job:
                continue
            if candidate.deleted_at is not None or not candidate.is_active:
                continue

            results.append({
                "id": application.id,
                "employee_id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "source_application_id": application.id,
                "accepted_job_id": job.id,
                "accepted_job_title": job.title,
                "accepted_at": application.created_at,
            })

        return results

    async def list_contracts(
        self,
        *,
        company_id: int,
        page: int,
        page_size: int,
        q: str | None,
        status: str | None,
        contract_type: str | None,
        employee_id: int | None,
        current_only: bool,
        expiring_in_days: int | None,
    ) -> tuple[list[Contract], int]:
        filters = [Contract.deleted_at.is_(None), Contract.company_id == company_id]
        join_employee = False

        if status:
            filters.append(Contract.status == status)
        if contract_type:
            filters.append(Contract.contract_type == contract_type)
        if employee_id:
            filters.append(Contract.employee_id == employee_id)
        if current_only:
            filters.append(Contract.is_current.is_(True))

        if expiring_in_days is not None:
            max_date = date.today() + timedelta(days=max(expiring_in_days, 0))
            filters.extend([
                Contract.end_date.is_not(None),
                Contract.end_date >= date.today(),
                Contract.end_date <= max_date,
            ])

        if q:
            keyword = f"%{q}%"
            join_employee = True
            filters.append(
                or_(
                    Contract.contract_code.ilike(keyword),
                    Contract.title.ilike(keyword),
                    User.full_name.ilike(keyword),
                    User.email.ilike(keyword),
                )
            )

        where_clause = and_(*filters)

        total_stmt = select(func.count(Contract.id)).select_from(Contract)
        list_stmt = select(Contract)
        if join_employee:
            total_stmt = total_stmt.join(User, User.id == Contract.employee_id)
            list_stmt = list_stmt.join(User, User.id == Contract.employee_id)

        total_stmt = total_stmt.where(where_clause)
        list_stmt = (
            list_stmt.options(selectinload(Contract.employee), selectinload(Contract.documents))
            .where(where_clause)
            .order_by(Contract.is_current.desc(), Contract.start_date.desc(), Contract.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        total = await self.db.scalar(total_stmt)
        items = (await self.db.scalars(list_stmt)).all()
        return list(items), int(total or 0)

    async def get_contract(self, contract_id: int, company_id: int) -> Contract:
        contract = await self.db.scalar(
            select(Contract)
            .options(
                selectinload(Contract.employee),
                selectinload(Contract.documents),
                selectinload(Contract.status_history),
            )
            .where(
                Contract.id == contract_id,
                Contract.company_id == company_id,
                Contract.deleted_at.is_(None),
            )
        )
        if not contract:
            raise AppException("Contract not found", status_code=404)
        return contract

    async def create_contract(self, *, company_id: int, created_by_id: int, payload) -> Contract:
        self._validate_dates(payload.start_date, payload.end_date)

        accepted_application = await self._get_accepted_application(
            company_id=company_id,
            source_application_id=payload.source_application_id,
        )

        employee = accepted_application.candidate
        job = accepted_application.job
        if not employee:
            raise AppException("Accepted candidate is not available", status_code=400)

        status = self._derive_lifecycle_status(start_date=payload.start_date, end_date=payload.end_date)

        title = self._build_contract_title(
            candidate_name=employee.full_name,
            job_title=job.title if job else f"Job #{accepted_application.job_id}",
        )

        contract = Contract(
            contract_code=self._generate_contract_code(company_id),
            title=title,
            employee_id=employee.id,
            company_id=company_id,
            source_application_id=accepted_application.id,
            contract_type=payload.contract_type.value,
            status=status.value,
            start_date=payload.start_date,
            end_date=payload.end_date,
            signed_at=datetime.now(timezone.utc) if status == ContractStatus.ACTIVE else None,
            salary_amount=payload.salary_amount,
            salary_currency=payload.salary_currency.upper(),
            benefits=payload.benefits,
            terms=payload.terms,
            notes=payload.notes,
            version=1,
            is_current=True,
            created_by_id=created_by_id,
        )
        self.db.add(contract)
        await self.db.flush()

        await self._append_history(
            contract_id=contract.id,
            from_status=None,
            to_status=status,
            changed_by_id=created_by_id,
            note=f"Contract created from accepted application #{accepted_application.id}",
        )

        await self.db.commit()
        return await self.get_contract(contract.id, company_id)

    async def update_contract(self, contract: Contract, payload, updated_by_id: int) -> Contract:
        if contract.status == ContractStatus.TERMINATED.value:
            raise AppException("Terminated contracts cannot be edited", status_code=400)

        updates = payload.model_dump(exclude_unset=True)
        proposed_start = updates.get("start_date", contract.start_date)
        proposed_end = updates.get("end_date", contract.end_date)
        self._validate_dates(proposed_start, proposed_end)

        for key, value in updates.items():
            if key == "salary_currency" and value is not None:
                setattr(contract, key, value.upper())
                continue
            setattr(contract, key, value)

        contract.notes = contract.notes
        await self.db.commit()
        await self.db.refresh(contract)
        return await self.get_contract(contract.id, contract.company_id)

    async def transition_status(
        self,
        *,
        contract: Contract,
        target_status: ContractStatus,
        changed_by_id: int,
        note: str | None,
    ) -> Contract:
        if target_status == ContractStatus.DRAFT:
            raise AppException("Draft status is no longer supported", status_code=400)

        current_status = ContractStatus(contract.status)
        if not self._can_transition(current_status, target_status):
            raise AppException(
                f"Invalid status transition from {current_status.value} to {target_status.value}",
                status_code=400,
            )

        if current_status == target_status:
            return await self.get_contract(contract.id, contract.company_id)

        if target_status == ContractStatus.ACTIVE and contract.end_date and contract.end_date < date.today():
            raise AppException("Cannot activate a contract that is already expired", status_code=400)

        contract.status = target_status.value
        if target_status == ContractStatus.ACTIVE:
            contract.signed_at = contract.signed_at or datetime.now(timezone.utc)
        if target_status == ContractStatus.TERMINATED:
            contract.terminated_at = datetime.now(timezone.utc)

        await self._append_history(
            contract_id=contract.id,
            from_status=current_status,
            to_status=target_status,
            changed_by_id=changed_by_id,
            note=note,
        )
        await self.db.commit()
        return await self.get_contract(contract.id, contract.company_id)

    async def renew_contract(self, *, contract: Contract, payload, renewed_by_id: int) -> Contract:
        if contract.status == ContractStatus.TERMINATED.value:
            raise AppException("Cannot renew terminated contracts", status_code=400)

        self._validate_dates(payload.start_date, payload.end_date)
        lifecycle_status = self._derive_lifecycle_status(start_date=payload.start_date, end_date=payload.end_date)

        contract.is_current = False
        new_contract = Contract(
            contract_code=self._generate_contract_code(contract.company_id),
            title=payload.title or contract.title,
            employee_id=contract.employee_id,
            company_id=contract.company_id,
            source_application_id=contract.source_application_id,
            contract_type=(payload.contract_type.value if payload.contract_type else contract.contract_type),
            status=lifecycle_status.value,
            start_date=payload.start_date,
            end_date=payload.end_date,
            signed_at=datetime.now(timezone.utc) if lifecycle_status == ContractStatus.ACTIVE else None,
            salary_amount=payload.salary_amount if payload.salary_amount is not None else contract.salary_amount,
            salary_currency=(payload.salary_currency.upper() if payload.salary_currency else contract.salary_currency),
            benefits=payload.benefits if payload.benefits is not None else contract.benefits,
            terms=payload.terms if payload.terms is not None else contract.terms,
            notes=payload.notes if payload.notes is not None else contract.notes,
            version=contract.version + 1,
            is_current=True,
            previous_contract_id=contract.id,
            created_by_id=renewed_by_id,
        )
        self.db.add(new_contract)
        await self.db.flush()

        await self._append_history(
            contract_id=new_contract.id,
            from_status=None,
            to_status=lifecycle_status,
            changed_by_id=renewed_by_id,
            note=payload.reason or f"Renewed from contract #{contract.id}",
        )

        await self.db.commit()
        return await self.get_contract(new_contract.id, contract.company_id)

    async def terminate_contract(
        self,
        *,
        contract: Contract,
        reason: str,
        terminated_by_id: int,
        terminated_at: datetime | None,
    ) -> Contract:
        if contract.status == ContractStatus.TERMINATED.value:
            raise AppException("Contract is already terminated", status_code=400)

        current_status = ContractStatus(contract.status)
        contract.status = ContractStatus.TERMINATED.value
        contract.termination_reason = reason
        contract.terminated_at = terminated_at or datetime.now(timezone.utc)

        await self._append_history(
            contract_id=contract.id,
            from_status=current_status,
            to_status=ContractStatus.TERMINATED,
            changed_by_id=terminated_by_id,
            note=reason,
        )

        await self.db.commit()
        return await self.get_contract(contract.id, contract.company_id)

    async def add_document(
        self,
        *,
        contract: Contract,
        document_type: str,
        file_name: str,
        file_path: str,
        mime_type: str | None,
        notes: str | None,
        uploaded_by_id: int,
    ) -> ContractDocument:
        document = ContractDocument(
            contract_id=contract.id,
            document_type=document_type,
            file_name=file_name,
            file_path=file_path,
            mime_type=mime_type,
            notes=notes,
            uploaded_by_id=uploaded_by_id,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def list_history(self, contract_id: int) -> list[ContractStatusHistory]:
        histories = (
            await self.db.scalars(
                select(ContractStatusHistory)
                .where(ContractStatusHistory.contract_id == contract_id)
                .order_by(ContractStatusHistory.changed_at.desc())
            )
        ).all()
        return list(histories)
