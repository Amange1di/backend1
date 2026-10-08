from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .accounts import User
from .applications import ApplicationStatus


class CompanyCategory(models.TextChoices):
    IT = "it", "IT"
    LANGUAGES = "languages", "Языки"
    CRAFTS = "crafts", "Ручная работа"
    SPORTS = "sports", "Спорт"
    MUSIC = "music", "Музыка"
    BUSINESS = "business", "Бизнес"
    OTHER = "other", "Другое"

class CompanyCity(models.TextChoices):
    BISHKEK = "Бишкек", "Бишкек"
    OSH = "Ош", "Ош"
    TALAS = "Талас", "Талас"
    NARYN = "Нарын", "Нарын"
    JALAL_ABAD = "Джалал-Абад", "Джалал-Абад"
    KARAKOL = "Каракол", "Каракол"
    ONLINE = "Онлайн", "Онлайн"

class Company(models.Model):
    """Public company profile for marketplace"""
    
    name = models.CharField(max_length=200, verbose_name="Company Name")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Slug")
    logo = models.ImageField(
        upload_to="companies/logos/",
        blank=True,
        null=True,
        verbose_name="Logo"
    )
    description = models.TextField(verbose_name="Description")
    category = models.CharField(
        max_length=20,
        choices=CompanyCategory.choices,
        verbose_name="Category"
    )
    city = models.CharField(
        max_length=20,
        choices=CompanyCity.choices,
        verbose_name="City"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="District"
    )
    phone = models.CharField(max_length=50, blank=True, verbose_name="Phone")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    whatsapp = models.CharField(max_length=100, blank=True, verbose_name="WhatsApp")
    website = models.URLField(blank=True, verbose_name="Website")
    instagram = models.CharField(max_length=100, blank=True, verbose_name="Instagram")
    facebook = models.CharField(max_length=100, blank=True, verbose_name="Facebook")
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name="Rating"
    )
    reviews_count = models.PositiveIntegerField(default=0, verbose_name="Reviews Count")
    
    # Admin user who owns this company
    owner = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="companies",
        limit_choices_to={"role": User.Role.COURSE_ADMIN}
    )
    
    branch_limit = models.PositiveIntegerField(default=1, verbose_name="Branch limit")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "company"
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class JobVacancy(models.Model):
    """Job vacancy posted by companies"""
    
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="vacancies"
    )
    title = models.CharField(max_length=200, verbose_name="Position Title")
    description = models.TextField(verbose_name="Description")
    category = models.CharField(
        max_length=20,
        choices=CompanyCategory.choices,
        verbose_name="Category"
    )
    city = models.CharField(
        max_length=20,
        choices=CompanyCity.choices,
        verbose_name="City"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="District"
    )
    salary_min = models.PositiveIntegerField(null=True, blank=True, verbose_name="Min Salary")
    salary_max = models.PositiveIntegerField(null=True, blank=True, verbose_name="Max Salary")
    schedule = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Work Schedule"
    )
    requirements = models.TextField(blank=True, verbose_name="Requirements")
    responsibilities = models.TextField(blank=True, verbose_name="Responsibilities")
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_promoted = models.BooleanField(default=False, help_text="Продвигается ли вакансия (TOP)")
    promoted_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты продвигается")
    is_urgent = models.BooleanField(default=False, help_text="Срочный бейдж")
    urgent_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты бейдж")
    views = models.PositiveIntegerField(default=0, verbose_name="Views")
    applications = models.PositiveIntegerField(default=0, verbose_name="Applications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Job Vacancy"
        verbose_name_plural = "Job Vacancies"
        ordering = ["-is_promoted", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} at {self.company.name}"

class PublicCourse(models.Model):
    """Public course offered by companies"""
    
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="courses"
    )
    title = models.CharField(max_length=200, verbose_name="Course Title")
    slug = models.SlugField(max_length=150, verbose_name="Slug")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price"
    )
    duration_weeks = models.PositiveIntegerField(verbose_name="Duration (weeks)")
    lesson_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Lesson Duration (minutes)"
    )
    description = models.TextField(verbose_name="Description")
    category = models.CharField(
        max_length=20,
        choices=CompanyCategory.choices,
        verbose_name="Category"
    )
    city = models.CharField(
        max_length=20,
        choices=CompanyCity.choices,
        verbose_name="City"
    )
    schedule = models.TextField(blank=True, verbose_name="Schedule")
    requirements = models.TextField(blank=True, verbose_name="Requirements")
    
    # Course materials
    curriculum = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Curriculum",
        help_text="List of lessons/modules"
    )
    
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name="Rating"
    )
    reviews_count = models.PositiveIntegerField(default=0, verbose_name="Reviews Count")
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_promoted = models.BooleanField(default=False, help_text="Продвигается ли курс (TOP)")
    promoted_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты продвигается")
    is_urgent = models.BooleanField(default=False, help_text="Срочный бейдж")
    urgent_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты бейдж")
    image = models.ImageField(
        upload_to="courses/images/",
        blank=True,
        null=True,
        verbose_name="Course Image"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="Views")
    applications_count = models.PositiveIntegerField(default=0, verbose_name="Applications Count")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Public Course"
        verbose_name_plural = "Public Courses"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while PublicCourse.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class CourseApplication(models.Model):
    """Application for a course by students"""
    
    course = models.ForeignKey(
        "PublicCourse",
        on_delete=models.CASCADE,
        related_name="applications"
    )
    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    phone = models.CharField(max_length=50, verbose_name="Phone")
    email = models.EmailField(blank=True, verbose_name="Email")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Age")
    experience_level = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Experience Level"
    )
    learning_goal = models.TextField(blank=True, verbose_name="Learning Goal")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course Application"
        verbose_name_plural = "Course Applications"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.full_name} - {self.course.title}"


# === Marketplace Monetization Models ===
