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
    Course,
    Expense,
    Group,
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

        self.stdout.write(self.style.SUCCESS("Demo database seeded successfully."))
        self.stdout.write("")
        self.stdout.write("Demo login:")
        self.stdout.write("  username: demo_admin")
        self.stdout.write("  password: Demo1234!")
        self.stdout.write("")
        self.stdout.write(
            f"Created/updated: {len(courses)} courses, {len(groups)} groups, "
            f"{len(students)} students, {len(teachers)} teachers, "
            f"{len(managers)} managers."
        )
