from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import (
    Attendance,
    Auditorium,
    Company,
    CompanyBalance,
    CompanyCategory,
    CompanyCity,
    Contract,
    Course,
    Expense,
    Group,
    GroupMonth,
    HomeworkSubmission,
    HomeworkTask,
    JobVacancy,
    LeadAssignment,
    Payment,
    PromoBalance,
    PromoCode,
    PublicCourse,
    Student,
    Task,
    TrialLead,
    User,
)


class Command(BaseCommand):
    help = "Seed the local database with a complete, reusable CRM demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Explicitly allow running outside DEBUG mode.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError(
                "Refusing to seed demo data while DEBUG=False. "
                "Use --allow-production only if you really intend to."
            )

        today = timezone.localdate()
        now = timezone.now()

        admin, _ = User.objects.get_or_create(
            username="demo_admin",
            defaults={
                "role": User.Role.COURSE_ADMIN,
                "first_name": "Аман",
                "last_name": "Админ",
                "email": "admin@demo.local",
                "is_active": True,
                "max_managers": 10,
            },
        )
        admin.role = User.Role.COURSE_ADMIN
        admin.is_active = True
        admin.must_set_password = False
        admin.set_password("Demo1234!")
        admin.save()

        company, _ = Company.objects.update_or_create(
            slug="demo-osh-academy",
            defaults={
                "name": "Demo Ош Академия",
                "description": "Демо учебный центр для локальной разработки CRM.",
                "category": CompanyCategory.IT,
                "city": CompanyCity.OSH,
                "district": "Центр",
                "phone": "+996 700 100 100",
                "telegram": "@demo_osh",
                "instagram": "@demo_osh_academy",
                "owner": admin,
                "is_active": True,
                "rating": Decimal("4.80"),
                "reviews_count": 42,
            },
        )
        admin.company = company
        admin.save(update_fields=["company"])

        managers = []
        for index, data in enumerate(
            [
                ("demo_manager_1", "Айбек", "Токтосунов"),
                ("demo_manager_2", "Нурия", "Абдыкадырова"),
            ],
            start=1,
        ):
            username, first_name, last_name = data
            manager, _ = User.objects.get_or_create(
                username=username,
                defaults={"role": User.Role.MANAGER},
            )
            manager.role = User.Role.MANAGER
            manager.first_name = first_name
            manager.last_name = last_name
            manager.phone = f"+996 700 200 10{index}"
            manager.company = company
            manager.created_by = admin
            manager.is_active = True
            manager.must_set_password = False
            manager.set_password("Demo1234!")
            manager.save()
            managers.append(manager)

        teachers = []
        for index, data in enumerate(
            [
                ("demo_teacher_1", "Эрмек", "Садыков"),
                ("demo_teacher_2", "Алина", "Жумабаева"),
                ("demo_teacher_3", "Бекзат", "Осмонов"),
            ],
            start=1,
        ):
            username, first_name, last_name = data
            teacher, _ = User.objects.get_or_create(
                username=username,
                defaults={"role": User.Role.TEACHER},
            )
            teacher.role = User.Role.TEACHER
            teacher.first_name = first_name
            teacher.last_name = last_name
            teacher.phone = f"+996 700 300 10{index}"
            teacher.company = company
            teacher.created_by = admin
            teacher.salary_rate = Decimal("35000.00") + index * 2500
            teacher.working_hours = "09:00–18:00"
            teacher.is_active = True
            teacher.must_set_password = False
            teacher.set_password("Demo1234!")
            teacher.save()
            teachers.append(teacher)

        courses = []
        course_specs = [
            ("Frontend React", "18000.00", 16, 90, "React, TypeScript, Next.js"),
            ("Python Django", "20000.00", 20, 90, "Python, Django, REST API"),
            ("UI/UX Design", "16000.00", 12, 80, "Figma жана продукт дизайн"),
        ]
        for title, price, weeks, lesson_minutes, description in course_specs:
            course, _ = Course.objects.get_or_create(
                title=title,
                defaults={
                    "price": Decimal(price),
                    "duration_weeks": weeks,
                    "lesson_duration_minutes": lesson_minutes,
                    "description": description,
                    "schedule": "Дүйшөмбү / Шаршемби / Жума",
                },
            )
            course.price = Decimal(price)
            course.duration_weeks = weeks
            course.lesson_duration_minutes = lesson_minutes
            course.description = description
            course.save()
            course.admins.add(admin)
            courses.append(course)

        teachers[0].teaching_courses.add(courses[0])
        teachers[1].teaching_courses.add(courses[1])
        teachers[2].teaching_courses.add(courses[2])

        auditoriums = []
        for name, number in [
            ("Frontend Room", "101"),
            ("Backend Room", "202"),
            ("Design Studio", "303"),
        ]:
            auditorium, _ = Auditorium.objects.get_or_create(
                company=company,
                name=name,
                defaults={"number": number},
            )
            auditorium.number = number
            auditorium.save(update_fields=["number"])
            auditoriums.append(auditorium)

        groups = []
        group_specs = [
            ("React-01", courses[0], teachers[0], auditoriums[0], "1,3,5", "18:30"),
            ("Django-01", courses[1], teachers[1], auditoriums[1], "2,4,6", "18:00"),
            ("Design-01", courses[2], teachers[2], auditoriums[2], "1,3,5", "16:00"),
        ]
        for name, course, teacher, auditorium, days, time_value in group_specs:
            group, _ = Group.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    "course": course,
                    "teacher": teacher,
                    "auditorium": auditorium,
                    "status": Group.Status.ACTIVE,
                    "schedule_days": days,
                    "schedule_time": time_value,
                    "lessons_count": 36,
                    "lessons_per_month": 12,
                    "total_months": 3,
                    "start_date": today - timedelta(days=20),
                    "end_date": today + timedelta(days=70),
                    "teacher_percent": Decimal("30.00"),
                },
            )
            group.course = course
            group.teacher = teacher
            group.auditorium = auditorium
            group.status = Group.Status.ACTIVE
            group.archived_at = None
            group.save()
            groups.append(group)

        students = []
        first_names = [
            "Айдана", "Нурсултан", "Али", "Мээрим", "Баястан",
            "Диана", "Элдар", "Арууке", "Темирлан", "Сезим",
            "Адилет", "Жанара",
        ]
        last_names = [
            "Абдиева", "Токтогулов", "Осмонов", "Жолдошева",
            "Садыков", "Мамбетова", "Ибраимов", "Касымова",
            "Эргешов", "Асанова", "Турсунов", "Абдыева",
        ]

        for index, (first_name, last_name) in enumerate(
            zip(first_names, last_names),
            start=1,
        ):
            student_user, _ = User.objects.get_or_create(
                username=f"demo_student_{index:02d}",
                defaults={"role": User.Role.STUDENT},
            )
            student_user.role = User.Role.STUDENT
            student_user.first_name = first_name
            student_user.last_name = last_name
            student_user.company = company
            student_user.is_active = True
            student_user.must_set_password = False
            student_user.set_password("Demo1234!")
            student_user.save()

            course = courses[(index - 1) % len(courses)]
            student, _ = Student.objects.update_or_create(
                company=company,
                phone=f"+996 555 10 {index:02d} 01",
                defaults={
                    "user": student_user,
                    "first_name": first_name,
                    "last_name": last_name,
                    "telegram": f"@demo_student_{index:02d}",
                    "primary_course": course,
                    "can_login": True,
                    "notes": "Demo student",
                    "archived_at": None,
                },
            )
            group = groups[(index - 1) % len(groups)]
            group.students.add(student)
            students.append(student)

        attendance_statuses = [
            Attendance.Status.PRESENT,
            Attendance.Status.PRESENT,
            Attendance.Status.ABSENT,
            Attendance.Status.EXCUSED,
        ]
        for day_offset in range(0, 12, 2):
            date_value = today - timedelta(days=day_offset)
            for index, student in enumerate(students):
                group = groups[(index) % len(groups)]
                if not group.students.filter(pk=student.pk).exists():
                    continue
                Attendance.objects.update_or_create(
                    group=group,
                    student=student,
                    date=date_value,
                    defaults={
                        "status": attendance_statuses[
                            (index + day_offset) % len(attendance_statuses)
                        ],
                    },
                )

        for index, student in enumerate(students):
            group = groups[index % len(groups)]
            Payment.objects.update_or_create(
                student=student,
                company=company,
                paid_at=today - timedelta(days=index % 8),
                defaults={
                    "group": group,
                    "amount": Decimal("18000.00") + (index % 3) * 1000,
                    "status": (
                        Payment.Status.PAID
                        if index % 4 != 0
                        else Payment.Status.DEBT
                    ),
                    "due_date": today + timedelta(days=7),
                    "archived_at": None,
                },
            )

        expense_specs = [
            ("Аренда офиса", "rent", "65000.00"),
            ("Интернет жана коммуналдык", "utilities", "12500.00"),
            ("Instagram реклама", "marketing", "18000.00"),
            ("Канцелярия", "materials", "6500.00"),
            ("Ноутбук для класса", "equipment", "78000.00"),
        ]
        for offset, (description, category, amount) in enumerate(expense_specs):
            Expense.objects.update_or_create(
                company=company,
                description=description,
                date=today - timedelta(days=offset * 4),
                defaults={
                    "category": category,
                    "amount": Decimal(amount),
                },
            )

        for index, manager in enumerate(managers):
            Task.objects.update_or_create(
                company=company,
                title=f"Demo задача {index + 1}: обзвон лидов",
                defaults={
                    "description": "Связаться с новыми лидами и обновить статус.",
                    "assigned_to": manager,
                    "created_by": admin,
                    "due_date": today + timedelta(days=index + 1),
                    "status": (
                        Task.Status.IN_PROGRESS
                        if index == 0
                        else Task.Status.PENDING
                    ),
                    "priority": (
                        Task.Priority.HIGH
                        if index == 0
                        else Task.Priority.MEDIUM
                    ),
                    "repeat_type": Task.RepeatType.NONE,
                },
            )

        lead_names = [
            "Эрлан Кубанычбеков",
            "Айпери Маматова",
            "Данияр Абдыкадыров",
            "Жылдыз Сапарова",
            "Бектур Алиев",
            "Наргиза Токтосунова",
        ]
        for index, full_name in enumerate(lead_names):
            lead, _ = TrialLead.objects.update_or_create(
                company=company,
                phone=f"+996 777 40 {index + 1:02d} 02",
                defaults={
                    "full_name": full_name,
                    "age": 18 + index,
                    "course_interest": courses[index % len(courses)].title,
                    "trial_attended": index % 2 == 0,
                    "status": [
                        TrialLead.Status.NEW,
                        TrialLead.Status.CONTACTED,
                        TrialLead.Status.TRIAL_SCHEDULED,
                        TrialLead.Status.ATTENDED,
                        TrialLead.Status.CONVERTED,
                        TrialLead.Status.NEW,
                    ][index],
                    "trial_date": today + timedelta(days=index - 2),
                    "source": "Instagram" if index % 2 == 0 else "Telegram",
                    "comment": "Demo lead",
                    "converted_to_student": index == 4,
                    "group_assigned": groups[index % len(groups)],
                    "payment_status": (
                        TrialLead.PaymentStatus.PAID
                        if index == 4
                        else TrialLead.PaymentStatus.NOT_PAID
                    ),
                },
            )
            if index < len(managers):
                LeadAssignment.objects.update_or_create(
                    lead=lead,
                    defaults={"manager": managers[index]},
                )

        for index, group in enumerate(groups):
            task, _ = HomeworkTask.objects.update_or_create(
                group=group,
                title=f"Demo үй тапшырма {index + 1}",
                defaults={
                    "teacher": group.teacher,
                    "company": company,
                    "lesson_number": index + 4,
                    "description": "Өтүлгөн теманы кайталап, тапшырманы аткарыңыз.",
                    "task_type": HomeworkTask.TaskType.HOMEWORK,
                    "deadline": now + timedelta(days=index + 3),
                    "is_published": True,
                    "allow_late": True,
                },
            )
            group_students = list(group.students.all()[:2])
            for student_index, student in enumerate(group_students):
                HomeworkSubmission.objects.update_or_create(
                    task=task,
                    student=student,
                    defaults={
                        "answer_text": "Demo жооп: тапшырма аткарылды.",
                        "status": (
                            HomeworkSubmission.Status.REVIEWED
                            if student_index == 0
                            else HomeworkSubmission.Status.PENDING
                        ),
                        "grade": 90 if student_index == 0 else None,
                        "teacher_comment": (
                            "Жакшы иш."
                            if student_index == 0
                            else ""
                        ),
                    },
                )

        marketplace_courses = [
            ("React Frontend Bootcamp", "react-frontend-bootcamp", "22000.00"),
            ("Django REST Professional", "django-rest-professional", "24000.00"),
            ("UI UX Starter", "ui-ux-starter", "17000.00"),
        ]
        for index, (title, slug, price) in enumerate(marketplace_courses):
            PublicCourse.objects.update_or_create(
                company=company,
                slug=slug,
                defaults={
                    "title": title,
                    "price": Decimal(price),
                    "duration_weeks": 12 + index * 2,
                    "lesson_duration_minutes": 90,
                    "description": f"{title} — практикалык курс.",
                    "category": CompanyCategory.IT,
                    "city": CompanyCity.OSH,
                    "schedule": "Кечки топ",
                    "requirements": "Ноутбук жана окууга кызыгуу",
                    "curriculum": [
                        {"title": "Модуль 1", "lessons": 6},
                        {"title": "Модуль 2", "lessons": 8},
                    ],
                    "rating": Decimal("4.70") + Decimal(index) / Decimal("10"),
                    "reviews_count": 12 + index * 7,
                    "is_active": True,
                    "views": 120 + index * 80,
                    "applications_count": 8 + index * 5,
                },
            )

        job_specs = [
            ("Junior Frontend Developer", 30000, 50000),
            ("Python Mentor", 35000, 60000),
            ("UI/UX Mentor", 30000, 55000),
        ]
        for index, (title, salary_min, salary_max) in enumerate(job_specs):
            JobVacancy.objects.update_or_create(
                company=company,
                title=title,
                defaults={
                    "description": f"{title} керек. Demo вакансия.",
                    "category": CompanyCategory.IT,
                    "city": CompanyCity.OSH,
                    "district": "Центр",
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "schedule": "Толук күн",
                    "requirements": "Коммерциялык же окуу долбоорлорунун тажрыйбасы",
                    "responsibilities": "Команда менен иштөө жана студенттерге жардам берүү",
                    "is_active": True,
                    "views": 70 + index * 20,
                    "applications": 5 + index * 3,
                },
            )

        for group in groups:
            for month_number in range(1, 4):
                GroupMonth.objects.update_or_create(
                    group=group,
                    month_number=month_number,
                    defaults={
                        "teacher_salary": Decimal("25000.00") + month_number * 1500,
                        "status": (
                            GroupMonth.Status.COMPLETED
                            if month_number == 1
                            else GroupMonth.Status.PENDING
                        ),
                        "completed_at": (
                            now - timedelta(days=10)
                            if month_number == 1
                            else None
                        ),
                    },
                )

        for index, student in enumerate(students[:6], start=1):
            Contract.objects.update_or_create(
                contract_number=f"DEMO-2026-{index:03d}",
                defaults={
                    "company": company,
                    "student": student,
                    "group": groups[(index - 1) % len(groups)],
                    "status": (
                        Contract.Status.SIGNED
                        if index % 2 == 0
                        else Contract.Status.DRAFT
                    ),
                    "amount": Decimal("18000.00") + (index % 3) * 1000,
                    "start_date": today - timedelta(days=20),
                    "end_date": today + timedelta(days=70),
                    "terms": "Demo contract for local CRM development.",
                    "created_by": admin,
                    "signed_at": (
                        now - timedelta(days=5)
                        if index % 2 == 0
                        else None
                    ),
                },
            )

        company_balance, _ = CompanyBalance.objects.get_or_create(
            company=company
        )
        company_balance.balance = 5000
        company_balance.save(update_fields=["balance"])

        promo, _ = PromoCode.objects.update_or_create(
            code="DEMO500",
            defaults={
                "reward_type": PromoCode.RewardType.COINS,
                "reward_value": 500,
                "max_usages": 100,
                "current_usages": 0,
                "is_active": True,
                "created_by": admin,
                "expiry_date": now + timedelta(days=90),
            },
        )
        promo_balance, _ = PromoBalance.objects.get_or_create(
            promo_code=promo
        )
        promo_balance.balance = 50000
        promo_balance.save(update_fields=["balance"])

        # Dedicated E2E company and accounts.
        # These credentials are intentionally deterministic for local automated tests.
        e2e_password = "E2ETest123!"

        e2e_super_admin, _ = User.objects.get_or_create(
            username="e2e_super_admin",
            defaults={"role": User.Role.SUPER_ADMIN},
        )
        e2e_super_admin.role = User.Role.SUPER_ADMIN
        e2e_super_admin.first_name = "E2E"
        e2e_super_admin.last_name = "Super Admin"
        e2e_super_admin.email = "e2e.superadmin@test.local"
        e2e_super_admin.is_active = True
        e2e_super_admin.is_staff = True
        e2e_super_admin.is_superuser = True
        e2e_super_admin.must_set_password = False
        e2e_super_admin.set_password(e2e_password)
        e2e_super_admin.save()

        e2e_course_admin, _ = User.objects.get_or_create(
            username="e2e_course_admin",
            defaults={"role": User.Role.COURSE_ADMIN},
        )
        e2e_course_admin.role = User.Role.COURSE_ADMIN
        e2e_course_admin.first_name = "E2E"
        e2e_course_admin.last_name = "Course Admin"
        e2e_course_admin.email = "e2e.courseadmin@test.local"
        e2e_course_admin.phone = "+996 700 900 001"
        e2e_course_admin.is_active = True
        e2e_course_admin.must_set_password = False
        e2e_course_admin.max_managers = 20
        e2e_course_admin.max_pages = 20
        e2e_course_admin.max_blocks = 20
        e2e_course_admin.set_password(e2e_password)
        e2e_course_admin.save()

        e2e_company, _ = Company.objects.update_or_create(
            slug="e2e-test-academy",
            defaults={
                "name": "E2E Test Academy",
                "description": "Dedicated company for Playwright end-to-end tests.",
                "category": CompanyCategory.IT,
                "city": CompanyCity.OSH,
                "district": "E2E District",
                "phone": "+996 700 900 000",
                "telegram": "@e2e_test_academy",
                "instagram": "@e2e_test_academy",
                "owner": e2e_course_admin,
                "is_active": True,
                "rating": Decimal("5.00"),
                "reviews_count": 1,
            },
        )
        e2e_course_admin.company = e2e_company
        e2e_course_admin.save(update_fields=["company"])

        e2e_admin, _ = User.objects.get_or_create(
            username="e2e_admin",
            defaults={"role": User.Role.ADMIN},
        )
        e2e_admin.role = User.Role.ADMIN
        e2e_admin.first_name = "E2E"
        e2e_admin.last_name = "Admin"
        e2e_admin.email = "e2e.admin@test.local"
        e2e_admin.phone = "+996 700 900 002"
        e2e_admin.company = e2e_company
        e2e_admin.is_active = True
        e2e_admin.must_set_password = False
        e2e_admin.set_password(e2e_password)
        e2e_admin.save()

        e2e_manager, _ = User.objects.get_or_create(
            username="e2e_manager",
            defaults={"role": User.Role.MANAGER},
        )
        e2e_manager.role = User.Role.MANAGER
        e2e_manager.first_name = "E2E"
        e2e_manager.last_name = "Manager"
        e2e_manager.email = "e2e.manager@test.local"
        e2e_manager.phone = "+996 700 900 003"
        e2e_manager.company = e2e_company
        e2e_manager.created_by = e2e_course_admin
        e2e_manager.is_active = True
        e2e_manager.must_set_password = False
        e2e_manager.set_password(e2e_password)
        e2e_manager.save()

        e2e_teacher, _ = User.objects.get_or_create(
            username="e2e_teacher",
            defaults={"role": User.Role.TEACHER},
        )
        e2e_teacher.role = User.Role.TEACHER
        e2e_teacher.first_name = "E2E"
        e2e_teacher.last_name = "Teacher"
        e2e_teacher.email = "e2e.teacher@test.local"
        e2e_teacher.phone = "+996 700 900 004"
        e2e_teacher.company = e2e_company
        e2e_teacher.created_by = e2e_course_admin
        e2e_teacher.salary_rate = Decimal("40000.00")
        e2e_teacher.working_hours = "09:00–18:00"
        e2e_teacher.is_active = True
        e2e_teacher.must_set_password = False
        e2e_teacher.set_password(e2e_password)
        e2e_teacher.save()

        e2e_student_user, _ = User.objects.get_or_create(
            username="e2e_student",
            defaults={"role": User.Role.STUDENT},
        )
        e2e_student_user.role = User.Role.STUDENT
        e2e_student_user.first_name = "E2E"
        e2e_student_user.last_name = "Student"
        e2e_student_user.email = "e2e.student@test.local"
        e2e_student_user.phone = "+996 700 900 005"
        e2e_student_user.company = e2e_company
        e2e_student_user.is_active = True
        e2e_student_user.must_set_password = False
        e2e_student_user.set_password(e2e_password)
        e2e_student_user.save()

        e2e_course, _ = Course.objects.get_or_create(
            title="E2E Frontend Course",
            defaults={
                "price": Decimal("15000.00"),
                "duration_weeks": 12,
                "lesson_duration_minutes": 90,
                "description": "Playwright E2E course.",
                "schedule": "Дүйшөмбү / Шаршемби / Жума",
            },
        )
        e2e_course.price = Decimal("15000.00")
        e2e_course.duration_weeks = 12
        e2e_course.lesson_duration_minutes = 90
        e2e_course.description = "Playwright E2E course."
        e2e_course.schedule = "Дүйшөмбү / Шаршемби / Жума"
        e2e_course.save()
        e2e_course.admins.add(e2e_course_admin)
        e2e_teacher.teaching_courses.add(e2e_course)

        e2e_auditorium, _ = Auditorium.objects.update_or_create(
            company=e2e_company,
            name="E2E Room",
            defaults={"number": "E2E-101"},
        )

        e2e_group, _ = Group.objects.get_or_create(
            company=e2e_company,
            name="E2E-Group-01",
            defaults={
                "course": e2e_course,
                "teacher": e2e_teacher,
                "auditorium": e2e_auditorium,
                "status": Group.Status.ACTIVE,
                "schedule_days": "1,3,5",
                "schedule_time": "10:00",
                "lessons_count": 24,
                "lessons_per_month": 8,
                "total_months": 3,
                "start_date": today - timedelta(days=7),
                "end_date": today + timedelta(days=77),
                "teacher_percent": Decimal("30.00"),
            },
        )
        e2e_group.course = e2e_course
        e2e_group.teacher = e2e_teacher
        e2e_group.auditorium = e2e_auditorium
        e2e_group.status = Group.Status.ACTIVE
        e2e_group.schedule_days = "1,3,5"
        e2e_group.schedule_time = "10:00"
        e2e_group.archived_at = None
        e2e_group.save()

        e2e_student, _ = Student.objects.update_or_create(
            company=e2e_company,
            phone="+996 700 900 005",
            defaults={
                "user": e2e_student_user,
                "first_name": "E2E",
                "last_name": "Student",
                "telegram": "@e2e_student",
                "primary_course": e2e_course,
                "can_login": True,
                "notes": "Dedicated Playwright student.",
                "archived_at": None,
            },
        )
        e2e_group.students.add(e2e_student)

        Attendance.objects.update_or_create(
            group=e2e_group,
            student=e2e_student,
            date=today,
            defaults={"status": Attendance.Status.PRESENT},
        )

        Payment.objects.update_or_create(
            student=e2e_student,
            company=e2e_company,
            paid_at=today,
            defaults={
                "group": e2e_group,
                "amount": Decimal("15000.00"),
                "status": Payment.Status.PAID,
                "due_date": today + timedelta(days=30),
                "archived_at": None,
            },
        )

        Expense.objects.update_or_create(
            company=e2e_company,
            description="E2E test expense",
            date=today,
            defaults={
                "category": "testing",
                "amount": Decimal("1000.00"),
            },
        )

        Task.objects.update_or_create(
            company=e2e_company,
            title="E2E manager task",
            defaults={
                "description": "Task used by Playwright tests.",
                "assigned_to": e2e_manager,
                "created_by": e2e_course_admin,
                "due_date": today + timedelta(days=2),
                "status": Task.Status.PENDING,
                "priority": Task.Priority.MEDIUM,
                "repeat_type": Task.RepeatType.NONE,
            },
        )

        e2e_lead, _ = TrialLead.objects.update_or_create(
            company=e2e_company,
            phone="+996 700 900 006",
            defaults={
                "full_name": "E2E Trial Lead",
                "age": 20,
                "course_interest": e2e_course.title,
                "trial_attended": False,
                "status": TrialLead.Status.NEW,
                "trial_date": today + timedelta(days=1),
                "source": "Playwright",
                "comment": "Dedicated E2E lead.",
                "converted_to_student": False,
                "group_assigned": e2e_group,
                "payment_status": TrialLead.PaymentStatus.NOT_PAID,
            },
        )
        LeadAssignment.objects.update_or_create(
            lead=e2e_lead,
            defaults={"manager": e2e_manager},
        )

        e2e_homework, _ = HomeworkTask.objects.update_or_create(
            group=e2e_group,
            title="E2E Homework",
            defaults={
                "teacher": e2e_teacher,
                "company": e2e_company,
                "lesson_number": 1,
                "description": "Homework used by Playwright tests.",
                "task_type": HomeworkTask.TaskType.HOMEWORK,
                "deadline": now + timedelta(days=7),
                "is_published": True,
                "allow_late": True,
            },
        )
        HomeworkSubmission.objects.update_or_create(
            task=e2e_homework,
            student=e2e_student,
            defaults={
                "answer_text": "E2E homework answer.",
                "status": HomeworkSubmission.Status.PENDING,
                "grade": None,
                "teacher_comment": "",
            },
        )

        PublicCourse.objects.update_or_create(
            company=e2e_company,
            slug="e2e-frontend-course",
            defaults={
                "title": "E2E Marketplace Course",
                "price": Decimal("15000.00"),
                "duration_weeks": 12,
                "lesson_duration_minutes": 90,
                "description": "Marketplace course used by Playwright tests.",
                "category": CompanyCategory.IT,
                "city": CompanyCity.OSH,
                "schedule": "10:00",
                "requirements": "E2E only",
                "curriculum": [{"title": "E2E Module", "lessons": 2}],
                "rating": Decimal("5.00"),
                "reviews_count": 1,
                "is_active": True,
                "views": 1,
                "applications_count": 0,
            },
        )

        JobVacancy.objects.update_or_create(
            company=e2e_company,
            title="E2E Frontend Developer",
            defaults={
                "description": "E2E vacancy used by Playwright tests.",
                "category": CompanyCategory.IT,
                "city": CompanyCity.OSH,
                "district": "E2E District",
                "salary_min": 30000,
                "salary_max": 50000,
                "schedule": "Толук күн",
                "requirements": "E2E only",
                "responsibilities": "Run automated tests.",
                "is_active": True,
                "views": 1,
                "applications": 0,
            },
        )

        for month_number in range(1, 4):
            GroupMonth.objects.update_or_create(
                group=e2e_group,
                month_number=month_number,
                defaults={
                    "teacher_salary": Decimal("12000.00"),
                    "status": (
                        GroupMonth.Status.COMPLETED
                        if month_number == 1
                        else GroupMonth.Status.PENDING
                    ),
                    "completed_at": now if month_number == 1 else None,
                },
            )

        Contract.objects.update_or_create(
            contract_number="E2E-CONTRACT-001",
            defaults={
                "company": e2e_company,
                "student": e2e_student,
                "group": e2e_group,
                "status": Contract.Status.SIGNED,
                "amount": Decimal("15000.00"),
                "start_date": today,
                "end_date": today + timedelta(days=90),
                "terms": "Dedicated E2E contract.",
                "created_by": e2e_course_admin,
                "signed_at": now,
            },
        )

        e2e_balance, _ = CompanyBalance.objects.get_or_create(
            company=e2e_company
        )
        e2e_balance.balance = 10000
        e2e_balance.save(update_fields=["balance"])

        self.stdout.write(self.style.SUCCESS("Demo database seeded successfully."))
        self.stdout.write("")
        self.stdout.write("Demo login:")
        self.stdout.write("  username: demo_admin")
        self.stdout.write("  password: Demo1234!")
        self.stdout.write("")
        self.stdout.write("E2E Test Academy logins:")
        self.stdout.write("  e2e_super_admin / E2ETest123!")
        self.stdout.write("  e2e_admin / E2ETest123!")
        self.stdout.write("  e2e_course_admin / E2ETest123!")
        self.stdout.write("  e2e_manager / E2ETest123!")
        self.stdout.write("  e2e_teacher / E2ETest123!")
        self.stdout.write("  e2e_student / E2ETest123!")
        self.stdout.write("")
        self.stdout.write(
            f"Created/updated: {len(courses)} courses, {len(groups)} groups, "
            f"{len(students)} students, {len(teachers)} teachers, "
            f"{len(managers)} managers."
        )
