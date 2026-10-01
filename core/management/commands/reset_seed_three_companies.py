from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import (
    Attendance,
    Auditorium,
    Company,
    CompanyBalance,
    CompanyPlatformPayment,
    CompanySubscription,
    CompanyCategory,
    CompanyCity,
    Contract,
    ContractTemplate,
    Course,
    Expense,
    Group,
    GroupMonth,
    HomeworkSubmission,
    HomeworkTask,
    JobVacancy,
    LandingPage,
    LandingSection,
    LeadAssignment,
    Payment,
    PromoBalance,
    PromoCode,
    PromoRedemption,
    PublicCourse,
    Student,
    Task,
    Transaction,
    TrialLead,
    User,
)


class Command(BaseCommand):
    help = (
        "Wipe the local database and seed three realistic companies with "
        "history from June, August and September through today."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Required confirmation because this command deletes all database data.",
        )
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Explicitly allow running outside DEBUG mode.",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError(
                "This command deletes ALL database data. "
                "Run again with --yes if that is intentional."
            )

        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError(
                "Refusing to wipe/seed data while DEBUG=False. "
                "Use --allow-production only if you really intend to."
            )

        self.stdout.write(self.style.WARNING("Flushing database..."))
        call_command("flush", interactive=False, verbosity=0)

        today = timezone.localdate()
        year = today.year

        company_specs = [
            {
                "key": "sanak",
                "name": "Sanak IT Academy",
                "slug": "sanak-it-academy",
                "start": date(year, 6, 1),
                "category": CompanyCategory.IT,
                "district": "Центр",
                "phone": "+996 700 610 101",
                "telegram": "@sanak_it",
                "instagram": "@sanak_it_academy",
                "description": (
                    "IT академия: frontend, backend, mobile, QA жана UI/UX."
                ),
                "plan": CompanySubscription.Plan.PRO,
                "monthly_fee": Decimal("15000.00"),
                "courses": [
                    ("Frontend React", 18000, 16, 90, "React, TypeScript, Next.js"),
                    ("Python Django", 20000, 20, 90, "Python, Django, REST API"),
                    ("Flutter Mobile", 21000, 18, 90, "Flutter, Dart, mobile development"),
                    ("QA Engineering", 16000, 14, 80, "Manual QA, API testing, automation basics"),
                    ("UI/UX Design", 17000, 14, 80, "Figma, UX research, product design"),
                ],
                "jobs": [
                    ("Junior Frontend Developer", 35000, 55000),
                    ("Python Mentor", 40000, 65000),
                    ("UI/UX Mentor", 35000, 55000),
                ],
            },
            {
                "key": "tilordo",
                "name": "TilOrdo Language Center",
                "slug": "tilordo-language-center",
                "start": date(year, 8, 1),
                "category": CompanyCategory.LANGUAGES,
                "district": "Черёмушки",
                "phone": "+996 700 810 202",
                "telegram": "@tilordo_osh",
                "instagram": "@tilordo_language",
                "description": (
                    "Тил борбору: англис, IELTS, түрк жана корей тилдери."
                ),
                "plan": CompanySubscription.Plan.GROWTH,
                "monthly_fee": Decimal("10000.00"),
                "courses": [
                    ("English A1-A2", 9000, 12, 80, "General English for beginners"),
                    ("IELTS Preparation", 14000, 16, 90, "IELTS Academic preparation"),
                    ("Turkish Language", 10000, 12, 80, "Turkish A1-B1"),
                    ("Korean Language", 11000, 14, 80, "Korean language and TOPIK basics"),
                ],
                "jobs": [
                    ("English Teacher", 30000, 50000),
                    ("IELTS Instructor", 40000, 65000),
                ],
            },
            {
                "key": "ishker",
                "name": "Ishker Business School",
                "slug": "ishker-business-school",
                "start": date(year, 9, 1),
                "category": CompanyCategory.BUSINESS,
                "district": "ХБК",
                "phone": "+996 700 910 303",
                "telegram": "@ishker_school",
                "instagram": "@ishker_business",
                "description": (
                    "Бизнес мектеби: сатуу, SMM, эсеп, аналитика жана ишкердик."
                ),
                "plan": CompanySubscription.Plan.START,
                "monthly_fee": Decimal("7000.00"),
                "courses": [
                    ("SMM & Content", 12000, 10, 80, "SMM strategy, content and ads"),
                    ("Sales Management", 13000, 10, 80, "Sales funnel and negotiation"),
                    ("Accounting 1C", 15000, 12, 90, "Accounting basics and 1C"),
                    ("Excel & Analytics", 11000, 8, 80, "Excel, reporting and dashboards"),
                    ("Entrepreneurship", 16000, 12, 90, "Business model, finance and growth"),
                ],
                "jobs": [
                    ("SMM Manager", 30000, 50000),
                    ("Sales Manager", 30000, 60000),
                    ("Business Mentor", 45000, 70000),
                ],
            },
        ]

        platform_admin = User.objects.create_user(
            username="demo_admin",
            password="DemoAdmin123!",
            role=User.Role.ADMIN,
            first_name="Аман",
            last_name="Платформа Админ",
            email="admin@demo.local",
            is_active=True,
            is_staff=True,
            is_superuser=True,
            must_set_password=False,
        )

        created_companies = []

        for company_index, spec in enumerate(company_specs, start=1):
            start_date = min(spec["start"], today)
            start_dt = self._at_date(start_date, 9)

            course_admin = User.objects.create_user(
                username=f'{spec["key"]}_admin',
                password="Demo1234!",
                role=User.Role.COURSE_ADMIN,
                first_name=spec["name"].split()[0],
                last_name="Администратор",
                email=f'{spec["key"]}.admin@demo.local',
                phone=f"+996 700 {company_index}00 001",
                is_active=True,
                must_set_password=False,
                max_managers=20,
                max_pages=20,
                max_blocks=30,
            )
            User.objects.filter(pk=course_admin.pk).update(date_joined=start_dt)

            company = Company.objects.create(
                name=spec["name"],
                slug=spec["slug"],
                description=spec["description"],
                category=spec["category"],
                city=CompanyCity.OSH,
                district=spec["district"],
                phone=spec["phone"],
                telegram=spec["telegram"],
                whatsapp=spec["phone"],
                website=f'https://{spec["slug"]}.example.local',
                instagram=spec["instagram"],
                facebook="",
                owner=course_admin,
                is_active=True,
                rating=Decimal("4.70") + Decimal(company_index) / Decimal("20"),
                reviews_count=20 + company_index * 13,
            )
            Company.objects.filter(pk=company.pk).update(created_at=start_dt)

            course_admin.company = company
            course_admin.save(update_fields=["company"])
            created_companies.append(company)

            managers = self._create_managers(
                course_admin=course_admin,
                company=company,
                prefix=spec["key"],
                company_index=company_index,
                start_date=start_date,
            )

            course_data = self._create_courses_and_teachers(
                course_admin=course_admin,
                company=company,
                prefix=spec["key"],
                course_specs=spec["courses"],
                start_date=start_date,
            )
            courses = course_data["courses"]
            teachers = course_data["teachers"]

            auditoriums = self._create_auditoriums(
                company=company,
                prefix=spec["key"],
                count=min(4, len(courses)),
                start_date=start_date,
            )

            groups = self._create_groups(
                company=company,
                prefix=spec["key"],
                courses=courses,
                teachers=teachers,
                auditoriums=auditoriums,
                start_date=start_date,
                today=today,
            )

            students = self._create_students(
                company=company,
                course_admin=course_admin,
                prefix=spec["key"],
                groups=groups,
                courses=courses,
                start_date=start_date,
                today=today,
                company_index=company_index,
            )

            self._create_attendance(groups=groups, start_date=start_date, today=today)
            self._create_payments(
                company=company,
                students=students,
                start_date=start_date,
                today=today,
            )
            self._create_expenses(company=company, start_date=start_date, today=today)
            self._create_tasks(
                company=company,
                course_admin=course_admin,
                managers=managers,
                start_date=start_date,
                today=today,
            )
            self._create_leads(
                company=company,
                managers=managers,
                groups=groups,
                courses=courses,
                start_date=start_date,
                today=today,
                company_index=company_index,
            )
            self._create_homework(
                company=company,
                groups=groups,
                teachers=teachers,
                today=today,
            )
            self._create_group_months(groups=groups, start_date=start_date, today=today)
            self._create_contracts(
                company=company,
                course_admin=course_admin,
                students=students,
                groups=groups,
                start_date=start_date,
                today=today,
                company_index=company_index,
            )
            self._create_marketplace(
                company=company,
                course_specs=spec["courses"],
                jobs=spec["jobs"],
                company_index=company_index,
            )
            self._create_landing(
                company=company,
                course_admin=course_admin,
                platform_admin=platform_admin,
                start_date=start_date,
                today=today,
            )
            self._create_finance_history(
                company=company,
                start_date=start_date,
                today=today,
            )
            self._create_platform_billing(
                company=company,
                plan=spec["plan"],
                monthly_fee=spec["monthly_fee"],
                start_date=start_date,
                today=today,
            )

        self._create_platform_promos(
            platform_admin=platform_admin,
            companies=created_companies,
            today=today,
            year=year,
        )

        self.stdout.write(self.style.SUCCESS("Database reset and seeded successfully."))
        self.stdout.write("")
        self.stdout.write("Platform admin:")
        self.stdout.write("  demo_admin / DemoAdmin123!")
        self.stdout.write("")
        self.stdout.write("Company admins:")
        for spec in company_specs:
            self.stdout.write(f'  {spec["key"]}_admin / Demo1234!')
        self.stdout.write("")
        self.stdout.write("Companies:")
        for company in created_companies:
            self.stdout.write(f"  - {company.name}")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "All previous database data was deleted before seeding."
            )
        )

    def _at_date(self, value, hour=9):
        return timezone.make_aware(
            datetime.combine(value, time(hour=hour))
        )

    def _month_starts(self, start_date, today):
        current = date(start_date.year, start_date.month, 1)
        last = date(today.year, today.month, 1)
        values = []
        while current <= last:
            values.append(current)
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return values

    def _create_managers(
        self,
        *,
        course_admin,
        company,
        prefix,
        company_index,
        start_date,
    ):
        names = [
            ("Айбек", "Токтосунов"),
            ("Нурия", "Абдыкадырова"),
        ]
        result = []
        for index, (first_name, last_name) in enumerate(names, start=1):
            user = User.objects.create_user(
                username=f"{prefix}_manager_{index}",
                password="Demo1234!",
                role=User.Role.MANAGER,
                first_name=first_name,
                last_name=last_name,
                phone=f"+996 555 {company_index}{index}0 10{index}",
                telegram=f"@{prefix}_manager_{index}",
                company=company,
                created_by=course_admin,
                is_active=True,
                must_set_password=False,
            )
            User.objects.filter(pk=user.pk).update(
                date_joined=self._at_date(start_date + timedelta(days=index), 10)
            )
            result.append(user)
        return result

    def _create_courses_and_teachers(
        self,
        *,
        course_admin,
        company,
        prefix,
        course_specs,
        start_date,
    ):
        courses = []
        teachers = []
        teacher_names = [
            ("Эрмек", "Садыков"),
            ("Алина", "Жумабаева"),
            ("Бекзат", "Осмонов"),
            ("Айпери", "Маматова"),
            ("Данияр", "Абдыкадыров"),
        ]

        for index, course_spec in enumerate(course_specs, start=1):
            title, price, weeks, lesson_minutes, description = course_spec
            course = Course.objects.create(
                title=f"{company.name} — {title}",
                price=Decimal(str(price)),
                duration_weeks=weeks,
                lesson_duration_minutes=lesson_minutes,
                description=description,
                schedule="Дүйшөмбү / Шаршемби / Жума",
            )
            course.admins.add(course_admin)
            Course.objects.filter(pk=course.pk).update(
                created_at=self._at_date(start_date + timedelta(days=index * 2), 11)
            )
            courses.append(course)

            first_name, last_name = teacher_names[(index - 1) % len(teacher_names)]
            teacher = User.objects.create_user(
                username=f"{prefix}_teacher_{index}",
                password="Demo1234!",
                role=User.Role.TEACHER,
                first_name=first_name,
                last_name=last_name,
                phone=f"+996 777 {index:03d} {len(courses):03d}",
                telegram=f"@{prefix}_teacher_{index}",
                salary_rate=Decimal("32000.00") + index * 3500,
                working_hours="09:00–18:00",
                company=company,
                created_by=course_admin,
                is_active=True,
                must_set_password=False,
            )
            teacher.teaching_courses.add(course)
            User.objects.filter(pk=teacher.pk).update(
                date_joined=self._at_date(start_date + timedelta(days=index * 2), 10)
            )
            teachers.append(teacher)

        return {"courses": courses, "teachers": teachers}

    def _create_auditoriums(self, *, company, prefix, count, start_date):
        result = []
        for index in range(1, count + 1):
            auditorium = Auditorium.objects.create(
                company=company,
                name=f"{company.name} Room {index}",
                number=f"{prefix[:2].upper()}-{100 + index}",
            )
            Auditorium.objects.filter(pk=auditorium.pk).update(
                created_at=self._at_date(start_date + timedelta(days=index), 9)
            )
            result.append(auditorium)
        return result

    def _create_groups(
        self,
        *,
        company,
        prefix,
        courses,
        teachers,
        auditoriums,
        start_date,
        today,
    ):
        result = []
        schedule_days = ["1,3,5", "2,4,6"]
        schedule_times = ["10:00", "14:00", "18:00", "19:00"]

        for index, course in enumerate(courses, start=1):
            group_start = start_date + timedelta(days=7 + index * 3)
            group = Group.objects.create(
                company=company,
                name=f"{prefix.upper()}-{index:02d}",
                course=course,
                teacher=teachers[index - 1],
                auditorium=auditoriums[(index - 1) % len(auditoriums)],
                status=Group.Status.ACTIVE,
                schedule_days=schedule_days[(index - 1) % len(schedule_days)],
                schedule_time=schedule_times[(index - 1) % len(schedule_times)],
                lessons_count=36,
                lessons_per_month=12,
                total_months=4,
                start_date=group_start,
                end_date=group_start + timedelta(days=120),
                teacher_percent=Decimal("30.00") + index,
            )
            Group.objects.filter(pk=group.pk).update(
                created_at=self._at_date(group_start, 9)
            )
            result.append(group)
        return result

    def _create_students(
        self,
        *,
        company,
        course_admin,
        prefix,
        groups,
        courses,
        start_date,
        today,
        company_index,
    ):
        first_names = [
            "Айдана", "Нурсултан", "Али", "Мээрим", "Баястан", "Диана",
            "Элдар", "Арууке", "Темирлан", "Сезим", "Адилет", "Жанара",
            "Азамат", "Наргиза", "Эмир", "Айпери", "Бектур", "Мадина",
            "Руслан", "Алина", "Эрлан", "Жылдыз", "Кубаныч", "Назгүл",
            "Ильяз", "Асел", "Нурбек", "Элина", "Самат", "Бермет",
            "Нурислам", "Аяна", "Дастан", "Арууза", "Ислам", "Элмира",
            "Байэл", "Салтанат", "Эрбол", "Адина",
        ]
        last_names = [
            "Абдиева", "Токтогулов", "Осмонов", "Жолдошева", "Садыков",
            "Мамбетова", "Ибраимов", "Касымова", "Эргешов", "Асанова",
            "Турсунов", "Абдыева", "Жээнбеков", "Маматова", "Алиев",
        ]

        result = []
        student_number = 0
        month_starts = self._month_starts(start_date, today)

        for month_index, month_start in enumerate(month_starts):
            # Deterministic realistic growth: every company gets 20–40 new
            # students every month, so charts remain stable between seed runs.
            students_this_month = 20 + (
                (company_index * 7 + month_index * 9) % 21
            )

            for local_index in range(students_this_month):
                student_number += 1

                group_index = (
                    month_index + local_index + company_index
                ) % len(groups)
                group = groups[group_index]
                course = courses[group_index]

                first_name = first_names[
                    (student_number + company_index * 3) % len(first_names)
                ]
                last_name = last_names[
                    (student_number + month_index * 2) % len(last_names)
                ]

                # Spread registrations through the month, but never into future.
                join_day = 1 + (local_index * 3 + company_index) % 27
                join_date = month_start + timedelta(days=join_day - 1)
                if join_date > today:
                    join_date = today

                user = User.objects.create_user(
                    username=f"{prefix}_student_{student_number:04d}",
                    password="Demo1234!",
                    role=User.Role.STUDENT,
                    first_name=first_name,
                    last_name=last_name,
                    phone=(
                        f"+996 {500 + company_index} "
                        f"{month_index + 1:02d}{local_index % 100:02d} "
                        f"{student_number % 100:02d}"
                    ),
                    company=company,
                    created_by=course_admin,
                    is_active=True,
                    must_set_password=False,
                )
                User.objects.filter(pk=user.pk).update(
                    date_joined=self._at_date(join_date, 12)
                )

                student = Student.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    phone=user.phone,
                    telegram=f"@{prefix}_student_{student_number:04d}",
                    company=company,
                    can_login=True,
                    primary_course=course,
                    notes=(
                        f"Клиент {company.name}, группа {group.name}, "
                        f"регистрация {join_date:%m.%Y}"
                    ),
                )
                Student.objects.filter(pk=student.pk).update(
                    created_at=self._at_date(join_date, 12)
                )

                group.students.add(student)
                result.append(student)

        return result

    def _create_attendance(self, *, groups, start_date, today):
        statuses = [
            Attendance.Status.PRESENT,
            Attendance.Status.PRESENT,
            Attendance.Status.PRESENT,
            Attendance.Status.ABSENT,
            Attendance.Status.EXCUSED,
        ]

        for group_index, group in enumerate(groups):
            lesson_date = group.start_date
            lesson_number = 0
            while lesson_date <= today:
                for student_index, student in enumerate(group.students.all()):
                    Attendance.objects.create(
                        group=group,
                        student=student,
                        date=lesson_date,
                        status=statuses[
                            (student_index + lesson_number + group_index)
                            % len(statuses)
                        ],
                    )
                lesson_date += timedelta(days=7)
                lesson_number += 1

    def _create_payments(self, *, company, students, start_date, today):
        months = self._month_starts(start_date, today)

        for student_index, student in enumerate(students):
            group = student.groups.first()
            if not group:
                continue

            amount = group.course.price if group.course else Decimal("10000.00")
            for month_index, month_start in enumerate(months):
                paid_at = month_start + timedelta(days=4 + student_index % 5)
                if paid_at > today:
                    paid_at = today

                is_current_month = (
                    month_start.year == today.year
                    and month_start.month == today.month
                )
                status_value = (
                    Payment.Status.DEBT
                    if is_current_month and student_index % 5 == 0
                    else Payment.Status.PAID
                )

                Payment.objects.create(
                    student=student,
                    group=group,
                    company=company,
                    amount=amount,
                    status=status_value,
                    paid_at=paid_at,
                    due_date=month_start + timedelta(days=10),
                )

    def _create_expenses(self, *, company, start_date, today):
        monthly_specs = [
            ("Аренда офиса", "rent", Decimal("65000.00")),
            ("Интернет жана коммуналдык", "utilities", Decimal("14000.00")),
            ("Маркетинг жана реклама", "marketing", Decimal("22000.00")),
            ("Окуу материалдары", "materials", Decimal("9000.00")),
        ]

        for month_index, month_start in enumerate(
            self._month_starts(start_date, today)
        ):
            for item_index, (description, category, amount) in enumerate(
                monthly_specs
            ):
                expense_date = month_start + timedelta(days=item_index * 4)
                if expense_date > today:
                    continue
                Expense.objects.create(
                    company=company,
                    description=f"{description} — {month_start:%m.%Y}",
                    amount=amount + month_index * 1000,
                    category=category,
                    date=expense_date,
                )

    def _create_tasks(
        self,
        *,
        company,
        course_admin,
        managers,
        start_date,
        today,
    ):
        titles = [
            "Обзвон новых лидов",
            "Проверить оплаты студентов",
            "Подготовить отчёт по группам",
            "Обновить расписание",
            "Запустить рекламную кампанию",
            "Собрать обратную связь",
        ]

        for index, title in enumerate(titles):
            Task.objects.create(
                company=company,
                title=title,
                description=f"{title} для {company.name}",
                assigned_to=managers[index % len(managers)],
                created_by=course_admin,
                due_date=today + timedelta(days=(index % 4) - 1),
                status=(
                    Task.Status.COMPLETED
                    if index % 3 == 0
                    else Task.Status.IN_PROGRESS
                    if index % 3 == 1
                    else Task.Status.PENDING
                ),
                priority=(
                    Task.Priority.HIGH
                    if index % 3 == 0
                    else Task.Priority.MEDIUM
                ),
                repeat_type=Task.RepeatType.NONE,
            )

    def _create_leads(
        self,
        *,
        company,
        managers,
        groups,
        courses,
        start_date,
        today,
        company_index,
    ):
        lead_names = [
            "Эрлан Кубанычбеков",
            "Айпери Маматова",
            "Данияр Абдыкадыров",
            "Жылдыз Сапарова",
            "Бектур Алиев",
            "Наргиза Токтосунова",
            "Асел Эрмекова",
            "Нурбек Жээнбеков",
        ]

        span_days = max((today - start_date).days, 1)
        for index, full_name in enumerate(lead_names):
            created_date = start_date + timedelta(
                days=min(index * max(span_days // len(lead_names), 1), span_days)
            )
            lead = TrialLead.objects.create(
                company=company,
                full_name=full_name,
                phone=f"+996 777 {company_index}{index:02d} 20{index}",
                age=18 + index,
                course_interest=courses[index % len(courses)].title,
                trial_attended=index % 3 != 0,
                status=[
                    TrialLead.Status.NEW,
                    TrialLead.Status.CONTACTED,
                    TrialLead.Status.TRIAL_SCHEDULED,
                    TrialLead.Status.ATTENDED,
                    TrialLead.Status.CONVERTED,
                ][index % 5],
                trial_date=min(created_date + timedelta(days=3), today),
                source=["Instagram", "Telegram", "Рекомендация"][index % 3],
                comment=f"Лид {company.name}",
                converted_to_student=index % 5 == 4,
                group_assigned=groups[index % len(groups)],
                payment_status=(
                    TrialLead.PaymentStatus.PAID
                    if index % 4 == 0
                    else TrialLead.PaymentStatus.PARTIAL
                    if index % 4 == 1
                    else TrialLead.PaymentStatus.NOT_PAID
                ),
            )
            TrialLead.objects.filter(pk=lead.pk).update(
                created_at=self._at_date(created_date, 13)
            )
            LeadAssignment.objects.create(
                lead=lead,
                manager=managers[index % len(managers)],
            )

    def _create_homework(self, *, company, groups, teachers, today):
        now = timezone.now()
        for group_index, group in enumerate(groups):
            for task_index in range(1, 3):
                task = HomeworkTask.objects.create(
                    group=group,
                    teacher=teachers[group_index],
                    company=company,
                    lesson_number=task_index * 4,
                    title=f"{group.name}: задание {task_index}",
                    description="Практическое задание по пройденной теме.",
                    task_type=(
                        HomeworkTask.TaskType.PROJECT
                        if task_index == 2
                        else HomeworkTask.TaskType.HOMEWORK
                    ),
                    deadline=now + timedelta(days=task_index * 4),
                    is_published=True,
                    allow_late=True,
                    grace_period_minutes=60,
                )
                for student_index, student in enumerate(
                    group.students.all()[:4]
                ):
                    HomeworkSubmission.objects.create(
                        task=task,
                        student=student,
                        answer_text=f"Ответ студента #{student_index + 1}",
                        status=(
                            HomeworkSubmission.Status.REVIEWED
                            if student_index % 2 == 0
                            else HomeworkSubmission.Status.PENDING
                        ),
                        grade=90 - student_index * 5
                        if student_index % 2 == 0
                        else None,
                        teacher_comment="Жакшы иш."
                        if student_index % 2 == 0
                        else "",
                    )

    def _create_group_months(self, *, groups, start_date, today):
        for group in groups:
            for month_number in range(1, 5):
                month_start = group.start_date + timedelta(
                    days=(month_number - 1) * 30
                )
                completed = month_start + timedelta(days=30) <= today
                GroupMonth.objects.create(
                    group=group,
                    month_number=month_number,
                    teacher_salary=Decimal("22000.00") + month_number * 2000,
                    status=(
                        GroupMonth.Status.COMPLETED
                        if completed
                        else GroupMonth.Status.PENDING
                    ),
                    completed_at=(
                        self._at_date(month_start + timedelta(days=30), 18)
                        if completed
                        else None
                    ),
                )

    def _create_contracts(
        self,
        *,
        company,
        course_admin,
        students,
        groups,
        start_date,
        today,
        company_index,
    ):
        ContractTemplate.objects.create(
            company=company,
            name="Стандартный договор",
            html_content=(
                "<h1>{{ company_name }}</h1>"
                "<p>{{ student_name }} — {{ course_name }}</p>"
                "<p>Сумма: {{ amount }}</p>"
            ),
            is_default=True,
        )

        for index, student in enumerate(students, start=1):
            group = student.groups.first()
            if not group:
                continue
            signed = index % 4 != 0
            contract = Contract.objects.create(
                company=company,
                student=student,
                group=group,
                status=(
                    Contract.Status.SIGNED
                    if signed
                    else Contract.Status.DRAFT
                ),
                contract_number=f"C{company_index}-{today.year}-{index:04d}",
                amount=group.course.price,
                start_date=group.start_date,
                end_date=group.end_date,
                terms="Стандартные условия обучения и оплаты.",
                created_by=course_admin,
                signed_at=(
                    self._at_date(min(group.start_date + timedelta(days=1), today), 15)
                    if signed
                    else None
                ),
            )
            Contract.objects.filter(pk=contract.pk).update(
                created_at=self._at_date(min(group.start_date, today), 14)
            )

    def _create_marketplace(
        self,
        *,
        company,
        course_specs,
        jobs,
        company_index,
    ):
        for index, course_spec in enumerate(course_specs, start=1):
            title, price, weeks, lesson_minutes, description = course_spec
            PublicCourse.objects.create(
                company=company,
                slug=f"{company.slug}-{index}",
                title=title,
                price=Decimal(str(price)),
                duration_weeks=weeks,
                lesson_duration_minutes=lesson_minutes,
                description=description,
                category=company.category,
                city=company.city,
                schedule="Кечки жана күндүзгү топтор",
                requirements="Окууга кызыгуу жана туруктуу катышуу",
                curriculum=[
                    {"title": "Модуль 1", "lessons": 6},
                    {"title": "Модуль 2", "lessons": 8},
                    {"title": "Практика", "lessons": 4},
                ],
                rating=Decimal("4.60") + Decimal(index) / Decimal("20"),
                reviews_count=10 + index * 4,
                is_active=True,
                views=100 + company_index * 70 + index * 25,
                applications_count=5 + index * 3,
            )

        for index, (title, salary_min, salary_max) in enumerate(jobs, start=1):
            JobVacancy.objects.create(
                company=company,
                title=title,
                description=f"{company.name} командасына {title} керек.",
                category=company.category,
                city=company.city,
                district=company.district,
                salary_min=salary_min,
                salary_max=salary_max,
                schedule="Толук күн",
                requirements="Тажрыйба, жоопкерчилик жана команда менен иштөө.",
                responsibilities="Негизги милдеттерди сапаттуу аткаруу.",
                is_active=True,
                views=70 + index * 30,
                applications=4 + index * 2,
            )

    def _create_landing(
        self,
        *,
        company,
        course_admin,
        platform_admin,
        start_date,
        today,
    ):
        active_page = LandingPage.objects.create(
            title=f"{company.name} — Главная",
            slug=f"{company.slug}-home",
            company=company,
            owner=course_admin,
            status=LandingPage.Status.ACTIVE,
            submitted_at=self._at_date(start_date, 10),
            moderated_at=self._at_date(start_date, 11),
            moderated_by=platform_admin,
            published_at=self._at_date(start_date, 12),
        )
        LandingPage.objects.filter(pk=active_page.pk).update(
            created_at=self._at_date(start_date, 9)
        )

        active_sections = [
            (
                LandingSection.SectionType.HERO,
                {
                    "title": company.name,
                    "subtitle": company.description,
                    "buttonText": "Записаться",
                },
            ),
            (
                LandingSection.SectionType.ABOUT,
                {
                    "title": "О нас",
                    "description": company.description,
                },
            ),
            (
                LandingSection.SectionType.COURSE_GRID,
                {"title": "Наши курсы"},
            ),
            (
                LandingSection.SectionType.STATISTICS,
                {
                    "title": "Результаты",
                    "items": [
                        {"label": "Курсы", "value": company.courses.count()},
                        {"label": "Студенты", "value": company.students.count()},
                    ],
                },
            ),
            (
                LandingSection.SectionType.BENEFITS,
                {
                    "title": "Почему выбирают нас",
                    "items": [
                        "Практическое обучение",
                        "Сильные преподаватели",
                        "Поддержка студентов",
                    ],
                },
            ),
            (
                LandingSection.SectionType.LEAD_FORM,
                {"title": "Записаться на консультацию"},
            ),
            (
                LandingSection.SectionType.CONTACTS,
                {
                    "phone": company.phone,
                    "telegram": company.telegram,
                    "instagram": company.instagram,
                },
            ),
        ]
        for order, (section_type, section_content) in enumerate(active_sections):
            LandingSection.objects.create(
                page=active_page,
                section_type=section_type,
                order=order,
                content=section_content,
            )

        # Every company has its own current moderation item.
        submitted_date = max(start_date, today - timedelta(days=2))
        pending_page = LandingPage.objects.create(
            title=f"{company.name} — Осенняя кампания",
            slug=f"{company.slug}-autumn-{today.year}",
            company=company,
            owner=course_admin,
            status=LandingPage.Status.PENDING,
            submitted_at=self._at_date(submitted_date, 14),
        )
        LandingPage.objects.filter(pk=pending_page.pk).update(
            created_at=self._at_date(submitted_date, 13)
        )

        landing_courses = [
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "price": f"{int(course.price):,} сом".replace(",", " "),
                "duration_weeks": course.duration_weeks,
            }
            for course in company.courses.filter(is_active=True)[:6]
        ]
        landing_teachers = [
            {
                "name": f"{teacher.first_name} {teacher.last_name}".strip(),
                "specialization": (
                    teacher.teaching_courses.first().title
                    if teacher.teaching_courses.exists()
                    else "Преподаватель"
                ),
                "color": teacher.color or "#45B2EF",
            }
            for teacher in company.users.filter(role=User.Role.TEACHER)[:6]
        ]

        pending_sections = [
            (
                LandingSection.SectionType.HERO,
                {
                    "title": f"Новый набор — {company.name}",
                    "subtitle": (
                        f"{company.description} Запишитесь сейчас и начните обучение "
                        "в ближайшей группе."
                    ),
                    "button_label": "Оставить заявку",
                    "button_href": "#lead-form",
                },
            ),
            (
                LandingSection.SectionType.ABOUT,
                {
                    "title": f"О {company.name}",
                    "text": (
                        f"{company.description} Мы работаем в Оше и делаем упор "
                        "на практику, понятную программу и поддержку студентов."
                    ),
                },
            ),
            (
                LandingSection.SectionType.STATISTICS,
                {
                    "title": "Мы в цифрах",
                    "items": [
                        {
                            "number": str(company.students.count()),
                            "label": "студентов",
                        },
                        {
                            "number": str(company.courses.filter(is_active=True).count()),
                            "label": "направлений",
                        },
                        {
                            "number": str(company.users.filter(role=User.Role.TEACHER).count()),
                            "label": "преподавателей",
                        },
                        {
                            "number": f"{company.rating}",
                            "label": "рейтинг",
                        },
                    ],
                },
            ),
            (
                LandingSection.SectionType.COURSE_GRID,
                {
                    "title": "Популярные направления",
                    "description": "Выберите программу под свою цель и уровень.",
                    "courses": landing_courses,
                },
            ),
            (
                LandingSection.SectionType.BENEFITS,
                {
                    "title": "Почему выбирают нас",
                    "items": [
                        {
                            "icon": "star",
                            "title": "Практика с первого дня",
                            "description": "Минимум сухой теории — больше задач и реальных кейсов.",
                        },
                        {
                            "icon": "group",
                            "title": "Небольшие группы",
                            "description": "Преподаватель успевает работать с каждым студентом.",
                        },
                        {
                            "icon": "schedule",
                            "title": "Удобное расписание",
                            "description": "Дневные и вечерние группы для учёбы и работы.",
                        },
                        {
                            "icon": "support",
                            "title": "Поддержка",
                            "description": "Помогаем по вопросам обучения и домашних заданий.",
                        },
                    ],
                },
            ),
            (
                LandingSection.SectionType.TEACHER_SLIDER,
                {
                    "title": "Преподаватели",
                    "teachers": landing_teachers,
                },
            ),
            (
                LandingSection.SectionType.PRICING,
                {
                    "title": "Стоимость обучения",
                    "items": "\n".join(
                        [
                            f"{course['title']}|{course['price']}|{course['duration_weeks']} недель"
                            for course in landing_courses[:3]
                        ]
                    ),
                },
            ),
            (
                LandingSection.SectionType.TESTIMONIALS,
                {
                    "title": "Отзывы студентов",
                    "items": [
                        {
                            "name": "Айдана",
                            "text": "Очень понравилась практика и понятное объяснение преподавателя.",
                            "rating": 5,
                        },
                        {
                            "name": "Нурсултан",
                            "text": "За короткое время собрал хороший результат и стал увереннее.",
                            "rating": 5,
                        },
                        {
                            "name": "Мээрим",
                            "text": "Удобное расписание, сильная команда и хорошая атмосфера.",
                            "rating": 5,
                        },
                    ],
                },
            ),
            (
                LandingSection.SectionType.FAQ,
                {
                    "title": "Частые вопросы",
                    "items": [
                        {
                            "q": "Можно начать с нуля?",
                            "a": "Да. Для начинающих есть группы с базовой программой.",
                        },
                        {
                            "q": "Есть ли пробное занятие?",
                            "a": "Да, менеджер подберёт ближайшую доступную дату.",
                        },
                        {
                            "q": "Как проходит оплата?",
                            "a": "Оплата производится помесячно по условиям выбранного курса.",
                        },
                        {
                            "q": "Можно учиться вечером?",
                            "a": "Да, у большинства направлений есть вечерние группы.",
                        },
                    ],
                },
            ),
            (
                LandingSection.SectionType.LEAD_FORM,
                {
                    "title": "Запишитесь на бесплатную консультацию",
                },
            ),
            (
                LandingSection.SectionType.CONTACTS,
                {
                    "phone": company.phone,
                    "telegram": company.telegram,
                    "whatsapp": company.whatsapp,
                    "address": company.district or "Ош",
                },
            ),
        ]
        for order, (section_type, section_content) in enumerate(pending_sections):
            LandingSection.objects.create(
                page=pending_page,
                section_type=section_type,
                order=order,
                content=section_content,
            )

    def _create_platform_promos(
        self,
        *,
        platform_admin,
        companies,
        today,
        year,
    ):
        month_names = {
            1: "JAN",
            2: "FEB",
            3: "MAR",
            4: "APR",
            5: "MAY",
            6: "JUN",
            7: "JUL",
            8: "AUG",
            9: "SEP",
            10: "OCT",
            11: "NOV",
            12: "DEC",
        }

        # Monthly promo campaigns from June through the current month.
        for month in range(6, today.month + 1):
            month_start = date(year, month, 1)
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)

            expiry = timezone.make_aware(
                datetime.combine(next_month - timedelta(days=1), time(23, 59))
            )
            is_current = month == today.month
            promo = PromoCode.objects.create(
                code=f"{month_names[month]}{year}",
                reward_type=PromoCode.RewardType.COINS,
                reward_value=500 + (month - 6) * 100,
                max_usages=50,
                current_usages=0,
                expiry_date=expiry,
                is_active=is_current,
                created_by=platform_admin,
            )
            balance = PromoBalance.objects.create(
                promo_code=promo,
                balance=0,
            )
            balance.add_coins(promo.reward_value * promo.max_usages)

            # Historical months include realistic redemptions.
            if not is_current:
                for company in companies[: min(len(companies), 2)]:
                    owner = company.owner
                    if owner and promo.activate(owner):
                        PromoRedemption.objects.get_or_create(
                            promo_code=promo,
                            company=company,
                            defaults={"user": owner},
                        )

        holiday_promos = [
            {
                "code": f"NOORUZ{year}",
                "reward": 1200,
                "expires": date(year, 3, 31),
                "active": False,
            },
            {
                "code": f"INDEPENDENCE{year}",
                "reward": 1800,
                "expires": date(year, 8, 31),
                "active": today == date(year, 8, 31),
            },
            {
                "code": f"BACKTOSCHOOL{year}",
                "reward": 1500,
                "expires": date(year, 9, 15),
                "active": False,
            },
            {
                "code": f"AUTUMN{year}",
                "reward": 1000,
                "expires": date(year, 10, 31),
                "active": today <= date(year, 10, 31),
            },
            {
                "code": f"NEWYEAR{year + 1}",
                "reward": 2000,
                "expires": date(year + 1, 1, 10),
                "active": today.month >= 12,
            },
        ]

        for item in holiday_promos:
            expiry = timezone.make_aware(
                datetime.combine(item["expires"], time(23, 59))
            )
            promo = PromoCode.objects.create(
                code=item["code"],
                reward_type=PromoCode.RewardType.COINS,
                reward_value=item["reward"],
                max_usages=100,
                current_usages=0,
                expiry_date=expiry,
                is_active=item["active"],
                created_by=platform_admin,
            )
            balance = PromoBalance.objects.create(
                promo_code=promo,
                balance=0,
            )
            balance.add_coins(promo.reward_value * promo.max_usages)

    def _create_platform_billing(
        self,
        *,
        company,
        plan,
        monthly_fee,
        start_date,
        today,
    ):
        month_starts = self._month_starts(start_date, today)
        current_month = date(today.year, today.month, 1)
        next_month = (
            date(today.year + 1, 1, 1)
            if today.month == 12
            else date(today.year, today.month + 1, 1)
        )

        subscription = CompanySubscription.objects.create(
            company=company,
            plan=plan,
            monthly_fee=monthly_fee,
            status=CompanySubscription.Status.ACTIVE,
            started_at=start_date,
            next_payment_date=next_month,
            auto_renew=True,
        )

        for month_start in month_starts:
            if month_start.month == 12:
                period_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(
                    month_start.year,
                    month_start.month + 1,
                    1,
                ) - timedelta(days=1)

            is_current = month_start == current_month
            paid = not is_current or today.day >= 5

            CompanyPlatformPayment.objects.create(
                company=company,
                subscription=subscription,
                amount=monthly_fee,
                period_start=month_start,
                period_end=period_end,
                due_date=month_start + timedelta(days=4),
                paid_at=(
                    self._at_date(month_start + timedelta(days=4), 11)
                    if paid
                    else None
                ),
                status=(
                    CompanyPlatformPayment.Status.PAID
                    if paid
                    else CompanyPlatformPayment.Status.PENDING
                ),
                note=f"Оплата тарифа {subscription.get_plan_display()}",
            )

    def _create_finance_history(self, *, company, start_date, today):
        balance = CompanyBalance.objects.create(
            company=company,
            balance=25000,
        )

        for index, month_start in enumerate(
            self._month_starts(start_date, today),
            start=1,
        ):
            Transaction.objects.create(
                company=company,
                amount=5000 + index * 500,
                reason=f"Пополнение demo-баланса {month_start:%m.%Y}",
                transaction_type=Transaction.Type.DEPOSIT,
            )
            if index % 2 == 0:
                Transaction.objects.create(
                    company=company,
                    amount=-1000,
                    reason=f"Продвижение {month_start:%m.%Y}",
                    transaction_type=Transaction.Type.WITHDRAWAL,
                )
