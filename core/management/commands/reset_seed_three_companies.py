from datetime import date, datetime, time, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finance.models import Budget, BudgetCategory, MonthlySummary, SalaryRecord

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
        "Wipe the local database and seed four production-like companies with "
        "realistic monthly history, groups, students, finance and marketplace data."
    )

    def _create_seed_user(self, *, password, **kwargs):
        """
        Create seed users quickly by reusing one already-computed password hash
        per distinct password. This avoids running expensive password hashing
        hundreds of times during seed generation.
        """
        if password not in self._password_hash_cache:
            self._password_hash_cache[password] = make_password(password)

        return User.objects.create(
            password=self._password_hash_cache[password],
            **kwargs,
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

        self._password_hash_cache = {}
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
                "description": "Практическая IT-академия в Оше с программами по разработке, тестированию и дизайну.",
                "plan": CompanySubscription.Plan.PRO,
                "monthly_fee": Decimal("15000.00"),
                "courses": [
                    ("Frontend React", 8000, 16, 90, "React, TypeScript, Next.js жана командалык долбоорлор."),
                    ("Python Django", 8000, 20, 90, "Python, Django, REST API жана PostgreSQL."),
                    ("Flutter Mobile", 8000, 18, 90, "Flutter, Dart жана Android/iOS колдонмолору."),
                    ("QA Engineering", 7000, 14, 80, "Manual QA, API testing жана automation негиздери."),
                    ("UI/UX Design", 8000, 14, 80, "Figma, UX research жана продукт дизайн."),
                    ("Data Analytics", 9000, 16, 90, "Excel, SQL, Power BI жана аналитикалык отчеттор."),
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
                "start": date(year, 7, 1),
                "category": CompanyCategory.LANGUAGES,
                "district": "Черёмушки",
                "phone": "+996 700 710 202",
                "telegram": "@tilordo_osh",
                "instagram": "@tilordo_language",
                "description": "Языковой центр с разговорными программами, подготовкой к экзаменам и небольшими группами.",
                "plan": CompanySubscription.Plan.GROWTH,
                "monthly_fee": Decimal("10000.00"),
                "courses": [
                    ("English A1-A2", 3000, 12, 80, "General English для начинающих."),
                    ("English B1-B2", 4000, 14, 80, "Разговорный английский и академическая лексика."),
                    ("IELTS Preparation", 7000, 16, 90, "Подготовка к IELTS Academic по четырём навыкам."),
                    ("Turkish Language", 3500, 12, 80, "Турецкий язык от A1 до B1."),
                    ("Korean Language", 4500, 14, 80, "Корейский язык и основы TOPIK."),
                    ("Russian Speaking", 2500, 12, 80, "Практический русский язык для учёбы и работы."),
                ],
                "jobs": [
                    ("English Teacher", 30000, 50000),
                    ("IELTS Instructor", 40000, 65000),
                    ("Korean Language Teacher", 32000, 52000),
                ],
            },
            {
                "key": "ishker",
                "name": "Ishker Business School",
                "slug": "ishker-business-school",
                "start": date(year, 8, 1),
                "category": CompanyCategory.BUSINESS,
                "district": "ХБК",
                "phone": "+996 700 810 303",
                "telegram": "@ishker_school",
                "instagram": "@ishker_business",
                "description": "Бизнес-школа для предпринимателей и специалистов по продажам, маркетингу и финансам.",
                "plan": CompanySubscription.Plan.GROWTH,
                "monthly_fee": Decimal("10000.00"),
                "courses": [
                    ("SMM & Content", 6000, 10, 80, "SMM стратегия, контент, таргет жана аналитика."),
                    ("Sales Management", 7000, 10, 80, "Воронка продаж, переговоры и CRM."),
                    ("Accounting 1C", 8000, 12, 90, "Бухгалтерский учёт и практическая работа в 1C."),
                    ("Excel & Analytics", 5000, 8, 80, "Excel, отчёты, сводные таблицы и dashboards."),
                    ("Entrepreneurship", 9000, 12, 90, "Бизнес-модель, финансы, продукт жана масштабирование."),
                    ("Digital Marketing", 7000, 12, 80, "Performance marketing, контент и рекламные каналы."),
                ],
                "jobs": [
                    ("SMM Manager", 30000, 50000),
                    ("Sales Manager", 30000, 60000),
                    ("Business Mentor", 45000, 70000),
                ],
            },
            {
                "key": "muras",
                "name": "Muras Creative Academy",
                "slug": "muras-creative-academy",
                "start": date(year, 9, 1),
                "category": CompanyCategory.CRAFTS,
                "district": "Юго-Восток",
                "phone": "+996 700 910 404",
                "telegram": "@muras_creative",
                "instagram": "@muras_creative_academy",
                "description": "Креативная академия с практическими программами по дизайну, медиа и прикладным направлениям.",
                "plan": CompanySubscription.Plan.START,
                "monthly_fee": Decimal("7000.00"),
                "courses": [
                    ("Graphic Design", 7000, 12, 80, "Айдентика, композиция, типографика жана Adobe tools."),
                    ("Motion Design", 9000, 14, 90, "After Effects, motion graphics жана анимация."),
                    ("Photography", 6000, 10, 80, "Камера, свет, композиция жана обработка."),
                    ("Video Editing", 8000, 12, 90, "Монтаж, звук, цветокоррекция жана storytelling."),
                    ("Sewing & Fashion", 7000, 14, 90, "Конструирование, крой, пошив жана базовый fashion design."),
                    ("Interior Design", 10000, 16, 90, "Планировка, визуализация, материалы жана проектирование."),
                ],
                "jobs": [
                    ("Graphic Design Mentor", 35000, 55000),
                    ("Video Editor", 35000, 60000),
                    ("Fashion Instructor", 32000, 52000),
                ],
            },
        ]

        platform_admin = self._create_seed_user(
            username="platform_admin",
            password="Platform2026!",
            role=User.Role.ADMIN,
            first_name="Азамат",
            last_name="Сатыбалдиев",
            email="admin@eduosh.kg",
            is_active=True,
            is_staff=True,
            is_superuser=True,
            must_set_password=False,
        )

        created_companies = []
        admin_names = [
            ("Эрмек", "Токтосунов"),
            ("Айпери", "Жумабаева"),
            ("Данияр", "Абдыкадыров"),
            ("Мээрим", "Сапарова"),
        ]

        for company_index, spec in enumerate(company_specs, start=1):
            start_date = min(spec["start"], today)
            start_dt = self._at_date(start_date, 9)

            admin_first_name, admin_last_name = admin_names[company_index - 1]
            course_admin = self._create_seed_user(
                username=f'{spec["key"]}_admin',
                password="Company2026!",
                role=User.Role.COURSE_ADMIN,
                first_name=admin_first_name,
                last_name=admin_last_name,
                email=f'{spec["key"]}.admin@eduosh.kg',
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
                website="",
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
            teachers_by_course = course_data["teachers_by_course"]

            auditoriums = self._create_auditoriums(
                company=company,
                prefix=spec["key"],
                count=max(6, len(courses)),
                start_date=start_date,
            )

            groups = self._create_groups(
                company=company,
                prefix=spec["key"],
                courses=courses,
                teachers=teachers,
                teachers_by_course=teachers_by_course,
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
            self._create_group_months(groups=groups, start_date=start_date, today=today)
            self._create_salary_records(
                company=company,
                managers=managers,
                teachers=teachers,
                groups=groups,
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
            self._create_finance_reporting(
                company=company,
                start_date=start_date,
                today=today,
            )
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
        self.stdout.write("  platform_admin / Platform2026!")
        self.stdout.write("")
        self.stdout.write("Company admins:")
        for spec in company_specs:
            self.stdout.write(f'  {spec["key"]}_admin / Company2026!')
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
            ("Элдияр", "Жээнбеков"),
            ("Айпери", "Маматова"),
            ("Бекзат", "Осмонов"),
            ("Арууке", "Сапарова"),
            ("Темирлан", "Касымов"),
            ("Мээрим", "Жолдошева"),
            ("Данияр", "Турсунов"),
            ("Жанара", "Эргешова"),
            ("Нурбек", "Асанов"),
            ("Сезим", "Мамбетова"),
        ]
        result = []
        offset = (company_index - 1) * 3
        for index in range(1, 4):
            first_name, last_name = names[(offset + index - 1) % len(names)]
            user = self._create_seed_user(
                username=f"{prefix}_manager_{index}",
                password="Company2026!",
                role=User.Role.MANAGER,
                first_name=first_name,
                last_name=last_name,
                phone=f"+996 555 {company_index}{index}0 10{index}",
                telegram=f"@{prefix}_manager_{index}",
                salary_rate=Decimal(str(35000 + index * 5000)),
                working_hours="09:00–18:00",
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
        teachers_by_course = {}
        teacher_names = [
            ("Эрмек", "Садыков"), ("Алина", "Жумабаева"), ("Бекзат", "Осмонов"),
            ("Айпери", "Маматова"), ("Данияр", "Абдыкадыров"), ("Назгүл", "Токтогулова"),
            ("Кубаныч", "Жээнбеков"), ("Бермет", "Асанова"), ("Адилет", "Ибраимов"),
            ("Аяна", "Касымова"), ("Самат", "Эргешов"), ("Салтанат", "Мамбетова"),
            ("Нурислам", "Турсунов"), ("Элина", "Абдиева"), ("Баястан", "Алиев"),
            ("Мадина", "Сапарова"), ("Эрбол", "Калыбеков"), ("Асел", "Омуралиева"),
            ("Азизбек", "Шарипов"), ("Дилноза", "Рахматова"), ("Шахзод", "Каримов"),
            ("Малика", "Юлдашева"), ("Иван", "Петров"), ("Анна", "Смирнова"),
        ]
        teacher_colors = [
            "#45B2EF",
            "#22C55E",
            "#F59E0B",
            "#A855F7",
            "#EF4444",
            "#14B8A6",
            "#F97316",
            "#6366F1",
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
                created_at=self._at_date(
                    start_date + timedelta(days=index * 2),
                    11,
                )
            )
            courses.append(course)

            # Two teachers per course gives the seeded business enough real
            # capacity for several parallel monthly groups without impossible
            # teacher or room collisions.
            course_teachers = []
            for teacher_variant in range(2):
                teacher_global_index = (
                    (index - 1) * 2
                    + teacher_variant
                )
                teacher_offset = (
                    sum(ord(char) for char in prefix)
                    + teacher_global_index
                ) % len(teacher_names)
                first_name, last_name = teacher_names[teacher_offset]

                teacher_number = teacher_global_index + 1
                teacher = self._create_seed_user(
                    username=f"{prefix}_teacher_{teacher_number}",
                    password="Company2026!",
                    role=User.Role.TEACHER,
                    first_name=first_name,
                    last_name=last_name,
                    color=teacher_colors[
                        (
                            teacher_number
                            + sum(ord(char) for char in prefix)
                        )
                        % len(teacher_colors)
                    ],
                    phone=(
                        f"+996 777 "
                        f"{teacher_number:03d} "
                        f"{index:03d}"
                    ),
                    telegram=f"@{prefix}_teacher_{teacher_number}",
                    salary_rate=(
                        Decimal("32000.00")
                        + Decimal(teacher_number * 2500)
                    ),
                    working_hours="09:00–21:00",
                    company=company,
                    created_by=course_admin,
                    is_active=True,
                    must_set_password=False,
                )
                teacher.teaching_courses.add(course)
                User.objects.filter(pk=teacher.pk).update(
                    date_joined=self._at_date(
                        start_date
                        + timedelta(days=index * 2 + teacher_variant),
                        10,
                    )
                )
                teachers.append(teacher)
                course_teachers.append(teacher)

            teachers_by_course[course.id] = course_teachers

        return {
            "courses": courses,
            "teachers": teachers,
            "teachers_by_course": teachers_by_course,
        }

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
        teachers_by_course,
        auditoriums,
        start_date,
        today,
    ):
        result = []
        # 0 = Monday ... 6 = Sunday. Keep several patterns so rooms and
        # teachers can be scheduled without collisions.
        schedule_patterns = [
            "0,2,4",
            "1,3,5",
            "0,3,5",
            "1,4",
            "2,5",
            "0,2",
            "1,3",
            "3,5",
            "0,4",
            "2,4",
        ]
        schedule_times = [
            "08:00",
            "10:00",
            "12:00",
            "14:00",
            "16:00",
            "18:00",
            "20:00",
        ]
        month_starts = self._month_starts(start_date, today)

        def parse_days(value):
            return {int(item) for item in value.split(",") if item.strip()}

        def time_to_minutes(value):
            hours, minutes = value.split(":")
            return int(hours) * 60 + int(minutes)

        def overlaps_dates(start_a, end_a, start_b, end_b):
            return start_a <= end_b and start_b <= end_a

        def slot_is_free(
            *,
            teacher,
            auditorium,
            schedule_days,
            schedule_time,
            group_start,
            group_end,
            lesson_duration,
        ):
            target_days = parse_days(schedule_days)
            target_start = time_to_minutes(schedule_time)
            # Keep a short turnover/break between lessons. A room or teacher
            # must not start the next lesson at the exact minute the previous
            # one ends.
            break_minutes = 15
            target_end = target_start + lesson_duration

            for existing in result:
                if not overlaps_dates(
                    group_start,
                    group_end,
                    existing.start_date,
                    existing.end_date,
                ):
                    continue

                existing_days = parse_days(existing.schedule_days or "")
                if not target_days.intersection(existing_days):
                    continue

                existing_start = time_to_minutes(existing.schedule_time)
                existing_duration = (
                    existing.course.lesson_duration_minutes
                    if existing.course
                    else 90
                ) or 90
                existing_end = existing_start + existing_duration

                times_overlap = (
                    target_start < existing_end + break_minutes
                    and existing_start < target_end + break_minutes
                )
                if not times_overlap:
                    continue

                # A room and a teacher can only have one lesson at a time.
                if (
                    existing.auditorium_id == auditorium.id
                    or existing.teacher_id == teacher.id
                ):
                    return False

            return True

        for month_index, month_start in enumerate(month_starts):
            for course_index, course in enumerate(courses):
                groups_count = 1 + (
                    (company.id + course_index + month_index) % 3
                )

                base_group_name = course.title
                company_prefix = f"{company.name} — "
                if base_group_name.startswith(company_prefix):
                    base_group_name = base_group_name[len(company_prefix):]
                base_group_name = base_group_name.strip()

                course_teachers = teachers_by_course.get(course.id) or [
                    teachers[course_index % len(teachers)]
                ]
                lesson_duration = course.lesson_duration_minutes or 90

                for local_index in range(groups_count):
                    day_offset = [1, 10, 20][local_index]
                    group_start = month_start + timedelta(days=day_offset - 1)
                    if group_start > today:
                        group_start = today

                    duration_months = max(
                        2,
                        min(6, int(round(course.duration_weeks / 4))),
                    )
                    group_end = group_start + relativedelta(
                        months=duration_months
                    )

                    # Try every room/day/time combination until a truly free
                    # slot is found. This prevents impossible seed schedules.
                    slot = None
                    seed_offset = (
                        course_index
                        + month_index
                        + local_index
                    )

                    for teacher_offset in range(len(course_teachers)):
                        teacher = course_teachers[
                            (seed_offset + teacher_offset)
                            % len(course_teachers)
                        ]

                        for room_offset in range(len(auditoriums)):
                            auditorium = auditoriums[
                                (seed_offset + room_offset)
                                % len(auditoriums)
                            ]

                            for pattern_offset in range(len(schedule_patterns)):
                                schedule_days = schedule_patterns[
                                    (seed_offset + pattern_offset)
                                    % len(schedule_patterns)
                                ]

                                for time_offset in range(len(schedule_times)):
                                    schedule_time = schedule_times[
                                        (seed_offset + time_offset)
                                        % len(schedule_times)
                                    ]

                                    if slot_is_free(
                                        teacher=teacher,
                                        auditorium=auditorium,
                                        schedule_days=schedule_days,
                                        schedule_time=schedule_time,
                                        group_start=group_start,
                                        group_end=group_end,
                                        lesson_duration=lesson_duration,
                                    ):
                                        slot = (
                                            teacher,
                                            auditorium,
                                            schedule_days,
                                            schedule_time,
                                        )
                                        break

                                if slot:
                                    break

                            if slot:
                                break

                        if slot:
                            break

                    if not slot:
                        raise CommandError(
                            "Could not allocate a conflict-free schedule "
                            f"for {company.name}: {base_group_name} "
                            f"starting {group_start}."
                        )

                    (
                        teacher,
                        auditorium,
                        selected_days,
                        selected_time,
                    ) = slot

                    sequence = (
                        Group.objects.filter(
                            company=company,
                            course=course,
                        ).count()
                        + 1
                    )

                    group = Group.objects.create(
                        company=company,
                        name=(
                            f"{base_group_name} "
                            f"{group_start:%y%m}-{sequence:02d}"
                        ),
                        course=course,
                        teacher=teacher,
                        auditorium=auditorium,
                        status=Group.Status.ACTIVE,
                        schedule_days=selected_days,
                        schedule_time=selected_time,
                        lessons_count=duration_months * 12,
                        lessons_per_month=12,
                        total_months=duration_months,
                        start_date=group_start,
                        end_date=group_end,
                        teacher_percent=Decimal(
                            str(7 + ((course_index + local_index) % 4))
                        ),
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
        kyrgyz_first_names = [
            "Айдана", "Нурсултан", "Мээрим", "Баястан", "Арууке", "Сезим",
            "Адилет", "Жанара", "Азамат", "Айпери", "Бектур", "Наргиза",
            "Эрлан", "Жылдыз", "Кубаныч", "Назгүл", "Асел", "Нурбек",
            "Самат", "Бермет", "Аяна", "Дастан", "Арууза", "Элмира",
            "Байэл", "Салтанат", "Эрбол", "Адина", "Элдияр", "Каныкей",
            "Акжол", "Айсулуу", "Бегимай", "Нурэл", "Эрмек", "Чолпон",
            "Темирлан", "Мадина", "Нурислам", "Керемет",
        ]
        kyrgyz_last_names = [
            "Абдиев", "Токтогулов", "Осмонов", "Жолдошев", "Садыков",
            "Мамбетов", "Ибраимов", "Касымов", "Эргешов", "Асанов",
            "Турсунов", "Абдыкадыров", "Жээнбеков", "Маматов", "Алиев",
            "Сапаров", "Калыбеков", "Омуралиев", "Токтосунов", "Кубанычбеков",
            "Исмаилов", "Бекболотов", "Жумабаев", "Мураталиев", "Сулайманов",
            "Кожомбердиев", "Талантбеков", "Ниязов", "Анарбеков", "Эсеналиев",
            "Кудайбердиев", "Шаршенов", "Болотбеков", "Абдрахманов", "Кулматов",
            "Мырзабеков", "Усенов", "Жапаров", "Токтомушев", "Сыдыков",
        ]
        uzbek_first_names = [
            "Азизбек", "Шахзод", "Жасур", "Бехруз", "Дилшод", "Сардор",
            "Мухаммад", "Акмал", "Фаррух", "Отабек", "Дилноза", "Малика",
            "Шахноза", "Нилуфар", "Зухра", "Мафтуна", "Гулноза", "Мадина",
            "Севара", "Феруза",
        ]
        uzbek_last_names = [
            "Каримов", "Рахматов", "Юлдашев", "Турсунов", "Абдуллаев",
            "Хасанов", "Рустамов", "Норматов", "Эргашев", "Хакимов",
            "Саидов", "Умаров", "Исмаилов", "Мирзаев", "Кодиров",
            "Назаров", "Аббасов", "Хамидов", "Бурханов", "Шарипов",
        ]
        other_first_names = [
            "Иван", "Анна", "Максим", "София", "Алексей", "Мария",
            "Артур", "Диана", "Тимур", "Алина", "Роман", "Елена",
            "Давид", "Кристина", "Руслан", "Виктория",
        ]
        other_last_names = [
            "Петров", "Смирнов", "Иванов", "Кузнецов", "Попов", "Соколов",
            "Морозов", "Волков", "Орлов", "Новиков", "Федоров", "Михайлов",
            "Беляев", "Григорьев", "Лебедев", "Ковалев",
        ]

        result = []
        student_number = 0

        def pick_name(index):
            bucket = index % 100
            if bucket < 80:
                first_pool = kyrgyz_first_names
                last_pool = kyrgyz_last_names
                local = index
            elif bucket < 92:
                first_pool = uzbek_first_names
                last_pool = uzbek_last_names
                local = index * 3 + company_index
            else:
                first_pool = other_first_names
                last_pool = other_last_names
                local = index * 5 + company_index

            first_name = first_pool[local % len(first_pool)]
            last_name = last_pool[
                (local // len(first_pool) + local * 7) % len(last_pool)
            ]
            return first_name, last_name

        for group_index, group in enumerate(groups):
            students_count = 6 + (
                (company_index * 5 + group_index * 7) % 7
            )

            for local_index in range(students_count):
                student_number += 1
                global_index = (
                    company_index * 10000
                    + group_index * 20
                    + local_index
                )
                first_name, last_name = pick_name(global_index)

                join_date = group.start_date + timedelta(
                    days=min(local_index // 3, 5)
                )
                if join_date > today:
                    join_date = today

                username = (
                    f"{prefix}.student."
                    f"{student_number:05d}"
                )
                user = self._create_seed_user(
                    username=username,
                    password="Company2026!",
                    role=User.Role.STUDENT,
                    first_name=first_name,
                    last_name=last_name,
                    phone=(
                        f"+996 {500 + company_index} "
                        f"{(group_index + 10) % 100:02d}"
                        f"{local_index:02d} "
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
                    telegram=f"@{prefix}_student_{student_number:05d}",
                    company=company,
                    can_login=True,
                    primary_course=group.course,
                    notes="",
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
        all_months = self._month_starts(start_date, today)

        for student_index, student in enumerate(students):
            group = student.groups.first()
            if not group or not group.course:
                continue

            persisted_student = Student.objects.only("created_at").get(pk=student.pk)
            joined_on = persisted_student.created_at.date()
            joined_month = date(joined_on.year, joined_on.month, 1)

            # A student pays only from the month they actually joined.
            months = [month for month in all_months if month >= joined_month]
            amount = group.course.price

            for month_index, month_start in enumerate(months):
                paid_at = month_start + timedelta(days=3 + student_index % 7)
                if paid_at > today:
                    paid_at = today

                is_current_month = (
                    month_start.year == today.year
                    and month_start.month == today.month
                )

                # Roughly 10% of current-month invoices stay unpaid.
                status_value = (
                    Payment.Status.DEBT
                    if is_current_month and student_index % 10 == 0
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
        from calendar import monthrange
        from django.db.models import Sum

        months = self._month_starts(start_date, today)

        for month_index, month_start in enumerate(months):
            month_end = date(
                month_start.year,
                month_start.month,
                monthrange(month_start.year, month_start.month)[1],
            )
            period_end = min(month_end, today)

            monthly_income = (
                Payment.objects.filter(
                    company=company,
                    status=Payment.Status.PAID,
                    paid_at__gte=month_start,
                    paid_at__lte=period_end,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )

            if monthly_income <= 0:
                continue

            # В реальной учебной компании расходы обычно меняются вместе с
            # выручкой. Для тестовой базы держим их примерно в диапазоне 48–56%.
            expense_ratio = Decimal(
                str(0.48 + ((month_index + company.id) % 5) * 0.02)
            )
            target_total_expenses = (
                monthly_income * expense_ratio
            ).quantize(Decimal("0.01"))

            salary_expenses = (
                Expense.objects.filter(
                    company=company,
                    category="salary",
                    date__gte=month_start,
                    date__lte=period_end,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )

            remaining = max(
                target_total_expenses - salary_expenses,
                Decimal("0"),
            )

            categories = [
                ("Аренда офиса", "rent", Decimal("0.42")),
                ("Коммунальные и интернет", "utilities", Decimal("0.10")),
                ("Маркетинг и реклама", "marketing", Decimal("0.20")),
                ("Учебные материалы", "materials", Decimal("0.09")),
                ("Оборудование и сервисы", "equipment", Decimal("0.08")),
                ("Налоги и обязательные платежи", "tax", Decimal("0.11")),
            ]

            distributed = Decimal("0")
            for item_index, (description, category, share) in enumerate(categories):
                if item_index == len(categories) - 1:
                    amount = remaining - distributed
                else:
                    amount = (remaining * share).quantize(Decimal("0.01"))
                    distributed += amount

                if amount <= 0:
                    continue

                expense_date = min(
                    month_start + timedelta(days=2 + item_index * 4),
                    period_end,
                )
                Expense.objects.create(
                    company=company,
                    description=f"{description} — {month_start:%m.%Y}",
                    amount=amount,
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
                    teacher=group.teacher,
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
        for group_index, group in enumerate(groups, start=1):
            for month_number in range(1, 5):
                month_start = group.start_date + timedelta(
                    days=(month_number - 1) * 30
                )
                month_end = month_start + timedelta(days=30)
                completed = month_end <= today

                # Base pay per group stays modest; the automatic percentage
                # is calculated separately from actual group revenue.
                base_salary = Decimal(
                    str(9000 + group_index * 1000 + (month_number - 1) * 500)
                )

                GroupMonth.objects.create(
                    group=group,
                    month_number=month_number,
                    teacher_salary=base_salary,
                    status=(
                        GroupMonth.Status.COMPLETED
                        if completed
                        else GroupMonth.Status.PENDING
                    ),
                    completed_at=(
                        self._at_date(month_end, 18)
                        if completed
                        else None
                    ),
                )

    def _create_salary_records(
        self,
        *,
        company,
        managers,
        teachers,
        groups,
        start_date,
        today,
    ):
        current_month = date(today.year, today.month, 1)
        months = self._month_starts(start_date, today)

        for employee in [*managers, *teachers]:
            joined_month = date(
                employee.date_joined.year,
                employee.date_joined.month,
                1,
            )
            employee_months = [
                month_start
                for month_start in months
                if month_start >= joined_month
            ]

            for month_index, month_start in enumerate(employee_months):
                is_current = month_start == current_month
                base_salary = employee.salary_rate or Decimal("0")
                percent_amount = Decimal("0")
                bonus_amount = Decimal("0")

                if employee.role == User.Role.TEACHER:
                    teaching_groups = [
                        group
                        for group in groups
                        if group.teacher_id == employee.id and group.course
                    ]
                    for group in teaching_groups:
                        teacher_percent = group.teacher_percent or Decimal("0")
                        if teacher_percent <= 0:
                            continue

                        student_count = group.students.filter(
                            created_at__date__lte=(
                                month_start + relativedelta(months=1) - timedelta(days=1)
                            )
                        ).count()
                        if student_count <= 0:
                            continue

                        percent_amount += (
                            group.course.price
                            * Decimal(student_count)
                            * teacher_percent
                            / Decimal("100")
                        )

                    # Small performance bonus in some completed months.
                    if not is_current and (month_index + employee.id) % 3 == 0:
                        bonus_amount = Decimal("5000")

                elif employee.role == User.Role.MANAGER:
                    if not is_current and (month_index + employee.id) % 4 == 0:
                        bonus_amount = Decimal("3000")

                paid_at = None
                status = SalaryRecord.Status.PENDING
                if not is_current:
                    next_month = month_start + relativedelta(months=1)
                    paid_at = next_month - timedelta(days=5)
                    status = SalaryRecord.Status.PAID

                record = SalaryRecord.objects.create(
                    company=company,
                    employee=employee,
                    year=month_start.year,
                    month=month_start.month,
                    base_salary=base_salary,
                    percent_amount=percent_amount.quantize(Decimal("0.01")),
                    bonus_amount=bonus_amount,
                    status=status,
                    paid_at=paid_at,
                    note=(
                        "Фиксированная ставка + процент от групп"
                        if employee.role == User.Role.TEACHER
                        else "Фиксированная зарплата менеджера"
                    ),
                )

                if status == SalaryRecord.Status.PAID and paid_at:
                    Expense.objects.create(
                        company=company,
                        description=(
                            f"Зарплата сотрудника #{record.id}: "
                            f"{employee.get_full_name() or employee.username} — "
                            f"{month_start:%m.%Y}"
                        ),
                        amount=record.total_amount,
                        category="salary",
                        date=paid_at,
                    )

    def _create_finance_reporting(self, *, company, start_date, today):
        from calendar import monthrange
        from django.db.models import Sum

        months = self._month_starts(start_date, today)

        for month_start in months:
            last_day = date(
                month_start.year,
                month_start.month,
                monthrange(month_start.year, month_start.month)[1],
            )
            period_end = min(last_day, today)

            income = (
                Payment.objects.filter(
                    company=company,
                    status=Payment.Status.PAID,
                    paid_at__gte=month_start,
                    paid_at__lte=period_end,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )
            regular_expenses = (
                Expense.objects.filter(
                    company=company,
                    date__gte=month_start,
                    date__lte=period_end,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )
            salaries = (
                Expense.objects.filter(
                    company=company,
                    category="salary",
                    date__gte=month_start,
                    date__lte=period_end,
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )

            total_expenses = regular_expenses
            students_count = (
                Payment.objects.filter(
                    company=company,
                    paid_at__gte=month_start,
                    paid_at__lte=period_end,
                )
                .values("student_id")
                .distinct()
                .count()
            )
            groups_count = (
                Payment.objects.filter(
                    company=company,
                    paid_at__gte=month_start,
                    paid_at__lte=period_end,
                )
                .values("group_id")
                .distinct()
                .count()
            )

            MonthlySummary.objects.update_or_create(
                company=company,
                year=month_start.year,
                month=month_start.month,
                defaults={
                    "total_income": income,
                    "total_expenses": total_expenses,
                    "total_salaries": salaries,
                    "net_profit": income - total_expenses,
                    "total_students": students_count,
                    "total_groups": groups_count,
                },
            )

        current_month = date(today.year, today.month, 1)
        current_month_end = date(
            today.year,
            today.month,
            monthrange(today.year, today.month)[1],
        )
        budget_specs = [
            (BudgetCategory.RENT, Decimal("80000")),
            (BudgetCategory.UTILITIES, Decimal("22000")),
            (BudgetCategory.MARKETING, Decimal("40000")),
            (BudgetCategory.MATERIALS, Decimal("20000")),
            (BudgetCategory.SALARY, Decimal("180000")),
        ]
        for category, amount in budget_specs:
            Budget.objects.create(
                company=company,
                category=category,
                amount=amount,
                period_start=current_month,
                period_end=current_month_end,
                is_active=True,
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
            balance=0,
        )

        for index, month_start in enumerate(
            self._month_starts(start_date, today),
            start=1,
        ):
            Transaction.objects.create(
                company=company,
                amount=5000 + index * 500,
                reason=f"Пополнение баланса {month_start:%m.%Y}",
                transaction_type=Transaction.Type.DEPOSIT,
            )
            if index % 2 == 0:
                Transaction.objects.create(
                    company=company,
                    amount=-1000,
                    reason=f"Продвижение {month_start:%m.%Y}",
                    transaction_type=Transaction.Type.WITHDRAWAL,
                )
