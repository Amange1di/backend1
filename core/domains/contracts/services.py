import io
import logging

from django.template import Context, Template
from django.template.loader import render_to_string

from core.models import ContractTemplate, User

logger = logging.getLogger(__name__)


def build_contract_context(contract):
    company = contract.company
    student = contract.student
    group = contract.group

    admin = User.objects.filter(
        role=User.Role.COURSE_ADMIN,
        company=company,
    ).first()
    admin_name = (
        f"{admin.first_name} {admin.last_name}".strip()
        or (admin.username if admin else "Администратор")
    )
    course_name = group.course.title if group and group.course else "—"

    return {
        "contract_number": contract.contract_number,
        "company_name": company.name,
        "company_city": company.city or "Бишкек",
        "company_address": company.district or company.city or "",
        "company_phone": company.phone or "",
        "admin_name": admin_name,
        "student_name": str(student),
        "student_phone": student.phone,
        "student_passport_info": "паспорт: данные паспорта",
        "course_name": course_name,
        "group_name": group.name if group else "—",
        "amount": int(contract.amount),
        "start_date": contract.start_date.strftime("%d.%m.%Y"),
        "end_date": (
            contract.end_date.strftime("%d.%m.%Y")
            if contract.end_date
            else "—"
        ),
        "payment_terms": "100% предоплата",
        "terms": contract.terms,
    }


def render_contract_html(contract, *, prefer_company_template=True):
    context = build_contract_context(contract)

    if prefer_company_template:
        custom_template = ContractTemplate.objects.filter(
            company=contract.company,
            is_default=True,
        ).first()
        if custom_template and custom_template.html_content:
            return Template(custom_template.html_content).render(Context(context))

    return render_to_string("core/contract_template.html", context)


def generate_contract_pdf(contract, *, save_to_model=True):
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("weasyprint not available, skipping PDF generation")
        return None

    if save_to_model and contract.pdf_file:
        return contract.pdf_file

    html_string = render_contract_html(contract)
    pdf_bytes = HTML(string=html_string).write_pdf()

    if save_to_model:
        contract.pdf_file.save(
            f"contract_{contract.contract_number}.pdf",
            io.BytesIO(pdf_bytes),
            save=True,
        )
        logger.info("PDF auto-generated for contract %s", contract.contract_number)

    return pdf_bytes
