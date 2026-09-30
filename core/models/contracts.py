from django.db import models


class Contract(models.Model):
    """
    Договор / соглашение между учебным центром и студентом.
    Генерируется в PDF и подписывается сторонами.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Черновик")
        SENT = "sent", _("Отправлен студенту")
        SIGNED = "signed", _("Подписан")
        CANCELLED = "cancelled", _("Аннулирован")

    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="contracts",
        verbose_name="Компания (учебный центр)",
    )
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="contracts",
        verbose_name="Студент",
    )
    group = models.ForeignKey(
        "Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
        verbose_name="Группа / курс",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Статус",
    )
    contract_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Номер договора",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма договора",
    )
    start_date = models.DateField(
        verbose_name="Дата начала",
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата окончания",
    )
    terms = models.TextField(
        blank=True,
        verbose_name="Дополнительные условия",
        help_text="Особые условия, не указанные в шаблоне",
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_contracts",
        verbose_name="Кто создал",
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата подписания",
    )
    pdf_file = models.FileField(
        upload_to="contracts/",
        null=True,
        blank=True,
        verbose_name="PDF файл",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.contract_number} — {self.student}"

    def generate_contract_number(self):
        """Генерация номера договора: ДОГ-{YYYY}-{XXXX}"""
        from django.utils import timezone
        year = timezone.now().year
        prefix = f"ДОГ-{year}-"
        last = Contract.objects.filter(
            contract_number__startswith=prefix
        ).order_by("-contract_number").first()
        if last:
            last_num = int(last.contract_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f"{prefix}{new_num:04d}"

    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self.generate_contract_number()
        super().save(*args, **kwargs)

class ContractTemplate(models.Model):
    """
    Шаблон договора для компании.
    Компания может загрузить свой HTML-шаблон с переменными.
    """
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="contract_templates",
        verbose_name="Компания",
    )
    name = models.CharField(
        max_length=200,
        default="Стандартный шаблон",
        verbose_name="Название шаблона",
    )
    html_content = models.TextField(
        verbose_name="HTML содержимое",
        help_text="HTML шаблон с переменными Django: {{ student_name }}, {{ course_name }}, {{ amount }}, {{ start_date }}, {{ company_name }}, {{ admin_name }}, {{ group_name }}, {{ student_phone }}",
        blank=True,
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="По умолчанию",
        help_text="Использовать этот шаблон для всех новых договоров компании",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Шаблон договора"
        verbose_name_plural = "Шаблоны договоров"
        ordering = ("-is_default", "-created_at")

    def __str__(self) -> str:
        return f"{self.name} — {self.company.name}"
